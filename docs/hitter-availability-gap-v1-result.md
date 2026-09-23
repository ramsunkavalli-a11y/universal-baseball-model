# Regular-player PA shortfall and league-budget result

Completed 2026-09-22 under the [user-proposed proxy contract](hitter-availability-gap-v1-plan.md).
**No forecast replacement.** A position-aware shortfall is useful to describe, but
this implementation did not add two-year predictive value beyond position, prior
regular status and existing PA history. This does not establish that it is useless
for one-year availability or minor-league players; those are not this test.

## What the proxy means

Before a season starts, classify prior MLB regulars using the preceding season's
workload and historical position. Build position-specific high-workload references
from the three previous completed ordinary seasons. Compare actual PA with that
reference adjusted for observed season length. Missing prior role/history remains
unknown; a player does not have to survive or reach MLB later to enter the test.

For the 2023 feature season, the learned full-season reference was about 450 PA for
catchers, 630 for shortstops, 535 for center fielders and 590 for designated hitters.
These are 75th-percentile workload references, **not medically healthy ceilings**.
The pool includes prior regulars who subsequently lose their job or do not appear.
An apparent gap can mean injury, platooning, demotion or role loss. A season-end
shortfall measures missed workload; it does not identify why it was missed.

MLB position records support this reconstruction back to 2004. The recovered
all-level position table covers 2021–2024 only, insufficient for the same rolling
two-year comparison. We did not backfill a prospect's historical position from
their eventual MLB role or call a missing minor-league record healthy.

## Fixed comparison

All players stay in value/PA scoring, including future no-play rows. Four outer
origins: 2019, 2021, 2022, 2023; ordinary-window scoring uses the latter three,
targeting 2023–2025. Training starts in 2016 and requires fully mature Year-2 labels.
No 2026 results were read. Participation and estimated batting-plus-replacement
rate are identical across all three forms:

- E: exposure-aware PA model with the existing 81 predictors;
- T: add position, prior regular/measurement flags and workload-reference controls;
- P: add two seasons of shortfall and their change.

The P-versus-T comparison isolates the extra gap transformation from simply adding
position/context. This is exposed development evidence, not an independent holdout.
The health-state transaction fitting arm was superseded before any fits when the
user proposed this simpler proxy; the source audit was retained separately.

| Ordinary-window PA RMSE | E | T: position/context | P: add shortfall |
|---|---:|---:|---:|
| All 12,412 player-season rows | 83.97 | 83.72 | 83.78 |
| 637 measured prior-regular rows | 181.36 | 181.91 | 183.37 |

P versus T improves only one of three origins. Overall paired MSE change is +9.02,
95% player-cluster interval [-22.53, +39.04]. Among measured regulars it is +530.73
[82.94, 966.46]; MAE also worsens from 146.64 to 147.43 PA. Their average bias is
slightly smaller, but the individual forecasts are worse. The value non-inferiority
guards pass; the primary accuracy gates do not.

P versus E is slightly better overall but uncertain, and this cannot establish a
benefit for the gap: adding position/context already accounts for that difference.
No form is selected after the scores. The raw PA history was already an input, so
the gap is a contextual/nonlinear transformation, not new independent injury data.
Transfer to a different model family or horizon remains untested.

## The league accounting check found a separate problem

The current three-year explorer's 3,907 named players sum to:

| Forecast year | Expected PA | Above the 182,926 PA reference | Batting + replacement value |
|---|---:|---:|---:|
| 2026 | 184,724 | 1,798 (1.0%) | 523.85 |
| 2027 | 189,695 | 6,769 (3.7%) | 601.14 |
| 2028 | 191,607 | 8,681 (4.7%) | 615.44 |

The PA reference is the median normal-schedule total in completed seasons 2023–2025,
known at the 2025 cutoff. **PA is not a physical year-to-year constant**: offense,
schedule and rules affect it. These are deviations from a fixed expected pool,
not proof that the actual future league total cannot be larger.

Nevertheless, the named cohort already consumes that pool without reserving PA
for players outside it. Raising all projections to fix selected stars' shortfalls
would worsen this accounting tension. Current MLB players' forecast PA falls
171,801 -> 157,923 -> 140,390, while current minor leaguers' MLB PA grows faster
than the released opportunity. That identifies an interface to test, not proof
that every prospect forecast is too high.

This label system's complete-league normal-season batting-plus-replacement budget
is 570. It is **not complete hitter WAR or combined hitter/pitcher WAR**. A named
cohort may legitimately exceed the league's value total if outsiders contribute
negative value: in the 2019 cohort's 2021 target, actual outsiders had 5,846 PA and
-59.07 partial value. Therefore a signed value gap is not automatically missing
future talent, nor an automatic violation. It can reflect omitted players and/or
calibration error; don't force every named cohort's value to exactly 570.

Historical outsiders used 2,147, 2,981 and 2,290 PA in the three ordinary target
seasons (roughly 1.2–1.6% of league PA). Their signed partial values are preserved.
These are observed diagnostics, not future entrants assigned with hindsight.
Actual MLB PA equals pitcher BF in all 17 certified 2009–2025 seasons. Full-WAR
conservation remains unaudited because this is only the partial-value label system.

No predictions were rescaled or redistributed to make totals look correct. The
ledger explicitly records unallocated PA, excess PA, signed value differences,
and the distinction between full-league and named-cohort outcomes.

## Injury-source caution

Across 127,945 saved transaction rows from 2015–2023, 10,710 have differing date
fields and 2,009 have dates spanning years. These counts cover all transactions,
not just injuries. The conservative normalization retains 13,301 MLB IL events
and uses the latest valid transaction/effective/resolution date for eligibility.
Eight beyond-window rows are excluded before inspecting their descriptions.

This avoids moving a later event backward merely to match its capture year. It
does not prove when a corrected historical description became public. Existing
parsers and frozen results were preserved; the older offseason injury tests were
not revalidated here. Neither offseason reinstatement nor in-season activation
is automatically evidence of full medical recovery. No injury-state model was
promoted in this batch.

## What changed / next

Added the reproducible proxy, its position-only control, a conservative injury-source
audit and a league/cohort budget ledger. The explorer and all original forecasts are
unchanged. Focused tests cover date safety, future-label mutation, fixed prior role,
unknown evidence, exposure maturity, unchanged participation/rate and budget identities.

Next priorities: check the gap on **next-season** availability before dismissing a
shorter-lived health signal; separately test cutoff-safe league opportunity allocation
with an explicit outsider reserve and individual-error guards. Neither requires
predicting team job openings. Minor-league extension first needs historical position
and schedule support; do not extrapolate this MLB result to future MLB survivors.

Package: `model_artifacts/hitter-availability-gap-v1-2026-09-22/`. It includes keyed
features/predictions, prior-reference support, source hashes, all gates, and ledgers.
Reproduce with `scripts/evaluate_hitter_availability_gap_v1.py`; verify with
`tests/test_hitter_availability_gap.py` and the existing original-freeze verifier.
