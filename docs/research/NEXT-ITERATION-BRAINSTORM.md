# Next Iteration Brainstorm

Date: 2026-02-27 (local)
Scope: improvement ideas after Republic + Science parity rollout.
Inputs:
- `docs/research/DEEP-ANALYSIS-RESEARCH-CRITIQUE-2026-02-27.md`
- `docs/research/DEEP-ANALYSIS-IMPLEMENTATION-PLAN-2026-02-27.md`

## 1) Research Quality and Falsifiability

- Add explicit falsification criteria per shift page (what evidence would weaken the thesis).
- Run hinge-year sensitivity checks (for example: 2022, 2023, 2024, 2025) and publish whether core claims hold.
- Add counter-model testing (continuity model vs hinge model) and report fit comparisons.

## 2) Selection Robustness

- Report phase selection rates beside final selected counts (to expose asymmetric candidate pressure).
- Publish relevance-score distribution by phase (median + spread, not only selected count).
- Add a no-backfill diagnostic mode to compare with backfill-to-cap mode.

## 3) Domain Purity and Overlap

- Add a science-domain purity gate so Science Shift does not over-absorb general democracy essays.
- Publish overlap diagnostics between Republic and Science selected sets each release.
- Define overlap policy: allowed overlap, justified overlap, and hard upper threshold.

## 4) Card-Level Argument Quality

- Move takeaways to quote-span-grounded argument generation (argument sentence + evidence sentence).
- Add a repetition guard that flags duplicate takeaways over a configured threshold.
- Add summary-quality guardrails for placeholder/low-signal snippets before narrative rendering.

## 5) Transparency UX

- Add an audit appendix block to each deep-analysis page:
  - candidate counts, selected counts, selection rates, thresholds, and exclusion reasons.
- Add a contested/edge evidence panel showing near-threshold and contradictory records.
- Add "why selected" hover/detail drilldown per card.

## 6) Release Guardrails

- Add CI parity checks that fail on:
  - selected non-full-text evidence in strict mode,
  - phase balance outside tolerance,
  - quote-source quality floor regressions.
- Add build-script health checks (script existence + executable independence via `python3` calls).

## 7) Data/Source Balance

- Add publication concentration warning thresholds for selected packet outputs.
- Add source-diversity targets (warning-first, then optional blocking).
- Add weekly drift summary comparing current packet mix vs previous release.

## Priority Cut for Next Sprint

1. Parity gate script (blocking checks for strict/full-text/phase balance/quote source).
2. Quote-grounded takeaway generator with duplicate-text checks.
3. Audit appendix on both deep-analysis pages.
4. Overlap diagnostics report between Republic and Science packets.
