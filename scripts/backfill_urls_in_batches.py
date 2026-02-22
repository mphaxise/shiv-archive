#!/usr/bin/env python3
"""Backfill missing TNIE URLs in batches using date+title heuristics."""

from __future__ import annotations

import argparse
import re
import sqlite3
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

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

BASE_URL = "https://www.newindianexpress.com"


def to_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(title: str) -> str:
    lowered = to_ascii(title).lower()
    lowered = lowered.replace("'", "")
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return lowered or "untitled"


def build_opinions_url(title: str, published_at: str) -> str:
    year, month, day = published_at.split("-")
    month_abbr = MONTH_ABBR[month]
    slug = slugify(title)
    return f"{BASE_URL}/opinions/{year}/{month_abbr}/{day}/{slug}"


def append_note(existing: str | None, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def fetch_target_rows(cur: sqlite3.Cursor, rewrite_heuristic: bool) -> list[sqlite3.Row]:
    if rewrite_heuristic:
        return cur.execute(
            """
            SELECT id, title, published_at, section, canonical_url, provenance_note
            FROM articles
            WHERE canonical_url LIKE 'urn:%'
               OR retrieval_method = 'heuristic_url_backfill'
            ORDER BY published_at DESC, id DESC
            """
        ).fetchall()

    return cur.execute(
        """
        SELECT id, title, published_at, section, canonical_url, provenance_note
        FROM articles
        WHERE canonical_url LIKE 'urn:%'
        ORDER BY published_at DESC, id DESC
        """
    ).fetchall()


def chunked(items: list[sqlite3.Row], size: int) -> list[list[sqlite3.Row]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


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
        help="Number of rows per transaction batch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview updates without writing to DB.",
    )
    parser.add_argument(
        "--rewrite-heuristic",
        action="store_true",
        help="Also recompute URLs for rows already filled by heuristic_url_backfill.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = fetch_target_rows(cur, args.rewrite_heuristic)
    if not rows:
        print("No missing URLs detected. Nothing to update.")
        conn.close()
        return 0

    now = datetime.now(UTC).strftime("%Y-%m-%d")
    provenance_note = f"URL backfilled via title+date heuristic on {now}; verify if needed"

    total_updated = 0
    batches = chunked(rows, max(args.batch_size, 1))
    for idx, batch in enumerate(batches, start=1):
        print(f"Batch {idx}/{len(batches)}: {len(batch)} records")
        if not args.dry_run:
            cur.execute("BEGIN")

        for row in batch:
            article_id = int(row["id"])
            title = str(row["title"])
            published_at = str(row["published_at"])
            url = build_opinions_url(title, published_at)
            note = append_note(row["provenance_note"], provenance_note)

            print(f"  - {article_id}: {published_at} -> {url}")
            if not args.dry_run:
                cur.execute(
                    """
                    UPDATE articles
                    SET
                        canonical_url = ?,
                        retrieval_method = 'heuristic_url_backfill',
                        source_capture_date = COALESCE(source_capture_date, ?),
                        provenance_note = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (url, now, note, article_id),
                )
                total_updated += 1

        if not args.dry_run:
            conn.commit()

    if args.dry_run:
        print(f"Dry run complete. Missing URL rows previewed: {len(rows)}")
    else:
        remaining = cur.execute(
            "SELECT COUNT(*) FROM articles WHERE canonical_url LIKE 'urn:%'"
        ).fetchone()[0]
        print(f"Rows updated: {total_updated}")
        print(f"Rows still missing URL: {remaining}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
