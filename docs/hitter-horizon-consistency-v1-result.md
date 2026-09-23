# Why the leading hitters usually decline from Year 1 to Year 2

2026-09-22. Work follows the committed
[bounded comparison](hitter-horizon-consistency-v1-plan.md). Historical results are
exposed development evidence, not independent prospective confirmation. All values
below mean MLB batting plus replacement, not full WAR or conditional hitting talent.

## The like-for-like diagnostic

Hold membership fixed at the 50 highest **original Year-1 forecasts**, rather than
selecting different stars under each model. For the current 2025-cutoff forecasts:

| Method | Average 2026 value | Average 2027 value | Change |
|---|---:|---:|---:|
| Displayed: rich first year, aggregate Ridge second year | 3.478 | 2.798 | -0.679 |
| Aggregate Ridge both years, mature labels for each | 3.194 | 2.798 | -0.396 |
| Aggregate Ridge both years, exactly matched training rows | 3.190 | 2.798 | -0.392 |

The model/information switch accounts for about 0.28 of the 0.68-unit displayed
difference in this diagnostic substitution. It does not explain the remaining
0.40-unit decline. Matching the training rows makes very little additional
difference here. This is not a causal attribution of physical aging, injury,
attrition, or regression to the mean. Separate horizon regressions can themselves
be miscalibrated; using the same family does not certify the learned slope.

The switch matters much more for some players than others:

| Player | Displayed 2026 | Same-family 2026 | Existing 2027 |
|---|---:|---:|---:|
| James Wood | 3.538 | 2.764 | 2.587 |
| Jackson Holliday | 2.492 | 1.215 | 1.187 |
| Gunnar Henderson | 3.965 | 3.251 | 2.931 |
| Bobby Witt Jr. | 4.402 | 4.054 | 3.649 |

Lowering the first year would make the trajectory look smoother without making
the forecast better. It is a diagnostic, not an authorized production change.
Nor should the second year simply be increased to match a desired shape.

## Fair comparison and limitations

The sole replacement candidate extends the existing equal-weight five-model
recipe to Year 2, using the same cutoff features and correctly replaced Year-2
activity, PA and value targets. All target years must be complete at fitting time.
No next-year performance is supplied as an input, and no 2026 results are read.

The rich feature set has 449 columns. Entirely missing columns by origin are
292 in 2015, 146 in 2016, zero in 2017/2018, 146 in 2021/2022, and zero in
2023/2024. The existing model adapters retain their usual missing-value treatment;
no new source imputation or post-result feature selection is introduced. The
earliest rich two-year fits therefore have weaker evidence than recent ones.

All model comparisons use identical players and fixed top-50 memberships. Stars
selected by a high first-year forecast are not an unbiased sample for interpreting
later regression toward the mean. Year-to-year projected change is descriptive;
actual later-year error and calibration determine acceptance.

## Replacement decision

**Reject the rich Year-2 extension; retain the v2 explorer unchanged.** The candidate
has adequate rich support in 2018, 2021, 2022 and 2023, improves MSE in only two of
those four origins, and fails the paired improvement, nonpandemic, top-player MSE
and top-player bias gates. Three earlier origins correctly retain D1; those ties
are not counted as rich-model successes.

| Historical Year-2 test | Existing D1 | Fixed rich extension |
|---|---:|---:|
| Overall RMSE, seven origins | 0.50228 | 0.50195 |
| Overall MAE | 0.19198 | 0.17168 |
| Nonpandemic RMSE | 0.51937 | 0.52110 |
| Current MLB RMSE | 1.17720 | 1.18048 |
| Current MLB age <26 RMSE | 1.36067 | 1.38412 |
| Fixed top-50 RMSE | 1.98353 | 2.04555 |
| Young players within fixed top 50 RMSE | 2.11211 | 2.18157 |

The equal-origin Year-2 MSE difference is -0.000330, with paired player-cluster
95% interval [-0.005777, +0.005696]. Top-50 MSE worsens 6.4%, and young-top-50 MSE
worsens 6.7%, beyond the predeclared 5% guard. The smaller absolute error is real
within this comparison, but it does not establish improved mean projections or
resolve the concern about stars. Current MLB age >=30 and minor-league groups
perform better on average; these are diagnostics, not permission to select a new
subgroup mixture after examining the results. Cumulative three-year retention
passes, but that alone does not override the failed annual gates.

## The young-star concern remains

In the nonpandemic fixed young-top-50 sample (79 player-season observations, not
79 independent players), equal-origin actual average value is 3.800 in Year 1
and 3.793 in Year 2: essentially flat. The displayed procedure predicts 3.151 to
2.722, a decline of 0.429. Using Ridge in both years reduces that predicted
decline to 0.252; matching training rows barely changes it. The rich Year-2
extension instead predicts 2.656 in Year 2 and does not repair this pattern.

This supports a calibration concern, not a rule that all young hitters should
improve. The cell is below the frozen 100-row subgroup gate and has repeated
players and common season shocks. Across all seven origins, the larger young-top
cell has 117 rows and does meet the support gate; both approaches underpredict
its Year-2 mean, and the rich replacement has worse squared error. Exact fold,
group, model-family and trajectory diagnostics are in the package report.

## Next bounded question

The model-family switch is only part of the issue. Audit whether the aggregate
longer-horizon regression loses persistent batting-talent differences, confuses
conditional performance with the chance of playing, or compresses the high end
when averaging over all players. A possible next challenger would retain the
cutoff-time talent signal and learn subsequent change/retention with age and
workload interactions. It must be specified and tested against the unchanged
direct-value baseline, not implemented as a flat youth bonus or a guarantee that
Year 2 cannot be lower. The present experiment does not validate that next idea.

No individual forecast, chance, PA estimate, uncertainty range, or frozen package
is changed by this completed comparison. Rejected current candidate values remain
diagnostics only; no best-looking member or post-result blend is delivered.

## Reproduction and verification

Run `scripts/evaluate_hitter_horizon_consistency_v1.py` with the recovered local
source inventory. The committed package at
`model_artifacts/hitter-horizon-consistency-v1-2026-09-22/` contains seven-origin
historical predictions, current diagnostic predictions, the complete report and
source hashes. The generated fit cache also retains the five member predictions.
`scripts/verify_hitter_horizon_consistency_v1.py` checks those local cache members
against the equal-weight ensemble by player ID, source/package hashes, target
cutoffs and unchanged v2 reference forecasts. It verified 19,750 matched rows.

44 focused tests pass, including future-label mutation, shuffled-ID joins, complete
Year-2 target replacement and preserved unsupported-player fallbacks. The original
2026 freeze passes its 31-file verifier with its original forecast hash. Missing-
feature warnings and nonfatal joblib temporary-file cleanup warnings occurred;
all five-member fits completed, produced finite predictions and passed keyed
ensemble reproduction checks. No result was substituted after a failed fit.
