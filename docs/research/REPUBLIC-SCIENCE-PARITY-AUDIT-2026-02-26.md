# Republic vs Science Shift Parity Audit

Last updated: 2026-02-26 (local)
Scope: compare research generation, evidence artifacts, and narrative display between Science Shift and Republic Shift.

## Snapshot (Post-Implementation)

- Science selected set (`src/data/science_shift_story_2026-02-26.json`): 24 records (12 before, 12 after).
- Science selected quote sources: 24/24 `body_paragraph`.
- Science selected full-text state: 24/24 full-text-backed.
- Republic selected set (`src/data/republic_shift_story_2026-02-26.json`): 24 records (12 before, 12 after).
- Republic selected quote sources: 24/24 `body_paragraph`.
- Republic selected full-text state: 24/24 full-text-backed.

## What Changed in the Recommended Path

1. Added Republic packet generator:
   - `scripts/generate_republic_shift_research_packet.py`
2. Enforced strict full-text default for Republic selection:
   - `scripts/generate_republic_critical_evidence.py`
   - Opt-out is explicit via `--allow-non-full-text`.
3. Wired Republic packet + brief into build:
   - `scripts/build_v01_site.sh`
4. Migrated Republic narrative + opinion cards to packet-first:
   - `src/components/story/RepublicShiftNarrative.tsx`
   - `src/components/layers/OpinionShiftView.tsx`
5. Standardized card fields:
   - `Summary`, `Takeaway`, `Themes` across long-form shift cards.

## Current Comparison

| Dimension | Science Shift | Republic Shift | Parity Status |
| --- | --- | --- | --- |
| Primary generator | `generate_science_shift_research_packet.py` | `generate_republic_shift_research_packet.py` | Aligned |
| Output artifact | Packet JSON + brief markdown + app-facing story JSON | Packet JSON + brief markdown + app-facing story JSON | Aligned |
| Candidate visibility | `candidate_records` + phase totals + selection params | `candidate_records` + phase totals + selection params | Aligned |
| Text constraint | Full-text strict mode | Full-text strict mode by default (explicit opt-out flag) | Aligned |
| Phase balancing | Backfill to phase cap | Backfill to phase cap | Aligned |
| Opinion view source | Packet-first | Packet-first (with compatibility fallback) | Aligned |
| Deep-analysis card fields | `Summary` / `Takeaway` / `Themes` | `Summary` / `Takeaway` / `Themes` | Aligned |

## Remaining Gap

- No standalone parity regression gate exists yet to fail builds if either shift drifts on:
  - selected full-text strictness,
  - phase-balance tolerance,
  - quote-source quality floor.

## Next Recommended Hardening

1. Add a parity check script that validates both story packets in CI/release checks.
2. Treat parity regression as blocking in the release checklist.
