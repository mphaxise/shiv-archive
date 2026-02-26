#!/usr/bin/env python3
"""Generate quote-backed research evidence for the Science Shift track."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_METHOD = "rule_based_research"
DEFAULT_VERSION = "science_research_v1"

SCIENCE_ANCHORS = [
    "science",
    "scientific",
    "social science",
    "knowledge",
    "university",
    "expert",
    "innovation",
    "technology",
    "bureaucratic",
    "commons",
    "play",
    "playfulness",
    "panchayat",
    "cognitive justice",
    "public",
]

PHASE_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "before": {
        "institutional_knowledge": [
            "university",
            "institute",
            "institution",
            "csds",
            "social science",
            "expert",
            "discipline",
            "bureaucratic",
            "big science",
            "state policy",
        ],
        "diagnosing_closure": [
            "sadness",
            "gasping",
            "crisis",
            "hollow",
            "impoverished",
            "banal",
            "closure",
            "authoritarian",
            "violence",
        ],
        "democratic_learning": [
            "commons",
            "public sphere",
            "dissent",
            "dialogue",
            "secularism",
            "democracy",
            "citizen",
            "rights",
        ],
    },
    "after": {
        "distributed_publics": [
            "knowledge panchayat",
            "distributed",
            "plural",
            "cognitive justice",
            "orality",
            "commons",
            "publics",
            "citizen",
        ],
        "playful_science": [
            "play",
            "playfulness",
            "creative",
            "imagination",
            "experiment",
            "beyond big science",
            "creative society",
        ],
        "ethics_of_knowledge": [
            "ethics",
            "conscience",
            "humanity",
            "morality",
            "peace",
            "survival",
            "care",
        ],
    },
}

TAG_SIGNALS: dict[str, set[str]] = {
    "before": {
        "education-policy",
        "science-policy",
        "technology-and-society",
        "knowledge-systems",
        "public-institutions",
        "university",
        "secularism",
    },
    "after": {
        "science-policy",
        "technology-and-society",
        "knowledge-systems",
        "public-institutions",
        "pluralism",
        "ethics",
        "public-sphere",
        "ecology",
    },
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def split_paragraphs(body_text: str) -> list[str]:
    if not body_text:
        return []
    parts = [re.sub(r"\s+", " ", chunk).strip() for chunk in body_text.split("\n\n")]
    return [part for part in parts if len(part) >= 80]


def first_sentence(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "")).strip()
    if not normalized:
        return ""
    match = re.match(r"^(.+?[.!?])(\s|$)", normalized)
    return (match.group(1) if match else normalized).strip()


def shorten_quote(text: str, max_chars: int = 520) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
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


def count_occurrences(text: str, probes: list[str]) -> int:
    return sum(1 for probe in probes if probe in text)


def compute_group_hits(phase: str, text: str) -> dict[str, int]:
    groups = PHASE_KEYWORDS[phase]
    return {name: count_occurrences(text, probes) for name, probes in groups.items()}


def score_article(
    phase: str,
    title: str,
    summary: str,
    body_text: str,
    tag_slugs: list[str],
) -> tuple[float, dict[str, int], int, int]:
    title_norm = normalize(title)
    summary_norm = normalize(summary)
    body_norm = normalize(body_text)

    title_hits = compute_group_hits(phase, title_norm)
    summary_hits = compute_group_hits(phase, summary_norm)
    body_hits = compute_group_hits(phase, body_norm)

    group_hits = {
        group: (title_hits[group] * 4) + (summary_hits[group] * 2) + min(body_hits[group], 7)
        for group in PHASE_KEYWORDS[phase].keys()
    }
    phase_score = float(sum(group_hits.values()))
    anchor_hits = count_occurrences(" ".join([title_norm, summary_norm, body_norm]), SCIENCE_ANCHORS)
    tag_score = sum(1 for slug in tag_slugs if slug in TAG_SIGNALS[phase]) * 1.25
    total = phase_score + (anchor_hits * 0.85) + tag_score
    active_groups = sum(1 for value in group_hits.values() if value > 0)
    return total, group_hits, anchor_hits, active_groups


def paragraph_score(phase: str, paragraph: str) -> float:
    text = normalize(paragraph)
    group_hits = compute_group_hits(phase, text)
    anchors = count_occurrences(text, SCIENCE_ANCHORS)
    return float(sum(group_hits.values()) + (anchors * 1.5))


def pick_quote(phase: str, body_text: str, summary: str, title: str) -> tuple[str, str, float]:
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

    sentence = first_sentence(summary)
    if sentence:
        return sentence, "summary_sentence", 0.42
    return title.strip(), "title", 0.25


def strength_label(score: float) -> str:
    if score >= 18:
        return "strong"
    if score >= 11:
        return "moderate"
    return "weak"


def build_connection_text(phase: str, strongest_group: str) -> str:
    if phase == "before":
        if strongest_group == "institutional_knowledge":
            return "Phase 1 link: diagnoses how institutional science narrowed public imagination and democratic learning."
        if strongest_group == "diagnosing_closure":
            return "Phase 1 link: documents closure, exhaustion, and bureaucratic drift inside knowledge systems."
        return "Phase 1 link: treats science as a civic commons with democratic stakes."
    if strongest_group == "distributed_publics":
        return "Phase 2 link: advances distributed knowledge publics beyond expert monopolies."
    if strongest_group == "playful_science":
        return "Phase 2 link: recasts science as creative, experimental, and publicly co-authored."
    return "Phase 2 link: grounds knowledge politics in ethics, conscience, and social repair."


def build_rationale(
    phase: str,
    score: float,
    anchor_hits: int,
    group_hits: dict[str, int],
    selected: bool,
) -> str:
    strongest = sorted(group_hits.items(), key=lambda item: item[1], reverse=True)
    lead_group = strongest[0][0] if strongest else "none"
    hit_summary = ", ".join(f"{name}:{value}" for name, value in strongest)
    decision = (
        "Selected for narrative because concept fit and evidence density are high."
        if selected
        else "Not selected because relevance did not clear this cycle's strict cutoff."
    )
    return (
        f"{decision} Score={score:.1f}; phase={phase}; anchors={anchor_hits}; "
        f"lead_group={lead_group}; group_hits=[{hit_summary}]."
    )


def summarize_text(text: str, max_chars: int = 260) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def build_fingerprint(article_uid: str, phase: str, score: float, quote: str, tags: list[str]) -> str:
    payload = "|".join(
        [article_uid, phase, f"{score:.4f}", normalize(quote), ",".join(sorted(tags))]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def collect_data(
    master_conn: sqlite3.Connection, analysis_conn: sqlite3.Connection
) -> tuple[list[sqlite3.Row], dict[str, str], dict[str, list[str]], dict[str, str]]:
    phase_rows = analysis_conn.execute(
        """
        WITH latest AS (
            SELECT
                article_uid,
                phase,
                ROW_NUMBER() OVER (
                    PARTITION BY article_uid, shift_id
                    ORDER BY generated_at DESC, id DESC
                ) AS rn
            FROM shift_annotations
            WHERE shift_id = 'science_shift'
        )
        SELECT article_uid, phase
        FROM latest
        WHERE rn = 1
        """
    ).fetchall()
    phase_by_uid = {str(row["article_uid"]): str(row["phase"]) for row in phase_rows}

    summary_rows = analysis_conn.execute(
        """
        SELECT article_uid, COALESCE(summary, '') AS summary
        FROM article_analysis
        """
    ).fetchall()
    summary_by_uid = {str(row["article_uid"]): str(row["summary"] or "") for row in summary_rows}

    tag_rows = analysis_conn.execute(
        """
        SELECT at.article_uid, t.slug
        FROM article_tags at
        JOIN tags t ON t.id = at.tag_id
        ORDER BY at.article_uid ASC, t.slug ASC
        """
    ).fetchall()
    tags_by_uid: dict[str, list[str]] = defaultdict(list)
    for row in tag_rows:
        uid = str(row["article_uid"])
        slug = str(row["slug"])
        if slug not in tags_by_uid[uid]:
            tags_by_uid[uid].append(slug)

    article_rows = master_conn.execute(
        """
        SELECT
            a.article_uid,
            a.title,
            a.canonical_url AS url,
            a.published_at,
            p.name AS publication,
            COALESCE(tx.body_text, '') AS body_text,
            COALESCE(tx.text_state, 'missing') AS text_state
        FROM articles a
        JOIN publications p
          ON p.id = a.publication_id
        LEFT JOIN article_texts tx
          ON tx.article_uid = a.article_uid
         AND tx.is_primary = 1
        WHERE a.status IN ('verified', 'published')
        ORDER BY a.published_at ASC, a.id ASC
        """
    ).fetchall()
    return article_rows, summary_by_uid, tags_by_uid, phase_by_uid


def select_candidates(
    article_rows: list[sqlite3.Row],
    summary_by_uid: dict[str, str],
    tags_by_uid: dict[str, list[str]],
    phase_by_uid: dict[str, str],
    min_score: float,
    min_anchor_hits: int,
    min_group_hits: int,
    max_per_phase: int,
    backfill_to_cap: bool,
) -> tuple[list[dict], list[dict], dict[str, int], dict[str, int]]:
    all_candidates: list[dict] = []
    phase_totals = {"before": 0, "after": 0}
    phase_full_text_totals = {"before": 0, "after": 0}

    for row in article_rows:
        article_uid = str(row["article_uid"])
        if article_uid not in phase_by_uid:
            continue
        phase = phase_by_uid[article_uid]
        phase_totals[phase] += 1
        text_state = str(row["text_state"] or "missing")
        if text_state != "full":
            continue
        phase_full_text_totals[phase] += 1

        title = str(row["title"] or "")
        url = str(row["url"] or "")
        publication = str(row["publication"] or "")
        published_at = str(row["published_at"] or "")
        summary = summary_by_uid.get(article_uid, "")
        body_text = str(row["body_text"] or "")
        tag_slugs = tags_by_uid.get(article_uid, [])

        score, group_hits, anchor_hits, active_groups = score_article(
            phase=phase,
            title=title,
            summary=summary,
            body_text=body_text,
            tag_slugs=tag_slugs,
        )
        strongest_group = max(group_hits.items(), key=lambda item: item[1])[0]
        quote_text, quote_source, quote_confidence = pick_quote(
            phase=phase,
            body_text=body_text,
            summary=summary,
            title=title,
        )

        include = (
            score >= min_score
            and anchor_hits >= min_anchor_hits
            and active_groups >= min_group_hits
        )

        all_candidates.append(
            {
                "article_uid": article_uid,
                "phase": phase,
                "published_date": published_at[:10],
                "publication": publication,
                "title": title,
                "url": url,
                "summary_snippet": summarize_text(summary, max_chars=280),
                "signal_tags": [slug for slug in tag_slugs if slug in TAG_SIGNALS[phase]],
                "signal_count": sum(1 for slug in tag_slugs if slug in TAG_SIGNALS[phase]),
                "relevance_score": round(score, 2),
                "strength_label": strength_label(score),
                "anchor_hits": anchor_hits,
                "active_groups": active_groups,
                "group_hits": group_hits,
                "connection_text": build_connection_text(phase=phase, strongest_group=strongest_group),
                "quote_text": quote_text,
                "quote_source": quote_source,
                "quote_confidence": round(float(quote_confidence), 3),
                "candidate_include": include,
                "rationale": "",
                "include_in_story": False,
                "selection_reason": "",
                "fingerprint": build_fingerprint(
                    article_uid=article_uid,
                    phase=phase,
                    score=score,
                    quote=quote_text,
                    tags=tag_slugs,
                ),
            }
        )

    selected_uids: dict[str, set[str]] = {"before": set(), "after": set()}
    selected: list[dict] = []
    for phase in ("before", "after"):
        phase_rows = [row for row in all_candidates if row["phase"] == phase]
        phase_rows.sort(key=lambda row: (-float(row["relevance_score"]), row["published_date"]), reverse=False)

        auto_selected = [row for row in phase_rows if bool(row["candidate_include"])]
        auto_selected.sort(key=lambda row: (-float(row["relevance_score"]), row["published_date"]), reverse=False)
        picks = auto_selected[:max_per_phase]

        if backfill_to_cap and len(picks) < max_per_phase:
            picked_ids = {str(item["article_uid"]) for item in picks}
            for row in phase_rows:
                if row["article_uid"] in picked_ids:
                    continue
                picks.append(row)
                picked_ids.add(str(row["article_uid"]))
                if len(picks) >= max_per_phase:
                    break

        for row in picks:
            selected_uids[phase].add(str(row["article_uid"]))

    for row in all_candidates:
        row["include_in_story"] = str(row["article_uid"]) in selected_uids[row["phase"]]
        row["rationale"] = build_rationale(
            phase=row["phase"],
            score=float(row["relevance_score"]),
            anchor_hits=int(row["anchor_hits"]),
            group_hits=dict(row["group_hits"]),
            selected=bool(row["include_in_story"]),
        )
        if row["include_in_story"]:
            if row["candidate_include"]:
                row["selection_reason"] = "passed_threshold"
            else:
                row["selection_reason"] = "backfill_to_phase_cap"
            selected.append(row)
        else:
            row["selection_reason"] = "below_cutoff"

    selected.sort(key=lambda row: (row["phase"], -float(row["relevance_score"]), row["published_date"]))
    all_candidates.sort(
        key=lambda row: (row["phase"], -float(row["relevance_score"]), row["published_date"])
    )
    return selected, all_candidates, phase_totals, phase_full_text_totals


def build_markdown(
    selected: list[dict],
    method: str,
    version: str,
    generated_at: str,
    min_score: float,
    min_anchor_hits: int,
    min_group_hits: int,
    max_per_phase: int,
    phase_totals: dict[str, int],
    phase_full_text_totals: dict[str, int],
    top_n: int = 6,
) -> str:
    selected_before = [row for row in selected if row["phase"] == "before"]
    selected_after = [row for row in selected if row["phase"] == "after"]

    lines: list[str] = []
    lines.append("# Science Shift Research Brief")
    lines.append("")
    lines.append(f"Generated at: {generated_at}")
    lines.append(f"Method/version: {method}/{version}")
    lines.append("")
    lines.append("## Selection Parameters")
    lines.append("")
    lines.append(f"- min_score: {min_score}")
    lines.append(f"- min_anchor_hits: {min_anchor_hits}")
    lines.append(f"- min_group_hits: {min_group_hits}")
    lines.append(f"- max_per_phase: {max_per_phase}")
    lines.append("")
    lines.append("## Coverage Snapshot")
    lines.append("")
    lines.append(f"- before candidates: {phase_totals['before']} (full text: {phase_full_text_totals['before']})")
    lines.append(f"- after candidates: {phase_totals['after']} (full text: {phase_full_text_totals['after']})")
    lines.append(f"- selected before: {len(selected_before)}")
    lines.append(f"- selected after: {len(selected_after)}")
    lines.append("")
    lines.append("## Working Thesis")
    lines.append("")
    lines.append(
        "- The archive moves from diagnosing institutional closure of knowledge systems to proposing distributed, playful, and ethically grounded knowledge publics."
    )
    lines.append("")
    lines.append("## Phase 1 Evidence (Before)")
    lines.append("")
    for index, row in enumerate(selected_before[:top_n], start=1):
        lines.append(
            f"{index}. {row['published_date']} | {row['title']} ({row['publication']}) | score {row['relevance_score']}"
        )
        lines.append(f"Quote: \"{row['quote_text']}\"")
        lines.append(f"Why it matters: {row['connection_text']}")
        lines.append("")
    lines.append("## Phase 2 Evidence (After)")
    lines.append("")
    for index, row in enumerate(selected_after[:top_n], start=1):
        lines.append(
            f"{index}. {row['published_date']} | {row['title']} ({row['publication']}) | score {row['relevance_score']}"
        )
        lines.append(f"Quote: \"{row['quote_text']}\"")
        lines.append(f"Why it matters: {row['connection_text']}")
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Evidence and scoring are rule-based and intended for comparative research triage, not final interpretive truth.")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
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
        "--output-json",
        required=True,
        help="Output JSON path for research evidence packet.",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Output Markdown path for readable research brief.",
    )
    parser.add_argument("--method", default=DEFAULT_METHOD, help="Method label.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Version label.")
    parser.add_argument("--max-per-phase", type=int, default=12, help="Max selected per phase.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=14.0,
        help="Minimum relevance score for automatic selection.",
    )
    parser.add_argument(
        "--min-anchor-hits",
        type=int,
        default=2,
        help="Minimum anchor hits for automatic selection.",
    )
    parser.add_argument(
        "--min-group-hits",
        type=int,
        default=2,
        help="Minimum active concept groups for automatic selection.",
    )
    parser.add_argument(
        "--no-backfill",
        action="store_true",
        help="Do not fill to per-phase cap when strict filters yield fewer results.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    master_conn = sqlite3.connect(Path(args.master_db_path))
    analysis_conn = sqlite3.connect(Path(args.analysis_db_path))
    master_conn.row_factory = sqlite3.Row
    analysis_conn.row_factory = sqlite3.Row

    article_rows, summary_by_uid, tags_by_uid, phase_by_uid = collect_data(master_conn, analysis_conn)
    selected, candidates, phase_totals, phase_full_text_totals = select_candidates(
        article_rows=article_rows,
        summary_by_uid=summary_by_uid,
        tags_by_uid=tags_by_uid,
        phase_by_uid=phase_by_uid,
        min_score=float(args.min_score),
        min_anchor_hits=int(args.min_anchor_hits),
        min_group_hits=int(args.min_group_hits),
        max_per_phase=int(args.max_per_phase),
        backfill_to_cap=not bool(args.no_backfill),
    )

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = {
        "generated_at": generated_at,
        "shift_id": "science_shift",
        "method": args.method,
        "version": args.version,
        "selection_params": {
            "max_per_phase": int(args.max_per_phase),
            "min_score": float(args.min_score),
            "min_anchor_hits": int(args.min_anchor_hits),
            "min_group_hits": int(args.min_group_hits),
            "backfill_to_phase_cap": not bool(args.no_backfill),
            "full_text_only": True,
            "latest_shift_annotation_only": True,
        },
        "phase_totals": phase_totals,
        "phase_full_text_totals": phase_full_text_totals,
        "selected_counts": {
            "before": sum(1 for row in selected if row["phase"] == "before"),
            "after": sum(1 for row in selected if row["phase"] == "after"),
        },
        "selected_records": selected,
        "candidate_records": candidates,
    }

    output_json_path = Path(args.output_json)
    output_md_path = Path(args.output_md)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    brief = build_markdown(
        selected=selected,
        method=args.method,
        version=args.version,
        generated_at=generated_at,
        min_score=float(args.min_score),
        min_anchor_hits=int(args.min_anchor_hits),
        min_group_hits=int(args.min_group_hits),
        max_per_phase=int(args.max_per_phase),
        phase_totals=phase_totals,
        phase_full_text_totals=phase_full_text_totals,
    )
    output_md_path.write_text(brief, encoding="utf-8")

    print(f"Science candidates (full text): {len(candidates)}")
    print(f"Selected before: {payload['selected_counts']['before']}")
    print(f"Selected after: {payload['selected_counts']['after']}")
    print(f"Output JSON: {output_json_path}")
    print(f"Output MD: {output_md_path}")

    master_conn.close()
    analysis_conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
