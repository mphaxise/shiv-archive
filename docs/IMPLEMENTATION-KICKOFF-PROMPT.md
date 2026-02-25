# Implementation Kickoff Prompt

You are implementing the next phase of Shiv Archive in `/Users/praneet/shiv-archive`.

Read and follow these canonical docs first:
- `/Users/praneet/shiv-archive/docs/discovery-analysis.md`
- `/Users/praneet/shiv-archive/docs/requirements-catalog.md`
- `/Users/praneet/shiv-archive/docs/implementation-options.md`

Implementation goals (already decided, do not re-open unless blocked):
1. Keep public output summary/snippet/stub + attribution + outbound links; full text stays internal-only.
2. Enforce 240-char summary snippets with sentence-boundary trimming when possible and ellipsis only when trimmed.
3. Add/ensure mandatory top-level methodology+rights page with required sections:
   - scope, sources, rights posture, limitations, update cadence, feedback channel
4. Add/ensure mandatory top-level public build-log page with structured release fields:
   - release scope, inputs, workflow/tooling, prompt patterns, quality outcomes, next actions
5. Enforce safe-note policy for build-log prompt/process notes:
   - no secrets, no private prompts, no PII
   - explicit release-owner sign-off (default owner: project owner)
6. Keep strict blocking gates for data/compliance quality decisions already defined.
7. Coverage exceptions must be tracked in a versioned release artifact JSON file alongside build outputs, with:
   - article_uid, reason, owner, expiry/remediation target
8. Performance checks are advisory only:
   - lightweight usability sanity checks only when significant UI/data changes ship
   - no fixed numeric performance gate; flag only clearly disruptive slowness

Execution style:
- Make concrete code/documentation changes now (not just a plan).
- Auto-resolve high-confidence implementation details.
- Ask only if a blocker requires a real product decision.
- Batch related edits together and keep changes consistent across docs/code.

Deliverables:
- Implemented code changes
- Any new/updated docs/templates needed for these policies
- Verification steps run and outcomes
- Brief summary of what was shipped
