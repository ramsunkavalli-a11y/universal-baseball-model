# Addressing the 2021 prospect forecast failure

2026-09-23. Diagnosis supported; useful partial repairs, no production replacement.

## Latest follow-up: a better conditional playing-time model

The [workload comparison](hitter-conditional-workload-v1-result.md) finds a
useful improvement. With participation probabilities unchanged, the detailed
direct PA model beats the stronger ensemble in all three horizons. Three-year
prospect PA RMSE falls from 126.18 to 121.67 and passes the fixed evidence rule.
The brief/part-time/regular mixture does not pass. Keep the direct model as a
research candidate, not a deployed value model.

This is a partial repair: the 2021 cohort's three-year PA rises from 65,943 to
72,078 versus 121,444 actual. Pena's next-year expected PA rises from 76 to 92
versus 558 actual. Future regulars remain difficult to identify. No explorer
or frozen forecast changed. Next test the value connection without the invalid
new-PA/old-PA scaling of direct nonbatting totals.

## Previous follow-up: does the improvement reach playing time and value?

The [fixed transfer test](hitter-arrival-value-transfer-v1-result.md) improves
prospect PA prediction in Years 1–3; cumulative PA RMSE falls 144.96→127.03 versus
accepted C2, though the stronger ensemble is still slightly better (126.18).
The repaired probabilities' incremental batting-value benefit over original R
is uncertain. The old conditional workload is still low for many eventual
regulars; the 2021-origin cohort predicts 20.3 total PA per prospect versus 37.4.

An automatic value transfer fails: multiplying old direct nonbatting totals by
large new/old PA ratios creates implausible values and worsens next-year lower-
minors error. Those experimental values were not deployed. Keep the source and
arrival repairs, but next test corrected conditional workload and an explicit
opportunity-aware component connection before changing player-value forecasts.

## Previous follow-up: correct the historical inputs

The [source-repair experiment](hitter-arrival-source-repair-v1-result.md) finds
a larger, more consistent improvement than the calendar tweaks. Complete older
debut records, year-end rather than October roster status, and dated Mexican
League context improve next-year Brier/log loss 11.2%/9.5% versus the original
detailed model, in all six tested origins. Both stronger annual benchmarks are
beaten in the four years where matched predictions exist. This is now the
preferred research arrival candidate, pending delivered-value testing.

The 2021-origin estimate rises from 58.1 to 84.7 versus 157 actual arrivals in
2022. Peña's individual estimate rises 3.9%→64.8%; Duran's 1.2%→22.1%. Their
November roster additions are now available at the year-end cutoff, as they
should be. Training and test sources are repaired together, not player-by-player.
But 2021 remains substantially underpredicted, and three-year regular-workload
improvement remains uncertain. All-player regular Brier slightly worsens.
The frozen forecast and explorer remain unchanged; no 2026 outcomes were used.

## Previous follow-up: schedules and the era flag

The [fixed follow-up](hitter-era-schedule-v1-result.md) is complete: 20 new fits,
two future-data mutation replays, and 20 focused unit tests. No live forecast
changed. These are still exposed development results, not fresh confirmation.

**Shorter schedules are real, but this encoding did not fix the forecasts.**
The typical Double-A team played 118 completed regular games in 2021 versus 139
in 2019; High-A and Single-A were also shorter. Actual captured schedules match
3,249 of 3,250 prospects at the 2021 origin. We retained real PA as the sample
size and added PA relative to full team schedules. In four matched annual tests,
Brier improves slightly and uncertainly, while pooled log loss gets slightly
worse. The difficult 2021 forecast worsens. This fails the fixed evidence rule;
it does not establish that schedules are irrelevant or justify calling low PA
an injury. The test uses a 2015-onward training control because earlier local
schedule captures are absent, so comparing it directly with the original model
would mix schedule and training-history effects.

**The explicit modern-era flag accounts for a small part of the next-cohort
overshoot, not most of it.** Removing it from the outage-aware candidate changes
the 2022-origin estimate from 159.7 to 155.0 against 106 arrivals in 2023. Both
proper scores improve. Removing the flag from the original model alone does not
improve pooled scores, so this is an interaction with the outage treatment, not
evidence to delete all era information everywhere. At the 2021 origin there is
no mature modern training cohort, so removing the constant flag changes nothing.

Across six annual tests, the combined outage-aware/no-era model improves Brier
1.45% and log loss 2.12% versus the original rich model, with favorable paired
player-cluster intervals. However, the gain is concentrated in 2021; only three
of six origins improve and the three latest origins remain worse than the
original. The 2021 count remains 83.9 versus 157. This is a retained research
candidate, not a solved 2021 problem or a validated player-value replacement.

The sensible next gate is stronger-benchmark, Year 1–3 and delivered-value
testing of retained candidates, with later-year harm checked explicitly. A
shared-year opportunity model with partial pooling remains a possible separate
experiment, not a conclusion from this test. Do not keep adding calendar fixes
until the exposed 2021 answer is reproduced.

## The issue we actually found

The model receives an ordinary missing-history signal for a canceled league-wide
season. Those are different situations. All 3,250 never-debuted minor leaguers at
the 2021 snapshot have no 2020 annual record. In 2017/2018, ordinary missing prior
records were associated with only 4/1,061 and 2/1,149 next-year MLB appearances.
In 2021, that same signal covers a cohort with 157 next-year appearances.

Here **2021 means the forecast origin**: next-year arrivals happen in 2022.
The [2020 cancellation](https://www.milb.com/news/2020-minor-league-baseball-season-cancelled-x0977)
was known at the cutoff; its realized future impact was not.

We reproduced the mechanism in earlier data. Hiding the prior annual inputs at
2017 reduced predicted arrivals from 92.5 to 55.6 versus 95 observed. Fitting to
the available inputs instead restored 90.4. Both proper scores improved relative
to the masked original in all four fixed 2017/2018 missing-input scenarios.
This is evidence of a source-missingness problem, not proof of the full pandemic
effect or a simulation of lost physical development.

## What we tested and what happened

| Origin | Actual next-year arrivals | Original | Omit canceled block | Teach source-outage distinction |
|---|---:|---:|---:|---:|
| 2021 | 157 | 58.1 | 93.5 | 83.9 |
| 2022 | 106 | 112.5 | 176.2 | 159.7 |

The first fix removes the canceled annual block from both fit and query, leaving
the other correctly dated history intact. It improves 2021 Brier by 13.1% and log
loss by 15.3%, recovering about 36% of the absolute count shortfall. It does not
pretend that 2019 happened in 2020. But its two-year routing harms 2022 and fails
the predeclared acceptance rule.

The second fix teaches the model using artificially unavailable prior inputs,
explicit outage flags and unchanged total training weight. A duplicate-only
control isolates the effect of repeating rows. It improves 2021 Brier/log loss
by 11.0%/12.8%, but still overpredicts the next cohort. Across all six annual
tests it predicts 676.4 arrivals versus 677 observed, yet its Brier improvement
is uncertain and 2022 Brier worsens 10.2%. The almost-perfect pooled count is
not a valid acceptance argument. Its stronger-reference point scores improve,
but it fails the fixed pooled-interval and annual-harm gates.

Three-year arrival shows some improvement, but only two overlapping normal
origins exist. The regular-workload gap remains: at the 2021 origin, the original
expects 6.7 versus 17 observed; the two repairs expect 7.8 and 7.4. Regular means
450+ MLB PA in at least two of three following seasons, not WAR or star status.

## How to proceed without fitting to the answer

1. Keep the distinction between source unavailability and personal absence in
   the data contract. Do not replace an absent source with an invented stat line,
   interpret it as injury, or shift 2019 into a one-year lag. The research module
   now represents the distinction; no production forecast was replaced.
2. Diagnose the **time-period effect** separately from individual player history.
   At the 2022 annual cutoff, the only mature post-reorganization origin is 2021,
   and the model uses `reorganization_era`. Thus an unusual first cohort could be
   learned as a permanent modern-era change. This is a specific hypothesis, not
   a proven attribution. A next fixed test should partially pool shared year
   effects rather than let one modern cohort set a permanent probability uplift.
3. Build a cutoff-dated schedule/opportunity audit: how much of each player's
   shorter PA total reflects fewer available team games? Keep actual PA for
   sampling uncertainty and add opportunity fractions; do not universally scale
   every minor-league level by one number or call short PA an injury.
4. Require the next candidate to improve both the disrupted origin and ordinary
   years, then test delivered player value. Do not discard 2021, tune counts to
   157, select only its favorable result, or promote a correct pooled total.

MLB announced temporary 28-player rosters in March 2022, after this forecast's
cutoff. [Official announcement](https://www.mlb.com/news/mlb-rule-changes-for-2022).
That is a possible opportunity confound, not an identified explanation of the
remaining error or a permissible input to a year-end-2021 backtest. Later-dated
forecasts could use then-known changes under a separate cutoff contract.

## Evidence and verification

- [Canceled-block experiment](hitter-canceled-season-v1-result.md): 12 targeted
  fits, six historical stress fits and one mutation refit.
- [Source-outage training experiment](hitter-structural-missingness-v1-result.md):
  20 fits and one mutation refit, specified only after the first result.
- 23 targeted unit tests passed; both artifact packages verify. Original-model
  replays and future-label/predictor mutation checks show zero forecast change.
- Original frozen 2026 seal verified: 3,907 players and 31 files unchanged.
- No live means, player explorer, protected 2026 outcomes or delivered WAR changed.

These are sequential, exposed development tests. Stop after the two specified
mechanisms rather than continue tuning on the same 2021 outcome until it fits.
