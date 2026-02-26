#!/usr/bin/env python3
"""Generate quote-backed research evidence packet for the Republic Shift track."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_METHOD = "republic_research_packet"
DEFAULT_VERSION = "republic_research_v1"

LEAD_GROUPS = {
    "institutional_grammar",
    "decay_diagnostics",
    "democratic_urgency",
    "new_grammar",
    "embodied_ethics",
    "plural_futures",
    "cross_currents",
}

TAG_SIGNALS: dict[str, set[str]] = {
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

ARGUMENT_TEXT: dict[str, str] = {
    "institutional_grammar":
        "The article argues that constitutional language is surviving while institutional guarantees are weakening in practice.",
    "decay_diagnostics":
        "The article argues that democratic erosion is systemic, not episodic, and is visible in ordinary institutional life.",
    "democratic_urgency":
        "The article argues that ethics, dissent, and civic imagination are now prerequisites for democratic repair.",
    "new_grammar":
        "The article argues that a contested Second Republic is being built through new participatory vocabularies.",
    "embodied_ethics":
        "The article argues that democratic practice must move from abstraction to embodied ethics and public pedagogy.",
    "plural_futures":
        "The article argues that democratic futures require ecological responsibility and plural knowledge systems.",
    "cross_currents":
        "The article argues that democracy now depends on connecting institutional critique with constructive civic invention.",
}


def normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def summarize_text(text: str | None, max_chars: int = 280) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "..."


def parse_lead_group(rationale: str) -> str:
    match = re.search(r"lead_group=([a-z_]+)", rationale or "")
    lead_group = (match.group(1) if match else "").strip()
    if lead_group in LEAD_GROUPS:
        return lead_group
    return "cross_currents"


def classify_unselected_reason(row: dict, full_text_only: bool) -> str:
    if row["candidate_include"] and full_text_only and row["text_state"] != "full":
        return "blocked_non_full_text"
    if row["candidate_include"]:
        if "per-phase cap" in str(row["rationale"]).lower():
            return "below_phase_cap"
        return "below_cutoff"
    return "below_cutoff"


def collect_data(
    master_conn: sqlite3.Connection, analysis_conn: sqlite3.Connection
) -> tuple[list[sqlite3.Row], dict[str, str], dict[str, list[str]], sqlite3.Row | None]:
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

    evidence_rows = analysis_conn.execute(
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
        ORDER BY e.relevance_score DESC, e.article_uid ASC
        """
    ).fetchall()

    latest_run = analysis_conn.execute(
        """
        SELECT
            run_uid,
            started_at,
            finished_at,
            method,
            version,
            inserted_count,
            skipped_count,
            selected_before_count,
            selected_after_count,
            notes
        FROM republic_shift_evidence_runs
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    return evidence_rows, summary_by_uid, tags_by_uid, latest_run


def build_candidates(
    evidence_rows: list[sqlite3.Row],
    summary_by_uid: dict[str, str],
    tags_by_uid: dict[str, list[str]],
    master_conn: sqlite3.Connection,
) -> list[dict]:
    article_rows = master_conn.execute(
        """
        SELECT
            a.article_uid,
            a.title,
            a.canonical_url AS url,
            a.published_at,
            p.name AS publication,
            COALESCE(tx.text_state, 'missing') AS text_state
        FROM articles a
        JOIN publications p
          ON p.id = a.publication_id
        LEFT JOIN article_texts tx
          ON tx.article_uid = a.article_uid
         AND tx.is_primary = 1
        WHERE a.status IN ('verified', 'published')
        """
    ).fetchall()
    article_by_uid = {str(row["article_uid"]): row for row in article_rows}

    candidates: list[dict] = []
    for row in evidence_rows:
        uid = str(row["article_uid"])
        article = article_by_uid.get(uid)
        if article is None:
            continue

        phase = str(row["phase"])
        tag_slugs = tags_by_uid.get(uid, [])
        lead_group = parse_lead_group(str(row["rationale"] or ""))
        connection = str(row["connection_text"] or "").strip()
        argument_text = ARGUMENT_TEXT.get(lead_group, ARGUMENT_TEXT["cross_currents"])
        summary = summarize_text(summary_by_uid.get(uid, ""), max_chars=300)

        candidates.append(
            {
                "article_uid": uid,
                "phase": phase,
                "published_date": str(article["published_at"] or "")[:10],
                "publication": str(article["publication"] or ""),
                "title": str(article["title"] or ""),
                "url": str(article["url"] or ""),
                "summary_snippet": summary,
                "signal_tags": [slug for slug in tag_slugs if slug in TAG_SIGNALS[phase]],
                "signal_count": sum(1 for slug in tag_slugs if slug in TAG_SIGNALS[phase]),
                "relevance_score": float(row["relevance_score"]),
                "strength_label": str(row["strength_label"]),
                "lead_group": lead_group,
                "argument_text": argument_text,
                "connection_text": connection,
                "quote_text": str(row["quote_text"] or "").strip(),
                "quote_source": str(row["quote_source"]),
                "quote_confidence": float(row["quote_confidence"]),
                "candidate_include": bool(row["include_in_story"]),
                "rationale": str(row["rationale"] or ""),
                "include_in_story": False,
                "selection_reason": "",
                "fingerprint": str(row["input_fingerprint"] or ""),
                "text_state": str(article["text_state"] or "missing"),
                "evidence_method": str(row["method"]),
                "evidence_version": str(row["version"]),
                "evidence_run_uid": str(row["run_uid"]),
                "evidence_generated_at": str(row["generated_at"]),
            }
        )

    candidates.sort(
        key=lambda item: (item["phase"], -float(item["relevance_score"]), item["published_date"], item["title"])
    )
    return candidates


def select_records(
    candidates: list[dict],
    max_per_phase: int,
    full_text_only: bool,
    backfill_to_cap: bool,
) -> tuple[list[dict], dict[str, int], dict[str, int]]:
    phase_totals = {"before": 0, "after": 0}
    phase_full_text_totals = {"before": 0, "after": 0}
    for row in candidates:
        phase = row["phase"]
        phase_totals[phase] += 1
        if row["text_state"] == "full":
            phase_full_text_totals[phase] += 1

    selected_uids: dict[str, set[str]] = {"before": set(), "after": set()}
    for phase in ("before", "after"):
        phase_rows = [row for row in candidates if row["phase"] == phase]
        eligible = [
            row
            for row in phase_rows
            if (not full_text_only or row["text_state"] == "full") and bool(row["candidate_include"])
        ]
        eligible.sort(
            key=lambda item: (-float(item["relevance_score"]), item["published_date"], item["title"])
        )
        picks = eligible[:max_per_phase]

        if backfill_to_cap and len(picks) < max_per_phase:
            picked_uids = {str(item["article_uid"]) for item in picks}
            fallback_pool = [
                row
                for row in phase_rows
                if (not full_text_only or row["text_state"] == "full")
                and str(row["article_uid"]) not in picked_uids
            ]
            fallback_pool.sort(
                key=lambda item: (-float(item["relevance_score"]), item["published_date"], item["title"])
            )
            for row in fallback_pool:
                picks.append(row)
                picked_uids.add(str(row["article_uid"]))
                if len(picks) >= max_per_phase:
                    break

        selected_uids[phase] = {str(item["article_uid"]) for item in picks}

    selected_records: list[dict] = []
    for row in candidates:
        phase = row["phase"]
        uid = str(row["article_uid"])
        row["include_in_story"] = uid in selected_uids[phase]
        if row["include_in_story"]:
            if bool(row["candidate_include"]):
                row["selection_reason"] = "passed_threshold"
            else:
                row["selection_reason"] = "backfill_to_phase_cap"
            selected_records.append(row)
        else:
            row["selection_reason"] = classify_unselected_reason(row, full_text_only)
            if row["selection_reason"] == "blocked_non_full_text":
                row["rationale"] = (
                    "Not selected for packet because strict mode requires full-text evidence. "
                    + str(row["rationale"])
                ).strip()

    selected_records.sort(
        key=lambda item: (item["phase"], -float(item["relevance_score"]), item["published_date"], item["title"])
    )
    return selected_records, phase_totals, phase_full_text_totals


def build_markdown(
    selected: list[dict],
    generated_at: str,
    method: str,
    version: str,
    max_per_phase: int,
    full_text_only: bool,
    backfill_to_cap: bool,
    phase_totals: dict[str, int],
    phase_full_text_totals: dict[str, int],
    top_n: int = 6,
) -> str:
    selected_before = [row for row in selected if row["phase"] == "before"]
    selected_after = [row for row in selected if row["phase"] == "after"]

    lines: list[str] = []
    lines.append("# Republic Shift Research Brief")
    lines.append("")
    lines.append(f"Generated at: {generated_at}")
    lines.append(f"Method/version: {method}/{version}")
    lines.append("")
    lines.append("## Selection Parameters")
    lines.append("")
    lines.append(f"- max_per_phase: {max_per_phase}")
    lines.append(f"- full_text_only: {str(full_text_only).lower()}")
    lines.append(f"- backfill_to_phase_cap: {str(backfill_to_cap).lower()}")
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
        "- The archive moves from diagnosing First Republic institutional erosion toward constructing a contested Second Republic through civic invention."
    )
    lines.append("")
    lines.append("## Phase 1 Evidence (Before)")
    lines.append("")
    for index, row in enumerate(selected_before[:top_n], start=1):
        lines.append(
            f"{index}. {row['published_date']} | {row['title']} ({row['publication']}) | score {row['relevance_score']:.2f}"
        )
        lines.append(f"Summary: {row['summary_snippet']}")
        lines.append(f"Takeaway: {row['argument_text']} {row['connection_text']}".strip())
        lines.append("")
    lines.append("## Phase 2 Evidence (After)")
    lines.append("")
    for index, row in enumerate(selected_after[:top_n], start=1):
        lines.append(
            f"{index}. {row['published_date']} | {row['title']} ({row['publication']}) | score {row['relevance_score']:.2f}"
        )
        lines.append(f"Summary: {row['summary_snippet']}")
        lines.append(f"Takeaway: {row['argument_text']} {row['connection_text']}".strip())
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Packet output is a research artifact for comparative narrative curation and auditability.")
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
        help="Output JSON path for republic packet.",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Output Markdown path for republic brief.",
    )
    parser.add_argument("--method", default=DEFAULT_METHOD, help="Method label.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Version label.")
    parser.add_argument("--max-per-phase", type=int, default=12, help="Maximum selected per phase.")
    parser.add_argument(
        "--allow-non-full-text",
        action="store_true",
        help="Allow non-full-text records in selected output.",
    )
    parser.add_argument(
        "--no-backfill",
        action="store_true",
        help="Do not backfill selected lists to the per-phase cap.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    full_text_only = not bool(args.allow_non_full_text)
    backfill_to_cap = not bool(args.no_backfill)

    master_conn = sqlite3.connect(Path(args.master_db_path))
    analysis_conn = sqlite3.connect(Path(args.analysis_db_path))
    master_conn.row_factory = sqlite3.Row
    analysis_conn.row_factory = sqlite3.Row

    evidence_rows, summary_by_uid, tags_by_uid, latest_run = collect_data(master_conn, analysis_conn)
    if not evidence_rows:
        raise SystemExit("No republic_shift_evidence rows found. Run generate_republic_critical_evidence.py first.")

    candidates = build_candidates(evidence_rows, summary_by_uid, tags_by_uid, master_conn)
    selected, phase_totals, phase_full_text_totals = select_records(
        candidates=candidates,
        max_per_phase=int(args.max_per_phase),
        full_text_only=full_text_only,
        backfill_to_cap=backfill_to_cap,
    )

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    payload = {
        "generated_at": generated_at,
        "shift_id": "republic_shift",
        "method": args.method,
        "version": args.version,
        "selection_params": {
            "max_per_phase": int(args.max_per_phase),
            "full_text_only": full_text_only,
            "backfill_to_phase_cap": backfill_to_cap,
            "source": "latest_republic_shift_evidence_rows",
        },
        "phase_totals": phase_totals,
        "phase_full_text_totals": phase_full_text_totals,
        "selected_counts": {
            "before": sum(1 for row in selected if row["phase"] == "before"),
            "after": sum(1 for row in selected if row["phase"] == "after"),
        },
        "source_run": dict(latest_run) if latest_run is not None else None,
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
        generated_at=generated_at,
        method=args.method,
        version=args.version,
        max_per_phase=int(args.max_per_phase),
        full_text_only=full_text_only,
        backfill_to_cap=backfill_to_cap,
        phase_totals=phase_totals,
        phase_full_text_totals=phase_full_text_totals,
    )
    output_md_path.write_text(brief, encoding="utf-8")

    print(f"Republic candidates: {len(candidates)}")
    print(f"Selected before: {payload['selected_counts']['before']}")
    print(f"Selected after: {payload['selected_counts']['after']}")
    print(f"Output JSON: {output_json_path}")
    print(f"Output MD: {output_md_path}")

    master_conn.close()
    analysis_conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
