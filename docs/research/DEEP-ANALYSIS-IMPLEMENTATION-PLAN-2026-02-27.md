# Deep Analysis Hardening Plan (Research + Implementation)

Date: 2026-02-27 (local)  
Source critique: `docs/research/DEEP-ANALYSIS-RESEARCH-CRITIQUE-2026-02-27.md`

## Program Goal

Upgrade the Republic Shift and Science Shift pages from strong narrative essays to auditable, testable research arguments with explicit falsification, robustness checks, and transparent evidence diagnostics.

## Success Criteria

- Shift claims remain stable under alternative cut years and selection caps.
- Science and Republic corpora have explicit overlap policy and measured orthogonality.
- Page-level claims are traceable to article-level quote spans and confidence-bearing labels.
- Readers can inspect selection mechanics (candidate pools, rates, score distributions, exclusions).
- Regressions in parity or evidence quality fail CI.

## Milestones

### M0: Program Setup (Target: 2026-03-02)

- Create and scope issue backlog for research and implementation workstreams.
- Define dependency order and integration checkpoints.
- Establish decision log path in docs.

Exit criteria:
- All core tickets opened with acceptance criteria and linked dependencies.

### M1: Research Validation Layer (Target: 2026-03-06)

- Define falsification rules and rival models.
- Run hinge-year sensitivity checks and phase-cap robustness runs.
- Establish science domain-purity gate and overlap diagnostic baseline.

Exit criteria:
- Research memo with pass/fail outcomes for falsification and robustness tests.

### M2: Data/Pipeline Hardening (Target: 2026-03-13)

- Add source-diversity/concentration checks.
- Implement multi-label group assignment with confidence.
- Produce quote-span-grounded takeaways instead of mostly template outputs.

Exit criteria:
- New packet outputs include confidence fields and richer traceability metadata.

### M3: Narrative/UI Transparency (Target: 2026-03-20)

- Add audit appendix sections to both deep-analysis pages.
- Add contested/negative evidence panels.
- Add overlap diagnostics disclosure between pages.

Exit criteria:
- Pages display diagnostic modules and hard-case evidence samples.

### M4: Release Guardrails (Target: 2026-03-27)

- Add CI parity/regression checks for both shift packets.
- Gate release on full-text quote quality, phase-balance tolerance, and overlap constraints.

Exit criteria:
- CI fails on research-quality regressions; release checklist updated.

## Workstreams

### A. Research Track

- A1: Falsification + counter-model framework.
- A2: Hinge-year and selection-cap sensitivity analysis.
- A3: Science domain-purity criteria and recuration protocol.
- A4: Cross-page overlap/orthogonality policy.
- A5: Source concentration analysis and target thresholds.

### B. Implementation Track

- B1: Audit appendix generator and data contract.
- B2: Multi-label + confidence lead-group scoring.
- B3: Quote-span-grounded takeaway generation.
- B4: Contested evidence panel in deep-analysis UI.
- B5: CI parity/regression gate.

## Dependency Order

1. A1 -> A2 -> A4
2. A3 -> B2
3. A5 -> B1 and B5
4. B2 + B3 -> B4
5. B1 + B4 + B5 -> release hardening sign-off

## Execution Cadence

- Weekly checkpoint on Fridays (2026-03-06, 2026-03-13, 2026-03-20, 2026-03-27).
- Mid-week risk review on Tuesdays (2026-03-03, 2026-03-10, 2026-03-17, 2026-03-24).
- Each issue must include:
  - concrete deliverable,
  - acceptance tests,
  - explicit dependency tags,
  - documentation update requirement.

## Risk Register (Initial)

- Risk: Overlap reduction may drop narrative coherence.
  - Mitigation: keep an overlap rationale mode before strict orthogonality enforcement.
- Risk: Multi-label scoring adds complexity without interpretive gain.
  - Mitigation: require confidence calibration report before UI rollout.
- Risk: Source-diversity constraints may reduce packet size.
  - Mitigation: allow warnings mode first, then enforce gradually.

## Backlog Links

- Program umbrella:
  - [#2 Program: Deep-analysis research hardening](https://github.com/mphaxise/shiv-archive/issues/2)
- Research track:
  - [#4 A1: Define falsification framework and rival models](https://github.com/mphaxise/shiv-archive/issues/4)
  - [#5 A2: Run hinge-year and phase-cap sensitivity analysis](https://github.com/mphaxise/shiv-archive/issues/5)
  - [#6 A3: Establish science domain-purity gate and recuration protocol](https://github.com/mphaxise/shiv-archive/issues/6)
  - [#7 A4: Analyze cross-page overlap and define orthogonality policy](https://github.com/mphaxise/shiv-archive/issues/7)
  - [#8 A5: Define source-diversity thresholds and concentration diagnostics](https://github.com/mphaxise/shiv-archive/issues/8)
- Implementation track:
  - [#9 B1: Build audit appendix contract and generators](https://github.com/mphaxise/shiv-archive/issues/9)
  - [#10 B2: Implement multi-label lead-group scoring with confidence](https://github.com/mphaxise/shiv-archive/issues/10)
  - [#11 B3: Generate quote-span-grounded, article-specific takeaways](https://github.com/mphaxise/shiv-archive/issues/11)
  - [#12 B4: Add contested evidence + overlap diagnostics to deep-analysis pages](https://github.com/mphaxise/shiv-archive/issues/12)
  - [#13 B5: Add CI parity/regression gate for deep-analysis research quality](https://github.com/mphaxise/shiv-archive/issues/13)
