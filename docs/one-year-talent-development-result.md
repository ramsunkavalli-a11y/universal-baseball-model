# One-year talent development result

Last updated: 2026-09-12  
Status: **PROMISING HISTORICAL REPLAY; CURRENT RANKING NOT YET CHANGED**

## What was tested

The model predicts next-season translated component quality at any affiliated level.
It does not predict whether the player appears, how much he plays, his position, WAR,
contract value or public rank.

The source is official StatsAPI component history from 2003 through completed 2025.
The missing 2020 minor-league season is excluded as both an origin and target. At every
historical origin, level translations are refit using only seasons already complete at
that time. A future season needs at least 50 PA/BF to be scored; a missing future season
is reported as unobserved rather than labeled bad talent.

The permanent comparison is carry-forward: the player's translated, regressed current
component profile remains unchanged. Two challengers were selected on 2015–2017 after
training through 2014:

1. age, age relative to level, level and evidence amount;
2. the same fields plus current component shape and component-by-age-relative-to-level
   interactions.

All component probabilities are modeled together in log-ratio space, so every predicted
profile remains positive and sums to one.

## Result versus no development

The selected component-development model beat carry-forward on both proper scores in
every later replay.

| Target | Hitter log-loss change | Hitter Brier change | Pitcher log-loss change | Pitcher Brier change |
|---|---:|---:|---:|---:|
| 2019 | -0.01156 | -0.00421 | -0.02791 | -0.00752 |
| 2022 | -0.00955 | -0.00348 | -0.03737 | -0.01016 |
| 2023 | -0.00682 | -0.00241 | -0.04147 | -0.01093 |
| 2024 | -0.01306 | -0.00469 | -0.03569 | -0.01008 |
| 2025 | -0.01022 | -0.00340 | -0.04102 | -0.01138 |

Negative is better. Each hitter replay covers 2,731–2,951 players and roughly
841,000–875,000 future PA. Each pitcher replay covers 2,927–3,288 players and roughly
777,000–829,000 future BF.

## Does the extra complexity earn its place?

Mostly yes, but by a much smaller amount than the main gain over no development.

- Hitters: richer form beats age/level on log loss in 5/5 replays and Brier in 4/5.
- Pitchers: richer form beats age/level on log loss in 4/5 and Brier in 5/5.
- Selected hitter ridge strength: 1,000, which is intentionally heavy shrinkage.
- Selected pitcher ridge strength: 100.

This is logical baseball structure: age and level set the broad expected development;
the player's current strikeout, walk, power and contact mix changes how that development
is distributed. It is not a single bonus for being young, and it does not assume every
young player improves.

## Boundary and next gate

This is strong development evidence, not final promotion. Before current values change:

1. add player-cluster uncertainty and age/level subgroup reversal checks;
2. run the direct two-year version rather than chaining the one-year adjustment twice;
3. fit the selected forms through completed 2025 and generate current 2027/2028 talent
   profiles and ranges;
4. only then attach the external top-50 list and explain agreements/disagreements.

Public ranks/FV were not read by this test and cannot choose its form or parameters.
