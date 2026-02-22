#!/usr/bin/env python3
"""Import curated Shiv TNIE article JSON into the SQLite corpus."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

DEFAULT_CAPTURE_DATE = "2026-02-22"

DOMAIN_BY_LABEL = {
    "methodology": "sociology",
    "individualism": "sociology",
    "the banal": "sociology",
    "culture": "anthropology",
    "art": "anthropology",
    "memory": "anthropology",
    "knowledge": "anthropology",
    "policy": "policy",
    "politics": "policy",
    "law": "policy",
    "democracy": "policy",
    "university": "policy",
    "anthropocene": "cross_cutting",
    "ecology": "cross_cutting",
    "nationalism": "cross_cutting",
    "peace": "cross_cutting",
    "morality": "cross_cutting",
    "ethics": "cross_cutting",
    "south asia": "cross_cutting",
    "swadeshi": "cross_cutting",
    "innovation": "cross_cutting",
}


def to_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(value: str) -> str:
    value = to_ascii(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "untitled"


def normalize_title(title: str) -> str:
    lowered = to_ascii(title).lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def ensure_tone_column(cur: sqlite3.Cursor) -> None:
    columns = {row[1] for row in cur.execute("PRAGMA table_info(articles)").fetchall()}
    if "tone" not in columns:
        cur.execute("ALTER TABLE articles ADD COLUMN tone TEXT")


def pick_domain(label: str) -> str:
    key = label.strip().lower()
    return DOMAIN_BY_LABEL.get(key, "cross_cutting")


def ensure_tag(cur: sqlite3.Cursor, label: str) -> int:
    name = label.strip()
    if not name:
        raise ValueError("Tag label cannot be blank.")

    row = cur.execute(
        "SELECT id FROM tags WHERE lower(name) = lower(?) LIMIT 1",
        (name,),
    ).fetchone()
    if row:
        return int(row[0])

    slug = slugify(name)
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
            pick_domain(name),
            "Imported from user-curated v1 JSON tags.",
        ),
    )
    return int(cur.lastrowid)


def fallback_urn(title: str, published_at: str) -> str:
    return f"urn:tnie:shiv:{published_at}:{slugify(title)}"


def coerce_records(payload: object) -> list[dict]:
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of article objects.")
    return [row for row in payload if isinstance(row, dict)]


def row_score(row: sqlite3.Row) -> tuple:
    url = str(row["canonical_url"] or "")
    has_https = 1 if url.startswith("https://") else 0
    is_verified = 1 if row["status"] == "verified" else 0
    has_summary = 1 if str(row["summary"] or "").strip() else 0
    has_tone = 1 if str(row["tone"] or "").strip() else 0
    has_external_id = 1 if str(row["external_id"] or "").strip() else 0
    return (has_https, is_verified, has_summary, has_tone, has_external_id, int(row["id"]))


def find_existing_article_id(
    cur: sqlite3.Cursor, normalized: str, published_at: str
) -> int | None:
    row = cur.execute(
        """
        SELECT id
        FROM articles
        WHERE normalized_title = ? AND published_at = ?
        ORDER BY id
        LIMIT 1
        """,
        (normalized, published_at),
    ).fetchone()
    if row:
        return int(row["id"])

    candidates = cur.execute(
        """
        SELECT id, title, canonical_url, status, summary, tone, external_id
        FROM articles
        WHERE published_at = ?
        """,
        (published_at,),
    ).fetchall()

    exact_matches = [
        row for row in candidates if normalize_title(str(row["title"] or "")) == normalized
    ]
    if not exact_matches:
        return None
    return int(max(exact_matches, key=row_score)["id"])


def merge_duplicate_rows(
    cur: sqlite3.Cursor, keeper_id: int, duplicate_id: int, capture_date: str
) -> None:
    keeper = cur.execute(
        """
        SELECT id, external_id, canonical_url, summary, tone, status
        FROM articles
        WHERE id = ?
        """,
        (keeper_id,),
    ).fetchone()
    duplicate = cur.execute(
        """
        SELECT id, external_id, canonical_url, summary, tone, status
        FROM articles
        WHERE id = ?
        """,
        (duplicate_id,),
    ).fetchone()

    if keeper is None or duplicate is None:
        return

    merged_external_id = keeper["external_id"] or duplicate["external_id"]
    keeper_url = str(keeper["canonical_url"] or "")
    duplicate_url = str(duplicate["canonical_url"] or "")
    merged_url = keeper_url
    if keeper_url.startswith("urn:") and duplicate_url.startswith("https://"):
        merged_url = duplicate_url

    merged_summary = keeper["summary"] or duplicate["summary"]
    merged_tone = keeper["tone"] or duplicate["tone"]
    merged_status = "verified" if (keeper["status"] == "verified" or duplicate["status"] == "verified") else keeper["status"]

    cur.execute(
        """
        UPDATE articles
        SET
            external_id = ?,
            canonical_url = ?,
            summary = ?,
            tone = ?,
            status = ?,
            source_capture_date = COALESCE(source_capture_date, ?),
            provenance_note = COALESCE(
                provenance_note,
                'Merged duplicate records during curated JSON import.'
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            merged_external_id,
            merged_url,
            merged_summary,
            merged_tone,
            merged_status,
            capture_date,
            keeper_id,
        ),
    )

    cur.execute(
        """
        INSERT OR IGNORE INTO article_tags (article_id, tag_id, confidence, method, created_at)
        SELECT ?, tag_id, confidence, method, created_at
        FROM article_tags
        WHERE article_id = ?
        """,
        (keeper_id, duplicate_id),
    )

    cur.execute(
        "UPDATE source_assets SET article_id = ? WHERE article_id = ?",
        (keeper_id, duplicate_id),
    )
    cur.execute(
        "UPDATE article_notes SET article_id = ? WHERE article_id = ?",
        (keeper_id, duplicate_id),
    )
    cur.execute("DELETE FROM articles WHERE id = ?", (duplicate_id,))


def dedupe_articles(cur: sqlite3.Cursor, capture_date: str) -> int:
    rows = cur.execute(
        """
        SELECT id, published_at, title, canonical_url, status, summary, tone, external_id
        FROM articles
        ORDER BY id
        """
    ).fetchall()

    grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for row in rows:
        key = (str(row["published_at"]), normalize_title(str(row["title"] or "")))
        grouped.setdefault(key, []).append(row)

    merged = 0
    for _, items in grouped.items():
        if len(items) <= 1:
            continue

        keeper = max(items, key=row_score)
        keeper_id = int(keeper["id"])
        for row in items:
            duplicate_id = int(row["id"])
            if duplicate_id == keeper_id:
                continue
            merge_duplicate_rows(cur, keeper_id, duplicate_id, capture_date)
            merged += 1

    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-path",
        default="/Users/praneet/shiv-archive/data/seed/tnie_shiv_curated_v1_2026-02-22.json",
        help="Path to curated JSON file.",
    )
    parser.add_argument(
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Path to SQLite DB.",
    )
    parser.add_argument(
        "--capture-date",
        default=DEFAULT_CAPTURE_DATE,
        help="Capture date (YYYY-MM-DD) to stamp provenance fields.",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    db_path = Path(args.db_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    records = coerce_records(payload)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    ensure_tone_column(cur)
    existing_tag_ids = {
        int(row["id"]) for row in cur.execute("SELECT id FROM tags").fetchall()
    }

    inserted = 0
    updated = 0
    tags_created = 0
    tag_links = 0

    for record in records:
        meta = record.get("meta") or {}
        analysis = record.get("analysis") or {}
        raw_tags = record.get("tags") or []

        title = str(meta.get("title") or "").strip()
        published_at = str(meta.get("date_iso") or "").strip()
        canonical_url = str(meta.get("url") or "").strip()
        section = str(meta.get("section") or "").strip() or None
        external_id = str(record.get("id") or "").strip() or None
        summary = str(analysis.get("summary") or "").strip()
        tone = str(analysis.get("tone") or "").strip() or None

        if not title or not published_at:
            continue

        normalized = normalize_title(title)
        canonical_url = canonical_url or fallback_urn(title, published_at)
        provenance_note = f"Imported from user-curated v1 JSON on {args.capture_date}"

        existing_id = find_existing_article_id(cur, normalized, published_at)

        if existing_id is not None:
            article_id = existing_id
            cur.execute(
                """
                UPDATE articles
                SET
                    external_id = COALESCE(?, external_id),
                    canonical_url = COALESCE(NULLIF(?, ''), canonical_url),
                    title = ?,
                    normalized_title = ?,
                    section = COALESCE(?, section),
                    summary = COALESCE(NULLIF(?, ''), summary),
                    tone = COALESCE(NULLIF(?, ''), tone),
                    summary_method = CASE
                        WHEN ? IS NOT NULL AND ? != '' THEN 'manual_curated'
                        ELSE summary_method
                    END,
                    retrieval_method = 'user_curated_json',
                    source_capture_date = COALESCE(?, source_capture_date),
                    provenance_note = ?,
                    status = 'verified',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    external_id,
                    canonical_url,
                    title,
                    normalized,
                    section,
                    summary,
                    tone,
                    summary,
                    summary,
                    args.capture_date,
                    provenance_note,
                    article_id,
                ),
            )
            updated += 1
        else:
            cur.execute(
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
                    summary,
                    tone,
                    summary_method,
                    retrieval_method,
                    source_capture_date,
                    provenance_note,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    external_id,
                    canonical_url,
                    section or "Opinion",
                    title,
                    normalized,
                    "Shiv Visvanathan",
                    published_at,
                    summary or None,
                    tone,
                    "manual_curated" if summary else "manual",
                    "user_curated_json",
                    args.capture_date,
                    provenance_note,
                    "verified",
                ),
            )
            article_id = int(cur.lastrowid)
            inserted += 1

        cur.execute(
            "DELETE FROM article_tags WHERE article_id = ? AND method IN ('manual', 'keyword')",
            (article_id,),
        )

        seen_labels: set[str] = set()
        for item in raw_tags:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            key = label.lower()
            if key in seen_labels:
                continue
            seen_labels.add(key)

            tag_id = ensure_tag(cur, label)
            if tag_id not in existing_tag_ids:
                tags_created += 1
                existing_tag_ids.add(tag_id)

            cur.execute(
                """
                INSERT OR REPLACE INTO article_tags (article_id, tag_id, confidence, method)
                VALUES (?, ?, ?, ?)
                """,
                (article_id, tag_id, 0.95, "manual"),
            )
            tag_links += 1

    merged_duplicates = dedupe_articles(cur, args.capture_date)

    conn.commit()

    total_articles = cur.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    total_tags = cur.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    verified_articles = cur.execute(
        "SELECT COUNT(*) FROM articles WHERE status = 'verified'"
    ).fetchone()[0]

    print(f"Records in curated JSON: {len(records)}")
    print(f"Articles updated: {updated}")
    print(f"Articles inserted: {inserted}")
    print(f"Duplicate article rows merged: {merged_duplicates}")
    print(f"New tags created: {tags_created}")
    print(f"Manual tag links written: {tag_links}")
    print(f"Total articles in DB: {total_articles}")
    print(f"Total tags in DB: {total_tags}")
    print(f"Verified articles in DB: {verified_articles}")
    print(f"Database path: {db_path}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
