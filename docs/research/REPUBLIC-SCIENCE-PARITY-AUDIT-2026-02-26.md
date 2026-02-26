# Republic vs Science Shift Parity Audit

Last updated: 2026-02-26 (local)
Scope: compare current research generation, evidence artifacts, and narrative display between Science Shift and Republic Shift.

## Snapshot (Current Repo + DB State)

- Science selected set (`src/data/science_shift_story_2026-02-26.json`): 24 records (12 before, 12 after).
- Science selected quote sources: 24/24 `body_paragraph`.
- Science selected text availability (master DB): 24/24 `full`.
- Republic selected set (latest exported `republic_critical` from analysis DB): 23 records (12 before, 11 after).
- Republic selected quote sources: 21 `body_paragraph`, 2 `summary_sentence`.
- Republic selected text availability (master DB): 21 `full`, 2 `missing`.

## Pipeline Comparison

| Dimension | Science Shift | Republic Shift | Gap |
| --- | --- | --- | --- |
| Primary generator | `scripts/generate_science_shift_research_packet.py` | `scripts/generate_republic_critical_evidence.py` | Different output contracts |
| Output artifact | Explicit packet JSON + brief markdown (`docs/research/*`) and app-facing packet (`src/data/science_shift_story_2026-02-26.json`) | DB table rows (`republic_shift_evidence`) merged into `articles.json` as `republic_critical` | Republic lacks dedicated packet + brief output |
| Candidate visibility | Includes `candidate_records`, phase totals, selection reasons in docs artifact | No packet-style candidate export | Republic triage is less inspectable |
| Text constraint | Full-text-only candidate path | All verified/published articles considered; selected set can include non-full-text records | Republic can emit weaker summary/title-derived evidence |
| Phase balancing | Configurable backfill to phase cap (`--no-backfill` toggle) | Strict threshold only; latest run ended 12/11 selected | Republic can under-fill one phase |
| App opinion view source | Curated packet-driven for `science_shift` in `OpinionShiftView` | Generic split + `republic_critical` overlay | Science has tighter research-to-display path |
| Deep-analysis card language | Updated to `Summary`, `Takeaway`, `Themes` | Still uses `Key message`, `Republic linkage` | Republic narrative fields lag parity |

## Why This Matters

- Science currently has a cleaner research chain: `research packet -> narrative + opinion cards`.
- Republic still depends on embedded evidence fields in `articles.json`, which is robust but less transparent for candidate-level audit and narrative field consistency.
- The two missing-text Republic selections are the clearest quality parity gap versus Science.

## Alignment Plan (Bring Republic Closer to Science Pattern)

1. Add `scripts/generate_republic_shift_research_packet.py` with a Science-like packet schema:
   - `selection_params`, `phase_totals`, `phase_full_text_totals`
   - `selected_records`, `candidate_records`
   - `selection_reason`, `group_hits`, quote metadata
2. Prefer full-text-only Republic selection by default (with explicit override flag when needed).
3. Add Republic brief export:
   - `docs/research/republic-shift-evidence-YYYY-MM-DD.json`
   - `docs/research/republic-shift-brief-YYYY-MM-DD.md`
4. Update `scripts/build_v01_site.sh` to regenerate Republic packet + brief in the same pass as Science.
5. Update `src/components/story/RepublicShiftNarrative.tsx` card fields to match Science pattern:
   - `Summary` + `Takeaway` + `Themes` (replace `Key message` + `Republic linkage`)
6. Optionally switch Republic `OpinionShiftView` to packet-first data source (mirroring Science), while retaining `republic_critical` as fallback for compatibility.
7. Add parity check script (or release check block) to fail when:
   - selected phase counts are imbalanced beyond configured tolerance
   - selected records include non-full-text evidence when strict mode is enabled
   - quote source quality drops below configured threshold

## Immediate Next Recommended Work Item

- Implement Step 1 + Step 2 first (Republic packet generator with full-text-only default), then migrate Republic narrative rendering to packet output in Step 5.
