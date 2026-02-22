#!/usr/bin/env python3
"""Split legacy single DB into master + analysis DBs with stable article UIDs."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import unicodedata
from pathlib import Path


def to_ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(value: str) -> str:
    value = to_ascii(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "item"


def normalize_title(title: str) -> str:
    lowered = to_ascii(title).lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def normalize_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return ""
    if cleaned.endswith("/") and len(cleaned) > len("https://x/"):
        cleaned = cleaned.rstrip("/")
    return cleaned.lower()


def load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def stable_article_uid(
    publication_slug: str,
    external_id: str,
    canonical_url: str,
    published_at: str,
    normalized_title: str,
) -> str:
    ext = (external_id or "").strip()
    url = (canonical_url or "").strip()
    if ext:
        seed = f"ext|{publication_slug}|{ext}"
    elif url and not url.startswith("urn:"):
        seed = f"url|{publication_slug}|{normalize_url(url)}"
    else:
        seed = f"title|{publication_slug}|{published_at}|{normalized_title}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:20]
    return f"art_{digest}"


def copy_publications(
    source_cur: sqlite3.Cursor,
    master_cur: sqlite3.Cursor,
) -> tuple[dict[int, str], int]:
    rows = source_cur.execute(
        """
        SELECT id, name, base_url
        FROM publications
        ORDER BY id ASC
        """
    ).fetchall()

    pub_slug_by_id: dict[int, str] = {}
    used_slugs: set[str] = set()
    slug_collisions = 0

    for row in rows:
        pub_id = int(row["id"])
        name = str(row["name"] or "").strip()
        base_url = str(row["base_url"] or "").strip()
        base_slug = slugify(name)
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug_collisions += 1
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs.add(slug)
        pub_slug_by_id[pub_id] = slug

        master_cur.execute(
            """
            INSERT INTO publications (id, slug, name, base_url)
            VALUES (?, ?, ?, ?)
            """,
            (pub_id, slug, name, base_url),
        )

    return pub_slug_by_id, slug_collisions


def copy_articles(
    source_cur: sqlite3.Cursor,
    master_cur: sqlite3.Cursor,
    analysis_cur: sqlite3.Cursor,
    pub_slug_by_id: dict[int, str],
) -> tuple[dict[int, str], int]:
    rows = source_cur.execute(
        """
        SELECT
            id,
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
            status,
            created_at,
            updated_at
        FROM articles
        ORDER BY id ASC
        """
    ).fetchall()

    uid_by_article_id: dict[int, str] = {}
    used_uids: set[str] = set()
    uid_collisions = 0

    for row in rows:
        article_id = int(row["id"])
        publication_id = int(row["publication_id"])
        publication_slug = pub_slug_by_id[publication_id]

        title = str(row["title"] or "").strip()
        normalized = str(row["normalized_title"] or "").strip()
        if not normalized:
            normalized = normalize_title(title)

        canonical_url = str(row["canonical_url"] or "").strip()
        external_id = str(row["external_id"] or "").strip()
        published_at = str(row["published_at"] or "").strip()
        article_uid = stable_article_uid(
            publication_slug=publication_slug,
            external_id=external_id,
            canonical_url=canonical_url,
            published_at=published_at,
            normalized_title=normalized,
        )

        unique_uid = article_uid
        suffix = 2
        while unique_uid in used_uids:
            uid_collisions += 1
            unique_uid = f"{article_uid}-{suffix}"
            suffix += 1
        article_uid = unique_uid
        used_uids.add(article_uid)
        uid_by_article_id[article_id] = article_uid

        canonical_url_norm = normalize_url(canonical_url)
        if not canonical_url_norm:
            canonical_url_norm = f"urn:{article_uid}"
            canonical_url = canonical_url or canonical_url_norm

        master_cur.execute(
            """
            INSERT INTO articles (
                article_uid,
                publication_id,
                external_id,
                canonical_url,
                canonical_url_norm,
                section,
                title,
                normalized_title,
                author_name,
                published_at,
                reading_minutes,
                status,
                retrieval_method,
                source_capture_date,
                provenance_note,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_uid,
                publication_id,
                external_id or None,
                canonical_url,
                canonical_url_norm,
                str(row["section"] or "Opinion").strip() or "Opinion",
                title,
                normalized,
                str(row["author_name"] or "Shiv Visvanathan").strip() or "Shiv Visvanathan",
                published_at,
                row["reading_minutes"],
                str(row["status"] or "draft").strip() or "draft",
                str(row["retrieval_method"] or "manual_screenshot").strip(),
                row["source_capture_date"],
                row["provenance_note"],
                row["created_at"],
                row["updated_at"],
            ),
        )

        master_cur.execute(
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
                is_primary,
                created_at,
                updated_at
            )
            VALUES (?, NULL, 'missing', 'plain', NULL, 'en', 'not_collected', NULL, ?, NULL, 1, ?, ?)
            """,
            (
                article_uid,
                canonical_url if canonical_url.startswith("http://") or canonical_url.startswith("https://") else None,
                row["created_at"],
                row["updated_at"],
            ),
        )

        analysis_cur.execute(
            """
            INSERT INTO article_analysis (
                article_uid,
                summary,
                tone,
                summary_method,
                summary_model,
                analysis_status,
                provenance_note,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_uid,
                row["summary"],
                row["tone"],
                str(row["summary_method"] or "manual").strip() or "manual",
                row["summary_model"],
                str(row["status"] or "draft").strip() or "draft",
                row["provenance_note"],
                row["created_at"],
                row["updated_at"],
            ),
        )

    return uid_by_article_id, uid_collisions


def copy_tags(source_cur: sqlite3.Cursor, analysis_cur: sqlite3.Cursor) -> None:
    rows = source_cur.execute(
        """
        SELECT id, name, slug, domain, description, is_seed, created_at
        FROM tags
        ORDER BY id ASC
        """
    ).fetchall()

    for row in rows:
        analysis_cur.execute(
            """
            INSERT INTO tags (id, name, slug, domain, description, is_seed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                row["name"],
                row["slug"],
                row["domain"],
                row["description"],
                int(row["is_seed"]),
                row["created_at"],
            ),
        )


def copy_article_tags(
    source_cur: sqlite3.Cursor,
    analysis_cur: sqlite3.Cursor,
    uid_by_article_id: dict[int, str],
) -> int:
    rows = source_cur.execute(
        """
        SELECT article_id, tag_id, confidence, method, created_at
        FROM article_tags
        ORDER BY article_id ASC
        """
    ).fetchall()

    copied = 0
    for row in rows:
        article_uid = uid_by_article_id.get(int(row["article_id"]))
        if not article_uid:
            continue
        analysis_cur.execute(
            """
            INSERT INTO article_tags (article_uid, tag_id, confidence, method, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                article_uid,
                int(row["tag_id"]),
                float(row["confidence"]),
                row["method"],
                row["created_at"],
            ),
        )
        copied += 1
    return copied


def copy_ingestion_runs(source_cur: sqlite3.Cursor, master_cur: sqlite3.Cursor) -> int:
    rows = source_cur.execute(
        """
        SELECT
            id,
            started_at,
            finished_at,
            source_type,
            input_count,
            success_count,
            error_count,
            notes
        FROM ingestion_runs
        ORDER BY id ASC
        """
    ).fetchall()
    for row in rows:
        master_cur.execute(
            """
            INSERT INTO ingestion_runs (
                id,
                started_at,
                finished_at,
                source_type,
                input_count,
                success_count,
                error_count,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                row["started_at"],
                row["finished_at"],
                row["source_type"],
                int(row["input_count"]),
                int(row["success_count"]),
                int(row["error_count"]),
                row["notes"],
            ),
        )
    return len(rows)


def copy_source_assets(
    source_cur: sqlite3.Cursor,
    master_cur: sqlite3.Cursor,
    uid_by_article_id: dict[int, str],
) -> int:
    rows = source_cur.execute(
        """
        SELECT
            id,
            article_id,
            asset_type,
            file_path,
            sha256,
            capture_date,
            ocr_text,
            ocr_confidence,
            created_at
        FROM source_assets
        ORDER BY id ASC
        """
    ).fetchall()
    copied = 0
    for row in rows:
        source_article_id = row["article_id"]
        article_uid = uid_by_article_id.get(int(source_article_id)) if source_article_id is not None else None
        master_cur.execute(
            """
            INSERT INTO source_assets (
                id,
                article_uid,
                asset_type,
                file_path,
                sha256,
                capture_date,
                ocr_text,
                ocr_confidence,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                article_uid,
                row["asset_type"],
                row["file_path"],
                row["sha256"],
                row["capture_date"],
                row["ocr_text"],
                row["ocr_confidence"],
                row["created_at"],
            ),
        )
        copied += 1
    return copied


def copy_article_notes(
    source_cur: sqlite3.Cursor,
    master_cur: sqlite3.Cursor,
    uid_by_article_id: dict[int, str],
) -> int:
    rows = source_cur.execute(
        """
        SELECT id, article_id, note_type, body, created_at
        FROM article_notes
        ORDER BY id ASC
        """
    ).fetchall()
    copied = 0
    for row in rows:
        article_uid = uid_by_article_id.get(int(row["article_id"]))
        if not article_uid:
            continue
        master_cur.execute(
            """
            INSERT INTO article_notes (id, article_uid, note_type, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                article_uid,
                row["note_type"],
                row["body"],
                row["created_at"],
            ),
        )
        copied += 1
    return copied


def copy_shift_annotation_runs(source_cur: sqlite3.Cursor, analysis_cur: sqlite3.Cursor) -> int:
    rows = source_cur.execute(
        """
        SELECT
            id,
            run_uid,
            started_at,
            finished_at,
            shift_scope,
            annotation_method,
            annotation_version,
            inserted_count,
            skipped_count,
            notes
        FROM shift_annotation_runs
        ORDER BY id ASC
        """
    ).fetchall()
    for row in rows:
        analysis_cur.execute(
            """
            INSERT INTO shift_annotation_runs (
                id,
                run_uid,
                started_at,
                finished_at,
                shift_scope,
                annotation_method,
                annotation_version,
                inserted_count,
                skipped_count,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                row["run_uid"],
                row["started_at"],
                row["finished_at"],
                row["shift_scope"],
                row["annotation_method"],
                row["annotation_version"],
                int(row["inserted_count"]),
                int(row["skipped_count"]),
                row["notes"],
            ),
        )
    return len(rows)


def copy_shift_annotations(
    source_cur: sqlite3.Cursor,
    analysis_cur: sqlite3.Cursor,
    uid_by_article_id: dict[int, str],
) -> int:
    rows = source_cur.execute(
        """
        SELECT
            id,
            article_id,
            shift_id,
            phase,
            connection_text,
            key_message,
            annotation_method,
            annotation_version,
            input_fingerprint,
            run_uid,
            provenance_note,
            generated_at
        FROM shift_annotations
        ORDER BY id ASC
        """
    ).fetchall()
    copied = 0
    for row in rows:
        article_uid = uid_by_article_id.get(int(row["article_id"]))
        if not article_uid:
            continue
        analysis_cur.execute(
            """
            INSERT INTO shift_annotations (
                id,
                article_uid,
                shift_id,
                phase,
                connection_text,
                key_message,
                annotation_method,
                annotation_version,
                input_fingerprint,
                run_uid,
                provenance_note,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["id"]),
                article_uid,
                row["shift_id"],
                row["phase"],
                row["connection_text"],
                row["key_message"],
                row["annotation_method"],
                row["annotation_version"],
                row["input_fingerprint"],
                row["run_uid"],
                row["provenance_note"],
                row["generated_at"],
            ),
        )
        copied += 1
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Legacy single-db source path.",
    )
    parser.add_argument(
        "--master-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_master.db",
        help="Output master DB path.",
    )
    parser.add_argument(
        "--analysis-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_analysis.db",
        help="Output analysis DB path.",
    )
    parser.add_argument(
        "--master-schema-sql",
        default="/Users/praneet/shiv-archive/db/master_schema.sql",
        help="Master schema SQL file path.",
    )
    parser.add_argument(
        "--analysis-schema-sql",
        default="/Users/praneet/shiv-archive/db/analysis_schema.sql",
        help="Analysis schema SQL file path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output DB files if they already exist.",
    )
    args = parser.parse_args()

    source_db_path = Path(args.source_db_path)
    master_db_path = Path(args.master_db_path)
    analysis_db_path = Path(args.analysis_db_path)
    master_schema_path = Path(args.master_schema_sql)
    analysis_schema_path = Path(args.analysis_schema_sql)

    if not source_db_path.exists():
        raise FileNotFoundError(f"Source DB missing: {source_db_path}")

    for target in (master_db_path, analysis_db_path):
        if target.exists():
            if not args.force:
                raise FileExistsError(
                    f"Refusing to overwrite existing DB: {target} (pass --force to replace)"
                )
            target.unlink()

    master_db_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_db_path.parent.mkdir(parents=True, exist_ok=True)

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    source_cur = source_conn.cursor()

    master_conn = sqlite3.connect(master_db_path)
    master_conn.row_factory = sqlite3.Row
    master_cur = master_conn.cursor()
    master_cur.executescript(load_sql(master_schema_path))

    analysis_conn = sqlite3.connect(analysis_db_path)
    analysis_conn.row_factory = sqlite3.Row
    analysis_cur = analysis_conn.cursor()
    analysis_cur.executescript(load_sql(analysis_schema_path))

    pub_slug_by_id, slug_collisions = copy_publications(source_cur, master_cur)
    uid_by_article_id, uid_collisions = copy_articles(
        source_cur=source_cur,
        master_cur=master_cur,
        analysis_cur=analysis_cur,
        pub_slug_by_id=pub_slug_by_id,
    )
    copy_tags(source_cur, analysis_cur)
    article_tag_links = copy_article_tags(source_cur, analysis_cur, uid_by_article_id)
    ingestion_runs = copy_ingestion_runs(source_cur, master_cur)
    source_assets = copy_source_assets(source_cur, master_cur, uid_by_article_id)
    article_notes = copy_article_notes(source_cur, master_cur, uid_by_article_id)
    shift_runs = copy_shift_annotation_runs(source_cur, analysis_cur)
    shift_annotations = copy_shift_annotations(source_cur, analysis_cur, uid_by_article_id)

    master_conn.commit()
    analysis_conn.commit()

    master_total = master_cur.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
    analysis_total = analysis_cur.execute("SELECT COUNT(*) AS c FROM article_analysis").fetchone()["c"]
    text_total = master_cur.execute("SELECT COUNT(*) AS c FROM article_texts").fetchone()["c"]
    text_full = master_cur.execute(
        "SELECT COUNT(*) AS c FROM article_texts WHERE text_state = 'full'"
    ).fetchone()["c"]
    by_pub = master_cur.execute(
        """
        SELECT p.name, COUNT(*) AS c
        FROM articles a
        JOIN publications p ON p.id = a.publication_id
        GROUP BY p.name
        ORDER BY c DESC, p.name ASC
        """
    ).fetchall()

    print(f"Source DB: {source_db_path}")
    print(f"Master DB: {master_db_path}")
    print(f"Analysis DB: {analysis_db_path}")
    print(f"Publications copied: {len(pub_slug_by_id)} (slug collisions resolved: {slug_collisions})")
    print(f"Articles copied: {master_total} (uid collisions resolved: {uid_collisions})")
    print(f"Article text rows: {text_total} (full text rows: {text_full})")
    print(f"Article analysis rows: {analysis_total}")
    print(f"Tag links copied: {article_tag_links}")
    print(f"Shift annotation runs copied: {shift_runs}")
    print(f"Shift annotations copied: {shift_annotations}")
    print(f"Ingestion runs copied: {ingestion_runs}")
    print(f"Source assets copied: {source_assets}")
    print(f"Article notes copied: {article_notes}")
    for row in by_pub:
        print(f"  - {row['name']}: {row['c']}")

    source_conn.close()
    master_conn.close()
    analysis_conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
