#!/usr/bin/env python3
"""Safely update canonical URL for a single article in master DB."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def normalize_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return ""
    if cleaned.endswith("/") and len(cleaned) > len("https://x/"):
        cleaned = cleaned.rstrip("/")
    return cleaned.lower()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update canonical_url for one article.")
    parser.add_argument(
        "--master-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_master.db",
        help="Path to shiv_master.db",
    )
    parser.add_argument(
        "--article-uid",
        default="",
        help="Article UID to update (preferred key).",
    )
    parser.add_argument(
        "--external-id",
        default="",
        help="External ID to update (fallback key).",
    )
    parser.add_argument(
        "--canonical-url",
        required=True,
        help="New canonical URL to store.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview change without writing.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    db_path = Path(args.master_db_path)
    if not db_path.exists():
        raise SystemExit(f"Master DB not found: {db_path}")

    article_uid = (args.article_uid or "").strip()
    external_id = (args.external_id or "").strip()
    if not article_uid and not external_id:
        raise SystemExit("Provide --article-uid or --external-id.")

    canonical_url = (args.canonical_url or "").strip()
    if not canonical_url:
        raise SystemExit("--canonical-url cannot be empty.")
    canonical_url_norm = normalize_url(canonical_url)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = "article_uid = ?" if article_uid else "external_id = ?"
    lookup = article_uid or external_id
    row = cur.execute(
        f"""
        SELECT id, article_uid, external_id, title, canonical_url, canonical_url_norm
        FROM articles
        WHERE {where}
        LIMIT 1
        """,
        (lookup,),
    ).fetchone()

    if row is None:
        raise SystemExit(f"Article not found for key: {lookup}")

    print("Matched article:")
    print(f"  article_uid: {row['article_uid']}")
    print(f"  external_id: {row['external_id']}")
    print(f"  title: {row['title']}")
    print(f"  canonical_url (old): {row['canonical_url']}")
    print(f"  canonical_url_norm (old): {row['canonical_url_norm']}")
    print(f"  canonical_url (new): {canonical_url}")
    print(f"  canonical_url_norm (new): {canonical_url_norm}")

    if args.dry_run:
        print("Dry run only. No write performed.")
        conn.close()
        return 0

    cur.execute(
        """
        UPDATE articles
        SET canonical_url = ?,
            canonical_url_norm = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (canonical_url, canonical_url_norm, int(row["id"])),
    )
    conn.commit()
    conn.close()
    print("Update committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

