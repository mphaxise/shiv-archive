#!/usr/bin/env python3
"""Export a public-safe JSON payload for the v0.1 Shiv article browser."""

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


def pick_tag(existing: dict, candidate: dict) -> dict:
    existing_score = (METHOD_PRIORITY.get(existing["method"], 0), existing["confidence"])
    candidate_score = (METHOD_PRIORITY.get(candidate["method"], 0), candidate["confidence"])
    return candidate if candidate_score > existing_score else existing


def gather_shift_annotations(cur: sqlite3.Cursor) -> dict[int, dict[str, dict]]:
    annotations: dict[int, dict[str, dict]] = {}
    rows = cur.execute(
        """
        SELECT
            sa.article_id,
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
            SELECT article_id, shift_id, MAX(id) AS max_id
            FROM shift_annotations
            GROUP BY article_id, shift_id
        ) latest ON latest.max_id = sa.id
        ORDER BY sa.article_id ASC, sa.shift_id ASC
        """
    ).fetchall()

    for row in rows:
        article_id = int(row["article_id"])
        shift_id = str(row["shift_id"])
        article_bucket = annotations.setdefault(article_id, {})
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


def gather_articles(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    article_rows = cur.execute(
        """
        SELECT
            a.id,
            a.external_id,
            a.title,
            a.published_at,
            CAST(strftime('%Y', a.published_at) AS INTEGER) AS year,
            a.canonical_url,
            p.name AS publication_name,
            a.section,
            a.reading_minutes,
            a.summary,
            a.tone,
            a.summary_method,
            a.retrieval_method,
            a.status
        FROM articles a
        JOIN publications p ON p.id = a.publication_id
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()

    tags_by_article: dict[int, dict[str, dict]] = {}
    tag_rows = cur.execute(
        """
        SELECT
            at.article_id,
            t.name,
            t.slug,
            t.domain,
            at.method,
            at.confidence
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_id ASC
        """
    ).fetchall()
    for row in tag_rows:
        article_id = int(row["article_id"])
        tag_slug = row["slug"]
        candidate = {
            "label": row["name"],
            "slug": tag_slug,
            "domain": row["domain"],
            "method": row["method"],
            "confidence": float(row["confidence"]),
        }
        article_tags = tags_by_article.setdefault(article_id, {})
        if tag_slug in article_tags:
            article_tags[tag_slug] = pick_tag(article_tags[tag_slug], candidate)
        else:
            article_tags[tag_slug] = candidate

    annotations_by_article = gather_shift_annotations(cur)

    output: list[dict] = []
    for row in article_rows:
        article_id = int(row["id"])
        tags = sorted(
            tags_by_article.get(article_id, {}).values(),
            key=lambda item: (item["domain"], item["label"].lower()),
        )
        url = row["canonical_url"] or ""
        output.append(
            {
                "id": article_id,
                "external_id": row["external_id"],
                "title": row["title"],
                "date_iso": row["published_at"],
                "year": int(row["year"]),
                "url": url if url.startswith("http://") or url.startswith("https://") else None,
                "has_source_url": bool(url.startswith("http://") or url.startswith("https://")),
                "publication": row["publication_name"],
                "section": row["section"],
                "reading_minutes": row["reading_minutes"],
                "summary": row["summary"],
                "tone": row["tone"],
                "status": row["status"],
                "summary_method": row["summary_method"],
                "retrieval_method": row["retrieval_method"],
                "tags": tags,
                "shift_annotations": annotations_by_article.get(article_id, {}),
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
    publication_count = len(publications)
    dataset_label = (
        f"Multi-publication archive v1.0 "
        f"({verified} verified articles across {publication_count} sources)"
    )
    total_shift_annotations = sum(len(a.get("shift_annotations") or {}) for a in articles)
    republic_annotations = sum(
        1 for a in articles if "republic_shift" in (a.get("shift_annotations") or {})
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
        "article_count": len(articles),
        "verified_count": verified,
        "source_url_count": with_urls,
        "shift_annotation_count": total_shift_annotations,
        "republic_annotation_count": republic_annotations,
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
        "--db-path",
        default="/Users/praneet/shiv-archive/data/shiv_opinions_v0.db",
        help="Path to source SQLite DB.",
    )
    parser.add_argument(
        "--output-path",
        default="/Users/praneet/shiv-archive/web/public/data/articles.json",
        help="Output JSON path.",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    articles = gather_articles(conn)
    metadata = build_metadata(articles)
    conn.close()

    payload = {"metadata": metadata, "articles": articles}
    output_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Exported {len(articles)} records to {output_path}")
    print(f"Verified records: {metadata['verified_count']}")
    print(f"Records with source URL: {metadata['source_url_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
