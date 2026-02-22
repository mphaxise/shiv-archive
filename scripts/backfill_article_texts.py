#!/usr/bin/env python3
"""Backfill full article text into master DB in small batches."""

from __future__ import annotations

import argparse
import re
import sqlite3
from html import unescape
from pathlib import Path
from time import sleep

import requests


def sanitize_text(text: str) -> str:
    cleaned = re.sub(r"(?is)<[^>]+>", " ", text)
    cleaned = unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def pick_html_block(html: str) -> str:
    for tag in ("article", "main"):
        match = re.search(rf"(?is)<{tag}\b[^>]*>(.*?)</{tag}>", html)
        if match:
            return match.group(1)
    body = re.search(r"(?is)<body\b[^>]*>(.*?)</body>", html)
    if body:
        return body.group(1)
    return html


def extract_article_text(html: str) -> str:
    block = pick_html_block(html)
    paragraphs = re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", block)
    parts: list[str] = []
    for paragraph in paragraphs:
        line = sanitize_text(paragraph)
        if len(line) < 40:
            continue
        lowered = line.lower()
        if lowered.startswith(("read also", "also read", "follow us", "for more updates")):
            continue
        if "copyright" in lowered and len(line) < 140:
            continue
        parts.append(line)

    if not parts:
        return ""

    # Deduplicate adjacent repeated paragraphs seen on some templates.
    unique_parts: list[str] = []
    previous = ""
    for part in parts:
        if part == previous:
            continue
        unique_parts.append(part)
        previous = part

    return "\n\n".join(unique_parts).strip()


def fetch_html(url: str, timeout: int, retries: int) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if response.status_code == 200 and response.text:
                return response.text
        except Exception:
            pass
        if attempt < retries:
            sleep(1.0 + attempt * 0.5)
    return None


def update_article_text(
    cur: sqlite3.Cursor,
    article_uid: str,
    source_url: str,
    text: str,
) -> None:
    words = len(text.split())
    text_state = "full" if words >= 250 else ("partial" if words > 0 else "missing")
    existing = cur.execute(
        """
        SELECT id
        FROM article_texts
        WHERE article_uid = ? AND is_primary = 1
        LIMIT 1
        """,
        (article_uid,),
    ).fetchone()

    if existing:
        cur.execute(
            """
            UPDATE article_texts
            SET
                body_text = ?,
                text_state = ?,
                text_format = 'plain',
                word_count = ?,
                language = 'en',
                extraction_method = 'html_paragraph_extract_v1',
                extraction_model = NULL,
                source_url = ?,
                extracted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (text if text else None, text_state, words if words else None, source_url, int(existing["id"])),
        )
    else:
        cur.execute(
            """
            INSERT INTO article_texts (
                article_uid,
                body_text,
                text_state,
                text_format,
                word_count,
                language,
                extraction_method,
                extraction_model,
                source_url,
                extracted_at,
                is_primary
            )
            VALUES (?, ?, ?, 'plain', ?, 'en', 'html_paragraph_extract_v1', NULL, ?, CURRENT_TIMESTAMP, 1)
            """,
            (article_uid, text if text else None, text_state, words if words else None, source_url),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_master.db",
        help="Path to master DB.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of URLs per batch.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=25,
        help="HTTP timeout per request (seconds).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per URL on failure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview updates without writing.",
    )
    args = parser.parse_args()

    db_path = Path(args.master_db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            a.article_uid,
            a.canonical_url,
            a.title,
            COALESCE(t.text_state, 'missing') AS text_state
        FROM articles a
        LEFT JOIN article_texts t
            ON t.article_uid = a.article_uid
           AND t.is_primary = 1
        WHERE a.status IN ('verified', 'published')
          AND (a.canonical_url LIKE 'http://%' OR a.canonical_url LIKE 'https://%')
          AND (
                t.article_uid IS NULL
             OR t.text_state <> 'full'
             OR t.body_text IS NULL
             OR TRIM(t.body_text) = ''
          )
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()

    batch_size = max(1, int(args.batch_size))
    total = len(rows)
    if total == 0:
        print("No pending article text backfill rows.")
        conn.close()
        return 0

    updated = 0
    skipped = 0
    failed = 0

    for offset in range(0, total, batch_size):
        batch = rows[offset : offset + batch_size]
        batch_no = (offset // batch_size) + 1
        batch_total = (total + batch_size - 1) // batch_size
        print(f"Batch {batch_no}/{batch_total} | size={len(batch)}")

        for row in batch:
            article_uid = str(row["article_uid"])
            url = str(row["canonical_url"])
            html = fetch_html(url, timeout=int(args.timeout), retries=int(args.retries))
            if not html:
                failed += 1
                print(f"  - FAIL  {article_uid} | {url}")
                continue

            body_text = extract_article_text(html)
            words = len(body_text.split()) if body_text else 0
            state = "full" if words >= 250 else ("partial" if words > 0 else "missing")
            print(f"  - TEXT  {article_uid} | words={words} | state={state}")

            if args.dry_run:
                if words > 0:
                    updated += 1
                else:
                    skipped += 1
                continue

            update_article_text(cur, article_uid, url, body_text)
            if words > 0:
                updated += 1
            else:
                skipped += 1

        if not args.dry_run:
            conn.commit()

    print(f"Candidates: {total}")
    print(f"Updated rows: {updated}")
    print(f"Skipped (empty extraction): {skipped}")
    print(f"Failed fetches: {failed}")
    print(f"Master DB path: {db_path}")
    if args.dry_run:
        print("Dry run: no DB changes committed.")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
