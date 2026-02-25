# Next Questions

Last updated: 2026-02-25 (PST)
Discovery state: Open
Decision process preference: auto-resolve high-confidence decisions; ask only assumption checks where uncertainty is material.

## Recently Resolved

1. 2026-02-25: Full-text public policy resolved.
   - Full article text is internal-only.
   - Public experience shows summaries/snippets/stubs with attribution and outbound source links.
2. 2026-02-25: Publishing cadence resolved.
   - Corpus refreshes and releases are on-demand only.
3. 2026-02-25: Release gate strictness resolved.
   - Quality gate failures are strict-blocking.
4. 2026-02-25: Threshold profile resolved.
   - Strict-blocking thresholds: summary >=95%, tags >=95%, shifts =100%.
5. 2026-02-25: Transparency page mandate resolved.
   - Methodology and rights posture page is mandatory before next release.
6. 2026-02-25: Public build-log page mandate resolved.
   - A top-level page must track each public build's process and AI collaboration notes.
7. 2026-02-25: Snippet/stub guardrail profile resolved.
   - Summary-only snippets, max 240 chars, attribution + outbound links required.
8. 2026-02-25: Performance policy direction resolved.
   - Performance should be use-case aligned for intentional research workflows; strict sub-1-second blocking gates are out of scope.
9. 2026-02-25: Coverage exception tracking resolved.
   - Use a structured release-level registry (`article_uid`, reason, owner, expiry/remediation target).
10. 2026-02-25: Build-log template structure resolved.
   - Use a required-field template for scope, inputs, workflow/tooling, prompt patterns, quality outcomes, and next actions.
11. 2026-02-25: Non-blocking performance monitoring method resolved.
   - Use a lightweight scripted per-release check on core research flows and log outcomes in the build log.
12. 2026-02-25: Coverage registry storage resolved.
   - Store as a versioned release artifact JSON file alongside build outputs.
13. 2026-02-25: Prompt/process note safety policy resolved.
   - Use fixed safe-note rubric (no secrets/private prompts/PII) with release-owner sign-off.
14. 2026-02-25: Advisory severe-regression thresholds resolved.
   - Flag severe regression when key flow is >35% slower than baseline or >2.5s absolute.
15. 2026-02-25: Coverage exception review cadence resolved.
   - Review unresolved exceptions per release and weekly until closure.
16. 2026-02-25: Snippet truncation style resolved.
   - Use sentence-boundary trim when possible, with ellipsis only when trimmed.
17. 2026-02-25: Methodology checklist sections resolved.
   - Use fixed required sections: `scope`, `sources`, `rights posture`, `limitations`, `update cadence`, `feedback channel`.
18. 2026-02-25: Default sign-off owner resolved.
   - Project owner is default sign-off owner for transparency pages and safe notes.
19. 2026-02-25: Performance assumption adjusted for user profile fit.
   - No fixed baseline device/profile or numeric threshold; flag only clearly disruptive slowness as advisory risk.
20. 2026-02-25: Coverage exception escalation assumption adjusted.
   - No automatic SLA-based escalation; escalation is owner-driven during review cadence.

## Active Assumption Checks (Only Uncertain Items)

1. Discovery assumptions are now resolved for current scope.
2. Implementation transition approval is pending.

## Queue (Unresolved After Active Question)

1. None pending for discovery.
