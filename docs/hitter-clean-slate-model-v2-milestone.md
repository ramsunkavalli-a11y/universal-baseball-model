# Clean-slate hitter model: development baseline milestone

Status: **batting, roster-aware workload, position, baserunning, and catcher defense
selected for development; general defense remains neutral; 2026 results remain sealed**

## The result in plain baseball language

The model uses a hitter's last three available seasons of age, level, playing time,
ordinary batting results, and detailed contact-result history. It then combines five
independent estimates of his next-season MLB batting value. Some estimates predict
value directly; others first estimate whether he will play in MLB and how much he will
play. Their simple average is the new offensive-value baseline.

The core statistical forecast is **next-season MLB batting plus replacement value**.
It includes players who produce zero MLB value. A separate workload forecast now
scales the selected position and baserunning components. The resulting development
baseline is still partial WAR because general-position defense has not earned
inclusion. Catcher throwing, blocking, and framing are now included separately.

## A data error found and fixed

The first clean-slate panel accidentally required a hitter to appear in both the
traditional-stat feed and the contact feed. That excluded 6,395 player-seasons and
about 858,000 plate appearances.

The corrected panel starts from the traditional-stat population and adds contact data
when available. Missing contact coverage is explicitly marked; it is never treated as
real zero contact skill.

- 38,886 origin player-seasons
- 28,183 predictions in six forward tests
- 5,117,677 terminal contact events
- forecast origins 2015-2018 and 2021-2024
- no invented 2020 minor-league season
- old Short-Season A remains its own historical level

This correction made the test much harder and much more representative. It also
removed the misleading conclusion that NGBoost was a near-winner.

## What was compared

Nine model families received the same chronology-safe data and tests: ridge
regression, Extra Trees, scikit-learn histogram boosting, XGBoost, LightGBM,
CatBoost, Explainable Boosting Machine, GPBoost, and NGBoost.

Three ways to express the target were also compared:

1. predict next-season value directly;
2. predict MLB participation, then value if active;
3. predict MLB participation, playing time if active, and value rate if active.

No single engine or target structure won for every kind of player. Limited nested
tuning also failed to improve any finalist. Stable settings were better than chasing
the best setting in each historical fold.

## Selected model

The selected development model is an equal average of:

- direct LightGBM value;
- three-part LightGBM participation, playing-time, and rate value;
- two-part XGBoost participation and value;
- two-part Explainable Boosting Machine participation and value;
- two-part ridge participation and value.

CatBoost and a redundant two-part LightGBM estimate were removed. Their removal
improved pooled error, reduced duplication, and left a model in which every retained
member makes the result worse when removed.

| Forward-tested method | RMSE |
|---|---:|
| Always predict zero | 0.6697 |
| Predict the training-population mean | 0.6587 |
| Direct LightGBM | 0.4417 |
| Three-part LightGBM | 0.4393 |
| Best single engine: two-part LightGBM | 0.4395 |
| Seven-model average | 0.4329 |
| Selected five-model average | **0.4321** |

The five-model average beats the best single engine by 0.0074 RMSE. A player-level
95% resampling range for that improvement is 0.0047 to 0.0103. It beats the best
single engine in all six tested forecast seasons.

## Like-for-like comparison with the older system

The older March 27, 2025 forecast was reconstructed on the same
batting-plus-replacement basis by removing its baserunning, defense, and positional
runs. On 3,744 players shared by both forecast universes:

| 2025 forecast | RMSE | MAE |
|---|---:|---:|
| Older system | 0.4904 | 0.1664 |
| New candidate | **0.4626** | **0.1451** |

The 0.0278 RMSE improvement has a player-level 95% resampling range of 0.0093 to
0.0475. The new model is substantially better for current MLB hitters, modestly better
for upper-minors hitters, and trivially worse for lower-minors hitters. This is one
already-exposed season, but it is the clean common-target benchmark that the earlier
contact-only work could not provide.

## Why the weights stay equal

Equal weights are no longer just a convenient choice. Three forward-only alternatives
were tested using only earlier out-of-fold results:

| Weighting rule, common five-fold sample | RMSE |
|---|---:|
| Equal weights | **0.43730** |
| Prior inverse-error weights | 0.43735 |
| Prior globally optimized convex weights | 0.43852 |
| Prior stage-specific convex weights | 0.43904 |

The learned weights either tied or worsened the forecast. Stage-specific weights were
especially unstable. Equal weights remain locked until untouched evidence says
otherwise.

## Park and opponent adjustment

Parks and opponent quality matter when describing what happened. The tested context
package therefore summarizes park-adjusted event results, opposing-pitcher quality,
pitcher handedness exposure, coverage, and reliability using only information known at
the historical cutoff.

Those fields did **not** earn a place in the base forecast yet:

- full three-lag context: RMSE 0.452768 without it and 0.452721 with it;
- current-season context only: RMSE 0.452768 without it and 0.452578 with it;
- both versions helped 2024 but hurt 2023;
- both player-level uncertainty ranges include meaningful improvement and harm.

Coverage is the main constraint. The complete adjusted package exists only for
2021-2024. Earlier rows are honestly missing, and the first modern training fold has
only 2021-2022 examples from which to learn. Keep building the park component, but do
not force this thin version into forecasts.

## Checks for hidden failure modes

The aggregate win is not produced by thousands of easy low-minors zeros.

- Players who actually reached MLB account for 97.0% of the selected model's squared
  error, and the ensemble improves their RMSE from 1.0807 to 1.0651.
- Current MLB players account for 89.4% of total squared error; their RMSE improves
  from 0.9873 to 0.9704.
- Upper-minors RMSE improves from 0.2680 to 0.2638.
- Lower-minors RMSE is slightly worse, 0.0519 to 0.0522.
- Age-20-and-under RMSE is also slightly worse, 0.0895 to 0.0912. These two groups
  remain explicit watch items for 2026 confirmation.
- For each season's predicted top 25 hitters, the candidate captures 79.0% of the WAR
  produced by the hindsight-perfect top 25, versus 76.7% for the best single model.
- The highest predicted decile averages 1.203 WAR and actually produces 1.194 WAR,
  so the top forecast group is well calibrated even though individual breakout stars
  remain difficult.

Sixty-one percent of predictions are slightly negative, mostly around zero. Flooring
them at zero improves MAE but worsens RMSE and creates upward bias. Negative expected
value is also baseball-possible for an active below-replacement hitter, so the model
keeps the unaltered estimates.

## Uncertainty ranges

Ranges use only residuals from earlier forward tests and are calibrated separately for
current MLB, upper-minors, and lower-minors players.

| Intended range | Observed coverage |
|---|---:|
| 50% | 52.0% |
| 80% | 82.5% |
| 90% | 91.5% |

Those original ranges cover batting plus replacement only. A second calibration now
uses the combined batting, position, baserunning, and catcher residual directly, so it
does not assume the component errors are independent. The immediately preceding
comparable season calibrated better than pooling the short modern history.

Across the two scoreable modern folds, the selected full-stack ranges covered 47.9%,
78.5%, and 88.7% at nominal 50%, 80%, and 90% levels. On the most recent 2025 fold,
coverage was 52.2%, 81.5%, and 90.0%. Current-MLB coverage was close to nominal;
upper-minors ranges remained too narrow in the earlier fold and are a 2026 watch item.

## Playing time

The new workload model averages five estimates: direct LightGBM playing time and
four participation-then-playing-time models using LightGBM, XGBoost, EBM, and ridge.
It predicts expected MLB plate appearances, including zero for players who never
reach MLB in the target season.

| Workload forecast | Next-season PA RMSE |
|---|---:|
| Carry forward current MLB PA | 71.37 |
| Best single workload model | 61.59 |
| Five-model workload average | **61.16** |

The average improves the best member by 0.43 PA RMSE, with a player-level 95% range
of 0.19 to 0.68 PA. Every member contributes when removed one at a time.

Certified October 15 40-man membership was then added only as opportunity evidence.
Across all six forward tests, PA RMSE improved from 61.16 to **60.82**, Brier score
improved from 0.0500 to 0.0485, and log loss improved from 0.1653 to 0.1609. The PA
improvement range was 0.17 to 0.54 PA. It improved all six forecast seasons.

The same information did not meaningfully improve batting value or partial WAR.
Therefore the user-facing workload and arrival forecast is roster-aware, but batting
skill stays roster-blind. Position and baserunning continue to use the original
roster-blind workload inside the value calculation because rescaling them with the
roster-aware PA forecast was essentially neutral and trivially worse in pooled RMSE.

## Position and baserunning

Position value uses the previously confirmed role-transition model and the new
expected-PA forecast. Across target seasons 2022-2025, it lowered partial-WAR RMSE
from 0.4437 to **0.4307**. The pooled improvement was 0.0130 RMSE, with a
player-level 95% range of 0.0041 to 0.0214. Position improved the forecast in all four
seasons.

Baserunning reuses the previously selected three-part public model: steal-attempt
propensity, steal success, and non-steal advancement. It scales those rates by the
expected-PA forecast.

| Pooled 2022-2025 partial-value forecast | RMSE |
|---|---:|
| Batting only | 0.4437 |
| Batting + transition position | 0.4307 |
| Add steals only | 0.4299 |
| Add non-steal advancement only | 0.4293 |
| Add both baserunning channels | **0.4291** |

The full baserunning addition improves pooled RMSE by 0.0016 beyond position, but its
95% range crosses zero. It helped in 2023 and 2025 and was essentially flat in 2022
and 2024. Its own component RMSE falls clearly from 0.0745 WAR under the neutral zero
assumption to 0.0592 WAR; both steals and non-steal advancement beat their neutral
baselines. It is retained as a real additive baseball component, with the small and
uncertain whole-stack gain stated explicitly.

## General defense did not earn inclusion

The first defense test used the frozen prior-year-MLB-outs exposure rule. It assigned
neutral defense to 2,362 of 3,929 players, including every player without prior MLB
defensive outs, and worsened total-value RMSE from 0.4517 to 0.4526.

That exposure weakness was then rebuilt rather than accepted. A chronology-safe
four-model average uses the new workload forecast plus prior fielding history to
predict next-season general-position defensive outs. On the 2025 development fold it
lowered exposure RMSE from 449 outs for the best simple baseline to 375; the paired
95% improvement range is 55 to 93 outs. It also improved entrants, and affiliated
position shares supplied roles for players without prior MLB innings.

The stronger bridge still did not make general defense valuable enough. Its component
RMSE improved slightly from 0.1286 WAR under neutral defense to 0.1262, but adding it
to total value worsened RMSE from 0.4517 to 0.4522. The uncertainty range spans both
help and harm. The remaining problem is therefore not primarily playing-time exposure:
the current public general-defense skill and run-value layer does not add stable enough
whole-player information. General defense stays out of the base model.

## Catcher defense earns provisional inclusion

Catcher defense was rebuilt as a separate component rather than routed through the
failed general-defense layer. The model carries forward public throwing, blocking,
and framing skill, learns only a shrink slope from earlier season-to-season
transitions, forecasts each native opportunity from expected MLB PA, and uses the
already-audited public run conversions.

Across target seasons 2023-2025:

| Same full target | RMSE |
|---|---:|
| Catcher defense neutral | 0.4515 |
| Add direct catcher model | **0.4488** |

The model improved all three seasons. Its whole-player RMSE gain was 0.0028; the 95%
range was -0.0064 to +0.0006, so the aggregate gain is favorable but not definitive.
The component itself is much clearer: catcher-defense RMSE improved from 0.0976 WAR
to 0.0861, with a fully favorable improvement range. Framing supplied most of the
signal; throwing and blocking were directionally helpful but individually uncertain.

This mirrors the baserunning decision: the component predicts its own future value,
has sound additive baseball meaning, and improves the whole stack consistently, so it
is retained for development while 2026 remains the final confirmation.

## What this does not prove

- It is not yet whole-player WAR because general-position defense is unresolved.
- The 2025 play-by-play snapshot is incomplete and cannot safely support a final 2026
  forecast fit.
- The older multi-year career reports are still not comparable, but the older 2025
  one-year forecast has now been reconstructed and scored on a common target above.
- Historical results were used for development. Only the sealed 2026 season can
  provide final confirmation.

## Decision and next build

Lock the five-model batting average, roster-aware standalone workload forecast,
confirmed position transition, confirmed baserunning model, and direct public catcher
model as the current hitter development baseline. Keep batting skill roster-blind and
do not add the current park/opponent fields, chronology-learned ensemble weights, or
the present general-defense layer. A chronology-safe 2015-2024 offseason injury
history was also tested after this selection: it produced only a small, uncertain PA
RMSE gain while worsening MAE and arrival-probability scores, so it is not selected.
Combined component uncertainty is now implemented using whole-stack residuals rather
than independent component ranges. The next priority is completing the 2025 source
snapshot, then fitting and freezing the final sealed 2026 forecast.
