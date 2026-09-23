# Hitter playing time: ordinary seasons versus calendar disruption

Completed 2026-09-22 under the [precommitted diagnostic plan](hitter-opportunity-calendar-v1-plan.md).
**No forecast changes.** The earlier statement that the challenger worsens top-player
playing time needs qualification: it improves the four ordinary forecast windows,
but loses badly on the shortened 2020 target and also loses on the 2021 target.
This is not a newly validated model or a reason to waive the prior acceptance gates.

## What the split shows

Saved accepted-v2 and challenger predictions are matched on 26,571 player/origin
rows, from origins 2016–19 and 2021/2022. The top 50 each year are fixed by the
original first-year value forecast, never by future outcomes or a swapped model.
The 2023 origin remains in the previous seven-origin value result, but is absent
here because it has no archived accepted-v2 opportunity replay.

Top-50 unconditional PA error, in PA RMSE; lower is better:

| Forecast window | Player-season rows | Accepted v2 | Challenger |
|---|---:|---:|---:|
| All six origins | 300 | 206.3 | 225.6 |
| Four ordinary forecast windows | 200 | 188.6 | 174.9 |
| Ordinary pre-pandemic windows | 100 | 173.4 | 150.1 |
| Ordinary post-pandemic windows | 100 | 202.7 | 196.6 |
| Origin 2018, shortened target 2020 | 50 | 290.2 | 381.4 |
| Origin 2019, pandemic before target 2021 | 50 | 169.7 | 194.1 |

The challenger improves top-50 PA MSE in all four ordinary origins. Its equal-origin
MSE difference is -4,998, with a player-cluster 95% interval [-10,518, +444]: the
direction is consistent, but this small group's improvement is still uncertain.
For **all players** in ordinary windows, PA RMSE improves 86.4 to 80.7; MSE
difference -943 [-1,183, -699]. That broader improvement is better supported.
These are exposed development folds, not a new confirmation sample.

“Ordinary post-pandemic” means the cutoff-to-target interval is ordinary. It does
not mean the player's training/input history was unaffected by 2020.

## Is it participation or workload?

We swap old/new participation probabilities and conditional PA in all four
combinations, then split the change in squared error symmetrically across the two
heads. The contributions sum exactly to the total error change for every player.
This is an accounting decomposition of predictions, not a causal claim.

For ordinary-window top-50 players, roughly 86% of the PA-MSE improvement comes
from conditional PA (-4,299); participation contributes -700. All 200 actually
played in the target year, but we do not use that outcome to select them or to set
their forecasts to 100% participation.

Their mean actual PA is 564.2. Accepted-v2 predicts 454.3; the challenger predicts
509.5. Most of the shortfall is the workload estimate, not failing to recognize
that stars are likely to play: mean activity probabilities are 96.5% and 97.1%.
The full-six-origin worsening is almost entirely conditional-PA error (+8,361 MSE,
versus +2 from activity). The 2020 workload miss overwhelms ordinary-window gains.

Do not conclude that participation is solved: ordinary top-50 Brier worsens while
log loss improves, and recent-window probabilities have their own misses.

## What season length explains—and does not

The certified 2020 schedule contains 898 completed MLB games, so its league-average
exposure is 898 / 2,430 = 0.369547 of a normal 162-game schedule. As a hindsight-only
sensitivity, multiply both models' conditional PA by that fraction. Actual outcomes
and activity probabilities remain unchanged; there is no refit or scaling up of
observed player production.

For 2020 top-50 players, PA RMSE becomes 74.2 for accepted-v2 and 63.1 for the
challenger. Mean challenger PA becomes 211.4 against actual 206.8, rather than the
unadjusted 572.0. The model forecasting more normal-season PA was punished more
heavily by the unforeseen loss of games.

That is **not** a forecast anyone could have made at the 2018 cutoff. It does not
model opt-outs, roster-rule changes, team-specific schedules, or participation
effects. The 2021 target failure also remains: an intervening pandemic is not the
same as a short target season. A single season shock cannot establish general
robustness, and player-resampling intervals do not measure season-shock uncertainty.

## Why not just raise the forecasts?

Among the 63 young top-50 observations in the four matched ordinary windows,
PA RMSE worsens from 148.9 to 159.3. Mean PA bias improves from -45.4 to -23.5,
but being closer on average does not mean assigning the right PA to each player.
This group is below the frozen 100-row support threshold; it remains descriptive.
It is smaller than the preceding 79-row young-star value sensitivity because that
earlier seven-origin analysis also includes 2023.

Holding the carry-forward performance estimate fixed, ordinary top-50 value MSE
barely changes: 3.74695 to 3.74067. For all ordinary-window players it changes
0.25657 to 0.25360. Improving total PA error does not automatically improve the
allocation of production to the right players. These values are **batting plus
replacement**, not full WAR, and neither is the delivered direct-value reference.
The diagnostic does not manufacture a hitting rate by dividing delivered value
by a separately fitted opportunity forecast.

In the two recent ordinary origins, both methods underpredict top-50 PA by roughly
130–137 on average. Thus the issue is not confined to scoring the 2020 target.
Whether shortened seasons in training contribute to later underprediction is a
specific hypothesis still to test, not a finding of this no-refit diagnostic.

## Next bounded experiment

Test an explicitly schedule-exposure-aware conditional-PA model, holding the
participation and performance estimates fixed. Historical training seasons may use
their already-observed exposure; a future ordinary-season forecast must not receive
the target year's realized games. Keep ordinary-season accuracy and full-calendar
stress performance separately visible, along with young-star and total-value tests.
First recover the missing accepted 2023 replay or explicitly freeze a matched
six-origin scope. Declare the new targets, fitting recipe and acceptance rules
before fitting; do not promote the best-looking head swap from this diagnostic.

The next question is whether this improves individual workloads and combined value,
not whether it makes more young players' lines slope upward. Preserve the original
failed experiment and 2026 holdout. No manual youth bonus or across-the-board PA boost.

## What was added and verified

Added a reusable, keyed head-swap/calendaring audit and tests for row/label mismatch,
chronology, no-play treatment, exact attribution, ordering stability and unchanged
forecast hashes. Current explorer, accepted means/opportunities and original frozen
packages are untouched; no 2026 outcomes were read. The original 31-file freeze
verifies unchanged.

Artifact package: `model_artifacts/hitter-opportunity-calendar-v1-2026-09-22/`.
It contains per-player predictions/contributions, separately labeled hindsight
rows, every origin/group score, support, intervals and source hashes.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/audit_hitter_opportunity_calendar_v1.py
.venv/Scripts/python.exe -X utf8 scripts/audit_hitter_opportunity_calendar_v1.py --verify
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_hitter_opportunity_calendar.py -q
```
