# Pitcher workload v2 result

Date: 2026-09-22

## Decision

Use the standalone four-model workload ensemble for pitcher opportunity accounting and
the next team-capacity test. Do not multiply it by a separately forecast pitcher rate
to replace the selected total-value model; that three-part WAR architecture already
lost to the two-part total-value architecture.

The selected workload forecast estimates:

1. the probability that the pitcher appears in MLB next season;
2. batters faced conditional on appearing; and
3. zero-inclusive expected batters faced as the product of those two quantities.

Across 29,491 player-season rows in six forward tests, expected-BF RMSE is **69.88**,
compared with **81.58** from carrying forward the pitcher's most recent MLB BF. The
improvement is **11.70 BF RMSE**, with a player-clustered 95% interval from **10.59 to
12.78 BF** in favor of the model. The model wins RMSE in all six seasons.

The model's pooled MAE is 25.43 BF versus 25.25 for carry-forward. That is a small loss:
the ensemble is better at avoiding large workload misses, not at every small or zero
case. RMSE and an approximately correct population mean are the more relevant criteria
for expected opportunity and later team-total reconciliation, but both scores remain
reported.

## Engines and selection

The workload ensemble averages Ridge, CatBoost, LightGBM, and Explainable Boosting
Machine forecasts. A chronology-only pruning rule retained all four members in every
fold. The same role-transition block that improved pitcher value was tested in Ridge,
CatBoost, and LightGBM workload models.

The role-aware workload challenger is effectively tied with the base ensemble:
**-0.0003 BF RMSE**, with a 95% interval from **-0.151 to +0.147**. Ridge and CatBoost
improve slightly, while LightGBM worsens slightly. The role block is therefore not
selected for workload. This is an intentional separation: a feature may help project
pitcher value without providing additional batters-faced accuracy.

## Integration

The exposed 2025 pitcher development table now includes:

- value-model MLB arrival probability;
- workload-model MLB arrival probability;
- conditional MLB BF;
- zero-inclusive expected MLB BF;
- conditional pitcher component WAR;
- expected pitcher component WAR; and
- calibrated component-WAR ranges.

The workload and value forecasts remain separate. Expected BF can now be constrained
against realistic team innings, starts, and relief capacity without changing portable
pitcher talent or the better total-value forecast.

## Limits and next test

The current workload model does not know the pitcher's future organization and does not
use organization depth. Carry-forward has slightly better MAE, and role features do not
provide a reliable incremental gain. The next experiment must apply team capacity only
as a downward opportunity constraint, preserve an organization-neutral view, and test
whether it improves future player-level BF and value for players whose current teams
otherwise project excess innings.

The 2026 outcome season remains sealed.

