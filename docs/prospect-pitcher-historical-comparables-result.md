# Universal pitcher historical comparables

Status: **arrival and expected outcome accepted; conditional rate rejected**.

Every current pre-MLB pitcher is evaluated with the same 150-neighbor procedure used
for hitters. Comparison stays within exact primary level and uses age, current BF and
regressed strikeout, walk, home-run and other-outcome rates. Players who never reach
MLB remain in the outcome population as zero.

| Four-year pitching-component WAR | Bias | MAE | RMSE |
|---|---:|---:|---:|
| Population baseline | 0.028 | 0.213 | 0.570 |
| Historical comparables | 0.022 | 0.191 | 0.557 |

The time-ordered 2021 test improves all three all-player point metrics. Arrival also
improves: Brier score is 0.0948 versus 0.1101 for the population baseline and log loss
is 0.3159 versus 0.3815.

Conditional pitching quality does **not** pass. Its MAE is 0.832 versus 0.790 for the
population baseline and RMSE is 1.105 versus 1.070. That current field is therefore
withheld from the explorer. Descriptive conditional cumulative production remains
visible to reconcile `arrival × conditional cumulative WAR = all-player expected
WAR`; it is not accepted as a pitcher-talent estimate. Role, workload projection,
total WAR and FV remain outside this foundation.

Machine-readable validation is in
`docs/prospect-pitcher-historical-comparables-result.json`.

The 25/50/100/150/250-neighbor sensitivity confirms the boundary. Fifty neighbors
has the best all-player MAE and RMSE, but no tested width makes conditional pitching
quality beat the population baseline. Changing neighborhood width cannot repair that
missing signal, so the foundation stays at 150 and keeps pitcher conditional quality
withheld.
