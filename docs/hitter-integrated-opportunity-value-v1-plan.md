# Integrated hitter opportunity/value v1

Fixed 2026-09-25 before new integrated predictions or scores. This is a bounded
assembly test of already fitted historical forecasts, not another learner search.
Historical folds have already been exposed during development; this is not an
independent confirmation. The original frozen 2026 forecast remains unchanged.

## Primary question and routing

Does one cutoff-known routing rule improve Years 1–3 expected PA and delivered
component value? H uses repaired F participation times detailed D conditional PA
for never-debuted minor leaguers, the existing ensemble E for players with a
known prior MLB debut, and accepted B for remaining inactive/unknown players.
Prospect and prior-debut scopes must be disjoint. No player-specific exceptions.
E's probability is an average of classifiers while its PA includes a direct
regressor: do not infer a conditional PA model from E_PA/E_probability.

Keep five mandatory controls: L (original unmodified component release), B
(accepted opportunity with safe component connector), D (retained research
prospect PA, B elsewhere), E (universal ensemble PA with common connector), N
(same E PA with its independently archived batting product). H is the sole
candidate. No selecting a diagnostic after H fails.

## Safe value connection

For B/D/E/H use the fixed independent horizon-specific batting-rate anchor r:

    batting-plus-replacement = B_value + (new_PA - B_PA) * r / 600

This marginal correction preserves a direct forecast; it is NOT a claim that
talent equals direct value divided by PA, nor a jointly fitted value model.
N keeps the exact archived ensemble batting product as a stronger reference.
L keeps original archived batting and component totals, without any correction.

Recover all seven original component records and their earlier-fold choices:
position, steals, advancement, general defense, framing, throwing and blocking.
For every arm, a selected benchmark head uses its explicitly archived run rate
times that arm's expected PA/600; a neutral head stays zero; a selected direct
total stays unchanged. Never divide a direct component total by old expected PA.
Use the original 10 runs/win conversion after confirming its source formula.
Replay original component predictions exactly before changing exposures.

Holding a direct total unchanged is a controlled limitation, not a finished
opportunity-consistent component model. Report the frequency and size of direct
totals at tiny PA. Refit with nested opportunity inputs only in a separately
specified follow-up if needed. No outcome-selected ratio caps or attenuation.

## Evidence and endpoints

Reuse identical frozen rows: H1 origins 2016/17/18/21/22, H2 2016/17/21/22,
H3 2016/21/22; three-year totals 2016/21/22. Score expanded component wins only
on complete measured labels (three-year origins 2021/22); missing is not zero.
This target is not exact published WAR. Existing future-mutation checks and
training manifests establish inherited chronology; new assembly cannot fit or
read outcomes. Test outcome mutation invariance explicitly.

Equal-origin RMSE/MSE, MAE, signed bias and absolute cohort-total error. Paired
whole-player bootstrap, 2,000 draws, seed 417, 95% intervals. Show each origin,
2021 separately, and non-2021 (not synonymous with COVID-unaffected). Scores
include nonparticipants. Cumulative rows require exactly all three horizons.

Fixed profiles: all, prospects, upper/lower prospects, prior-debut players,
current MLB, prior MLB PA <100 / 100–399 / 400+, age <=25 brief-debut players
with >=400 total current PA and <100 MLB PA, minor returners, returners with
400+ MLB PA in either prior year, and ages <23 / 23–26 / 27–31 / 32+.
Profile checks need >=200 rows and >=10 future participants; insufficient
groups remain descriptive. Age/PA totals concern the starting population only,
not the entire future league or new entrants absent from the database.

## Separate decisions, fixed before scoring

Opportunity gate: H cumulative all-player PA MSE interval favors D and E,
improves at least 2/3 origins against each, cumulative MAE and cohort-total
absolute error do not worsen against D/E, and annual H PA MSE is no worse
than E. Every supported profile has <=5% annual PA-MSE harm versus D/E;
annual Brier/log loss have <=5% harm versus D/E overall. This can retain an
opportunity improvement without claiming a value improvement.

Value gate: H cumulative batting and expanded-value MSE intervals favor B/D/N;
cumulative expanded point MSE also improves L. Majority of available origins
improve against B/D/N. Cumulative MAE and aggregate absolute error do not
worsen against D/N for batting and expanded value. All supported profile
annual batting/expanded MSE has <=5% harm versus D/N. PA gate must also pass.
Only two complete expanded origins make any pass provisional development
evidence, never a six-year/control-value or MiLB-defense claim.

Preserve input/prediction/code hashes, independent recomposition and decision
checks, tests and plain-language report. Commit milestones without replacing
live forecasts or explorers. A failed connector is a useful completed test,
not authorization to tune the same exposed outcomes until it passes.
