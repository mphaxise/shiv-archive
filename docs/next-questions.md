# Next Questions

Last updated: 2026-02-26 (PST)
Discovery state: Open (quality-gate track); parity alignment track completed
Decision process preference: auto-resolve high-confidence decisions; ask only assumption checks where uncertainty is material.

## Recently Resolved

1. 2026-02-26: Science opinion-card curation source resolved.
   - Science Opinion Shift cards now use curated packet evidence (`science_shift_story`) rather than generic heuristic split.
2. 2026-02-26: Science narrative field naming updated.
   - Science deep-analysis evidence cards now use `Summary`, `Takeaway`, and `Themes`.
3. 2026-02-26: Republic packet parity resolved.
   - Republic now has packet artifact + brief outputs (`republic_shift_story` + docs research packet/brief exports).
4. 2026-02-26: Republic strict full-text default resolved.
   - Republic strict selection now defaults to full-text-backed records, with explicit `--allow-non-full-text` opt-out.
5. 2026-02-26: Republic narrative/opinion field and source parity resolved.
   - Republic deep-analysis cards now use `Summary`, `Takeaway`, and `Themes`.
   - Republic Opinion Shift cards now use packet-first curation with compatibility fallback.

6. 2026-02-25: Full-text public policy resolved.
   - Full article text is internal-only.
   - Public experience shows summaries/snippets/stubs with attribution and outbound source links.
7. 2026-02-25: Publishing cadence resolved.
   - Corpus refreshes and releases are on-demand only.
8. 2026-02-25: Release gate strictness resolved.
   - Quality gate failures are strict-blocking.
9. 2026-02-25: Threshold profile resolved.
   - Strict-blocking thresholds: summary >=95%, tags >=95%, shifts =100%.
10. 2026-02-25: Transparency page mandate resolved.
   - Methodology and rights posture page is mandatory before next release.
11. 2026-02-25: Public build-log page mandate resolved.
   - A top-level page must track each public build's process and AI collaboration notes.
12. 2026-02-25: Snippet/stub guardrail profile resolved.
   - Summary-only snippets, max 240 chars, attribution + outbound links required.
13. 2026-02-25: Performance policy direction resolved.
   - Performance should be use-case aligned for intentional research workflows; strict sub-1-second blocking gates are out of scope.
14. 2026-02-25: Coverage exception tracking resolved.
   - Use a structured release-level registry (`article_uid`, reason, owner, expiry/remediation target).
15. 2026-02-25: Build-log template structure resolved.
   - Use a required-field template for scope, inputs, workflow/tooling, prompt patterns, quality outcomes, and next actions.
16. 2026-02-25: Non-blocking performance monitoring method resolved.
   - Use a lightweight scripted per-release check on core research flows and log outcomes in the build log.
17. 2026-02-25: Coverage registry storage resolved.
   - Store as a versioned release artifact JSON file alongside build outputs.
18. 2026-02-25: Prompt/process note safety policy resolved.
   - Use fixed safe-note rubric (no secrets/private prompts/PII) with release-owner sign-off.
19. 2026-02-25: Advisory severe-regression policy resolved.
   - No fixed numeric threshold; flag only clearly disruptive slowness in core research flows.
20. 2026-02-25: Coverage exception review cadence resolved.
   - Review unresolved exceptions per release and weekly until closure.
21. 2026-02-25: Snippet truncation style resolved.
   - Use sentence-boundary trim when possible, with ellipsis only when trimmed.
22. 2026-02-25: Methodology checklist sections resolved.
   - Use fixed required sections: `scope`, `sources`, `rights posture`, `limitations`, `update cadence`, `feedback channel`.
23. 2026-02-25: Default sign-off owner resolved.
   - Project owner is default sign-off owner for transparency pages and safe notes.
24. 2026-02-25: Performance assumption adjusted for user profile fit.
   - No fixed baseline device/profile or numeric threshold; flag only clearly disruptive slowness as advisory risk.
25. 2026-02-25: Coverage exception escalation assumption adjusted.
   - No automatic SLA-based escalation; escalation is owner-driven during review cadence.

## Active Assumption Checks (Only Uncertain Items)

- None for shift-parity scope.

## Queue (Unresolved After Active Question)

1. Add a parity gate script/check block to fail releases on selected full-text/phase-balance/quote-source regressions.
2. Continue Option A quality-gate/release-checklist hardening sequence.
3. Prioritize and execute next-iteration brainstorm items:
   - `docs/research/NEXT-ITERATION-BRAINSTORM.md`
