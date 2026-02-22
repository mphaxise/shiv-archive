#!/usr/bin/env python3
"""Generate reusable, auditable shift annotations in analysis DB using dual-DB corpus."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SHIFT_IDS = (
    "republic_shift",
    "ecological_shift",
    "science_shift",
    "political_shift",
)


@dataclass(frozen=True)
class ShiftRule:
    milestone_year: int


SHIFT_RULES: dict[str, ShiftRule] = {
    "republic_shift": ShiftRule(milestone_year=2024),
    "ecological_shift": ShiftRule(milestone_year=2021),
    "science_shift": ShiftRule(milestone_year=2023),
    "political_shift": ShiftRule(milestone_year=2022),
}


def ensure_annotation_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS shift_annotation_runs (
            id INTEGER PRIMARY KEY,
            run_uid TEXT NOT NULL UNIQUE,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT,
            shift_scope TEXT NOT NULL,
            annotation_method TEXT NOT NULL,
            annotation_version TEXT NOT NULL,
            inserted_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS shift_annotations (
            id INTEGER PRIMARY KEY,
            article_uid TEXT NOT NULL,
            shift_id TEXT NOT NULL CHECK (
                shift_id IN ('republic_shift', 'ecological_shift', 'science_shift', 'political_shift')
            ),
            phase TEXT NOT NULL CHECK (phase IN ('before', 'after')),
            connection_text TEXT NOT NULL,
            key_message TEXT NOT NULL,
            annotation_method TEXT NOT NULL,
            annotation_version TEXT NOT NULL,
            input_fingerprint TEXT NOT NULL,
            run_uid TEXT NOT NULL REFERENCES shift_annotation_runs(run_uid) ON DELETE RESTRICT,
            provenance_note TEXT,
            generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_shift_annotations_unique_input
        ON shift_annotations(article_uid, shift_id, annotation_version, input_fingerprint);

        CREATE INDEX IF NOT EXISTS idx_shift_annotations_lookup
        ON shift_annotations(article_uid, shift_id, generated_at DESC, id DESC);

        CREATE INDEX IF NOT EXISTS idx_shift_annotations_run_uid
        ON shift_annotations(run_uid);
        """
    )


def first_sentence(summary: str) -> str:
    normalized = " ".join((summary or "").split()).strip()
    if not normalized:
        return "This article captures a key transition point in the archive."

    stop = min(
        (
            index
            for index in (
                normalized.find(". "),
                normalized.find("? "),
                normalized.find("! "),
            )
            if index >= 0
        ),
        default=-1,
    )
    if stop == -1:
        return normalized
    return normalized[: stop + 1].strip()


def has_any(text: str, probes: list[str]) -> bool:
    return any(probe in text for probe in probes)


def republic_connection(text: str, phase: str) -> str:
    if has_any(
        text,
        [
            "constitution",
            "citizen",
            "citizenship",
            "republic",
            "democracy",
            "institution",
            "state",
        ],
    ):
        return (
            "Links to Phase 1 by showing strain in First Republic institutions and citizenship grammar."
            if phase == "before"
            else "Links to Phase 2 by reframing citizenship for a contested, post-formalist Second Republic."
        )

    if has_any(
        text,
        [
            "knowledge",
            "science",
            "university",
            "expert",
            "panchayat",
            "education",
            "innovation",
        ],
    ):
        return (
            "Links to Phase 1 by exposing how First Republic knowledge institutions narrowed democratic imagination."
            if phase == "before"
            else "Links to Phase 2 by proposing distributed knowledge as a design principle for the Second Republic."
        )

    if has_any(
        text,
        [
            "violence",
            "peace",
            "ethics",
            "morality",
            "nationalism",
            "dissent",
            "satyagraha",
            "yatra",
        ],
    ):
        return (
            "Links to Phase 1 by reading moral dissent as a response to First Republic fatigue."
            if phase == "before"
            else "Links to Phase 2 by placing ethics, embodiment, and public repair at the core of new politics."
        )

    if has_any(
        text,
        ["anthropocene", "ecology", "ecocide", "climate", "nature", "aravallis"],
    ):
        return (
            "Links to Phase 1 by widening First Republic debates toward ecological citizenship and survival."
            if phase == "before"
            else "Links to Phase 2 by treating ecological survival as central to the Second Republic social contract."
        )

    return (
        "Links to Phase 1 by documenting cracks between constitutional form and lived democratic experience."
        if phase == "before"
        else "Links to Phase 2 by tracing emergent civic vocabularies beyond legacy institutional comfort."
    )


def ecological_connection(text: str, phase: str) -> str:
    if has_any(text, ["anthropocene", "ecocide", "survival", "climate", "aravallis", "shaman"]):
        return (
            "Links to Phase 1 by testing environmental governance limits inside development-era policy language."
            if phase == "before"
            else "Links to Phase 2 by centering Anthropocene rupture, ecocide, and the right to survive."
        )
    return (
        "Links to Phase 1 by reading ecology through managerial conservation and policy compromise."
        if phase == "before"
        else "Links to Phase 2 by moving ecology into civilizational risk and plural lifeworld thinking."
    )


def science_connection(text: str, phase: str) -> str:
    if has_any(text, ["science", "expert", "big science", "university", "innovation"]):
        return (
            "Links to Phase 1 by critiquing institutional expertise and the closure of scientific authority."
            if phase == "before"
            else "Links to Phase 2 by opening science to distributed publics and experimental citizenship."
        )
    return (
        "Links to Phase 1 by exposing knowledge hierarchies in formal institutions."
        if phase == "before"
        else "Links to Phase 2 by arguing for cognitive justice and knowledge panchayats."
    )


def political_connection(text: str, phase: str) -> str:
    if has_any(text, ["yatra", "satyagraha", "body", "theatre", "civil society", "dissent"]):
        return (
            "Links to Phase 1 by documenting strategic dissent and civil-society petitioning."
            if phase == "before"
            else "Links to Phase 2 by foregrounding body politics, public theatre, and moral choreography."
        )
    return (
        "Links to Phase 1 by reading politics through institutional opposition."
        if phase == "before"
        else "Links to Phase 2 by emphasizing affective, embodied forms of democratic action."
    )


def build_connection(shift_id: str, text: str, phase: str) -> str:
    if shift_id == "republic_shift":
        return republic_connection(text, phase)
    if shift_id == "ecological_shift":
        return ecological_connection(text, phase)
    if shift_id == "science_shift":
        return science_connection(text, phase)
    return political_connection(text, phase)


def build_key_message(summary: str, shift_id: str, phase: str) -> str:
    base = first_sentence(summary)
    if shift_id == "republic_shift":
        suffix = (
            "First Republic signal: legacy institutions are under pressure."
            if phase == "before"
            else "Second Republic signal: democratic practice is being re-authored."
        )
        return f"{base} {suffix}"
    if shift_id == "ecological_shift":
        suffix = (
            "Ecological shift signal: management-era assumptions are being stress-tested."
            if phase == "before"
            else "Ecological shift signal: Anthropocene survival logic becomes central."
        )
        return f"{base} {suffix}"
    if shift_id == "science_shift":
        suffix = (
            "Science shift signal: expert monopoly frames are being questioned."
            if phase == "before"
            else "Science shift signal: plural knowledge publics gain legitimacy."
        )
        return f"{base} {suffix}"
    suffix = (
        "Political shift signal: strategic dissent remains institution-facing."
        if phase == "before"
        else "Political shift signal: politics expands into embodied public action."
    )
    return f"{base} {suffix}"


def build_input_fingerprint(
    shift_id: str,
    phase: str,
    title: str,
    summary: str,
    year: int,
    tag_slugs: list[str],
) -> str:
    payload = "|".join(
        [
            shift_id,
            phase,
            title.strip(),
            (summary or "").strip(),
            str(year),
            ",".join(sorted(tag_slugs)),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def parse_shift_scope(raw_values: list[str]) -> list[str]:
    if not raw_values:
        return list(SHIFT_IDS)
    if "all" in raw_values:
        return list(SHIFT_IDS)
    scoped: list[str] = []
    for value in raw_values:
        if value not in SHIFT_IDS:
            raise ValueError(f"Unsupported shift id: {value}")
        if value not in scoped:
            scoped.append(value)
    return scoped


def fetch_article_rows(
    master_cur: sqlite3.Cursor,
    analysis_cur: sqlite3.Cursor,
) -> list[dict]:
    master_rows = master_cur.execute(
        """
        SELECT
            a.article_uid,
            a.title,
            CAST(strftime('%Y', a.published_at) AS INTEGER) AS year
        FROM articles a
        WHERE a.status IN ('verified', 'published')
        ORDER BY a.published_at DESC, a.id DESC
        """
    ).fetchall()

    summary_rows = analysis_cur.execute(
        """
        SELECT article_uid, COALESCE(summary, '') AS summary
        FROM article_analysis
        """
    ).fetchall()
    summary_by_uid = {
        str(row["article_uid"]): str(row["summary"] or "")
        for row in summary_rows
    }

    out: list[dict] = []
    for row in master_rows:
        uid = str(row["article_uid"])
        out.append(
            {
                "article_uid": uid,
                "title": str(row["title"] or ""),
                "summary": summary_by_uid.get(uid, ""),
                "year": int(row["year"]),
            }
        )
    return out


def fetch_tags_by_article(cur: sqlite3.Cursor) -> dict[str, dict[str, set[str]]]:
    rows = cur.execute(
        """
        SELECT
            at.article_uid,
            t.name,
            t.slug
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_uid ASC
        """
    ).fetchall()

    tags_by_article: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        article_uid = str(row["article_uid"])
        bucket = tags_by_article.setdefault(article_uid, {"labels": set(), "slugs": set()})
        bucket["labels"].add(str(row["name"] or "").strip())
        bucket["slugs"].add(str(row["slug"] or "").strip())
    return tags_by_article


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
        "--shift-id",
        action="append",
        default=[],
        help="Shift id to process; pass multiple times. Use 'all' for all shifts.",
    )
    parser.add_argument(
        "--annotation-version",
        default="rule_based_v1",
        help="Version label for generated annotations.",
    )
    parser.add_argument(
        "--annotation-method",
        default="rule_based",
        help="Method label for annotation provenance.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview inserts without writing to DB.",
    )
    args = parser.parse_args()

    master_db_path = Path(args.master_db_path)
    analysis_db_path = Path(args.analysis_db_path)
    shift_scope = parse_shift_scope(args.shift_id)

    master_conn = sqlite3.connect(master_db_path)
    master_conn.row_factory = sqlite3.Row
    master_cur = master_conn.cursor()

    analysis_conn = sqlite3.connect(analysis_db_path)
    analysis_conn.row_factory = sqlite3.Row
    analysis_cur = analysis_conn.cursor()

    ensure_annotation_tables(analysis_cur)

    article_rows = fetch_article_rows(master_cur, analysis_cur)
    tags_by_article = fetch_tags_by_article(analysis_cur)

    run_uid = (
        f"shift-ann-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    )
    inserted = 0
    skipped = 0
    inserted_by_shift: dict[str, int] = defaultdict(int)
    skipped_by_shift: dict[str, int] = defaultdict(int)

    if not args.dry_run:
        analysis_cur.execute(
            """
            INSERT INTO shift_annotation_runs (
                run_uid,
                shift_scope,
                annotation_method,
                annotation_version,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_uid,
                ",".join(shift_scope),
                args.annotation_method,
                args.annotation_version,
                "Deterministic annotation generation from title + summary + tags (dual-db).",
            ),
        )

    for article in article_rows:
        article_uid = str(article["article_uid"])
        title = str(article["title"] or "").strip()
        summary = str(article["summary"] or "").strip()
        year = int(article["year"])
        tag_payload = tags_by_article.get(article_uid, {"labels": set(), "slugs": set()})
        tag_labels = sorted(tag_payload["labels"])
        tag_slugs = sorted(tag_payload["slugs"])
        corpus_text = " ".join([title, summary, " ".join(tag_labels), " ".join(tag_slugs)]).lower()

        for shift_id in shift_scope:
            rule = SHIFT_RULES[shift_id]
            phase = "before" if year < rule.milestone_year else "after"
            connection = build_connection(shift_id, corpus_text, phase)
            key_message = build_key_message(summary, shift_id, phase)
            fingerprint = build_input_fingerprint(
                shift_id=shift_id,
                phase=phase,
                title=title,
                summary=summary,
                year=year,
                tag_slugs=tag_slugs,
            )
            provenance_note = (
                "Generated from article title, summary, and tags via deterministic rules."
            )

            if args.dry_run:
                row = analysis_cur.execute(
                    """
                    SELECT 1
                    FROM shift_annotations
                    WHERE article_uid = ?
                      AND shift_id = ?
                      AND annotation_version = ?
                      AND input_fingerprint = ?
                    LIMIT 1
                    """,
                    (article_uid, shift_id, args.annotation_version, fingerprint),
                ).fetchone()
                if row:
                    skipped += 1
                    skipped_by_shift[shift_id] += 1
                else:
                    inserted += 1
                    inserted_by_shift[shift_id] += 1
                continue

            analysis_cur.execute(
                """
                INSERT OR IGNORE INTO shift_annotations (
                    article_uid,
                    shift_id,
                    phase,
                    connection_text,
                    key_message,
                    annotation_method,
                    annotation_version,
                    input_fingerprint,
                    run_uid,
                    provenance_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article_uid,
                    shift_id,
                    phase,
                    connection,
                    key_message,
                    args.annotation_method,
                    args.annotation_version,
                    fingerprint,
                    run_uid,
                    provenance_note,
                ),
            )
            if analysis_cur.rowcount == 1:
                inserted += 1
                inserted_by_shift[shift_id] += 1
            else:
                skipped += 1
                skipped_by_shift[shift_id] += 1

    if args.dry_run:
        print("Dry run: no DB writes performed.")
    else:
        analysis_cur.execute(
            """
            UPDATE shift_annotation_runs
            SET
                finished_at = CURRENT_TIMESTAMP,
                inserted_count = ?,
                skipped_count = ?
            WHERE run_uid = ?
            """,
            (inserted, skipped, run_uid),
        )
        analysis_conn.commit()

    print(f"Articles considered: {len(article_rows)}")
    print(f"Shift scope: {', '.join(shift_scope)}")
    print(f"Annotation method/version: {args.annotation_method}/{args.annotation_version}")
    print(f"Rows inserted: {inserted}")
    print(f"Rows skipped (already current): {skipped}")
    for shift_id in shift_scope:
        print(
            f"  - {shift_id}: inserted={inserted_by_shift[shift_id]}, skipped={skipped_by_shift[shift_id]}"
        )
    if not args.dry_run:
        print(f"Run UID: {run_uid}")
    print(f"Master DB path: {master_db_path}")
    print(f"Analysis DB path: {analysis_db_path}")

    master_conn.close()
    analysis_conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
