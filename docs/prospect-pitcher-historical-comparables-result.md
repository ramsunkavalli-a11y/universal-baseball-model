# Universal pitcher historical comparables

Status: **arrival and expected outcome accepted; conditional rate rejected**.

Every current pre-MLB pitcher is evaluated with the same 150-neighbor procedure used
for hitters. Comparison stays within exact primary level and uses age, current BF and
regressed strikeout, walk, home-run and other-outcome rates. Players who never reach
MLB remain in the outcome population as zero.

| Four-year pitching-plus-replacement WAR | Bias | MAE | RMSE |
|---|---:|---:|---:|
| Population baseline | 0.028 | 0.213 | 0.570 |
| Historical comparables | 0.022 | 0.191 | 0.557 |

The first retrospective 2021 test improved all-player and arrival metrics, but its
reference outcome window overlapped the target snapshot. A later strict chronology
audit supersedes that evidence. Under nonoverlapping 2008, 2013, 2018 and 2021 folds,
all-player MAE/RMSE and arrival Brier/log loss improve in every fold.

Conditional pitching quality does **not** pass. Its MAE is 0.832 versus 0.790 for the
population baseline and RMSE is 1.105 versus 1.070. That current field is therefore
withheld from the explorer. Descriptive conditional cumulative production remains
visible to reconcile `arrival × conditional cumulative WAR = all-player expected
WAR`; it is not accepted as a pitcher-talent estimate. Role, workload projection,
whole-player WAR and FV remain outside this foundation.

The strict audit confirms the rejection: conditional-rate error improves in 2013 and
2018 but fails in both 2008 and 2021. The 2021 MAE is 0.805 versus 0.791 for the
population baseline. See `docs/prospect-comparable-chronology-result.md`.

Machine-readable validation is in
`docs/prospect-pitcher-historical-comparables-result.json`.

The 25/50/100/150/250-neighbor sensitivity confirms the boundary. Fifty neighbors
has the best all-player MAE and RMSE, but no tested width makes conditional pitching
quality beat the population baseline. Changing neighborhood width cannot repair that
missing signal, so the foundation stays at 150 and keeps pitcher conditional quality
withheld.
