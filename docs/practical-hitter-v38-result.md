# Game involvement helps some opportunity forecasts, but is not the finish

2026-10-03. **Keep as a promising research extension; no working-model promotion.**
V33b stays visible. Protected 2026 and the frozen/deployed forecast are unchanged.

## What changed

Recovered games played from all 122,799 existing historical hitting stints,
2008–25, with complete keyed PA reconciliation and no missing game counts.
Added 40 games/PA-per-appearance history features to the same direct workload
learner. The strongest V34 batting-rate head stays bit-exact. The 35 historical
folds, 30,506 forecasts, non-arrivals and all public matches stay fixed.
No injury diagnosis, actual start count or future roster/job information.
See [the pre-fit contract](practical-hitter-v38-contract.md).

## Matched results

Errors average calendar-year losses; smaller is better. Contribution means
batting plus replacement wins, not full WAR or trade value.

| Population | Source-repaired control PA RMSE | Games PA RMSE | Control PA MAE | Games PA MAE | Control contribution RMSE | Games contribution RMSE |
|---|---:|---:|---:|---:|---:|---:|
| All 30,506 | 61.652 | 61.237 | 21.408 | 21.335 | 0.44060 | 0.43976 |
| Old V24 matches, 4,396 | 124.889 | 124.321 | 83.068 | 83.090 | 0.90886 | 0.90859 |
| Public active matches, 1,789 | 144.487 | 143.191 | 111.577 | 111.320 | 1.01638 | 1.01598 |

Working V33b public PA RMSE/MAE are 143.965/110.563, Steamer 135.019/92.399.
Games RMSE is 6.05% worse than Steamer (within the practical 10% goal), but MAE
is 20.48% worse (outside 15%). Public/value differences from the UBM controls
are small and uncertain. Public converted batting-value scores still have
environment/snapshot qualifications; they do not prove talent superiority.

The all-cohort paired PA MSE difference is −50.94, nominal player-clustered 95%
interval [−102.03, −7.32]; delivered-value difference −0.000743 has interval
[−0.001982, +0.000468]. This is exposed development evidence, not independent
confirmation. Thousands of zero outcomes must not obscure the modest active
player gains. Unchanged batting rate RMSE is 1.82465 wins/600.

## Totals and actual players

Upper-minor expected PA improve 93,314→100,089 against 102,951 actual across
the matched historical years. Lower-minor excess shrinks 10,785→9,843 against
6,072, but is not resolved. The 2021-origin shortfall shrinks: 168,633→171,777
against 181,583. Conversely, 2023-origin total grows to 192,114 against 182,194,
worse than 185,096 control. Improvements are not uniform calibration.

- Steer rises 180→233 expected PA against 665: regular AAA use helps, but the
  MLB starting-role transition remains underestimated.
- Meidroth rises 40→147 against 505; positive AAA role evidence is genuinely
  used. Origin-selected peers mostly do not reach comparable MLB workload.
- Winn changes only 306→308 against 637; sustained AAA play alone does not
  solve the model's transition into a regular MLB role.
- Kurtz falls 42→30 against 489. A short first professional season is not
  necessarily poor durability; pedigree/timing still need a better translation.
- Davidson rises 304→405 against zero despite being unlisted at origin. Recent
  regular use cannot replace knowledge of job retention.
- Farmer's predicted PA falls 235→208 as PA/game drops, a sensible use signal;
  the near-perfect delivered total is still partly compensating component errors.

Fifteen complete player reviews reconstruct raw statistics, new inputs, saved
tree paths, unchanged batting rates, products, realized outcomes and three
origin-selected peers. Exact tree path accounting is order/correlation dependent,
not SHAP or causal feature attribution. Every head replays, all old columns
are bit-exact; integrity does not certify predictive sufficiency.

See [the source review](evidence/practical-hitter-v38/source-walkthrough.md),
[player walkthrough](evidence/practical-hitter-v38/player-walkthrough.md), and
[scores/intervals](evidence/practical-hitter-v38/scores.json).

## One justified next step

Test a current-MLB-specific direct expected-PA head, selected solely by origin
MLB participation. Keep the existing non-MLB head and batting model unchanged.
Regular use/retention and first arrival are different processes; a shallow
shared learner may trade them off poorly. The test must retain all cases and
show whether gains require harms to brief debuts/retention, not just totals.
No algorithm sweep, automatic future-role labels or frozen forecast promotion.
