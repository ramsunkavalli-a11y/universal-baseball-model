# Late season opportunity helps modestly but does not finish the hitter model

2026-10-03. Separating recent MLB opportunity from annual totals gives a small
gain. Keep the verified timing source and candidate as research, not a replacement
for the working model or frozen forecast. All eighteen actual player reviews are
complete. The public playing-time gap and prospect-readiness problems remain.

## Source and exact comparison

Fifteen official seasons now have final and preceding nonoverlapping thirty-day
MLB PA windows. Every annual PA total matches the prior player-season source
exactly. The compact old schedule duplicated/rescheduled games and could label
postponements broadly Final; new captures use official dates, actual completed
F/O states and deduplicated identities. Window gamesPlayed does not consistently
match old annual team-summed games, including some regular players. The exact
cause is unresolved; all proposed new games/PA-per-appearance inputs were
withheld BEFORE fits, not explained away as trades or silently interchanged.

The [fixed contract and source amendment](practical-hitter-late-role-v46-contract.md)
adds ten PA-only timing inputs to the 239-input games model: current/prior-year
availability, late/preceding PA and each divided by scheduled league-average
team games. Same 35 chronological whole-player cells, 30,506 forecast identities,
settings, batting head and availability rules. No tuning, total rescaling,
new college information or hindsight medical labels. All old columns are exact
and all 35 heads replay. Protected 2026 remains closed. All 218 unverified roster-
only rows remain in headline scoring, with supported diagnostics separately.

## Matched scores

| Population | Forecast | PA RMSE | PA MAE | Contribution RMSE |
|---|---|---:|---:|---:|
| All, equal-origin scores | Games control | 61.149 | 21.292 | .43947 |
| All | Timing candidate | 60.944 | 21.269 | .43887 |
| All | Working V33b plus retirement | 61.543 | 21.290 | .44097 |
| Same 1,789 public matches | Games control | 143.191 | 111.320 | 1.01598 |
| Same public matches | Timing candidate | 142.817 | 111.049 | 1.01642 |
| Same public matches | Working model | 143.965 | 110.563 | 1.01787 |
| Same public matches | Steamer archive | 135.019 | 92.399 | 1.04348* |

Contribution is batting plus replacement, not full WAR. *Public conversion has a
run-environment mismatch; this score does not establish better batting talent.
Archives may contain later winter job/health information than our December
origin. These are development results, not untouched confirmation.

Timing-versus-games PA MSE is -24.96, nominal player-paired 95% interval
[-55.20,+7.18]; contribution MSE -.000525 [-.001449,+.000406]. The incremental
gain is uncertain. Versus working V33b, the combined games/timing/source extension
improves PA MSE -73.28 [-129.27,-19.02] and contribution -.001850
[-.003686,-.000094]. Do not attribute this entire combined contrast to timing.
Public intervals include no gain. Public PA MAE is slightly worse than working
and roughly 20% above Steamer, still failing the declared 15% tolerance.

## Baseball and cohort checks

PA RMSE improves in six of seven origins, but 2021 worsens 60.259 to 61.366 and
contribution .43014 to .43181. Brief debuts improve 132.356 to 130.685; brief
MLB players with at least 50 late PA improve 177.275 to 169.981, with little MAE
change. Never-debut upper minors worsen 57.089 to 57.480 versus games.

Upper-minor PA falls 100,089 to 97,619 against 102,951 actual. Lower-minor PA
rises 9,843 to 10,271 against 6,072, contribution 26.50 to 27.74 against 13.14.
A tiny lower-minor RMSE gain does not make those totals reasonable. The 2023
origin excess grows to 192,487 PA against 182,194; the 2024 total improves to
184,499 against 182,880. Two new late-profile groups are unseen and 88 rows have
fewer than twenty matching distinct training people. They stay in scoring;
broader legacy profile qualifications remain too.

The [eighteen player reviews](../reports/model-evidence/practical-hitter-late-role-v46/player-walkthrough.md)
show actual counts, timing inputs, exact tree paths, training support, arithmetic
and origin-selected successful AND unsuccessful comparisons. The separate
[nine source reviews](../reports/model-evidence/practical-hitter-late-role-v46/source-walkthrough.md)
were completed before fits, without claiming a predictive win.

- Swanson's 51 preceding/94 late PA support more opportunity: 227 to 274 expected
  PA against 551. But contribution gets worse because his actual offense is
  poorer than the unchanged batting estimate.
- Judge after 2023 has 111 late PA despite 458 annual PA. Expected next-year PA
  rises 532 to 569 against 704; the talent head still misses the huge season.
- Upton's 97 preceding/50 late PA reduce an overforecast 373 to 271 against zero.
  Morrison's 44/25 reduce 277 to 212 against 601: the same plausible declining-
  usage signal can miss a successful return.
- Kurtz/Volpe have no MLB timing yet and get worse. Bellinger's 465 AA PA with
  23 HR remain in the data, yet only ten expected MLB PA precede his 548-PA debut.
- Perez's PA is almost exact while contribution worsens. Fraley's contribution
  is almost exact while PA worsens: offsetting errors are not validation.

Tree paths are descriptive, not causal: terms inside a refit are not an additive
decomposition of the old-to-new change. Later absences and breakouts describe
realized misses; they do not enter the forecast inputs.

## Decision and next information need

Retain the source and this modestly stronger broad-population point candidate
as research. Working V33b plus reversible retirement stays unchanged. Public,
2021 and lower-minor checks do not support a confident replacement or a full
player-value claim. Do not waive the public MAE tolerance to call the goal done.

Next inspect dated prospect-readiness/scouting and finite-absence/job context,
not another objective/library sweep on annual counts. Existing public prospect
ranking audits are current snapshots, not a verified historical training panel.
Historical grades could separate elite fast movers from ordinary non-arrivals,
but must be source-checked; current ranks or hindsight names cannot supply those
labels. No new college collection is planned. This is an input need, not proof
rankings must help. Keep calendar offense, full WAR and career trade value distinct.

A new local team-filtered research comparison shows working, games and timing
forecasts with actual historical outcomes and reviewed cases. It does not change
the frozen/deployed 2026 forecast. The practical goal remains incomplete.

Open the [research explorer](http://127.0.0.1:8785/) while its local server is
running. The selected year is the information cutoff: 2024 forecasts 2025, not
2026. The organization filter selects the historical cohort; actual MLB results
follow those players anywhere, not only with their listed organization. The
Giants current-MLB working-model view contains 25 players and predicts 5,546 PA
against 5,553 actual. These are rounded display totals, not a future team budget.
The browser check also confirmed Judge's underlying timing windows and all three
forecast comparisons. Twelve focused tests and all 35 head replays passed;
neither is a claim that the full model or entire test suite passes.
