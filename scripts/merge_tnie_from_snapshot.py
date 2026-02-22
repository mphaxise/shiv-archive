#!/usr/bin/env python3
"""Merge missing TNIE records from a snapshot DB into current multi-source corpus."""

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


def get_tnie_pub_id(cur: sqlite3.Cursor) -> int:
    row = cur.execute(
        """
        SELECT id
        FROM publications
        WHERE lower(name) = lower('The New Indian Express')
           OR base_url LIKE 'https://www.newindianexpress.com%'
        ORDER BY id
        LIMIT 1
        """
    ).fetchone()
    if row:
        return int(row[0])

    cur.execute(
        """
        INSERT INTO publications (name, base_url)
        VALUES ('The New Indian Express', 'https://www.newindianexpress.com')
        """
    )
    return int(cur.lastrowid)


def ensure_tag(cur: sqlite3.Cursor, name: str, slug: str, domain: str) -> int:
    row = cur.execute("SELECT id FROM tags WHERE slug = ? LIMIT 1", (slug,)).fetchone()
    if row:
        return int(row[0])

    cur.execute(
        """
        INSERT INTO tags (name, slug, domain, description, is_seed)
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            name,
            slug,
            domain,
            "Merged from TNIE snapshot during corpus restoration.",
        ),
    )
    return int(cur.lastrowid)


def build_current_indexes(cur: sqlite3.Cursor) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    rows = cur.execute(
        """
        SELECT id, canonical_url, normalized_title, published_at
        FROM articles
        """
    ).fetchall()

    by_url: dict[str, int] = {}
    by_key: dict[tuple[str, str], int] = {}

    for row in rows:
        article_id = int(row["id"])
        url = str(row["canonical_url"] or "").strip()
        if url:
            by_url[url] = article_id
        key = (str(row["normalized_title"] or ""), str(row["published_at"] or ""))
        by_key[key] = article_id

    return by_url, by_key


def fetch_snapshot_tnie_rows(cur: sqlite3.Cursor) -> list[sqlite3.Row]:
    return cur.execute(
        """
        SELECT
            a.id,
            a.external_id,
            a.canonical_url,
            a.section,
            a.title,
            a.normalized_title,
            a.author_name,
            a.published_at,
            a.reading_minutes,
            a.summary,
            a.tone,
            a.summary_method,
            a.summary_model,
            a.retrieval_method,
            a.source_capture_date,
            a.provenance_note,
            a.status
        FROM articles a
        JOIN publications p ON p.id = a.publication_id
        WHERE p.base_url LIKE 'https://www.newindianexpress.com%'
           OR lower(p.name) = lower('The New Indian Express')
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()


def fetch_snapshot_tags(cur: sqlite3.Cursor) -> dict[int, list[sqlite3.Row]]:
    rows = cur.execute(
        """
        SELECT
            at.article_id,
            t.name,
            t.slug,
            t.domain,
            at.confidence,
            at.method
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_id ASC, t.slug ASC
        """
    ).fetchall()

    out: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        out.setdefault(int(row["article_id"]), []).append(row)
    return out


def fetch_snapshot_notes(cur: sqlite3.Cursor) -> dict[int, list[sqlite3.Row]]:
    rows = cur.execute(
        """
        SELECT article_id, note_type, body
        FROM article_notes
        ORDER BY article_id ASC, id ASC
        """
    ).fetchall()
    out: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        out.setdefault(int(row["article_id"]), []).append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Current target DB path.",
    )
    parser.add_argument(
        "--snapshot-db-path",
        default="/Users/praneet/shiv-archive/data/snapshots/shiv_opinions_v0_20260222T204026Z.db",
        help="Snapshot DB path containing complete TNIE corpus.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Rows per transaction batch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without writing changes.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    snapshot_db_path = Path(args.snapshot_db_path)

    current = sqlite3.connect(db_path)
    current.row_factory = sqlite3.Row
    ccur = current.cursor()

    snap = sqlite3.connect(snapshot_db_path)
    snap.row_factory = sqlite3.Row
    scur = snap.cursor()

    tnie_pub_id = get_tnie_pub_id(ccur)

    current_by_url, current_by_key = build_current_indexes(ccur)
    snapshot_rows = fetch_snapshot_tnie_rows(scur)
    snapshot_tags = fetch_snapshot_tags(scur)
    snapshot_notes = fetch_snapshot_notes(scur)

    missing_rows: list[sqlite3.Row] = []
    matched = 0
    for row in snapshot_rows:
        url = str(row["canonical_url"] or "").strip()
        key = (str(row["normalized_title"] or ""), str(row["published_at"] or ""))
        if url in current_by_url or key in current_by_key:
            matched += 1
            continue
        missing_rows.append(row)

    print(f"Snapshot TNIE rows: {len(snapshot_rows)}")
    print(f"Already present in current DB: {matched}")
    print(f"Missing TNIE rows to restore: {len(missing_rows)}")

    if not missing_rows:
        print("No missing TNIE rows detected.")
        current.close()
        snap.close()
        return 0

    restored = 0
    tag_links = 0
    notes_added = 0
    now = datetime.now(UTC).strftime("%Y-%m-%d")

    batches = [missing_rows[i : i + max(args.batch_size, 1)] for i in range(0, len(missing_rows), max(args.batch_size, 1))]

    for idx, batch in enumerate(batches, start=1):
        print(f"Batch {idx}/{len(batches)} | restore rows={len(batch)}")

        if not args.dry_run:
            ccur.execute("BEGIN")

        for row in batch:
            source_article_id = int(row["id"])
            title = str(row["title"])
            published_at = str(row["published_at"])
            source_url = str(row["canonical_url"])
            provenance_note = append_note(
                row["provenance_note"],
                f"Restored from snapshot {snapshot_db_path.name} on {now}.",
            )

            print(f"  - restore {published_at} | {title}")

            if args.dry_run:
                restored += 1
                continue

            ccur.execute(
                """
                INSERT INTO articles (
                    publication_id,
                    external_id,
                    canonical_url,
                    section,
                    title,
                    normalized_title,
                    author_name,
                    published_at,
                    reading_minutes,
                    summary,
                    tone,
                    summary_method,
                    summary_model,
                    retrieval_method,
                    source_capture_date,
                    provenance_note,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tnie_pub_id,
                    row["external_id"],
                    source_url,
                    row["section"],
                    title,
                    row["normalized_title"],
                    row["author_name"],
                    published_at,
                    row["reading_minutes"],
                    row["summary"],
                    row["tone"],
                    row["summary_method"],
                    row["summary_model"],
                    row["retrieval_method"],
                    row["source_capture_date"],
                    provenance_note,
                    row["status"],
                ),
            )
            new_article_id = int(ccur.lastrowid)

            for tag in snapshot_tags.get(source_article_id, []):
                tag_id = ensure_tag(
                    ccur,
                    name=str(tag["name"]),
                    slug=str(tag["slug"]),
                    domain=str(tag["domain"]),
                )
                ccur.execute(
                    """
                    INSERT OR IGNORE INTO article_tags (article_id, tag_id, confidence, method)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        new_article_id,
                        tag_id,
                        float(tag["confidence"]),
                        str(tag["method"]),
                    ),
                )
                if ccur.rowcount == 1:
                    tag_links += 1

            ccur.execute(
                """
                INSERT INTO article_notes (article_id, note_type, body)
                VALUES (?, 'qa', ?)
                """,
                (
                    new_article_id,
                    f"Restored from snapshot {snapshot_db_path.name} on {now}.",
                ),
            )
            notes_added += 1

            for note in snapshot_notes.get(source_article_id, []):
                ccur.execute(
                    """
                    INSERT INTO article_notes (article_id, note_type, body)
                    VALUES (?, ?, ?)
                    """,
                    (
                        new_article_id,
                        str(note["note_type"]),
                        str(note["body"]),
                    ),
                )
                notes_added += 1

            restored += 1

        if not args.dry_run:
            current.commit()

    if not args.dry_run:
        total = ccur.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        tnie_total = ccur.execute(
            "SELECT COUNT(*) FROM articles WHERE canonical_url LIKE 'https://www.newindianexpress.com/%'"
        ).fetchone()[0]
        print(f"Post-merge totals -> all articles: {total}, TNIE: {tnie_total}")

    print(f"Restored rows: {restored}")
    print(f"Tag links added: {tag_links}")
    print(f"Notes inserted: {notes_added}")

    current.close()
    snap.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
