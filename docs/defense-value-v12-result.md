# Defensive skill improves the forecast but position totals remain wrong

Adding the reviewed defensive histories reduces delivered defensive-run error
about 13% versus neutral defense. It also reduces expanded player-value error
about 2%, with batting and playing time unchanged. The same improvement appears
among actual defenders, not just the many non-arrivals. This is a useful MLB
defense layer, with real reversals and young-development failures, not full WAR
or proven lower-minors talent identification.

The [contract](defense-value-v12-integration-contract.md) fixes 12,432 forecasts
at the 2022–2024 origins. The three saved opportunity arms and three existing
skill recipes were crossed without fitting or tuning. Results are exposed
development evidence, not another untouched test. All forecasts are retained;
the complete-measurement accuracy subset has 12,114 rows, including 1,625 actual
defenders. Another 318 actual defenders, accounting for 372,452 fielding outs,
remain partial and are not quietly scored as neutral defense.

## The measured improvement

The primary comparison keeps the own-repertoire opportunity forecast fixed.
The history recipe directly shrinks actual MLB channel skill by its existing
prior exposure. Expanded value combines unchanged season-relative batting plus
replacement, exposure-based positional runs, and twelve distinct native defense
channels in common wins. It is not published FanGraphs WAR; baserunning, non-OF
arms and other WAR corrections remain outside this target.

| Measured complete subset | Neutral defense | History defense | History plus saved range calibration |
| --- | ---: | ---: | ---: |
| Defensive-run RMSE, equal-origin mean | 1.78285 | 1.55713 | 1.53500 |
| Expanded-value RMSE, common wins | 0.44184 | 0.43320 | 0.43259 |
| Defensive-run RMSE, actual defenders | 4.86435 | 4.24050 | 4.17430 |
| Expanded-value RMSE, actual defenders | 1.17985 | 1.15546 | 1.15291 |

The primary defensive-run difference is -0.22572 runs, nominal person-cluster
95% interval [-0.29121, -0.16257]. Expanded-value difference is -0.00864 wins
[-0.01314, -0.00419]. These intervals preserve a player's different origins
but do not account for historical model selection or common year shocks.

All twelve channel point errors improve among actual measured participants.
Framing falls 5.048 → 4.304 delivered runs; CF range 3.459 → 2.945; SS range
3.474 → 3.128; OF arms 1.435 → 1.375; receiving 1.261 → 1.203. That is not
separate proof of statistical significance for every channel. At actual future
opportunity, the corresponding quality diagnostics also improve; those counts
are diagnostic only and never supplied to a usable forecast.

The saved range calibration reduces defense error another 0.02213 runs
[-0.03753, -0.00729], but expanded value another 0.00061 wins
[-0.00219, +0.00098] is uncertain. It worsens 1B and 3B channel point errors
and has sparse/extrapolated profiles. Retain it as a qualified alternative,
not a universally better grade or an excuse for another age-model sweep.

The ratio and transition opportunity arms show the same broad skill benefit;
they are not independently selected replacement models. Removing framing from
both prediction and target as a full-ABS accounting scenario preserves the
history gain: expanded error 0.43375 → 0.42727. This does not forecast ABS
implementation or quantify the challenge system's effects.

## What the players confirm and contradict

[All 19 focal and 57 peer walks](defense-value-v12-player-review.md) are complete.
Bailey's positive framing/throwing history raises defense from neutral to
+12.505 against +31.473 actual. Raleigh's +7.421 estimate is close to +6.907
actual; adding it helps value but cannot repair his large batting/time miss.
Castellanos's negative RF/arm history and Olson's separate receiving credit are
baseball-sensible information, with genuine range and exposure misses.

Realmuto reverses from positive past catcher components to -10.250 total runs,
while the estimate is +6.854. Murphy's +7.819 estimate exceeds +0.598 actual
and makes an already optimistic playing-time/hitting forecast worse. Ruiz's
negative history is directionally useful but understates his later -22.323
runs by about twenty. Rafaela's young CF improvement and move away from SS are
missed; age calibration only partly helps. Kwan is the largest calibration harm.

Castellanos demonstrates why an accurate total alone is not sufficient: neutral
value was nearly exact because underestimated hitting cancelled omitted poor
defense. Adding useful defense worsens that total. Olson/Tucker show the reverse:
bad defensive estimates can improve a value forecast whose hitting is too low.
The paired skill result, separate delivery checks and player arithmetic—not one
total-value score—support keeping qualified MLB history.

For the 9,952 origin records with no measured channel history, all three skill
recipes are exactly identical. That group includes 323 actual future defenders.
Chourio and Wood receive the same unknown-quality mean despite different later
MLB defense. Small group-score differences elsewhere do not establish a minor
talent win. Missing history, sparse new MLB evidence and true young development
remain explicit gaps.

## Cohort totals expose a remaining position problem

Actual matched fielding exposure covers 99.47%, 99.87% and 99.97% of full MLB
outs in 2023–2025. That near-complete exposure coverage does not make every native
channel measured. Compare complete-subset value with the identical subset only:

| Target season | Neutral value forecast | History value forecast | Actual expanded value |
| --- | ---: | ---: | ---: |
| 2023 | 488.91 | 499.72 | 491.02 |
| 2024 | 515.60 | 525.91 | 458.24 |
| 2025 | 473.95 | 486.78 | 476.73 |

The 2024 overforecast is material. Do not force these incomplete common-win
totals to a full-MLB WAR number or confuse all-row forecast totals with an
actual sum excluding unmeasured players. Original batting, position and defense
accounting are retained separately.

Across the whole fixed population, actual positional runs are -505.78/-524.38/
-524.27; the own-repertoire forecast gives -345.60/-385.95/-380.08. This is
roughly +16.0/+13.8/+14.4 common wins too generous. It underprojects 1B use,
overprojects SS and understates DH starts by 694/521/561. DH alone explains
+75.03/+56.23/+60.59 runs of the positional surplus under the declared start
approximation. Better individual RMSE does not excuse this league-budget failure.

Skill totals also remain optimistic. On the complete subset, history predicts
+108.16/+103.06/+128.35 defensive runs against +47.37/+4.62/-48.24 actual.
Range calibration brings these to +14.23/+24.44/+39.26 but does not settle
the latest-year shortfall. Different components/positions cannot be balanced
by simply subtracting a global average and claiming better talent.

## What changes and what remains to finish

Retain a modular research layer that can turn qualified MLB skill and projected
positions/native opportunities into defensible component runs. Its units,
replacement treatment, no-history flags and missing target measurements are
explicit. All 12,432 identities and 149,184 channel records independently replay;
all nine combinations, score scopes and six person-cluster intervals reproduce.
No new fits, frozen forecasts, explorer changes or 2026 selection occurred.

Next resolve the physically constrained position/DH opportunity budget and
practical minor/sparse defensive talent evidence, using the reviewed source and
fixed skill layer. This new position-budget issue follows from completed value
accounting; it is not another opportunity algorithm/constant tournament. Preserve
individual roles and uncertainty, evaluate gains and harms, and do not use later
player assignments or injuries as preseason information. Current research export
and longer-horizon integration also remain before the defense goal is complete.
