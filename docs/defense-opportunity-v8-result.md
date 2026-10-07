# Defensive opportunity comparison identifies an allocation flaw

2026-10-07. The strongest simple reference scales prior-year defensive usage to
projected batting PA. Adding age and career stage to broad position averages
helps slightly, but neither learned-average method is suitable for the value
layer: player checks reveal expected innings at unrelated positions.

## Historical results

All 12,432 forecasts at the 2022–2024 origins remain in the test, including
nonarrivals and exits. PA, batting ability and defensive skill are unchanged.
Each score below is RMSE in fielding outs across eight position cells; divide by
three for innings. Smaller is better. These are exposed development seasons,
not new protected confirmation.

| Next season | Prior usage | Usage scaled to PA | Broad role averages | Role averages with age and stage |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 187.15 | 168.77 | 173.09 | 172.40 |
| 2024 | 180.48 | 164.70 | 173.75 | 173.22 |
| 2025 | 186.26 | 164.96 | 178.28 | 177.67 |

The contextual average improves by 0.608 outs over the pooled average, about
0.35%. Its paired whole-player 95% interval is −1.253 to −0.015 outs. This small
gain meets the stated score/group/totals tolerances, but is not competitive with
the stronger ratio anchor. Numerical tolerances do not override baseball logic.

## Why the allocation fails

Hoskins receives 89 projected catcher outs; Guerrero receives 130. There is no
personal catching evidence behind those numbers. The group calculation borrows
an entire future position vector from every player contributing some origin
role weight, then mixes those vectors a second time. That spreads unrelated
roles rather than estimating each player's actual repertoire.

The same review distinguishes omitted known plans from unavoidable surprises.
Varsho and Springer had dated December 2022 assignments that this historical
usage-only bridge omits. Hoskins' March 2023 ACL injury and McLain's March 2024
shoulder injury occurred after the forecast dates. The Tatis miss comes mainly
from an older cached playing-time forecast that did not handle his finite
suspension return. These require different treatment, not a generic low-defense
penalty. [All 13 focal and 39 peer explanations](defense-opportunity-v8-player-review.md).

## Coverage and opportunity conversions

The audited native counts can be connected to fielding exposure without treating
missing measurements as zero skill. Three-year league conversions use actual
catcher pitches, throwing/blocking opportunities, isolated OF advancement
opportunities and received 1B throws. Every one of the 75 conversions excludes
held players and future seasons. Available official exposure coverage is almost
100% for catcher/receiving sources, but only 70–80% for isolated OF arms because
mixed-position records cannot be cleanly separated.

On players with positive measured native opportunities, the ratio reference
usually beats persistence and the learned role averages; throwing in 2024 is
an exception where the old hybrid is better. The conversions identify a usable
bridge for counts, not validated defensive rates or guaranteed run-value gains.

Matched/full MLB totals reconcile in each position. Correct aggregate totals do
not establish calibration: new/returning defenders receive about half their
actual exposure, while exits/nonarrivals receive positive expectations. That
offset must remain visible alongside individual forecast errors.

## Decision and next work

Do not promote either role-average allocator. Retain the stronger simple anchor,
the verified position source and the separate tested skill histories. Complete
one position-repertoire/exposure repair before integrating delivered defensive
runs and expanded player value. Sparse minor-league skill is still unknown,
not a measured average; this opportunity test does not validate lower-minors
talent transfer or six years of control.

All 2,604 empirical tables, 12,432 forecasts, 7,598 native source records and
75 conversion cells independently replay. The player review is complete; the
result is a documented design failure, not an execution failure. Frozen 2026
forecasts, protected outcome selection and the explorer are unchanged. Lovich's
separate batting defect remains open.
