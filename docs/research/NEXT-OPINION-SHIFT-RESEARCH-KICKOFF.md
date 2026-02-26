# Next Opinion Shift Research Kickoff

Last updated: 2026-02-26 (local)

## 1) Research Agent Charter

Working persona for this cycle:
- Archivist: preserve source traceability, publication/date provenance, and repeatable audit steps.
- Library scientist: classify themes, compare phase coverage, and surface corpus bias/gaps.
- Political commentator: frame democratic stakes, institutional shifts, and public-language transitions.

Operating rule:
- Evidence first (DB + article text), interpretation second.

## 2) Kickoff Snapshot

Data readiness checks at kickoff:
- Articles: 97 total
- Summary coverage: 97/97 (100%)
- Tag coverage: 97/97 (100%)
- Shift coverage (all four shift IDs): 97/97 (100%)

Current phase split:
- `republic_shift`: before 64, after 33
- `ecological_shift`: before 27, after 70
- `science_shift`: before 40, after 57
- `political_shift`: before 28, after 69

## 3) Recommended “Next Opinion Shift”

Recommendation: **Science Shift** (`science_shift`)

Reason:
- Best balance for narrative comparison (before 40 vs after 57) without being too lopsided.
- Strongest full-text availability among non-republic tracks:
  - before: 27/40 full text (67.5%)
  - after: 55/57 full text (96.5%)
- Strong title/tag signal cluster around science-public themes:
  - `science-policy`
  - `technology-and-society`
  - `knowledge-systems`
  - `public-institutions`

Core thesis to test in this research run:
- Shift from critique of expert/closed knowledge systems to proposals for distributed, civic, and playful knowledge publics.

## 4) Seed Corpus Export (Created)

Research seed file generated:
- `/Users/praneet/shiv-archive/docs/research/science-shift-seed-2026-02-26.json`

Selection logic:
- Latest `science_shift` phase per article
- Full-text only
- Ranked by science-signal tag density, then recency
- Top 12 `before` + top 12 `after`

## 5) Immediate Next Actions

1. Extract quote-level evidence from the seeded science corpus (before/after) with explicit rationale fields.
2. Draft phase narrative outline (`Phase 1` vs `Phase 2`) using only seeded evidence.
3. Mark weak links (low signal density) for replacement before narrative lock.

## 6) Run Log (2026-02-26)

Completed now:
- Added reusable generator: `/Users/praneet/shiv-archive/scripts/generate_science_shift_research_packet.py`
- Produced evidence packet: `/Users/praneet/shiv-archive/docs/research/science-shift-evidence-2026-02-26.json`
- Produced readable brief: `/Users/praneet/shiv-archive/docs/research/science-shift-brief-2026-02-26.md`
- Added narrative page implementation:
  - `/Users/praneet/shiv-archive/src/app/deep-analysis/science-shift/page.tsx`
  - `/Users/praneet/shiv-archive/src/components/story/ScienceShiftNarrative.tsx`
