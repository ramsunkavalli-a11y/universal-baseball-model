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
| Exact pitcher opponent quality | Descriptive adjustment only | Actual prior hitter quality covers 95% of scored rows but is flat to worse in ridge, CatBoost, and LightGBM future-value tests |
| Raw pitcher hit-type detail | Do not use in the value model | Singles/doubles/triples slightly worsened three engines even when the target valued them |
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
2. **Event-level pitcher contact separation.** Keep the defense-independent target as
   the base. Revisit contact only after separating pitcher, park, opponent, and team
   defense effects; raw season-total hit types did not improve the fuller value target.
3. **Pitcher opportunity and role integration.** Player-history integration is
   complete and promoted to the development ensemble. Next add organization depth and
   realistic team innings limits without using future role as an input.
4. **General defense rebuild.** Infield RE24 conversion and full-value integration are
   complete: the component persists clearly but does not improve 2025 MLB hitter
   value. General defense remains neutral. Add outfield range or throwing only after
   each supplies stronger component evidence than the current weak arm result.
5. **Baserunning completion.** Complete. The minor-league RE24 prior improves the
   advancement component, but the chronology-safe bridge changes full hitter RMSE
   from 0.429098 to 0.429129. Retain it as a diagnostic and revisit only during final
   uncertainty-aware reconciliation.
6. **Catcher completion.** The all-level steal-deterrence and broader blocking tests
   are complete and rejected; neither prior catcher effect beats neutral reliably.
   Keep battery familiarity separate from portable catcher talent and plan explicitly
   for reduced framing value under ABS. The remaining provisional throwing and MLB
   framing estimates should enter final reconciliation with conservative uncertainty.
7. **Final reconciliation.** Combine batting, pitching, fielding, baserunning, role,
   and opportunity; constrain team totals; calibrate uncertainty; and compare the
   resulting player values with the strongest component-neutral alternatives.

At each milestone, commit code, tests, and the decision report together. Negative
results remain in the repository so the same attractive dead end is not retested.
