# Earlier MLB Statcast history is captured with small unresolved contact differences

2026-10-04. The bounded 2015 through 2022 capture completed all sixty-four
monthly requests. It retained exact compressed responses and projected only
ordinary identity/results plus exit velocity and launch angle. Together with
the accepted 2023 and 2024 cache recovery, we now have ten consecutive source
years rather than a two-season pilot. No new model has been fitted, and no
forecast, frozen file or explorer has changed.

The new earlier source contains 907,971 complete non-bunt terminal launch pairs.
With the 245,589 recovered from 2023 and 2024, the total is 1,153,560. This is
measurement availability, not evidence of predictive improvement or proof of
complete historical coverage. The local earlier capture occupies about 253 MB,
including compressed exact responses, projected files and receipts. Large raw
data stays outside Git; provenance and reconciliation evidence are retained.

## Independent count and measurement checks

| Season | Returned contact results | Non-bunt terminal results | Complete launch pairs | Residual player seasons after separating catcher interference |
| --- | ---: | ---: | ---: | ---: |
| 2015 | 130,480 | 128,185 | 125,366 | 2 |
| 2016 | 128,825 | 126,799 | 124,628 | 5 |
| 2017 | 127,564 | 125,761 | 124,974 | 1 |
| 2018 | 126,295 | 124,550 | 123,826 | 2 |
| 2019 | 125,768 | 124,234 | 123,273 | 5 |
| 2020 | 43,978 | 43,598 | 43,301 | 0 |
| 2021 | 121,707 | 120,287 | 119,920 | 4 |
| 2022 | 124,275 | 123,209 | 122,683 | 1 |

Every person's 1B, 2B, 3B and HR counts match the independently reconciled
official season counts in every captured year. Contact identities and dates
are checked, and exact retained response bytes reproduce their original hashes.
2020 retains actual shortened-season MLB measurements; there is no invented
minor-league 2020 sample. Earlier readings have greater missingness and their
provider estimation vintage is not certified. A filled field is not proof of
direct camera observation or unbiased measurement.

The official AB minus K plus sacrifice flies and bunts denominator is not the
same as every source terminal record. The contact query also returns catcher
interference records, coded S in the examples inspected; those are retained in
the raw source but are not normal measured BBE. The first adapter's all-X check
was incorrect and stopped. Its four successful chunks and original receipts
were preserved; the second adapter resumed the same queries and recorded all
exceptional rows. Across the recovered years all non-X records are catcher
interference, not a large unintended population of foul pitches.

After separating catcher interference, twenty player-seasons still differ by
one contact each, with either sign. The original aggregate failed-denominator
reports remain intact. The independent audit records these smaller, explicitly
defined residuals in separate files; no source counts were edited to manufacture
an exact match and no model-use waiver has been granted.

## Concrete cases and remaining source review

At origin 2021, Jorge Soler's raw source has 378 non-catcher-interference results
against an official contact denominator of 379. All his hit counts match. The
captured records also include two distinct catcher-interference plays, including
game 634495. Adding those to normal contact would not fix the denominator; it
would conflate a separate event with ordinary contact quality.

Isan Díaz has 170 such source results against 169 official. One captured event
in game 634317 is explicitly an interference error by pitcher Zack Godley, coded
as a fielding error with type X. That is a concrete source-semantic exception to
inspect, not evidence of superior measured contact or an extra ordinary out.

Bryan Reynolds has 443 source results against 444 official in 2021. A terminal
record in game 632195 explicitly describes batter interference, despite an
ordinary field-out event code. Carlos Santana has 467 against 468, without a
matching explanation established by this initial inspection. Their complete hit
reconciliation does not certify the missing/out-result denominator. The full
dated-stat-to-measurement-to-unchanged-forecast walkthrough for earlier source
years remains pending; these diagnostics do not substitute for it.

The remaining discrepancies are Longoria and Travis in 2015; Strange-Gordon,
Fielder, Jay, Gattis and Torreyes in 2016; Dietrich in 2017; Rojas and Alex Gordon
in 2018; Tomás, Cooper, Correa, Bellinger and Cordell in 2019; and Bote in 2022.
Tomás has only two captured results against three official contacts. That tiny
profile cannot be treated as strong power evidence merely because some readings
exist. Missing records and small samples need separate flags.

## Decision before any forecast test

Capture is finished; source approval and player review are not. Preserve both
raw and corrected-denominator diagnostics, explain the remaining semantics,
join actual historical game/venue authority, materialize age-appropriate history
with explicit missingness and count active training people in the actual folds.
Do not describe these earlier years as accepted for fitting under the current
exact source contract until that review is complete. If a defensible source-use
boundary is needed, declare it additively before fitting; do not quietly waive
this contract or select favorable players from future outcomes.

The next model comparison remains direct future MLB hitting with and without
measured contact quality, fixed current PA and exact fallback for untracked
players. Covered minor-league tracking remains a distinct source/calibration
task. None of this reopens team-record tests or the two failed Current Talent
contact residuals. The full hitter-model goal remains active.
