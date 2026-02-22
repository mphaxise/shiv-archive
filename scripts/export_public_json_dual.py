#!/usr/bin/env python3
"""Export a public-safe JSON payload from dual DBs (master + analysis)."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

METHOD_PRIORITY = {
    "manual": 4,
    "llm_map": 3,
    "hybrid": 2,
    "keyword": 1,
}


def table_exists(cur: sqlite3.Cursor, table_name: str) -> bool:
    row = cur.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def pick_tag(existing: dict, candidate: dict) -> dict:
    existing_score = (METHOD_PRIORITY.get(existing["method"], 0), existing["confidence"])
    candidate_score = (METHOD_PRIORITY.get(candidate["method"], 0), candidate["confidence"])
    return candidate if candidate_score > existing_score else existing


def gather_shift_annotations(cur: sqlite3.Cursor) -> dict[str, dict[str, dict]]:
    annotations: dict[str, dict[str, dict]] = {}
    rows = cur.execute(
        """
        SELECT
            sa.article_uid,
            sa.shift_id,
            sa.phase,
            sa.connection_text,
            sa.key_message,
            sa.annotation_method,
            sa.annotation_version,
            sa.input_fingerprint,
            sa.run_uid,
            sa.generated_at,
            sa.provenance_note
        FROM shift_annotations sa
        JOIN (
            SELECT article_uid, shift_id, MAX(id) AS max_id
            FROM shift_annotations
            GROUP BY article_uid, shift_id
        ) latest ON latest.max_id = sa.id
        ORDER BY sa.article_uid ASC, sa.shift_id ASC
        """
    ).fetchall()

    for row in rows:
        article_uid = str(row["article_uid"])
        shift_id = str(row["shift_id"])
        article_bucket = annotations.setdefault(article_uid, {})
        article_bucket[shift_id] = {
            "phase": row["phase"],
            "connection": row["connection_text"],
            "key_message": row["key_message"],
            "audit": {
                "method": row["annotation_method"],
                "version": row["annotation_version"],
                "input_fingerprint": row["input_fingerprint"],
                "run_uid": row["run_uid"],
                "generated_at": row["generated_at"],
                "provenance_note": row["provenance_note"],
            },
        }

    return annotations


def gather_republic_evidence(cur: sqlite3.Cursor) -> dict[str, dict]:
    if not table_exists(cur, "republic_shift_evidence"):
        return {}
    rows = cur.execute(
        """
        SELECT
            e.article_uid,
            e.phase,
            e.include_in_story,
            e.relevance_score,
            e.strength_label,
            e.connection_text,
            e.rationale,
            e.quote_text,
            e.quote_source,
            e.quote_confidence,
            e.method,
            e.version,
            e.input_fingerprint,
            e.run_uid,
            e.generated_at
        FROM republic_shift_evidence e
        JOIN (
            SELECT article_uid, MAX(id) AS max_id
            FROM republic_shift_evidence
            GROUP BY article_uid
        ) latest
            ON latest.max_id = e.id
        ORDER BY e.article_uid ASC
        """
    ).fetchall()

    out: dict[str, dict] = {}
    for row in rows:
        out[str(row["article_uid"])] = {
            "phase": row["phase"],
            "include_in_story": bool(row["include_in_story"]),
            "relevance_score": float(row["relevance_score"]),
            "strength_label": row["strength_label"],
            "connection_text": row["connection_text"],
            "rationale": row["rationale"],
            "quote_text": row["quote_text"],
            "quote_source": row["quote_source"],
            "quote_confidence": float(row["quote_confidence"]),
            "audit": {
                "method": row["method"],
                "version": row["version"],
                "input_fingerprint": row["input_fingerprint"],
                "run_uid": row["run_uid"],
                "generated_at": row["generated_at"],
            },
        }
    return out


def gather_analysis(cur: sqlite3.Cursor) -> tuple[dict[str, sqlite3.Row], dict[str, dict], dict[str, dict[str, dict]]]:
    analysis_rows = cur.execute(
        """
        SELECT
            article_uid,
            summary,
            tone,
            summary_method,
            analysis_status
        FROM article_analysis
        """
    ).fetchall()
    analysis_by_uid = {str(row["article_uid"]): row for row in analysis_rows}

    tags_by_article: dict[str, dict[str, dict]] = {}
    tag_rows = cur.execute(
        """
        SELECT
            at.article_uid,
            t.name,
            t.slug,
            t.domain,
            at.method,
            at.confidence
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_uid ASC
        """
    ).fetchall()
    for row in tag_rows:
        article_uid = str(row["article_uid"])
        tag_slug = row["slug"]
        candidate = {
            "label": row["name"],
            "slug": tag_slug,
            "domain": row["domain"],
            "method": row["method"],
            "confidence": float(row["confidence"]),
        }
        article_tags = tags_by_article.setdefault(article_uid, {})
        if tag_slug in article_tags:
            article_tags[tag_slug] = pick_tag(article_tags[tag_slug], candidate)
        else:
            article_tags[tag_slug] = candidate

    annotations_by_article = gather_shift_annotations(cur)
    return analysis_by_uid, tags_by_article, annotations_by_article


def gather_articles(master_conn: sqlite3.Connection, analysis_conn: sqlite3.Connection) -> list[dict]:
    master_conn.row_factory = sqlite3.Row
    analysis_conn.row_factory = sqlite3.Row
    master_cur = master_conn.cursor()
    analysis_cur = analysis_conn.cursor()

    master_rows = master_cur.execute(
        """
        SELECT
            a.id,
            a.article_uid,
            a.external_id,
            a.title,
            a.published_at,
            CAST(strftime('%Y', a.published_at) AS INTEGER) AS year,
            a.canonical_url,
            p.name AS publication_name,
            a.section,
            a.reading_minutes,
            a.status,
            a.retrieval_method,
            COALESCE(t.text_state, 'missing') AS text_state,
            CASE
                WHEN t.body_text IS NOT NULL AND TRIM(t.body_text) <> '' THEN 1
                ELSE 0
            END AS has_full_text
        FROM articles a
        JOIN publications p ON p.id = a.publication_id
        LEFT JOIN article_texts t
            ON t.article_uid = a.article_uid
           AND t.is_primary = 1
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()

    analysis_by_uid, tags_by_article, annotations_by_article = gather_analysis(analysis_cur)
    republic_evidence_by_article = gather_republic_evidence(analysis_cur)

    output: list[dict] = []
    for row in master_rows:
        article_uid = str(row["article_uid"])
        analysis = analysis_by_uid.get(article_uid)
        summary = analysis["summary"] if analysis else None
        tone = analysis["tone"] if analysis else None
        summary_method = analysis["summary_method"] if analysis else "manual"
        url = row["canonical_url"] or ""
        output.append(
            {
                "id": int(row["id"]),
                "article_uid": article_uid,
                "external_id": row["external_id"],
                "title": row["title"],
                "date_iso": row["published_at"],
                "year": int(row["year"]),
                "url": url if url.startswith("http://") or url.startswith("https://") else None,
                "has_source_url": bool(url.startswith("http://") or url.startswith("https://")),
                "publication": row["publication_name"],
                "section": row["section"],
                "reading_minutes": row["reading_minutes"],
                "summary": summary,
                "tone": tone,
                "status": row["status"],
                "summary_method": summary_method,
                "retrieval_method": row["retrieval_method"],
                "text_state": row["text_state"],
                "has_full_text": bool(row["has_full_text"]),
                "tags": sorted(
                    tags_by_article.get(article_uid, {}).values(),
                    key=lambda item: (item["domain"], item["label"].lower()),
                ),
                "shift_annotations": annotations_by_article.get(article_uid, {}),
                "republic_critical": republic_evidence_by_article.get(article_uid),
            }
        )
    return output


def build_metadata(articles: list[dict]) -> dict:
    years = sorted({a["year"] for a in articles}, reverse=True)
    tones = sorted({a["tone"] for a in articles if a.get("tone")})
    sections = sorted({a["section"] for a in articles if a.get("section")})
    publication_counter: dict[str, int] = {}
    for article in articles:
        publication = str(article.get("publication") or "").strip()
        if not publication:
            continue
        publication_counter[publication] = publication_counter.get(publication, 0) + 1
    publications = sorted(
        (
            {"name": name, "count": count}
            for name, count in publication_counter.items()
        ),
        key=lambda item: (-item["count"], item["name"].lower()),
    )
    verified = sum(1 for a in articles if a.get("status") == "verified")
    with_urls = sum(1 for a in articles if a.get("has_source_url"))
    with_full_text = sum(1 for a in articles if a.get("has_full_text"))
    publication_count = len(publications)
    dataset_label = (
        f"Multi-publication archive v1.1 "
        f"({verified} verified articles across {publication_count} sources)"
    )
    total_shift_annotations = sum(len(a.get("shift_annotations") or {}) for a in articles)
    republic_annotations = sum(
        1 for a in articles if "republic_shift" in (a.get("shift_annotations") or {})
    )
    republic_curated = sum(
        1 for a in articles if (a.get("republic_critical") or {}).get("include_in_story")
    )

    tag_counts: dict[str, dict] = {}
    for article in articles:
        seen = set()
        for tag in article["tags"]:
            slug = tag["slug"]
            if slug in seen:
                continue
            seen.add(slug)
            if slug not in tag_counts:
                tag_counts[slug] = {
                    "label": tag["label"],
                    "slug": slug,
                    "domain": tag["domain"],
                    "count": 0,
                }
            tag_counts[slug]["count"] += 1

    top_tags = sorted(tag_counts.values(), key=lambda item: (-item["count"], item["label"].lower()))

    return {
        "project": "Shiv Visvanathan Opinion Archive",
        "dataset": dataset_label,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "database_mode": "dual_db",
        "article_count": len(articles),
        "verified_count": verified,
        "source_url_count": with_urls,
        "full_text_count": with_full_text,
        "shift_annotation_count": total_shift_annotations,
        "republic_annotation_count": republic_annotations,
        "republic_curated_count": republic_curated,
        "year_range": [min(years), max(years)] if years else [],
        "years": years,
        "publications": publications,
        "tones": tones,
        "sections": sections,
        "tags": top_tags,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_master.db",
        help="Path to master SQLite DB.",
    )
    parser.add_argument(
        "--analysis-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_analysis.db",
        help="Path to analysis SQLite DB.",
    )
    parser.add_argument(
        "--output-path",
        default="/Users/praneet/shiv-archive/web/public/data/articles.json",
        help="Output JSON path.",
    )
    args = parser.parse_args()

    master_db_path = Path(args.master_db_path)
    analysis_db_path = Path(args.analysis_db_path)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    master_conn = sqlite3.connect(master_db_path)
    analysis_conn = sqlite3.connect(analysis_db_path)
    articles = gather_articles(master_conn, analysis_conn)
    metadata = build_metadata(articles)
    master_conn.close()
    analysis_conn.close()

    payload = {"metadata": metadata, "articles": articles}
    output_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Exported {len(articles)} records to {output_path}")
    print(f"Verified records: {metadata['verified_count']}")
    print(f"Records with source URL: {metadata['source_url_count']}")
    print(f"Records with full text: {metadata['full_text_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
