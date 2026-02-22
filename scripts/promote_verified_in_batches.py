#!/usr/bin/env python3
"""Promote draft articles to verified status in controlled batches."""

from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def append_note(existing: str | None, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def fetch_eligible_drafts(cur: sqlite3.Cursor, min_tags: int) -> list[sqlite3.Row]:
    return cur.execute(
        """
        WITH tag_counts AS (
          SELECT article_id, COUNT(DISTINCT tag_id) AS tag_count
          FROM article_tags
          GROUP BY article_id
        )
        SELECT
          a.id,
          a.title,
          a.published_at,
          a.summary_method,
          a.provenance_note,
          COALESCE(tc.tag_count, 0) AS tag_count
        FROM articles a
        LEFT JOIN tag_counts tc ON tc.article_id = a.id
        WHERE a.status = 'draft'
          AND a.canonical_url LIKE 'https://%'
          AND a.summary IS NOT NULL
          AND trim(a.summary) != ''
          AND COALESCE(tc.tag_count, 0) >= ?
        ORDER BY a.published_at DESC, a.id DESC
        """,
        (min_tags,),
    ).fetchall()


def chunked(rows: list[sqlite3.Row], size: int) -> list[list[sqlite3.Row]]:
    return [rows[i : i + size] for i in range(0, len(rows), size)]


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
        help="Rows per verification batch.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Optional cap on records to promote (0 means all eligible).",
    )
    parser.add_argument(
        "--min-tags",
        type=int,
        default=3,
        help="Minimum distinct tag count required for verification.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview eligible rows without writing changes.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = fetch_eligible_drafts(cur, min_tags=max(args.min_tags, 0))
    if args.max_records > 0:
        rows = rows[: args.max_records]

    if not rows:
        print("No eligible draft rows found.")
        conn.close()
        return 0

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    action_note = (
        f"Promoted to verified on {today} after baseline QA checks: "
        "source_url + summary + min_tags."
    )
    qa_note = (
        f"Baseline QA on {today}: status=draft -> verified; "
        f"checks passed (url, summary, min_tags={max(args.min_tags, 0)})."
    )

    print(f"Eligible drafts: {len(rows)}")
    batches = chunked(rows, max(args.batch_size, 1))
    promoted = 0

    for idx, batch in enumerate(batches, start=1):
        print(f"Batch {idx}/{len(batches)}: {len(batch)} records")
        if not args.dry_run:
            cur.execute("BEGIN")

        for row in batch:
            article_id = int(row["id"])
            title = str(row["title"])
            published_at = str(row["published_at"])
            tag_count = int(row["tag_count"])
            summary_method = str(row["summary_method"] or "")

            print(
                f"  - {article_id}: {published_at} | tags={tag_count} | "
                f"summary_method={summary_method} | {title}"
            )

            if args.dry_run:
                continue

            new_provenance = append_note(row["provenance_note"], action_note)
            cur.execute(
                """
                UPDATE articles
                SET
                  status = 'verified',
                  provenance_note = ?,
                  updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_provenance, article_id),
            )

            cur.execute(
                """
                INSERT INTO article_notes (article_id, note_type, body)
                VALUES (?, 'qa', ?)
                """,
                (article_id, qa_note),
            )
            promoted += 1

        if not args.dry_run:
            conn.commit()

    if args.dry_run:
        print("Dry run complete.")
    else:
        counts = cur.execute(
            """
            SELECT
              SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS drafts,
              SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) AS verified
            FROM articles
            """
        ).fetchone()
        print(f"Rows promoted: {promoted}")
        print(f"Current status counts -> draft: {counts['drafts']}, verified: {counts['verified']}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
