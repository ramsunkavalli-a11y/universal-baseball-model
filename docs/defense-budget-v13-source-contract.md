# Verify the fielding and designated hitter job inventory

2026-10-07. The reviewed defense integration gives too much positional credit
across the forecast population. Before testing a constrained allocation, verify
what the position source actually counts. This checkpoint repairs measurement
and identifies forecast-design problems; it cannot establish an accuracy gain.

## Scope and fixed evidence

Keep the existing position source and all 12,432 forecasts unchanged. Publish a
separate reviewed MLB designated-hitter start view for 2022–2025. Eight-position
fielding outs, batting, defensive quality, native opportunities, cohort identities,
and the frozen forecast/explorer remain unchanged. No 2026 results or new fits.

Inventory every MLB season in the existing 2004–2025 source. A single fielding
slot has the same total outs and starts as every other slot. DH starts are a
different unit, not defensive innings. Previous-season inventory is cutoff-known;
next-season inventory is only a source/coverage diagnostic, never a budget input.
Historical MLB DH rules differ: the two leagues were not both using a DH before
2022 except in 2020. A short season is not normalized into a full season silently.

The 2022 rule allows a starting pitcher to occupy the DH role too. The preliminary
inventory's DH shortfalls in 2022, 2023 and 2025 equal Ohtani's pitching starts.
That equality is a hypothesis, not permission to add all pitching appearances.
See [MLB's 2022 rules](https://img.mlbstatic.com/mlb-images/image/upload/mlb/hhvryxqioipb87os1puw.pdf),
Rule 5.11 and the rule-change summary.

## Certify dual starts rather than make a player override

Select all source player-seasons in 2022–2025 with positive pitching starts and
any DH appearance. Fetch their official regular-season pitching game logs and
boxscores for every pitching start, retaining exact raw responses and hashes.
This includes negative controls with a DH appearance but no DH start. Do not
limit the rule to Ohtani or infer dual starts from a player's reputation.

Require exactly one boxscore identity, pitching `gamesStarted=1`, an original
batting-order slot ending in `00`, and both pitcher and DH codes in `allPositions`.
Record missing/conflicting evidence as unresolved. Reconcile the number of
captured pitching starts to the annual inventory. Add certified dual starts only
in an additive reviewed DH ledger, with every contributing game ID. Reconcile
the corrected league DH total to fielding starts; do not manufacture a residual
correction if it still differs. Nonstarting DH appearances must not become starts.

## Audit the fixed forecasts before selecting a correction

For each 2022–2024 origin, show full origin-known job totals, captured forecast
population coverage, saved expected fielding/DH totals and unknown-role exposure.
Compare actual matched/remainder totals separately as diagnostics. Inspect all
fifteen saved repertoire training cells: list target years, distinct people,
PA, fielding outs and DH starts by DH-rule regime. Replay each selected prior's
numerators and the player-level current-history/prior decomposition. Quantify
how much DH exposure is predicted from own history versus pooled history.

Do not conclude that mixed-rule training caused all the underprediction merely
because it is present. Its effect on a new allocation must be tested. Do not
double historical AL DH rates to represent the new NL jobs, force an incomplete
cohort to occupy the whole league, or assign a new defensive role to fill a gap.

## Player review and decision

Walk Ohtani's three forecast origins, the negative dual-role controls, and the
fixed ordinary DH/mixed-role/shortstop/first-base cases Schwarber, Alvarez, Witt
and Eldridge. Show actual source starts and outs, prior support and rate, own
sample weight, expected PA, saved forecast, corrected measurement and missing
information. Select three peers from origin-known role/stage and nearest age/
exposure when supported; preserve empty peer groups rather than invent support.

An independent verifier must reconstruct captures, additive corrections,
population totals, all saved training numerators and forecast DH arithmetic.
Unit checks must reject relief pitching, pinch hitting, missing roles, duplicates
and pre-2022 dual-start assumptions. A source pass permits one subsequently
contracted budget comparison, not deployment, a universal talent claim or a
declared value improvement. Preserve the earlier source and results as history.
