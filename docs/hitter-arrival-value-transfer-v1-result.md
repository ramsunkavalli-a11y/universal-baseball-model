# Better arrival forecasts help playing time; value integration is not ready

2026-09-23. Completed the [fixed Years 1–3 transfer test](hitter-arrival-value-transfer-v1-plan.md).
The corrected-source arrival candidate is still useful. Its extra signal
improves playing-time prediction in every matched annual fold. But substituting
its probabilities into the old workload/value system does **not** pass the full
delivery rules. No production forecast or explorer changed; no 2026 outcomes
were used. Keep the source repairs, reject this automatic value-model replacement.

## What was held fixed

The test predicts MLB participation in each particular future season, not
arrival at any point within three years. Existing conditional PA and conditional
batting-rate heads remain unchanged. Primary R/F substitutions affect only
cutoff-known, never-debuted minor leaguers; established MLB players and returners
remain unchanged. A universal application is a diagnostic, not a fallback winner.

- B: accepted C2 opportunity/value baseline.
- R: original detailed probabilities substituted into B.
- F: corrected-source detailed probabilities substituted into B (primary).
- E: existing harmonized ensemble benchmark, not newly tuned.

Expected PA is new participation probability times inherited conditional PA.
Batting value retains the old direct forecast plus the independently estimated
value of the PA change. It is not obtained by dividing old value by old PA.
This is one explicit integration test, not a test of every joint value model.

## Playing time improves consistently, but the ensemble remains slightly better

Prospect PA RMSE, including players with zero future MLB PA; lower is better:

| Horizon | Accepted B | Original-detail R | Corrected F | Ensemble E |
|---|---:|---:|---:|---:|
| Year 1 | 32.79 | 30.55 | 29.89 | 29.63 |
| Year 2 | 57.69 | 53.35 | 52.26 | 51.92 |
| Year 3 | 74.76 | 68.32 | 67.62 | 67.08 |
| Three-year total | 144.96 | 130.32 | 127.03 | 126.18 |

F improves PA squared error versus both B and R in all 5/4/3 eligible annual
origins, respectively, with favorable paired player-history intervals at each
horizon. Three-year PA RMSE improves 12.4% versus B and 2.5% versus R. The paired
cumulative MSE change versus R is -846.8, interval [-1252.0, -511.3]; versus B
it is -4878.4, interval [-5900.1, -3886.7]. These are MSE, not RMSE intervals.

E has lower point-estimate PA RMSE in every horizon. The F–E paired PA intervals
include zero, so this is not proof E is decisively superior, but F does not meet
the declared requirement to beat it. Do not report the gain against B as a gain
over the project's strongest playing-time benchmark.

Prospects' average predicted three-year PA rises from 19.8 to 23.6 against
31.1 actually earned (equal weight per origin). That is useful, but still about
24% too low. The 2021-origin cohort remains especially difficult: 20.3 predicted
versus 37.4 actual PA per starting prospect. These are averages over everyone,
not workloads conditional on reaching MLB. Totals cover the starting population,
not future entrants absent from that year's database or the entire future league.

## Batting value: improvement against the delivered baseline, not from the repair itself

The target here is batting-plus-replacement wins, **not whole WAR**:

| Horizon | Accepted B | Original-detail R | Corrected F | Ensemble E |
|---|---:|---:|---:|---:|
| Year 1 | 0.16015 | 0.15995 | 0.16018 | 0.16198 |
| Year 2 | 0.27260 | 0.26671 | 0.26619 | 0.26318 |
| Year 3 | 0.34871 | 0.33898 | 0.33930 | 0.33745 |
| Three-year total | 0.59038 | 0.57201 | 0.57211 | 0.56939 |

F improves three-year RMSE about 3.1% versus B, with a favorable cumulative MSE
interval [-0.03665, -0.00658]. But R already produces essentially that gain.
F versus R is +0.000116 MSE, interval [-0.00566, +0.00482]: the source repair's
additional batting-value benefit is **not established**. Next-year batting-value
accuracy is essentially unchanged. Three-year value MAE worsens from 0.1774 to
0.1844, and aggregate absolute value error worsens from 97.0 to 100.5 wins across
the starting prospect cohorts. An improved average squared error is not the
same as improved calibration or uniformly better player valuation.

The 2022-origin cohort illustrates the tension: F gets total PA closer, while
forecast batting value per prospect rises to 0.137 versus 0.056 observed.
The probability, conditional workload and conditional performance pieces need
to work together; better participation probabilities cannot guarantee that.

## Expanded value exposes an unsafe propagation rule

The existing expanded target adds position, running, general defense and catcher
components. It is a project-defined component-wins target, not directly comparable
to published fWAR/bWAR. Only 2021 and 2022 have complete three-year component
labels. Missing labels were not zero-filled.

Across all players, cumulative expanded-value RMSE improves slightly from
1.2749 to 1.2650 (paired MSE interval [-0.05185, -0.00335]). Among prospects it
improves 0.7150 to 0.6920. But next-year prospect error worsens 0.1729 to 0.1839;
lower-minors prospect error worsens sharply, **0.0726 to 0.1008**, failing the
predeclared harm limit. These overlapping two-origin cumulative results cannot
override the annual failure.

The mechanism is visible in the experimental connector: some nonbatting heads
predict annual totals directly. Those totals are not necessarily proportional
to the old expected PA. Multiplying them by new PA / old PA can amplify small
totals into implausible forecasts when old PA is near zero.

- Maikel Garcia, 2021 origin: expected next-year PA rises 0.42→49.91. Scaling the
  old +0.0248 nonbatting wins by that approximately 120-fold ratio makes the
  experimental expanded forecast **3.09 wins for roughly 50 PA**.
- Edward Olivares, 2018 origin: 0.40→39.46 PA, with a negative old nonbatting
  total, becomes **-3.09 wins for roughly 39 PA**.

These are outputs of this **rejected experiment**, not forecasts now displayed
in the explorer. No player-specific overrides or fitted ratio caps were added.
The predeclared diagnostic that holds nonbatting totals fixed largely removes
this acute Year-1 problem (lower-minors RMSE 0.0732), but is not a selected
replacement or a complete way to propagate changing opportunity.

## A second limitation: an arrival forecast cannot repair a fixed workload head

For Peña at the 2021 cutoff, F predicts 64.8% participation in 2022, but the
inherited conditional workload is only 117.7 PA. Their product is 76.3 expected
PA versus 558 realized. That does not mean a correct forecast should have
predicted the realized number with certainty; it shows which unchanged model
piece limits the new probability's effect.

Across future participants, inherited conditional PA underpredicts average
workload in 10 of the 12 horizon/origin cells, although the gap varies materially.
Among the 22 prospect snapshots that later earned >=450 PA in Year 1, it averages
117.7 PA versus 527.5 realized. These are explicitly **outcome-selected diagnostic
groups**, not adoption criteria or justification for boosting all prospects.
The old archived research workload head differs from the delivered one; neither
was silently swapped into the primary candidate.

## Decision and next bounded experiment

The transfer fails its full gates: cumulative value improvement beyond R,
cumulative value MAE, a majority of cumulative value origins versus R, the
ensemble PA comparison, aggregate value totals, and annual expanded-value
safety. Ordinary annual PA/batting-value and probability guards pass. The
universal-F diagnostic improves some pooled errors but is not selected after
the primary fails.

Retain F as a better research participation model and preserve the repaired
source foundation. **Do not deploy this value propagation.** Next:

1. Refit conditional workload using the same corrected, cutoff-safe evidence;
   compare the old conditional head, a corrected-source head, and the existing
   ensemble on the same rows. Distinguish brief MLB opportunities from sustained
   roles without selecting players by future success at forecast time.
2. Connect nonbatting value through explicit, supported per-opportunity rates
   and appropriate opportunities (innings/position/catcher work), or refit
   direct future component totals with corrected opportunity inputs. Do not
   divide arbitrary direct totals by tiny old expected PA and call it talent.
3. Keep a single predeclared integration and mandatory ensemble/value benchmarks.
   Test annual and cumulative error, totals and vulnerable lower-minors groups.
   Do not tune a global boost, ratio cap or mixture to this exposed test.

These are follow-up requirements, not changes already fitted. Years 4–6,
service/control accounting and trade-value distributions remain outside this test.

## Verification and artifacts

16 new annual-activity fits, 8 reused exact Year-1 prediction sets, two zero-
difference future-data replays, and exact replay of two archived conditional
heads. 52,181 player-year/horizon forecasts. 34 focused tests pass. Source and
target identity, player weights, cutoff maturity, non-prospect preservation and
score reconstruction verify. The source-repair archive and original 31-file
2026 forecast seal still verify unchanged.

All historical results are exposed development evidence. Whole-player intervals
do not capture every common season shock. No probability recalibration, new
model search, complete-WAR claim or live forecast update was made.

Archive: `model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23/`.
The post-test diagnosis is descriptive only and made no new forecasts.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_arrival_value_transfer_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_arrival_value_transfer_v1.py
.venv/Scripts/python.exe -X utf8 scripts/diagnose_hitter_arrival_value_transfer_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_arrival_value_transfer_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_full_2026_freeze.py
```
