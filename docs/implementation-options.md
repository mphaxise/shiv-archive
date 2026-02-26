# Implementation Options

Last updated: 2026-02-26 (PST)
Scope: Next build phase after discovery

## Option A: Data Quality and Release Gates First (Recommended)

Summary:
- Add scripted validation checks between data generation and public export.
- Promote legal/editorial policy into explicit release gates.
- Add reproducible checks for summary/tag/annotation completeness.

Pros:
- Reduces risk of publishing broken or non-compliant corpus updates.
- Creates stable baseline before feature expansion.
- Improves confidence for future automation.

Cons:
- Slower visible product changes in first iteration.
- Requires defining thresholds and expected failure behavior.

Effort: Medium
Risk: Low

## Option B: Frontend Feature Acceleration First

Summary:
- Prioritize v0.2/v0.3 UX features (timeline trends, concept map, richer deep analysis views) before hardening pipeline quality gates.

Pros:
- Faster user-visible progress.
- Better feedback loop on interaction patterns.

Cons:
- Higher risk of surfacing low-quality or stale data.
- Harder rollback if data quality defects appear after feature launch.

Effort: Medium to High
Risk: Medium to High

## Option C: Ops and Deployment Automation First

Summary:
- Build CI/CD, scheduled refresh jobs, and deployment observability before major data or UI changes.

Pros:
- Strong operational reliability and repeatability.
- Lower manual burden for updates.

Cons:
- Delays both data quality and frontend improvements unless scoped tightly.
- Can over-invest in ops before requirements settle.

Effort: Medium
Risk: Medium

## Option D: Shift Pipeline Parity First

Summary:
- Make Republic Shift follow the same research-packet contract used by Science Shift.
- Add Republic packet artifacts (selected + candidates + brief) and migrate Republic narrative cards to the same `Summary`/`Takeaway`/`Themes` field style.

Pros:
- Aligns research generation and narrative display contracts across long-form shifts.
- Improves explainability (candidate-level trace) and reduces model/UI drift.
- Enables one shared QA policy for both shifts (full-text strictness, quote-source quality, phase balance).

Cons:
- Requires adding new packet generator and adapting Republic narrative mapper.
- Adds short-term migration complexity while preserving `republic_critical` compatibility.

Effort: Medium
Risk: Low to Medium

## Recommendation and Sequence

Recommended path: Option A -> Option D -> targeted Option C -> Option B

Proposed sequence:
1. Implement data quality gates and release checklist enforcement.
2. Unify Republic and Science shift research/display contracts (packet parity + card field parity).
3. Add lightweight automation for repeatable data refresh + export verification.
4. Resume feature roadmap with confidence in data contracts.

## Prerequisites Before Starting Implementation

- Implement sentence-boundary truncation for 240-char snippets with ellipsis-on-trim behavior and consistent attribution placement.
- Confirm runbook details for on-demand release triggers (owner, checklist, and rollback note).
- Implement the resolved coverage-exception artifact file format and path convention for each release.
- Implement the fixed methodology/rights required-section checklist (`scope`, `sources`, `rights posture`, `limitations`, `update cadence`, `feedback channel`).
- Implement the resolved structured build-log template fields and enforce the safe-note rubric plus release-owner sign-off for prompt/process notes.
- Apply the default sign-off owner role (project owner) for transparency pages and safe notes.
- Implement lightweight, non-blocking usability sanity checks on core research flows when significant UI/data changes are shipped, and log outcomes.
- Implement the resolved cadence for unresolved coverage exceptions (per release + weekly until closure).
