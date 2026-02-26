# Next Questions

Last updated: 2026-02-26 (PST)
Discovery state: Open (parity alignment track)
Decision process preference: auto-resolve high-confidence decisions; ask only assumption checks where uncertainty is material.

## Recently Resolved

1. 2026-02-26: Science opinion-card curation source resolved.
   - Science Opinion Shift cards now use curated packet evidence (`science_shift_story`) rather than generic heuristic split.
2. 2026-02-26: Science narrative field naming updated.
   - Science deep-analysis evidence cards now use `Summary`, `Takeaway`, and `Themes`.

3. 2026-02-25: Full-text public policy resolved.
   - Full article text is internal-only.
   - Public experience shows summaries/snippets/stubs with attribution and outbound source links.
4. 2026-02-25: Publishing cadence resolved.
   - Corpus refreshes and releases are on-demand only.
5. 2026-02-25: Release gate strictness resolved.
   - Quality gate failures are strict-blocking.
6. 2026-02-25: Threshold profile resolved.
   - Strict-blocking thresholds: summary >=95%, tags >=95%, shifts =100%.
7. 2026-02-25: Transparency page mandate resolved.
   - Methodology and rights posture page is mandatory before next release.
8. 2026-02-25: Public build-log page mandate resolved.
   - A top-level page must track each public build's process and AI collaboration notes.
9. 2026-02-25: Snippet/stub guardrail profile resolved.
   - Summary-only snippets, max 240 chars, attribution + outbound links required.
10. 2026-02-25: Performance policy direction resolved.
   - Performance should be use-case aligned for intentional research workflows; strict sub-1-second blocking gates are out of scope.
11. 2026-02-25: Coverage exception tracking resolved.
   - Use a structured release-level registry (`article_uid`, reason, owner, expiry/remediation target).
12. 2026-02-25: Build-log template structure resolved.
   - Use a required-field template for scope, inputs, workflow/tooling, prompt patterns, quality outcomes, and next actions.
13. 2026-02-25: Non-blocking performance monitoring method resolved.
   - Use a lightweight scripted per-release check on core research flows and log outcomes in the build log.
14. 2026-02-25: Coverage registry storage resolved.
   - Store as a versioned release artifact JSON file alongside build outputs.
15. 2026-02-25: Prompt/process note safety policy resolved.
   - Use fixed safe-note rubric (no secrets/private prompts/PII) with release-owner sign-off.
16. 2026-02-25: Advisory severe-regression policy resolved.
   - No fixed numeric threshold; flag only clearly disruptive slowness in core research flows.
17. 2026-02-25: Coverage exception review cadence resolved.
   - Review unresolved exceptions per release and weekly until closure.
18. 2026-02-25: Snippet truncation style resolved.
   - Use sentence-boundary trim when possible, with ellipsis only when trimmed.
19. 2026-02-25: Methodology checklist sections resolved.
   - Use fixed required sections: `scope`, `sources`, `rights posture`, `limitations`, `update cadence`, `feedback channel`.
20. 2026-02-25: Default sign-off owner resolved.
   - Project owner is default sign-off owner for transparency pages and safe notes.
21. 2026-02-25: Performance assumption adjusted for user profile fit.
   - No fixed baseline device/profile or numeric threshold; flag only clearly disruptive slowness as advisory risk.
22. 2026-02-25: Coverage exception escalation assumption adjusted.
   - No automatic SLA-based escalation; escalation is owner-driven during review cadence.

## Active Assumption Checks (Only Uncertain Items)

1. Should Republic deep-analysis cards be migrated to the same `Summary`/`Takeaway`/`Themes` language used in Science?
2. Should Republic strict selection default to full-text-only (matching Science quality profile)?
3. Should Republic get a packet-style research artifact (`selected_records` + `candidate_records`) as first-class output?
4. Implementation transition approval is pending.

## Queue (Unresolved After Active Question)

1. Sequence for parity implementation:
   - Republic packet generator
   - Republic narrative card field parity
   - Republic opinion-view packet source parity
