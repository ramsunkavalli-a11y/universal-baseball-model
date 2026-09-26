# Common-weight workload test: small cumulative gain, not a clean replacement

2026-09-25. [Fixed prefit plan](hitter-workload-common-weight-v1-plan.md).

## Decision

Keep D as the current research workload reference. Retain W as evidence that
training weights matter, but do not promote it across all three horizons. The
primary cumulative comparison improves, while annual and cohort diagnostics
show real tradeoffs. This is not a failed hypothesis about coherent weighting;
it is a mixed predictive result from one properly isolated change.

## The test

All twelve archived D fits replayed exactly before any W fit. W keeps the
participation-training weights when selecting positive-PA training outcomes,
instead of recalculating equal-player weights within those outcomes. Same
players, detailed columns, feature filtering, LightGBM settings, seed, clipping,
chronological cutoffs and fixed participation forecasts. Only never-debuted
prospect forecasts change; actual non-arrivers remain in evaluation.

| Prospect PA RMSE | D: existing | W: common weights | E: ensemble reference |
|---|---:|---:|---:|
| Year 1 | 28.603 | 28.744 | 29.631 |
| Year 2 | 50.814 | 50.805 | 51.917 |
| Year 3 | 66.281 | 65.743 | 67.075 |
| Three-year sum | 121.668 | 120.851 | 126.184 |

The primary equal-origin three-year MSE difference W−D is **−198.18 PA²**, with
a paired whole-player 95% interval **[−388.51, −14.74]** (4,000 draws, seed 1729).
This is about a 0.7% RMSE improvement, on 9,833 prospect-origin records / 7,050
players. It improves 2016 and 2021, slightly worsens 2022. Against E the interval
is [−2082.89, −601.37] PA² and all three cumulative origins improve.

## Why not simply declare success?

Year 1 worsens in four of five origins, though its pooled interval spans zero.
Conditional PA error among actual MLB participants worsens in all three years:
125.80→128.69, 167.06→168.26, 185.25→186.20. Conditional errors are not weighted
the same way as delivered expected PA, so the latter can still improve; neither
score should stand in for the other. Non-arriver errors also rise in every
horizon. Cumulative MAE worsens 33.12→33.79 PA.

Totals illustrate the tradeoff:

| Origin | Actual three-year prospect PA | D | W |
|---|---:|---:|---:|
| 2016 | 86,494 | 65,966 | 72,845 |
| 2021 | 121,444 | 72,078 | 79,220 |
| 2022 | 97,303 | 98,994 | 108,015 |

The average absolute cohort-total error improves 23,862→22,195 PA, but 2022's
overprediction expands substantially. The 2021 shortfall remains enormous;
weights do not repair participation probabilities, which were held fixed.

In the archived 2021-origin examples, Bobby Witt Jr.'s three-year expected PA
rises 704→846 against 2,035 actual; Joe Perez rises 638→712 against one actual.
For 2022, Anthony Volpe moves 952→1,118 against 1,886; Osleivis Basabe moves
567→652 against 94. These are diagnostics, not manual overrides. More generous
conditional workloads help eventual regulars but also inflate failed paths.

## Verification and limitations

52,181 annual rows, twelve exact old-head replays, twelve new fixed heads and
one exact future-label/input mutation replay. No changed probabilities,
non-prospect predictions, frozen forecasts, or protected 2026 outcomes.

An implementation amendment is retained beside the untouched prefit manifest:
the first run stopped before saving/scoring because the diagnostic previous-PA
field had legitimate nulls. The amendment keeps those players and reports an
unknown-workload group. Training and primary scoring did not change; all fits
were rerun. The amendment records before/after code hashes and the reason.

These are exposed historical development folds and just three complete origins.
The player bootstrap does not quantify uncertainty over new season regimes.
No horizon-specific W/D mix is selected after inspecting these results.

Artifact: `model_artifacts/hitter-common-weight-v1-2026-09-25/`.
Proceed to the already declared archived-input batting diagnostic, without
substituting W into it. Further W value-transfer work needs a separate contract.
