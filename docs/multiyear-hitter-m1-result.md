# Multi-year hitter milestone 1: source and target certification

Date: 2026-09-22. No challenger scores inspected at this checkpoint.

Recovered the existing snapshot, affiliated statistics and opportunity sources rather
than constructing a future-survivor cohort. There are 16 origin cohorts, 2009–2025
excluding 2020. The latest cohort contains 3,907 hitters, including 189 without
current component statistics and 177 without a sourced age. These rows remain in
the denominator. This is the existing roster/stat union, not a certification of all
organizational reserve rights or every international player.

MLB outcomes cover every completed season 2009–2025. Batting PA equals pitching BF
in every season. Player-season labels are unique. Small negative simple PA-accounting
residuals represent interference/other PA absent from the simple component sum;
component totals exceeding PA fail the audit. Original source certification is reused,
not represented as a new independent player-by-player source audit.

## Corrected calendar-value target

Version `calendar_batting_plus_replacement_v1` retains observed neutral batting runs
and scales only the replacement allocation by completed MLB team-games / (30 × 162).
The schedule must have completed status code F. Abstract status “Final” also includes
postponed/canceled games and is insufficient. Deduplicate resumed games by game ID.
The 2020 schedule has 898 completed games; the new batting-plus-replacement total is
210.641975, versus the old 570. This corrects accounting, not prediction accuracy.
Completed-early games count once. Actual batting production is never scaled to 162 games.

Certified no-MLB years receive zero. Unobserved years remain null, and cumulative
labels require all three years. Negative player value remains possible. No 2020
origin is used. Calendar lags are not compressed: 2021 retains a missing 2020 MiLB
lag, while actual 2020 MLB statistics remain available. Ages advance normally.

The common target omits position, running and defense. Source recovery found no
independent public whole-WAR label table in the recovered outcome inventory;
FanGraphs control/service files are not WAR outcomes, and our own WAR reports are
not an independent benchmark. A matched public whole-WAR comparison is unavailable
for this milestone. Do not describe the result as full WAR or superiority to public
projection systems.

## Inputs and test support

Use three calendar years of aggregate batting rates, PA, MLB exposure and level
shares, age, current level, historical MLB value and October-15 40-man membership.
Missing ages/statistics have explicit flags. No ID/name, future team, future level,
future season environment or 2026 result is a predictor. Features have 77 columns;
the simpler B0 reference uses 23 age/level/workload/membership columns.

The reconstructed cutoff is December 31. Sources are current-corrected historical
records, not archived publication vintages. Historical 40-man lists contain members;
absent players are treated as not listed, matching the existing opportunity contract.
This does not establish actual December-31 reserve ownership.

Six outer origins are 2016, 2017, 2018, 2019, 2021 and 2022. Each has at least two
earlier fully mature inner origins. Inner fitting excludes every validation player.
Outer fitting can use a returning player's legitimate prior history. Three windows
cross 2020; the other three are separately scored. The fixed nonoverlap diagnostic
uses origins 2016, 2019, 2022. The current forecast covers 2026–2028 using only inputs
through 2025; those outcome labels are null.

The [machine-readable frozen contract](multiyear-hitter-v1-contract.json) records
source artifact hashes, folds, numeric presets and baseline-derived subgroup limits.
Margins were set using only a 2012 player-disjoint B0 reference, before challenger
scoring. They are practical exploratory tolerances, not established baseball standards.
The complete reproducible source manifest and raw schedule captures are under the
ignored `reports/generated/multiyear-hitter-v1` output directory.

Reproduce with `scripts/materialize_multiyear_hitter_v1.py`, then verify the frozen
contract and run `scripts/evaluate_multiyear_hitter_v1.py`. The contract cannot be
overwritten by the freeze command. Unit tests cover schedule statuses, replacement
scaling, no-play versus censoring, exact maturity, player exclusion and future-feature
invariance. Original forecast packages are unchanged.
