# Universal Baseball Model development roadmap

Last updated: 2026-09-22

## The goal

Project future player value from evidence available at the forecast date. Build the
forecast from separate, testable baseball parts, then judge every part by whether it
improves a later player outcome. Keep the 2026 outcome season sealed until the regular
season is complete.

## Current model in plain language

### Hitters

The leading one-year hitter model combines five different forecasts of next-season
MLB batting value. They use the player's last three available seasons of age, level,
playing time, ordinary results, and detailed contact results. A separate five-model
forecast estimates MLB arrival and plate appearances. Projected position, baserunning,
and catcher defense are then added. General non-catcher defense remains neutral.

The selected batting ensemble has a forward-tested RMSE of 0.4321 WAR, compared with
0.4395 for the best single model. On players shared with the older 2025 system, RMSE
improved from 0.4904 to 0.4626. Position clearly helps the full value forecast.
Baserunning and catcher defense predict their own components better than neutral and
help total value modestly, but their whole-model gains are less certain.

A second, narrower gradient model projects next-season outcome rates rather than WAR.
It shows that detailed contact type and result, opponent quality, and park context all
contain real signal. Scikit-learn histogram boosting narrowly beat LightGBM and more
clearly beat XGBoost on that fixed 155-feature problem. This rate model is a useful
input and frozen 2026 challenger; it is not a replacement for the value ensemble.

### Pitchers

The clean-slate pitcher panel now covers 66,326 pitcher-seasons and has been tested in
six later-season folds. The best architecture estimates MLB arrival, then total value
conditional on pitching in MLB; separately multiplying arrival, workload, and rate is
worse. Ridge is the best original single engine at 0.3125 RMSE. A role-enhanced
chronology-safe multi-model average now reaches 0.3109, improving on the previous
0.3113 ensemble. Explicit starter/reliever movement, workload disruption, level
movement, and prior MLB exposure improve the three tested engines and the equal
ensemble. This is a strong development base, not a frozen forecast:
the present target values strikeouts, walks, hit batters, home runs, and workload but
still treats all other contact at league-average value.

A separate four-model pitcher workload ensemble now projects MLB arrival, conditional
batters faced, and zero-inclusive expected batters faced. It improves BF RMSE from
81.58 for carrying forward last year's MLB workload to 69.88 in six forward tests and
wins every season. Carry-forward retains a slightly better pooled MAE, so this is used
for expected opportunity and capacity accounting rather than as a universal workload
winner. Adding the role-transition block is effectively neutral for BF and is rejected
from this separate component.

### Reconciled player value

The first hitter-plus-pitcher development baseline now combines the accepted forecasts
at player level, including players who appear on both sides. Across 25,671 player-season
rows, RMSE improves from 0.39874 for the component-neutral comparison to 0.38807. The
player-clustered 95% interval for the 0.01067 improvement is entirely favorable. The
hitter additions supply nearly all of that gain; the pitcher role upgrade is still a
small, uncertain improvement inside this shorter common sample.

Combined 50/80/90% development ranges now cover 49.7%, 81.0%, and 91.1%. They use
strictly earlier residuals, forecast-time player stage, and fixed development cushions
that are now frozen for the protected test. This remains partial value because general
non-catcher defense and a validated pitcher contact-value layer are still absent.

## Evidence decisions

| Component | Current decision | Reason |
|---|---|---|
| Hitter batting value | Use five-model development ensemble | Beats the best single model in all six forward tests |
| Hitter workload | Use roster-aware five-model forecast for displayed opportunity | Improves arrival and PA accuracy; roster status does not improve batting skill |
| Detailed hitter contact | Keep | Adds clear signal beyond an age/level/workload tree |
| Park and opponent context | Keep in the event/rate layer; do not force a manual WAR correction | Improves fair event-rate prediction but has not consistently improved later WAR |
| Position value | Use | Improves partial-WAR RMSE in every tested season |
| Baserunning | Use provisionally | Strong component prediction; small, uncertain whole-model gain |
| Catcher defense | Use provisionally | Stronger component prediction and consistent but uncertain whole-model gain |
| General non-catcher defense | Neutral | Better exposure estimates did not make the current skill layer improve total value |
| Minor-league infield range | Keep as diagnostic; do not add to projected WAR | RE24 range persists in every later MiLB season, but its MLB hitter-value fallback worsens the old model and neutral defense still wins |
| Minor-league outfield range | Keep as diagnostic; do not add to projected WAR | Park-adjusted RE24 range persists in every later MiLB season, but outfield-only and combined MLB value bridges both lose to neutral general defense |
| Minor-league runner advancement | Keep as diagnostic; do not add to projected WAR | Improves the advancement component clearly, but full hitter RMSE is effectively flat and slightly worse |
| Outfield arm | Experimental only | Barely positive after heavy regression |
| Catcher throwing | Experimental only | Small positive caught-stealing signal; the separate attempt-deterrence model failed |
| Catcher steal deterrence | Reject current form | 2.78 million eligible PA starts produce no later-season improvement after separating catcher, pitcher, and runner effects |
| Catcher blocking | Reject current form | A broader 240,201-PA target fixes the old single-pitch restriction but still shrinks nearly to zero and is statistically indistinguishable from neutral next year |
| Catcher battery support | Retain as research evidence, not WAR | Walk effect is small and not decisive with new pitchers |
| Hitter-pitcher profile interactions | Retain as compact context, not standalone talent | Improves individual PA forecasts but mostly washes out in next-season player rates |
| Offseason injury history | Do not use yet | Small uncertain PA gain, worse arrival calibration and MAE |
| Explicit repeat-level penalty | Do not use | The base model already absorbs nearly all of the signal; overall result worsened |
| Learned ensemble weights | Do not use | Equal weights were more stable and more accurate |
| Pitcher target architecture | Use arrival chance x total value if active | Wins over direct and workload-times-rate targets for all four tested engines |
| Pitcher model engine | Use role-enhanced chronology-pruned ensemble for development | Best RMSE is 0.31092; the simpler equal ensemble also improves with favorable uncertainty |
| Pitcher role and workload transitions | Use in development ensemble | Improves ridge, CatBoost, LightGBM, and the equal ensemble |
| Pitcher expected workload | Use four-model base-feature ensemble for opportunity accounting | Improves BF RMSE by 11.70 in six forward tests; carry-forward has slightly better MAE |
| Role features in pitcher workload | Do not use | Ensemble BF RMSE changes by less than 0.001 and the clustered interval spans meaningful help and harm |
| Pitcher team-capacity scaling | Organization-context view only | Small workload and value gains have intervals spanning harm; forecast-time playing club is not verified future ownership |
| Pitcher uncertainty ranges | Use role-aware 80% and 90% development ranges | Earlier-fold residual calibration achieves 79.7% and 89.8% coverage overall and corrects severe starter undercoverage |
| Reconciled player-value baseline | Use for development | Accepted hitter and pitcher forecasts improve combined RMSE from 0.39874 to 0.38807 with a favorable clustered interval |
| Combined player-value ranges | Use development-cushioned 50/80/90% ranges | Coverage is 49.7%, 81.0%, and 91.1% across the two scored combined seasons |
| Exact pitcher opponent quality | Descriptive adjustment only | Actual prior hitter quality covers 95% of scored rows but is flat to worse in ridge, CatBoost, and LightGBM future-value tests |
| Raw pitcher hit-type detail | Do not use in the value model | Singles/doubles/triples slightly worsened three engines even when the target valued them |
| Context-neutral pitcher contact value | Descriptive adjustment only | 4.52 million park/defense/batter-adjusted BIP modestly help one full-result learner but fail the separate contact-value reconciliation against the leading pitcher model |
| High-minors pitch process | Keep for component skill; not whole value | Component forecasts improve, but whole-value gains are tiny, mixed, and uncertain |

## Statistical rule

A new component is promoted only when all of the following make sense:

1. The input existed at the historical forecast cutoff.
2. Training and tuning use only earlier seasons than the scored season.
3. The test includes players who produce zero MLB value, not only survivors.
4. It beats the current model and a simple baseball benchmark on the same target.
5. The gain is not confined to one season or one tiny subgroup.
6. Player-clustered uncertainty is favorable enough for the size and risk of the
   change.
7. The baseball mechanism is coherent and missing data is neutral, never favorable.

A descriptive adjustment may still be retained when it makes past events fairer, but
it does not become projection talent until it improves a future player target.

## Development order while 2026 remains sealed

1. **Pitcher information-block ablations.** Exact prior-only opponent quality is
   complete and rejected for future value; earlier park adjustment also failed its
   player gate. Keep both for fair past-event measurement. Test any remaining compact
   matchup signal only at the event level before another whole-value attempt.
2. **Event-level pitcher contact separation.** Complete for the current all-level
   source. The 4.52-million-event model separates contact shape, park, defense team,
   and batter context, but its residual does not improve the final separate contact
   reconciliation. Keep the defense-independent target as the base and wait for a new
   untouched season or materially better portable contact evidence.
3. **Pitcher opportunity and role integration.** Player-history integration is
   complete and promoted to the value ensemble. A separate expected-BF ensemble now
   strongly beats carry-forward RMSE and is exposed in the pitcher player table; role
   features do not improve this workload component. A simple parent-organization team
   cap has also been tested: it improves pooled workload and value slightly, but the
   uncertainty spans harm and results are mixed by season. Keep it as a separate
   organization-context view until historical rights and player-specific depth are
   available; do not change portable talent.
4. **General defense rebuild.** Infield and outfield RE24 conversion and full-value
   integration are complete. Both skills persist clearly in every later MiLB season,
   but neither the separate nor combined bridge improves 2025 MLB hitter value.
   General defense remains neutral; keep range and arm ratings as diagnostics until a
   new target or independent confirmation improves the whole forecast.
5. **Baserunning completion.** Complete. The minor-league RE24 prior improves the
   advancement component, but the chronology-safe bridge changes full hitter RMSE
   from 0.429098 to 0.429129. Retain it as a diagnostic and revisit only during final
   uncertainty-aware reconciliation.
6. **Catcher completion.** The all-level steal-deterrence and broader blocking tests
   are complete and rejected; neither prior catcher effect beats neutral reliably.
   Keep battery familiarity separate from portable catcher talent and plan explicitly
   for reduced framing value under ABS. The remaining provisional throwing and MLB
   framing estimates should enter final reconciliation with conservative uncertainty.
7. **Final reconciliation.** The first player-level hitter-plus-pitcher reconciliation
   is complete. It improves the component-neutral comparison clearly, preserves
   two-way contributions, and has development-calibrated combined ranges. A first
   pitcher team-capacity test is also complete and remains a separate context view
   because its value gain is uncertain and historical playing club is not future
   ownership. General non-catcher defense remains neutral, and the rejected contact,
   blocking, deterrence, park, opponent, and forced-capacity challengers remain outside
   portable projected WAR.

At each milestone, commit code, tests, and the decision report together. Negative
results remain in the repository so the same attractive dead end is not retested.
