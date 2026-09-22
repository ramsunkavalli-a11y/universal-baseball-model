# First three-year hitter forecast

Date: 2026-09-22. M1 and M2 completed for mean forecasts; playing-time consistency
remains unresolved and uncertainty ranges are withheld after a failed safety audit.

## What changed

We now have separate 2026, 2027 and 2028 hitter value forecasts and their three-year
sum for 3,907 players, using evidence through 2025. The longer-range model learns
from age, level, recent workload and three years of batting history. It is not the
next-year projection copied forward or multiplied by three.

The selected procedure improved three-year prediction error in all six historical
tests. The first-year estimate is shared with the reference, so this measures the
benefit of better Years 2 and 3. The stronger existing next-year batting ensemble is
refit where supported; early or unmatched rows receive a labeled simple fallback.

| Target | Simple longer-range reference RMSE | Selected procedure RMSE |
|---|---:|---:|
| Year 2 | 0.5550 | 0.5016 |
| Year 3 | 0.5675 | 0.5224 |
| Three-year sum | 1.2500 | 1.1180 |

The primary equal-origin MSE change is -0.31269, with a paired player-cluster 95%
interval of [-0.40411, -0.23985]. The approximately 11% reduction in RMSE survives
excluding pandemic windows, using nonoverlapping windows, and excluding validation
players from historical fitting. These are exposed historical development results,
not a fresh prospective confirmation or a comparison against public projections.

The improvement is largest for current MLB players (three-year RMSE 2.9802 to
2.6100). Upper minors improve from 0.9081 to 0.8867 and lower minors from 0.3481 to
0.3418. The inactive/unknown group is essentially unchanged and lacked the pilot
support required for a formal subgroup gate. Overall success does not prove every
individual player or subgroup is well estimated.

## Which model won, and what did not

The nested rule selected **D1, regularized linear regression**, before each outer
test and again for the current forecast. It passed all frozen supported subgroup,
annual-retention, uncertainty-of-improvement and season-sensitivity gates.

The two CatBoost forms actually had better pooled outer RMSE: 1.0823 for direct
annual value and 1.0745 for activity × conditional value. They were not selected by
the earlier player-disjoint inner tests. Calling them failures would be wrong;
promoting them simply because their subsequently exposed outer scores look best
would also be wrong. They remain named challengers, not the delivered forecast.
The discrepancy between new-player/disjoint selection and returning-player deployment
is a specific follow-up question, not permission for a new unrestricted sweep.

Predicting the three-year total directly (C1) gave RMSE 1.1424, worse than the selected
annual sum. We therefore do not force an after-the-fact reconciliation to that total.
Original one-year, six-year comparable and frozen-forecast packages remain unchanged.

## What the player report contains

- Annual and summed batting-plus-replacement value, including no-MLB outcomes.
- Separate annual MLB activity chances and expected PA, refit using the existing
  accepted multi-horizon opportunity form and its no-pandemic-crossing training rule.
- Current level/stage, age, evidence status, and historical roster-review flags.
- An explicit uncertainty-unavailable status. The attempted ranges and their failed
  conditional-coverage checks remain in the research report, not the player display.

The initial three-year ranges covered 83.4% of outcomes in the two later eligible
backtests, including 81.7% for current MLB players. **That reassuring aggregate was
misleading.** A post-fit display-safety check used each earlier calibration set's
80th percentile of predicted value to identify higher-value players. Coverage there
was only 50.0% for current MLB players, 36.6% for upper minors and 52.3% for lower
minors. The many near-zero outcomes hid the problem.

We therefore withhold all player-facing ranges, keep raw residual offsets for audit,
and make no interval-accuracy claim. No ranges were retuned against these exposed
results. This diagnostic did not change the frozen point-model selection. The
detailed report retains CRPS, coverage and width for both procedures. A later
conditional/distributional model must handle the changing variance and no-play mass,
not simply apply one stage-wide residual band to every player.

The current first year has 3,720 existing-stack forecasts and 187 B0 fallbacks.
Historical names recover some missing display identities; 136 rows still display
MLBAM IDs rather than an invented name. No certified organization mapping was attached,
so the new view filters by stage/level but does not mislabel affiliate IDs as MLB teams.

## Important weakness found while inspecting players

**The separate opportunity and value models are not yet jointly consistent.** The
old opportunity form uses age, level, workload and 40-man membership but not the full
batting signal. It can be pessimistic about established productive hitters. For
example, the recovered 2025 membership list has Pete Alonso absent despite 709 MLB
PA. His reused Year 3 opportunity forecast is about 28% and 88 expected PA; the direct
batting-value model forecasts 2.70. Aaron Judge is listed on the 40-man source but
still has only about 55% and 168 expected PA in Year 3 alongside 5.12 direct value.

These are not a coherent single player path. The explorer warns about this globally
and flags current MLB hitters absent from the historical membership list. Do not
divide direct value by these PA estimates to obtain “hitting talent.” No player was
manually boosted, no stored probability was silently replaced, and this diagnostic
did not change the predeclared value-model selection.

Before treating the combined output as a finished player-value product, audit the
membership source, test a talent-aware established-player opportunity update, and
replace the failed stage-only uncertainty method under a new frozen test.
Use the existing established-hitter opportunity research before rebuilding anything.
Keep the direct value forecast as the benchmark, and require out-of-sample probability,
workload and joint-consistency checks. This is the immediate bounded follow-up;
pitcher Year 1–3 and supported Years 4–6 remain the next main-plan extension.

## Scope and reproducibility

This target excludes position, baserunning and defense in every year. It is not full
WAR, club-controlled production or economic surplus. No independent public whole-WAR
table was recovered for this batch, so no whole-WAR/public-model superiority claim
is available. The historical denominator is the existing roster/stat union, not a
complete reserve-rights inventory. Current-corrected historical data are reconstructed
vintages, not archived publications.

The corrected 2020 replacement budget is 210.641975, based on 898 completed games,
instead of the old fixed 570. All candidates use the same corrected target. This is
an accounting correction, not counted as an accuracy gain. No 2026 results were used.
The original full-hitter 2026 freeze passed its 31-file hash/formula verification.

Files:

- [Frozen test contract](multiyear-hitter-v1-contract.json)
- [Machine-readable results](multiyear-hitter-v1-result.json)
- `model_artifacts/multiyear-hitter-development-2026-09-22/`: player forecast,
  outer predictions, selection, residual offsets, reports and hash manifest.
- `scripts/materialize_multiyear_hitter_v1.py`: source and calendar-label builder.
- `scripts/evaluate_multiyear_hitter_v1.py`: bounded cached nested fits.
- `scripts/report_multiyear_hitter_v1.py`: scoring, artifact package and local explorer.
- `reports/generated/multiyear-hitter-v1/index.html`: generated standalone player view.

The new modules plus reused target/opportunity tests passed 31 focused tests.
The UI was checked for search, player selection, annual totals, ranges and warnings.
Re-run the report builder to regenerate the local view; do not overwrite the frozen
test contract or original forecast files when pursuing the next hypothesis.
