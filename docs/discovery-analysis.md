# Discovery Analysis: Shiv Archive

Last updated: 2026-02-25 (PST)
Discovery status: Ready for implementation approval (current decision set resolved)
Implementation gate: Pending explicit user approval

## Scope and Constraints

- Scope for this discovery cycle:
  - Validate current repository state and architecture.
  - Define a concrete, low-risk path for next implementation work.
  - Capture resolved decisions and isolate true unresolved decisions.
- Constraints already present in repo policy:
  - Primary source of truth is dual DB (`data/shiv_master.db` + `data/shiv_analysis.db`).
  - Manual DB mutation is disallowed; scripts in `scripts/` are the change path.
  - Public output should remain summary/snippet/stub + attribution + source links; full article text stays internal-only.
  - Current delivery mode is static export from Next.js (`out`) with Cloudflare Pages compatibility.
  - Product intent is research/learning/discovery-first; technical rigor should match intentional-use workflows.

## Context Audit Summary

Source context reviewed in this run:
- `README.md`
- `PROJECT_PLAN.md`
- `package.json`
- `db/master_schema.sql`
- `db/analysis_schema.sql`
- `scripts/build_v01_site.sh`
- `scripts/export_public_json_dual.py`
- `src/app/page.tsx`
- `src/app/deep-analysis/republic-shift/page.tsx`
- `src/components/LayeredResearchEngine.tsx`
- `src/data/articles.json`

Current factual state:
- Dataset snapshot in `src/data/articles.json` (generated 2026-02-22T22:08:07Z):
  - 97 articles, all verified, 4 publications.
  - Year range 2010-2026.
  - 85 articles with full text in master DB.
  - 388 shift annotations total, 23 curated republic story picks.
- Product surface:
  - Next.js layered archive explorer.
  - Dedicated deep-analysis narrative page for Republic Shift.
- Data architecture:
  - Master DB stores article records and article text.
  - Analysis DB stores summaries, tags, shift annotations, and republic evidence.
  - Export script merges dual DB state into public JSON payload.

## Resolved Decisions (Canonical for This Cycle)

1. Source path and data ownership:
   - Resolved: Dual DB model remains canonical (`master` + `analysis`), legacy DB is compatibility input only.
2. Access model:
   - Resolved: Public, no-login read access via static website.
3. Privacy/sharing posture:
   - Resolved: Full article text is internal-only for personal analysis; public payload includes summaries/snippets/stubs, source attribution, and outbound source links.
4. Delivery mode:
   - Resolved: Static build pipeline remains default (`scripts/build_v01_site.sh` -> export JSON -> Next.js build).
5. Publishing cadence:
   - Resolved: Corpus refresh and publish runs are on-demand only (manual trigger), not scheduled.
6. Release gate behavior:
   - Resolved: Quality gate failures are strict-blocking; releases do not proceed on gate failure.
7. Release threshold profile:
   - Resolved: Strict-blocking thresholds are set to 95% summary coverage, 95% tag coverage, and 100% shift coverage.
8. Transparency page requirement:
   - Resolved: A top-level methodology and rights posture page is mandatory before the next public release.
9. Public build-log page requirement:
   - Resolved: A second top-level page is mandatory before the next public release, documenting each public build's process, tools, and AI collaboration approach.
10. Snippet/stub guardrail profile:
   - Resolved: Public snippets are summary-only, capped at 240 characters, and always shown with source attribution plus outbound source links.
11. Performance policy:
   - Resolved: Performance is evaluated against research-use usability, not strict sub-1-second blocking gates; severe latency is unacceptable, but speed checks remain advisory unless explicitly promoted to release gates.
12. Coverage exception tracking policy:
   - Resolved: Any allowed summary/tag coverage exceptions (within the <=5% envelope) must be tracked in a structured release-level registry with owner and remediation target.
13. Public build-log template policy:
   - Resolved: Release logs use a structured required-field template covering scope, inputs, workflow/tooling, prompt patterns, quality outcomes, and next actions.
14. Performance monitoring policy:
   - Resolved: Use lightweight, non-blocking usability sanity checks for core research flows only when significant UI/data changes are made; summarize findings in the build log.
15. Coverage registry storage policy:
   - Resolved: Coverage exceptions are stored as a versioned release artifact JSON file alongside release build outputs.
16. Public prompt/process notes safety policy:
   - Resolved: Public build-log notes follow a fixed safe-note rubric (no secrets, private prompts, or PII) with explicit release-owner sign-off.
17. Advisory performance threshold policy:
   - Resolved: No fixed numeric threshold is enforced; treat only clearly disruptive slowness in core research tasks as a performance issue.
18. Coverage exception review cadence policy:
   - Resolved: Unresolved coverage exceptions are reviewed every release and at least weekly until closure.
19. Snippet truncation style policy:
   - Resolved: Public 240-char snippets use sentence-boundary trimming when possible, with ellipsis only when content is trimmed.
20. Methodology/rights checklist policy:
   - Resolved: Methodology/rights page uses fixed required sections: scope, sources, rights posture, limitations, update cadence, and feedback channel.
21. Default sign-off owner policy:
   - Resolved: Project owner is the default release-owner sign-off role for transparency pages and safe notes.
22. Coverage exception escalation policy:
   - Resolved: No automatic SLA-based escalation; unresolved coverage exceptions are handled through owner judgment during scheduled review cadence.

## Risks and Gaps

- No explicit automated acceptance test suite for data quality gates (summary/tag/annotation completeness).
- Data freshness is dependent on manual script runs; no scheduled refresh workflow yet.
- Legal/editorial policy is implied in README but not codified as a release checklist gate.
- Frontend and data pipeline contracts are not currently validated in CI.

## Discovery Completion Criteria (For Move to Implementation)

Discovery for this cycle is complete when:
- One implementation option is chosen and frozen.
- Unresolved questions in `docs/next-questions.md` are either answered or scoped out of phase.
- Requirements in `docs/requirements-catalog.md` marked `resolved` are testable and non-conflicting.
- User explicitly approves transition from discovery to implementation.
