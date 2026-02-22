#!/usr/bin/env python3
"""Replace heuristic article summaries with page-derived summaries."""

from __future__ import annotations

import argparse
import re
import sqlite3
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from time import sleep

import requests


class MetaDescriptionParser(HTMLParser):
    """Extract description-related meta tags from HTML head."""

    def __init__(self) -> None:
        super().__init__()
        self.og_description: str | None = None
        self.description: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        content = attr_map.get("content", "").strip()
        if not content:
            return

        prop = attr_map.get("property", "").lower().strip()
        name = attr_map.get("name", "").lower().strip()

        if prop == "og:description" and not self.og_description:
            self.og_description = content
        elif name == "description" and not self.description:
            self.description = content


MONTH_ABBR = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "May",
    "06": "Jun",
    "07": "Jul",
    "08": "Aug",
    "09": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}


def append_note(existing: str | None, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def normalize_summary(text: str) -> str:
    clean = unescape(text).replace("\n", " ").replace("\r", " ")
    clean = " ".join(clean.split())
    return clean.strip()


def extract_summary(html_text: str) -> str | None:
    parser = MetaDescriptionParser()
    parser.feed(html_text)
    candidate = parser.og_description or parser.description
    if not candidate:
        return None
    summary = normalize_summary(candidate)
    if len(summary) < 30:
        return None
    return summary


def fetch_summary(url: str, timeout: int, retries: int) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    attempt = 0
    while attempt <= retries:
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")
            return extract_summary(response.text)
        except Exception:
            if attempt >= retries:
                return None
            sleep(1.0 + attempt * 0.5)
            attempt += 1
    return None


def slug_tokens(text: str) -> set[str]:
    text = unescape(text).lower()
    text = text.replace("'", "")
    parts = re.findall(r"[a-z0-9]+", text)
    return {p for p in parts if len(p) > 2}


def extract_candidate_links(search_html: str) -> list[str]:
    urls = re.findall(r"https://www\.newindianexpress\.com/[A-Za-z0-9\-_/\.]+", search_html)
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        if "/opinion/" in url or "/opinions/" in url or "/magazine/" in url or "/columns/" in url:
            out.append(url.rstrip("/"))
    return out


def resolve_canonical_url_from_search(
    title: str,
    published_at: str,
    section: str,
    timeout: int,
    retries: int,
) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    year, month, day = published_at.split("-")
    month_abbr = MONTH_ABBR[month]
    date_fragment = f"/{year}/{month_abbr}/{day}/"

    query = requests.utils.quote(title)
    search_url = f"https://www.newindianexpress.com/search?q={query}"

    attempt = 0
    while attempt <= retries:
        try:
            response = requests.get(search_url, headers=headers, timeout=timeout, allow_redirects=True)
            if response.status_code != 200:
                raise RuntimeError(f"search HTTP {response.status_code}")
            candidates = extract_candidate_links(response.text)
            if not candidates:
                return None

            title_tok = slug_tokens(title)
            section_l = section.strip().lower()

            scored: list[tuple[int, str]] = []
            for url in candidates:
                score = 0
                lower_url = url.lower()
                if date_fragment.lower() in lower_url:
                    score += 8
                if section_l == "opinion" and ("/opinion/" in lower_url or "/opinions/" in lower_url):
                    score += 3
                if section_l == "columns" and "/columns/" in lower_url:
                    score += 3
                if section_l == "magazine" and "/magazine/" in lower_url:
                    score += 3

                url_slug = lower_url.rsplit("/", 1)[-1]
                shared = len(title_tok.intersection(slug_tokens(url_slug)))
                score += shared

                scored.append((score, url))

            scored.sort(key=lambda item: item[0], reverse=True)
            best_score, best_url = scored[0]
            if best_score <= 4:
                return None
            return best_url
        except Exception:
            if attempt >= retries:
                return None
            sleep(1.0 + attempt * 0.5)
            attempt += 1

    return None


def chunked(rows: list[sqlite3.Row], size: int) -> list[list[sqlite3.Row]]:
    return [rows[i : i + size] for i in range(0, len(rows), size)]


def select_targets(cur: sqlite3.Cursor, only_heuristic: bool, limit: int) -> list[sqlite3.Row]:
    where = "a.canonical_url LIKE 'https://%'"
    if only_heuristic:
        where += " AND a.summary_method = 'heuristic_title'"
    else:
        where += " AND (a.summary_method = 'heuristic_title' OR a.summary LIKE 'Opinion piece by Shiv%')"

    sql = f"""
      SELECT a.id, a.title, a.published_at, a.section, a.canonical_url, a.provenance_note
      FROM articles a
      WHERE {where}
      ORDER BY a.published_at DESC, a.id DESC
    """
    rows = cur.execute(sql).fetchall()
    if limit > 0:
        rows = rows[:limit]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Path to SQLite DB.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Rows per DB transaction.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit on number of target rows (0 means all).",
    )
    parser.add_argument(
        "--only-heuristic",
        action="store_true",
        help="Only process rows with summary_method='heuristic_title'.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=25,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="HTTP retry count per URL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing.",
    )
    parser.add_argument(
        "--resolve-search",
        action="store_true",
        help="Try TNIE search-based canonical URL recovery when direct summary fetch fails.",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(Path(args.db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = select_targets(cur, args.only_heuristic, args.limit)
    if not rows:
        print("No rows matched enrichment criteria.")
        conn.close()
        return 0

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    provenance_marker = f"Summary enriched from page metadata on {today}"
    note_body = (
        f"Summary updated on {today} using page metadata "
        "(og:description/description) from source URL."
    )

    updated = 0
    failed = 0
    skipped = 0
    processed = 0
    resolved_url_updates = 0

    batches = chunked(rows, max(args.batch_size, 1))
    print(f"Target rows: {len(rows)}")
    for index, batch in enumerate(batches, start=1):
        print(f"Batch {index}/{len(batches)}: {len(batch)} records")

        if not args.dry_run:
            cur.execute("BEGIN")

        for row in batch:
            article_id = int(row["id"])
            title = str(row["title"])
            section = str(row["section"] or "Opinion")
            url = str(row["canonical_url"])
            published_at = str(row["published_at"])
            processed += 1

            summary = fetch_summary(url, timeout=max(args.timeout, 5), retries=max(args.retries, 0))
            resolved_url: str | None = None
            if not summary and args.resolve_search:
                resolved_url = resolve_canonical_url_from_search(
                    title=title,
                    published_at=published_at,
                    section=section,
                    timeout=max(args.timeout, 5),
                    retries=max(args.retries, 0),
                )
                if resolved_url and resolved_url != url:
                    summary = fetch_summary(
                        resolved_url, timeout=max(args.timeout, 5), retries=max(args.retries, 0)
                    )

            if not summary:
                failed += 1
                print(f"  - FAIL {article_id} | {published_at} | {title}")
                continue

            if len(summary) < 35:
                skipped += 1
                print(f"  - SKIP {article_id} | summary too short")
                continue

            print(f"  - OK   {article_id} | {published_at} | {title}")
            print(f"      {summary[:150]}{'...' if len(summary) > 150 else ''}")

            if args.dry_run:
                updated += 1
                continue

            provenance_note = append_note(row["provenance_note"], provenance_marker)
            canonical_url = resolved_url if resolved_url else url
            cur.execute(
                """
                UPDATE articles
                SET
                  canonical_url = ?,
                  summary = ?,
                  summary_method = 'meta_description',
                  summary_model = 'tnie-og-description',
                  provenance_note = ?,
                  updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (canonical_url, summary, provenance_note, article_id),
            )
            cur.execute(
                """
                INSERT INTO article_notes (article_id, note_type, body)
                VALUES (?, 'qa', ?)
                """,
                (article_id, note_body),
            )
            if resolved_url and resolved_url != url:
                resolved_url_updates += 1
            updated += 1

        if not args.dry_run:
            conn.commit()

    print(f"Processed: {processed}")
    print(f"Updated: {updated}")
    print(f"Resolved canonical URLs: {resolved_url_updates}")
    print(f"Failed fetch/extract: {failed}")
    print(f"Skipped: {skipped}")

    if not args.dry_run:
        counts = cur.execute(
            """
            SELECT
              SUM(CASE WHEN summary_method = 'meta_description' THEN 1 ELSE 0 END) AS meta_desc,
              SUM(CASE WHEN summary_method = 'manual_curated' THEN 1 ELSE 0 END) AS manual_curated,
              SUM(CASE WHEN summary_method = 'heuristic_title' THEN 1 ELSE 0 END) AS heuristic_left
            FROM articles
            """
        ).fetchone()
        print(
            "Summary method counts -> "
            f"meta_description: {counts['meta_desc']}, "
            f"manual_curated: {counts['manual_curated']}, "
            f"heuristic_title: {counts['heuristic_left']}"
        )

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
