# Anchored hitter development: result

Completed 2026-09-22 against the [precommitted plan](hitter-anchored-development-v1-plan.md).
**Keep the delivered model and explorer unchanged.** The learned development
adjustment failed its acceptance checks. Retaining a performance estimate is a
useful lead, not a validated replacement or evidence that young stars must decline.

## What we tested

At each historical cutoff, estimate performance per 600 MLB PA using only outcomes
already known then. Separately estimate Year-2 MLB participation, playing time if
active, and a change from that performance estimate. All later training rows have
their own genuinely earlier forecast, not a retrospectively fitted anchor.

This tests batting plus replacement, **not full WAR or pure hitting talent**.
Conditional rates are learned from players who subsequently played in MLB. Their
application to minor leaguers does not identify a universal MLB counterfactual.
PA weighting targets the rate appropriate for expected total production; it avoids
requiring independence between PA and rate in the population mean identity, but
does not guarantee that separately fitted finite models estimate that identity well.

The sole candidate A learns rate changes. Diagnostic C holds the estimated rate
unchanged with identical opportunity predictions. Diagnostic D directly regresses
the future rate. A and D have the same linear function class, with different
regularization centers; describing A as extra information would be misleading.

## Main result

Equal-weighted historical origins: 2016–19 and 2021–23. Lower error is better.
All players, including those with no subsequent MLB play, enter value scoring.

| Year-2 forecast | RMSE | MAE |
|---|---:|---:|
| Delivered reference | 0.50228 | 0.19198 |
| A: estimated rate plus learned change | 0.50955 | 0.14997 |
| C: retain estimated rate | 0.49349 | 0.14606 |
| D: predict later rate directly | 0.50986 | 0.14997 |

A improves only three of seven origins. Its paired MSE difference from the
reference is +0.00736, with a player-cluster 95% interval of [-0.00893, +0.02764].
Its MSE is worse than C by +0.01611 [0.00181, 0.03558]. PA-weighted active-player
rate MSE also fails to improve: A 4.20896 versus C 4.20484. The claimed benefit of
learning development is not established by this implementation.

C improves six of seven origins; its diagnostic paired MSE difference from the
reference is -0.00875 [-0.01617, -0.00179]. But it was not the promotion candidate,
and its full-sample top-50 MSE worsens about 22%. We do not substitute it after
seeing the scores. A similarly worsens top-50 MSE about 23%, as well as lower- and
upper-minors errors. Overall MAE, nonpandemic overall MSE, and the three-year
non-inferiority checks pass; the other failed gates still reject A.

## The pandemic sensitivity matters

Excluding origins 2018/2019, whose two-year windows cross the pandemic, overall
RMSE is 0.51937 for the reference, 0.51463 for A, and 0.50149 for C.

Among the 79 young top-50 player-season observations in these nonpandemic windows:

| Year-2 forecast | Mean projected value | Actual mean | RMSE |
|---|---:|---:|---:|
| Delivered reference | 2.722 | 3.793 | 2.171 |
| A: learned change | 3.728 | 3.793 | 1.854 |
| C: retain rate | 3.539 | 3.793 | 1.863 |

Thus the full-sample high-end failure is **not** a general failure among young stars
in normal-season windows. This small sensitivity group is below the predeclared
100-row subgroup threshold, uses already-exposed development data, and cannot
override the frozen all-origin gates. Report both views, not just the favorable one.
Actual shortened-season value and ordinary full-season talent are different
questions; a forecast made before an unforeseen shutdown cannot anticipate it.
No hindsight season-length feature or outcome-based exclusion was added to fitting.

## Opportunity is not settled either

On the six origins with archived accepted-v2 opportunity predictions, top-50 PA
MSE rises from 42,553 to 50,917 (about 20%). Mean PA error changes from 36 PA too
low to 33 PA too high. Activity Brier worsens from 0.00865 to 0.01000, while log
loss improves from 0.05675 to 0.05385. Conditional-PA MAE worsens from 170.09 to
175.40. The new opportunity heads are not an across-the-board improvement.
The 2023 origin is excluded only from this supplemental comparison because it
has no archived v2 opportunity replay; it remains in every Year-2 value gate.

These comparisons implicate opportunity estimation and calendar exposure as
remaining issues; they do not causally attribute all value error to either one.
For current top-50 hitters, Year-1 mean is 3.478, reference Year 2 is 2.798, A is
2.827, and C is 3.155. Learning the change largely erases the carry-forward uplift.
Current examples are diagnostics, not accuracy evidence.

## What changed and what comes next

Added a reproducible anchored-development experiment, cutoff-specific anchors,
separate rate/opportunity diagnostics, and a verified artifact package. No player
forecast, explorer, or original frozen package was replaced. No 2026 outcomes
were opened. Seven new tests cover future-label mutation through both fitting
paths, chronology, PA weighting, keyed joins, composition, and protected cutoffs.
The original 31-file freeze and prior horizon package also verify unchanged.

Next bounded work: decompose high-value-player opportunity errors by ordinary
versus disrupted calendar exposure and compare the accepted and challenger
opportunity heads on identical rows. Fix the ordinary-season target and calendar
stress-test rules **before** another model comparison. Keep no-play players and
all declared origins visible; do not retrospectively erase 2020 to obtain a pass.
Then decide whether a constrained development curve is justified. Do not launch
another unconstrained blend or reward prettier trajectories without error gains.

Reproduce from the repository root:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/evaluate_hitter_anchored_development_v1.py
.venv/Scripts/python.exe -X utf8 scripts/audit_hitter_anchored_development_v1.py
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_hitter_anchored_development.py -q
```

Package: `model_artifacts/hitter-anchored-development-v1-2026-09-22/`. Source
hashes, dependency versions, anchor vintages, clipping counts, individual forecasts,
all gates, and supplemental diagnostics are preserved there. Historical results
remain development evidence, not a fresh confirmation sample.
