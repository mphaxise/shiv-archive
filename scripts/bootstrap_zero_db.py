#!/usr/bin/env python3
"""Bootstrap an absolute-zero Shiv TNIE database from a seed CSV."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import unicodedata
from pathlib import Path


KEYWORD_TAGS: dict[str, list[str]] = {
    "anthropocene": ["ecology", "technology-and-society"],
    "ecocide": ["ecology"],
    "ecology": ["ecology"],
    "democracy": ["democracy", "public-sphere"],
    "democratic": ["democracy"],
    "citizen": ["democracy"],
    "citizenship": ["democracy"],
    "policy": ["public-institutions", "law-and-justice"],
    "ethics": ["ethics"],
    "morality": ["ethics"],
    "peace": ["pluralism", "public-sphere"],
    "violence": ["law-and-justice", "pluralism"],
    "civil society": ["social-movements", "pluralism"],
    "science": ["science-policy", "technology-and-society"],
    "knowledge": ["knowledge-systems", "public-sphere"],
    "panchayat": ["knowledge-systems", "public-institutions"],
    "university": ["education-policy", "knowledge-systems"],
    "education": ["education-policy"],
    "history": ["memory"],
    "memory": ["memory"],
    "nationalism": ["nationalism"],
    "patriotism": ["nationalism", "ethics"],
    "feminism": ["identity-politics", "ethics"],
    "caste": ["caste", "identity-politics"],
    "swadeshi": ["development", "nationalism"],
    "constitution": ["law-and-justice", "democracy"],
    "theatre": ["ritual-and-symbol", "public-sphere"],
    "playfulness": ["culture-and-modernity"],
    "play": ["culture-and-modernity"],
    "orality": ["knowledge-systems", "culture-and-modernity"],
}

FALLBACK_TAG_SLUGS = [
    "public-sphere",
    "ethics",
    "democracy",
    "pluralism",
    "culture-and-modernity",
]


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


def infer_tag_slugs(title: str) -> list[str]:
    lowered = to_ascii(title).lower()
    chosen: list[str] = []
    for keyword, slugs in KEYWORD_TAGS.items():
        if keyword in lowered:
            for slug in slugs:
                if slug not in chosen:
                    chosen.append(slug)
    for slug in FALLBACK_TAG_SLUGS:
        if len(chosen) >= 3:
            break
        if slug not in chosen:
            chosen.append(slug)
    return chosen[:5]


def build_summary(title: str, section: str) -> str:
    title = title.strip()
    section = section.strip() or "Opinion"
    return (
        f'{section} piece by Shiv Visvanathan on "{title}". '
        "Auto-generated from headline metadata; pending manual review."
    )


def load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed-csv",
        default="/Users/praneet/shiv-archive/data/seed/tnie_shiv_articles_ctrl_a_2026-02-22.csv",
        help="Path to seed CSV.",
    )
    parser.add_argument(
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Path to output SQLite DB.",
    )
    parser.add_argument(
        "--schema-sql",
        default="/Users/praneet/shiv-archive/db/schema.sql",
        help="Path to schema SQL file.",
    )
    parser.add_argument(
        "--seed-tags-sql",
        default="/Users/praneet/shiv-archive/db/seed_tags.sql",
        help="Path to tag seed SQL file.",
    )
    args = parser.parse_args()

    seed_csv = Path(args.seed_csv)
    db_path = Path(args.db_path)
    schema_sql = Path(args.schema_sql)
    seed_tags_sql = Path(args.seed_tags_sql)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript(load_sql(schema_sql))
    cur.executescript(load_sql(seed_tags_sql))
    conn.commit()

    tag_ids = {
        row["slug"]: row["id"]
        for row in cur.execute("SELECT id, slug FROM tags").fetchall()
    }

    imported = 0
    tagged_links = 0

    with seed_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row["title"].strip()
            published_at = row["published_at"].strip()
            section = row.get("section", "Opinion").strip() or "Opinion"
            read_minutes = int((row.get("read_minutes") or "0").strip() or 0)
            capture_date = row.get("source_capture_date", "").strip() or None
            note = row.get("provenance_note", "").strip() or None
            provided_url = row.get("canonical_url", "").strip()
            canonical_url = provided_url or (
                f"urn:tnie:shiv:{published_at}:{slugify(title)}"
            )

            cur.execute(
                """
                INSERT INTO articles (
                    publication_id,
                    canonical_url,
                    section,
                    title,
                    normalized_title,
                    author_name,
                    published_at,
                    reading_minutes,
                    summary,
                    summary_method,
                    retrieval_method,
                    source_capture_date,
                    provenance_note,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    section = excluded.section,
                    title = excluded.title,
                    normalized_title = excluded.normalized_title,
                    published_at = excluded.published_at,
                    reading_minutes = excluded.reading_minutes,
                    summary = excluded.summary,
                    summary_method = excluded.summary_method,
                    retrieval_method = excluded.retrieval_method,
                    source_capture_date = excluded.source_capture_date,
                    provenance_note = excluded.provenance_note,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    1,
                    canonical_url,
                    section,
                    title,
                    normalize_title(title),
                    "Shiv Visvanathan",
                    published_at,
                    read_minutes,
                    build_summary(title, section),
                    "heuristic_title",
                    "ctrl_a_copy",
                    capture_date,
                    note,
                    "draft",
                ),
            )

            article_id = cur.execute(
                "SELECT id FROM articles WHERE canonical_url = ?",
                (canonical_url,),
            ).fetchone()["id"]

            tag_slugs = infer_tag_slugs(title)
            for slug in tag_slugs:
                tag_id = tag_ids.get(slug)
                if tag_id is None:
                    continue
                cur.execute(
                    """
                    INSERT OR IGNORE INTO article_tags (
                        article_id,
                        tag_id,
                        confidence,
                        method
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (article_id, tag_id, 0.62, "keyword"),
                )
                tagged_links += 1

            imported += 1

    conn.commit()

    article_count = cur.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
    tag_link_count = cur.execute("SELECT COUNT(*) AS c FROM article_tags").fetchone()["c"]

    print(f"Processed seed rows: {imported}")
    print(f"Articles in DB: {article_count}")
    print(f"Attempted tag links: {tagged_links}")
    print(f"Stored article_tags rows: {tag_link_count}")
    print(f"Database path: {db_path}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
