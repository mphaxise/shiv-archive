#!/usr/bin/env python3
"""Update placeholder article URLs by matching titles from an author page HTML dump."""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
import unicodedata
from pathlib import Path

BASE_URL = "https://www.newindianexpress.com"


def to_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def normalize_title(title: str) -> str:
    cleaned = to_ascii(title).lower()
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_title_links(html_text: str) -> dict[str, str]:
    anchors = re.findall(
        r"""<a\b[^>]*href=(['"])(.*?)\1[^>]*>(.*?)</a>""",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    title_to_url: dict[str, str] = {}

    for _, href, inner_html in anchors:
        href = html.unescape(href).strip()
        if not href:
            continue
        if href.startswith("/"):
            full_url = f"{BASE_URL}{href}"
        elif href.startswith("http://") or href.startswith("https://"):
            full_url = href
        else:
            continue

        if "newindianexpress.com" not in full_url:
            continue

        text = html.unescape(re.sub(r"<[^>]+>", " ", inner_html))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 12:
            continue

        norm = normalize_title(text)
        if not norm:
            continue

        if norm not in title_to_url:
            title_to_url[norm] = full_url

    return title_to_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-path", required=True, help="Path to saved author page HTML.")
    parser.add_argument(
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Path to SQLite DB.",
    )
    args = parser.parse_args()

    html_path = Path(args.html_path)
    db_path = Path(args.db_path)

    html_text = html_path.read_text(encoding="utf-8", errors="ignore")
    title_links = extract_title_links(html_text)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    updated = 0
    unresolved = 0

    rows = cur.execute(
        """
        SELECT id, title, canonical_url
        FROM articles
        ORDER BY published_at DESC
        """
    ).fetchall()

    for row in rows:
        article_id = row["id"]
        title = row["title"]
        current_url = row["canonical_url"]

        if current_url.startswith("http://") or current_url.startswith("https://"):
            continue

        norm_title = normalize_title(title)
        matched_url = title_links.get(norm_title)
        if not matched_url:
            unresolved += 1
            continue

        cur.execute(
            "UPDATE articles SET canonical_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (matched_url, article_id),
        )
        updated += 1

    conn.commit()

    print(f"Candidate links in HTML: {len(title_links)}")
    print(f"Articles updated with real URLs: {updated}")
    print(f"Articles still unresolved: {unresolved}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
