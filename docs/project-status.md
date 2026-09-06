# Project status and handoff

Updated 2026-09-06. This is the current start-here document.

## Active plan

The user has prioritized model quality and paused interface development.
Read [the current model plan](current-model-plan.md).

This review branch builds on `hitter-v2-pbp-outcomes` at `b3d55cc`. It contains
model code, experiment records, and the plan. It does not change a website or
promote a model. Protected main and the v1 release are unchanged until integration.

## Completed research

- C2026A: two all-level output-calibration candidates failed.
  [Result](hitter-v2-C2026A-result.md).
- T2026B: one competition-normalized history candidate failed its prospective
  all-level gate. Its presaved MLB-conditional component materially improves
  prediction for prior-minor players but still needs calibration and confirmation.
  [Result](hitter-v2-T2026B-result.md).
- C2026C: two MLB-specific calibration candidates failed. The error audit shows
  much larger optimism among brief MLB call-ups than among players with 100+ PA.
  Future exposure is a diagnostic label, never a preseason predictor or exclusion
  rule. [Result and next step](hitter-v2-C2026C-result.md).

## Next modeling task

Retain the unchanged MLB-conditional transport component as a developmental
reference. Stop global calibration searches. Build MLB-arrival, retention, and
exposure labels including non-arrivals. Verify apparent zeros with complete official
MLB participation records before treating missing model-ready PBP as no appearance.
Freeze one simple opportunity baseline before adding age/development alternatives.

The 2022–2024 seasons are disclosed development evidence. Protected 2026 remains
closed. Do not claim long-term value or publish a model from these findings.
Preserve original G0/C0/Marcel benchmarks and all failed decisions.

## Reproduction

New model primitives have chronology, gradient, probability-conservation, and
player-cluster resampling tests. The runners require existing generated research
artifacts; hashes bind the inputs. They reject overwriting an inspected candidate
run. The local implementation passed its tests before this branch was prepared;
branch-specific verification is recorded in the pull request.

The prior long status file is preserved in
[project history through August 26](project-history-through-2026-08-26.md).
