# Minor infield play-share: locked development comparison

2026-10-05. This implements the bounded comparison in
[the nonbatting milestone](nonbatting-hitter-milestone-plan.md). No new 2026
outcomes, production changes, parameter sweep or algorithm search.

## Question and measurements

Does a coarse ground-ball play-share signal help predict next-calendar-year
MLB range? This is NOT a six-year value model, defensive scouting grade or OAA.
The archived outcome-complete ground-ball ledger contains 2016–19 and 2021–24.
It includes DSL league 130 as well as the US complexes and higher levels; it
does not certify every scheduled game. Use recorded lineup IDs at 2B/3B/SS.

Retain ordinary OUT, MULTI_OUT, 1B, 2B, 3B and ROE, without source conflicts or
bunts. Outs require a known first-handler position 1–9. Other labels and
unresolved events are counted but not fabricated as failed plays. A batter out
handled first at that position earns one credit; a double play earns ONE range
credit, not two. All three present infielders receive shared ground-ball exposure.
Through hits stay in that exposure. This does not blame an adjacent fielder for
a hit. The old-style proxy restricts exposure to first-handled balls at his
position and measures the same out indicator. It is a denominator contrast,
not an exact replay of the original richer-context model.

Expected rates: leave the defensive TEAM out of each season/level/league/position
reference. Compute handedness/park rates with 250 pseudo-opportunities at that
other-team league rate. No future MLB target, scorer coordinates or hit-location
difficulty predictor enters this adjustment. First-handler position supplies
outcome credit/legacy selection only. Unknown hands/parks remain explicit groups.
No pitcher-talent or fielder-starting-position adjustment is claimed.

Pool the last three calendar seasons at weights 1, .5, .25; a missing/canceled
season is not a zero performance season. Divide pooled excess credits by
pooled exposure + 600. Persist raw and adjusted numerator/denominator by position,
season, level and league. Equal exposure is not independent three-fielder evidence.

## Fixed population and future MLB outcomes

Starting rows: existing component panel origins 2016–24, excluding 2019 (short
2020 target) and 2020 (canceled minor input), with at least 25 weighted known
minor ground-ball exposures at 2B/3B/SS over the last three calendar years.
Include former MLB players and non-arrivals; report prior-MLB versus never-MLB
defense separately. The official 2004–25 position ledger identifies past/future
participation; absence of a native metric alone is NOT a zero.

Primary outcome: next-year delivered native MLB range runs. Zero only when
the certified official position ledger has no MLB defensive outs. Positive MLB
exposure with absent native range is unknown, retained but unscored. Position
changes remain in the target: these are delivered MLB range runs at actual
positions, not solely future infield talent. No batting/arm/DP/position credit.

Secondary quality outcome: range runs per 1,500 native defensive outs among
players with at least 150 native outs and at least half their official defensive
outs at 2B/3B/SS next year. This is a selected conditional diagnostic, NOT a
label for non-arrivals. Unknown quality stays null. Native annual metrics are
retrospectively published/revised measurements, not independent true talent.

## Fixed learning and comparisons

Five player-ID modulo folds, chronological training labels mature by the origin
and held-player exclusion across ALL training seasons. One fixed standardized
Ridge(alpha=100) per arm/outcome; no tuning. Arms: zero neutral; simple benchmark;
benchmark plus old-style proxy; benchmark plus complete-exposure proxy.

Benchmark: age/missing age, level indicators, historical batting workload,
MLB workload, observed position shares, log minor ground-ball exposure, exposure
shares at 2B/3B/SS and prior three-year native MLB range with defensive-outs
shrinkage (600 outs). Missing centered age terms are filled with zero alongside
the existing missing-age flag, not used to exclude players. Both challenger arms
add ONLY their three position rates.
Fit delivered runs unweighted. Fit conditional rate weighted by min(outs/1500,1).
No future role or future exposure is a predictor. Persist models and features.

Preflight each actual train/test subset before any fit: strict dates, uniqueness,
player separation, finite inputs, known labels, distinct-person counts by level,
age bands, position and prior MLB defense. Fewer than 30 distinct training
players or two target seasons: keep zero fallback, do not fit. Zero/sparse
profile support flags remain in predictions, not removed from headline scoring.
Twenty matched people is a warning threshold, not proof of adequacy.

## Scoring and decision

Primary recent origins 2022–24, equal-player delivered-range RMSE/MAE, matched
totals; additionally score each origin, level and prior-MLB group. Origin 2021
is separate stress evidence. Origin 2018 is an older sensitivity. Conditional
rate weighted-MSE and unweighted RMSE accompany, not replace, delivered scores.
Paired player-cluster bootstrap, 1,000 fixed-seed draws, is DEVELOPMENT evidence;
historical years were already examined and three recent years are not a large
independent-era validation sample.

No adoption unless primary loss improves against both simple and neutral,
the interval supports improvement, conditional evidence agrees, no major
supported level loses more than 5% MSE, and player review exposes no source/
logic defect. Lower-level support can block a general transport claim even if
pooled scores improve. Regardless of outcome, no automatic deployment.

Fixed case checks: Witt 677951/2021, Volpe 683011/2022, Peña 665161/2021,
Abrams 682928/2021, Lawlar 691783/2022, Mayer 691785/2024,
Downs 669023/2018 and Mateo 622761/2018. Keep ineligible/missing cases visible.
Add largest delivered improvement/harm, false high/low, ordinary case and
non-arrival. Select three peers by same origin/level, closest age and log
ground-ball exposure without looking at outcomes. Walk annual stats, raw versus
adjusted signal, support, all forecasts and actuals. Replay fits and show fixed-
parameter zero-signal sensitivities. Mandatory walkthrough before disposition.

Source/contract/code/test hashes must be sealed before fitting. Every output is
new/versioned; no overwrite of earlier results. Existing forecasts, completed
2026 evaluation and explorer remain byte-unchanged.
