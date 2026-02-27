# Requirements Catalog

Last updated: 2026-02-26 (PST)

Status legend:
- `resolved`: accepted for this discovery cycle
- `unresolved`: needs user decision before implementation
- `deferred`: intentionally out of current phase

| ID | Category | Requirement | Status | Source |
| --- | --- | --- | --- | --- |
| RQ-001 | Data architecture | Dual DB architecture remains canonical: `shiv_master.db` stores source corpus and text; `shiv_analysis.db` stores analysis layers. | resolved | README, schema files |
| RQ-002 | Mutation policy | Database changes are applied only through repository scripts, never ad-hoc manual DB edits. | resolved | README policy |
| RQ-003 | Public safety | Full article text remains internal-only; public payload is summaries/snippets/stubs with source attribution and outbound links. | resolved | User decision 2026-02-25 + README governance section |
| RQ-004 | Build pipeline | Data build runs: dual shift generation, republic evidence generation, science research packet generation, and JSON export to both web and app data paths. | resolved | `scripts/build_v01_site.sh` |
| RQ-005 | Core UX | Public site supports browse, search, year/tag filtering, and source URL opening. | resolved | PROJECT_PLAN, current app components |
| RQ-006 | Dataset integrity thresholds | Strict-blocking release thresholds are: at least 95% article summary coverage, at least 95% article tag coverage (>=1 tag), and 100% shift coverage. | resolved | User decision 2026-02-25 |
| RQ-007 | Shift coverage | Each article should retain latest annotation for all four shift IDs (`republic`, `ecological`, `science`, `political`). | resolved | analysis schema + DB query |
| RQ-008 | Release checklist | Add a machine-runnable release checklist with strict-blocking behavior when quality thresholds are not met. | resolved | User decision 2026-02-25 |
| RQ-009 | Performance policy | Performance rigor must match intentional research workflows: avoid severe slowness, but do not enforce strict sub-1-second interaction gates as release blockers. | resolved | User decision 2026-02-25 |
| RQ-010 | Auditability | Exported annotations and republic evidence include run-level audit metadata (`method`, `version`, `run_uid`, fingerprints). | resolved | `export_public_json_dual.py` |
| RQ-011 | Update cadence | Rebuild/export/publish runs are on-demand only, triggered manually when needed. | resolved | User decision 2026-02-25 |
| RQ-012 | Compliance communication | Publish a mandatory top-level methodology and rights posture page before the next release. | resolved | User decision 2026-02-25 |
| RQ-013 | Outbound linking UX | Public source links open the original article in a new tab and preserve clear source attribution near the link. | resolved | User decision 2026-02-25 |
| RQ-014 | Public build log page | Publish a mandatory top-level public build-log page for each release, documenting build process, tools, AI collaboration approach, and prompt patterns that improved output quality. | resolved | User decision 2026-02-25 |
| RQ-015 | Snippet guardrails | Public snippets are summary-only, capped at 240 characters, and always include source attribution plus outbound links. | resolved | User decision 2026-02-25 |
| RQ-016 | Performance monitoring | Run lightweight, non-blocking usability sanity checks on core research flows when significant UI/data changes occur, and log results in the public build log. | resolved | User decision 2026-02-25 |
| RQ-017 | Coverage exception registry | Track any allowed <=5% summary/tag coverage exceptions in a structured release-level registry (`article_uid`, reason, owner, expiry/remediation target). | resolved | User decision 2026-02-25 |
| RQ-018 | Build-log template | Use a structured required-field build-log template for each release: scope, inputs, workflow/tooling, prompt patterns, quality outcomes, and next actions. | resolved | User decision 2026-02-25 |
| RQ-019 | Coverage registry storage | Store the structured coverage-exception registry as a versioned release artifact JSON file alongside build outputs. | resolved | User decision 2026-02-25 |
| RQ-020 | Prompt/process note safety | Public build-log prompt/process notes must follow a fixed safe-note rubric (no secrets/private prompts/PII) with explicit release-owner sign-off. | resolved | User decision 2026-02-25 |
| RQ-021 | Advisory performance thresholds | Do not enforce fixed numeric thresholds; flag only clearly disruptive slowness in core research tasks as advisory performance risk. | resolved | User decision 2026-02-25 |
| RQ-022 | Coverage exception review cadence | Review unresolved coverage exceptions every release and at least weekly until each is remediated. | resolved | User decision 2026-02-25 |
| RQ-023 | Snippet truncation style | For 240-char public snippets, use sentence-boundary trim when possible, with ellipsis only when content is trimmed. | resolved | User decision 2026-02-25 |
| RQ-024 | Methodology checklist sections | Methodology/rights page must include fixed required sections: `scope`, `sources`, `rights posture`, `limitations`, `update cadence`, `feedback channel`. | resolved | User decision 2026-02-25 |
| RQ-025 | Default sign-off owner | Project owner is the default release-owner sign-off role for transparency pages and safe notes. | resolved | User decision 2026-02-25 |
| RQ-026 | Coverage exception escalation | No automatic SLA escalation is required; escalation for unresolved exceptions is owner-driven during review cadence. | resolved | User decision 2026-02-25 |
| RQ-027 | Science opinion-view curation | Science Opinion Shift cards must use curated packet-selected evidence records, not generic heuristic fallback selection. | resolved | `src/components/layers/OpinionShiftView.tsx` |
| RQ-028 | Narrative card language parity | Long-form evidence cards should standardize on `Summary`, `Takeaway`, and `Themes` field labels for consistency across views. | resolved | `src/components/story/RepublicShiftNarrative.tsx`, `src/components/story/ScienceShiftNarrative.tsx` |
| RQ-029 | Republic packet parity | Republic Shift should gain a dedicated research packet artifact (selected + candidate records + selection params) analogous to Science Shift. | resolved | `scripts/generate_republic_shift_research_packet.py`, `src/data/republic_shift_story_2026-02-26.json` |
| RQ-030 | Full-text strict mode parity | In strict mode, selected long-form shift evidence should default to full-text-backed records only. | resolved | `scripts/generate_republic_critical_evidence.py` (`--allow-non-full-text` opt-out flag) |

## Open Acceptance Criteria to Finalize

- Data completeness thresholds:
  - Resolved: summary >=95%, tag coverage >=95%, shift coverage =100%.
  - Resolved: temporary exceptions for remaining <=5% gap must be tracked in a structured registry.
  - Resolved: registry storage location is versioned release artifact JSON.
  - Resolved: unresolved exceptions are reviewed per release and weekly until closure.
  - Resolved: escalation is owner-driven, with no automatic SLA trigger.
- Snippet/stub policy:
  - Resolved: summary-only snippets, max 240 chars, attribution + outbound links required.
  - Resolved: sentence-boundary trimming preferred, ellipsis only when trimmed.
- Methodology/rights page:
  - Resolved: mandatory before release.
  - Resolved: fixed required-section checklist.
  - Resolved: project owner as default sign-off owner.
- Public build-log page:
  - Resolved: mandatory before release.
  - Resolved: structured per-release template fields are mandatory.
  - Resolved: fixed safe-note rubric and release-owner sign-off for prompt/process notes.
- Release blocking behavior:
  - Resolved: all defined data/compliance gate failures block publish.
  - Note: performance checks are advisory unless explicitly added as gates later.
- Performance verification (non-blocking):
  - Resolved: lightweight sanity checks are run only when significant UI/data changes are shipped.
  - Resolved: no fixed baseline profile or numeric threshold is required.
  - Resolved: only clearly disruptive slowness in core research tasks is flagged as advisory risk.
