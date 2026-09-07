# Project status and handoff

Updated 2026-09-06. This is the current start-here document.

## Active plan

The user has prioritized model quality and paused interface development.
Read [the current model plan](current-model-plan.md).

The clarified end goal is every-player trade value updated with each game.
The [direction review](trade-value-direction-review.md) finds useful foundations
but missing career/control/cost and continuous-update integration. It also identifies
older opportunity/roster models to reuse before building another challenger.
The broader roadmap now includes pitcher and whole-player value integration;
website work remains paused. No new valuation model was fitted in this review.

This review branch builds on `hitter-v2-pbp-outcomes` at `b3d55cc`. It contains
model code, experiment records, and the plan. It does not change a website or
promote a model. Protected main and the v1 release are unchanged until integration.

## Completed research

- Recovered the original 2024 opportunity forecast and verified exact IDs and
  official targets against O2026D. Its lower errors support reuse of the older
  model, with documented subgroup limits. [Comparison](recovered-opportunity-comparison.md).

- Tango-focused review executed: saved translation forecasts still improve
  common-MLB-centered absolute error; historical-support subgroups remain
  descriptive and selection risk remains. The old richer opportunity model has
  promising recorded results and should be recovered for an identical-target
  comparison. [Evidence and next work](tango-focused-model-work.md).

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
reference. Stop global calibration searches. O2026D now supplies certified MLB
batting-PA labels including zeros and a fixed level-aware opportunity benchmark.
It improves pooled any-PA Brier error by 10.0%, with modest playing-time gains.
[Results, population correction, and limitations](hitter-v2-O2026D-result.md).

Next audit cohort omissions and prior-date role/age/roster availability, then
predeclare one player-specific alternative. Prior-season-active coverage does
not yet cover inactive or entirely new players. Do not describe this as a complete
prospect model or convert its outputs to career value.

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
