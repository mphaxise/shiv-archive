#!/usr/bin/env python3
"""Generate strict, auditable Republic-shift evidence with quote-backed rationale."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

MILESTONE_YEAR = 2024
DEFAULT_METHOD = "rule_based_critical"
DEFAULT_VERSION = "critical_v1"

REPUBLIC_ANCHORS = [
    "republic",
    "constitution",
    "constitutional",
    "democracy",
    "democratic",
    "citizenship",
    "citizen",
    "state",
    "institution",
    "majoritarian",
    "public sphere",
]

PHASE_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "before": {
        "institutional_grammar": [
            "constitution",
            "constitutional",
            "institution",
            "nehru",
            "state",
            "citizenship",
            "citizen",
            "left and right",
            "secularism",
            "university",
        ],
        "decay_diagnostics": [
            "drying up",
            "sadness",
            "banal",
            "mediocre",
            "decay",
            "hollow",
            "crisis",
            "erosion",
            "impoverishes",
            "violence",
        ],
        "democratic_urgency": [
            "public sphere",
            "civil society",
            "dissent",
            "rights",
            "ethics",
            "morality",
            "democracy",
        ],
    },
    "after": {
        "new_grammar": [
            "second republic",
            "new republic",
            "reimagining democracy",
            "improvis",
            "digital",
            "populist",
            "knowledge panchayat",
            "citizen back",
        ],
        "embodied_ethics": [
            "body politics",
            "yatra",
            "satyagraha",
            "playfulness",
            "moral",
            "ethics",
            "conscience",
            "peace",
        ],
        "plural_futures": [
            "anthropocene",
            "ecocide",
            "cognitive justice",
            "plural",
            "commons",
            "survival",
            "knowledge systems",
        ],
    },
}

TAG_SLUG_SIGNALS = {
    "before": {
        "democracy",
        "law-and-justice",
        "public-institutions",
        "public-sphere",
        "nationalism",
        "secularism",
        "education-policy",
    },
    "after": {
        "democracy",
        "pluralism",
        "ethics",
        "knowledge-systems",
        "ecology",
        "technology-and-society",
        "public-sphere",
    },
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def split_paragraphs(body_text: str) -> list[str]:
    if not body_text:
        return []
    parts = [re.sub(r"\s+", " ", chunk).strip() for chunk in body_text.split("\n\n")]
    return [part for part in parts if len(part) >= 70]


def first_sentence(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "")).strip()
    if not normalized:
        return ""
    match = re.match(r"^(.+?[.!?])(\s|$)", normalized)
    return (match.group(1) if match else normalized).strip()


def count_occurrences(text: str, probes: list[str]) -> int:
    score = 0
    for probe in probes:
        if probe in text:
            score += 1
    return score


def compute_group_hits(phase: str, text: str) -> dict[str, int]:
    groups = PHASE_KEYWORDS[phase]
    return {group: count_occurrences(text, probes) for group, probes in groups.items()}


def score_article(
    phase: str,
    title: str,
    summary: str,
    tag_slugs: list[str],
    body_text: str,
) -> tuple[float, dict[str, int], int, int]:
    title_norm = normalize(title)
    summary_norm = normalize(summary)
    body_norm = normalize(body_text)

    groups_title = compute_group_hits(phase, title_norm)
    groups_summary = compute_group_hits(phase, summary_norm)
    groups_body = compute_group_hits(phase, body_norm)

    group_hits = {
        group: (groups_title[group] * 4) + (groups_summary[group] * 2) + min(groups_body[group], 6)
        for group in PHASE_KEYWORDS[phase].keys()
    }
    phase_score = float(sum(group_hits.values()))

    anchor_hits = count_occurrences(
        " ".join([title_norm, summary_norm, body_norm]),
        REPUBLIC_ANCHORS,
    )

    tag_score = sum(1 for slug in tag_slugs if slug in TAG_SLUG_SIGNALS[phase]) * 1.3
    total_score = phase_score + tag_score + (anchor_hits * 0.8)

    return total_score, group_hits, anchor_hits, int(sum(1 for value in group_hits.values() if value > 0))


def strength_label(score: float) -> str:
    if score >= 18:
        return "strong"
    if score >= 11:
        return "moderate"
    return "weak"


def build_connection_text(phase: str, strongest_group: str) -> str:
    if phase == "before":
        if strongest_group == "institutional_grammar":
            return "Strongly linked to Phase 1 because it interrogates constitutional-institutional grammar central to the First Republic."
        if strongest_group == "decay_diagnostics":
            return "Strongly linked to Phase 1 because it diagnoses democratic erosion within First Republic structures."
        return "Strongly linked to Phase 1 because it treats ethics, dissent, and civic urgency as responses to institutional decline."
    if strongest_group == "new_grammar":
        return "Strongly linked to Phase 2 because it articulates emerging vocabularies of a contested Second Republic."
    if strongest_group == "embodied_ethics":
        return "Strongly linked to Phase 2 because it shifts politics toward embodied action, moral imagination, and public pedagogy."
    return "Strongly linked to Phase 2 because it reframes democratic futures through plural knowledge and ecological survival."


def build_rationale(
    phase: str,
    score: float,
    anchor_hits: int,
    group_hits: dict[str, int],
    selected: bool,
) -> str:
    strongest = sorted(group_hits.items(), key=lambda item: item[1], reverse=True)
    lead = strongest[0][0] if strongest else "none"
    group_summary = ", ".join(f"{name}:{value}" for name, value in strongest)
    decision = (
        "Selected for narrative because relevance is high and concept coverage is multi-dimensional."
        if selected
        else "Excluded from core narrative because relevance is insufficient under strict selection criteria."
    )
    return (
        f"{decision} Score={score:.1f}; phase={phase}; anchors={anchor_hits}; "
        f"lead_group={lead}; group_hits=[{group_summary}]."
    )


def paragraph_score(phase: str, paragraph: str) -> float:
    text = normalize(paragraph)
    group_hits = compute_group_hits(phase, text)
    anchors = count_occurrences(text, REPUBLIC_ANCHORS)
    return float(sum(group_hits.values()) + (anchors * 1.5))


def shorten_quote(paragraph: str, max_chars: int = 520) -> str:
    clean = re.sub(r"\s+", " ", paragraph).strip()
    if len(clean) <= max_chars:
        return clean
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    selected: list[str] = []
    total = 0
    for sentence in sentences:
        if not sentence:
            continue
        new_total = total + len(sentence) + (1 if selected else 0)
        if new_total > max_chars:
            break
        selected.append(sentence)
        total = new_total
    if selected:
        return " ".join(selected).strip()
    return clean[:max_chars].rsplit(" ", 1)[0].strip()


def choose_quote(phase: str, body_text: str, summary: str, title: str) -> tuple[str, str, float]:
    paragraphs = split_paragraphs(body_text)
    if paragraphs:
        ranked = sorted(
            ((paragraph_score(phase, paragraph), paragraph) for paragraph in paragraphs),
            key=lambda item: item[0],
            reverse=True,
        )
        best_score, best_paragraph = ranked[0]
        if best_score > 0:
            return shorten_quote(best_paragraph), "body_paragraph", min(1.0, 0.45 + (best_score / 20))

    summary_sentence = first_sentence(summary)
    if summary_sentence:
        return summary_sentence, "summary_sentence", 0.42
    return title.strip(), "title", 0.25


def ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS republic_shift_evidence_runs (
            id INTEGER PRIMARY KEY,
            run_uid TEXT NOT NULL UNIQUE,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT,
            method TEXT NOT NULL,
            version TEXT NOT NULL,
            inserted_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            selected_before_count INTEGER NOT NULL DEFAULT 0,
            selected_after_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS republic_shift_evidence (
            id INTEGER PRIMARY KEY,
            article_uid TEXT NOT NULL,
            phase TEXT NOT NULL CHECK (phase IN ('before', 'after')),
            include_in_story INTEGER NOT NULL CHECK (include_in_story IN (0, 1)),
            relevance_score REAL NOT NULL,
            strength_label TEXT NOT NULL CHECK (strength_label IN ('strong', 'moderate', 'weak')),
            connection_text TEXT NOT NULL,
            rationale TEXT NOT NULL,
            quote_text TEXT NOT NULL,
            quote_source TEXT NOT NULL CHECK (quote_source IN ('body_paragraph', 'summary_sentence', 'title')),
            quote_confidence REAL NOT NULL CHECK (quote_confidence >= 0.0 AND quote_confidence <= 1.0),
            method TEXT NOT NULL,
            version TEXT NOT NULL,
            input_fingerprint TEXT NOT NULL,
            run_uid TEXT NOT NULL REFERENCES republic_shift_evidence_runs(run_uid) ON DELETE RESTRICT,
            generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_republic_shift_evidence_unique_input
        ON republic_shift_evidence(article_uid, version, input_fingerprint);

        CREATE INDEX IF NOT EXISTS idx_republic_shift_evidence_lookup
        ON republic_shift_evidence(article_uid, generated_at DESC, id DESC);

        CREATE INDEX IF NOT EXISTS idx_republic_shift_evidence_selected
        ON republic_shift_evidence(include_in_story, phase, relevance_score DESC);
        """
    )


def build_fingerprint(
    article_uid: str,
    phase: str,
    score: float,
    summary: str,
    tag_slugs: list[str],
    quote: str,
) -> str:
    payload = "|".join(
        [
            article_uid,
            phase,
            f"{score:.4f}",
            normalize(summary),
            ",".join(sorted(tag_slugs)),
            normalize(quote),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_master.db",
        help="Path to master DB.",
    )
    parser.add_argument(
        "--analysis-db-path",
        default="/Users/praneet/shiv-archive/data/shiv_analysis.db",
        help="Path to analysis DB.",
    )
    parser.add_argument(
        "--method",
        default=DEFAULT_METHOD,
        help="Method label.",
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help="Version label.",
    )
    parser.add_argument(
        "--max-per-phase",
        type=int,
        default=12,
        help="Maximum selected articles per phase.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=14.0,
        help="Minimum score to be selectable.",
    )
    parser.add_argument(
        "--min-anchor-hits",
        type=int,
        default=3,
        help="Minimum Republic anchor-term hits required for selection.",
    )
    parser.add_argument(
        "--min-group-hits",
        type=int,
        default=2,
        help="Minimum number of concept groups with non-zero hits required for selection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writes.",
    )
    args = parser.parse_args()

    master_conn = sqlite3.connect(Path(args.master_db_path))
    analysis_conn = sqlite3.connect(Path(args.analysis_db_path))
    master_conn.row_factory = sqlite3.Row
    analysis_conn.row_factory = sqlite3.Row
    master_cur = master_conn.cursor()
    analysis_cur = analysis_conn.cursor()

    ensure_tables(analysis_cur)

    tag_rows = analysis_cur.execute(
        """
        SELECT at.article_uid, t.slug
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_uid ASC
        """
    ).fetchall()
    tag_slugs_by_uid: dict[str, list[str]] = defaultdict(list)
    for row in tag_rows:
        uid = str(row["article_uid"])
        slug = str(row["slug"])
        if slug not in tag_slugs_by_uid[uid]:
            tag_slugs_by_uid[uid].append(slug)

    summary_rows = analysis_cur.execute(
        """
        SELECT article_uid, COALESCE(summary, '') AS summary
        FROM article_analysis
        """
    ).fetchall()
    summary_by_uid = {str(row["article_uid"]): str(row["summary"] or "") for row in summary_rows}

    rows = master_cur.execute(
        """
        SELECT
            a.article_uid,
            a.title,
            a.published_at,
            CAST(strftime('%Y', a.published_at) AS INTEGER) AS year,
            COALESCE(tx.body_text, '') AS body_text
        FROM articles a
        LEFT JOIN article_texts tx
            ON tx.article_uid = a.article_uid
           AND tx.is_primary = 1
        WHERE a.status IN ('verified', 'published')
        ORDER BY a.published_at ASC, a.id ASC
        """
    ).fetchall()

    candidates: list[dict] = []
    for row in rows:
        article_uid = str(row["article_uid"])
        title = str(row["title"] or "")
        summary = summary_by_uid.get(article_uid, "")
        body_text = str(row["body_text"] or "")
        year = int(row["year"])
        phase = "before" if year < MILESTONE_YEAR else "after"
        tag_slugs = tag_slugs_by_uid.get(article_uid, [])

        score, group_hits, anchor_hits, active_groups = score_article(
            phase=phase,
            title=title,
            summary=summary,
            tag_slugs=tag_slugs,
            body_text=body_text,
        )
        strongest_group = max(group_hits.items(), key=lambda item: item[1])[0]
        should_include = (
            score >= float(args.min_score)
            and anchor_hits >= int(args.min_anchor_hits)
            and active_groups >= int(args.min_group_hits)
        )
        quote_text, quote_source, quote_confidence = choose_quote(
            phase=phase,
            body_text=body_text,
            summary=summary,
            title=title,
        )
        connection_text = build_connection_text(phase=phase, strongest_group=strongest_group)
        rationale = build_rationale(
            phase=phase,
            score=score,
            anchor_hits=anchor_hits,
            group_hits=group_hits,
            selected=should_include,
        )
        candidates.append(
            {
                "article_uid": article_uid,
                "published_at": str(row["published_at"]),
                "phase": phase,
                "score": score,
                "strength": strength_label(score),
                "include": should_include,
                "connection": connection_text,
                "rationale": rationale,
                "quote_text": quote_text,
                "quote_source": quote_source,
                "quote_confidence": quote_confidence,
                "summary": summary,
                "tag_slugs": tag_slugs,
            }
        )

    selected_ids_by_phase: dict[str, set[str]] = {"before": set(), "after": set()}
    for phase in ("before", "after"):
        phase_candidates = [row for row in candidates if row["phase"] == phase and row["include"]]
        phase_candidates.sort(key=lambda row: (-row["score"], row["published_at"]))
        for row in phase_candidates[: int(args.max_per_phase)]:
            selected_ids_by_phase[phase].add(str(row["article_uid"]))

    run_uid = f"repcrit-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    inserted = 0
    skipped = 0

    if not args.dry_run:
        analysis_cur.execute(
            """
            INSERT INTO republic_shift_evidence_runs (
                run_uid,
                method,
                version,
                notes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                run_uid,
                args.method,
                args.version,
                (
                    "Strict selection for Republic shift with "
                    f"max_per_phase={args.max_per_phase}, min_score={args.min_score}, "
                    f"min_anchor_hits={args.min_anchor_hits}, min_group_hits={args.min_group_hits}."
                ),
            ),
        )

    for row in candidates:
        phase = str(row["phase"])
        article_uid = str(row["article_uid"])
        include_in_story = 1 if article_uid in selected_ids_by_phase[phase] else 0
        rationale = row["rationale"]
        if include_in_story == 0 and row["include"]:
            rationale = (
                f"Excluded due to per-phase cap despite passing score threshold. {row['rationale']}"
            )

        fingerprint = build_fingerprint(
            article_uid=article_uid,
            phase=phase,
            score=float(row["score"]),
            summary=str(row["summary"]),
            tag_slugs=list(row["tag_slugs"]),
            quote=str(row["quote_text"]),
        )

        exists = analysis_cur.execute(
            """
            SELECT 1
            FROM republic_shift_evidence
            WHERE article_uid = ?
              AND version = ?
              AND input_fingerprint = ?
            LIMIT 1
            """,
            (article_uid, args.version, fingerprint),
        ).fetchone()
        if exists:
            skipped += 1
            continue

        inserted += 1
        if args.dry_run:
            continue

        analysis_cur.execute(
            """
            INSERT INTO republic_shift_evidence (
                article_uid,
                phase,
                include_in_story,
                relevance_score,
                strength_label,
                connection_text,
                rationale,
                quote_text,
                quote_source,
                quote_confidence,
                method,
                version,
                input_fingerprint,
                run_uid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_uid,
                phase,
                include_in_story,
                float(row["score"]),
                str(row["strength"]),
                str(row["connection"]),
                rationale,
                str(row["quote_text"]),
                str(row["quote_source"]),
                float(row["quote_confidence"]),
                args.method,
                args.version,
                fingerprint,
                run_uid,
            ),
        )

    selected_before = len(selected_ids_by_phase["before"])
    selected_after = len(selected_ids_by_phase["after"])

    if not args.dry_run:
        analysis_cur.execute(
            """
            UPDATE republic_shift_evidence_runs
            SET
                finished_at = CURRENT_TIMESTAMP,
                inserted_count = ?,
                skipped_count = ?,
                selected_before_count = ?,
                selected_after_count = ?
            WHERE run_uid = ?
            """,
            (inserted, skipped, selected_before, selected_after, run_uid),
        )
        analysis_conn.commit()

    print(f"Articles considered: {len(candidates)}")
    print(f"Inserted rows: {inserted}")
    print(f"Skipped rows: {skipped}")
    print(f"Selected (before): {selected_before}")
    print(f"Selected (after): {selected_after}")
    print(f"Method/version: {args.method}/{args.version}")
    if not args.dry_run:
        print(f"Run UID: {run_uid}")
    print(f"Master DB path: {args.master_db_path}")
    print(f"Analysis DB path: {args.analysis_db_path}")

    master_conn.close()
    analysis_conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
