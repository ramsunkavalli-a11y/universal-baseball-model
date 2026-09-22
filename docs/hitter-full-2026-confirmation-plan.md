# Frozen 2026 full-hitter confirmation

This package is the pre-result forecast for the current best hitter system. It was built from information through 2025 without opening 2026 participation or performance.

The frozen population is the same 3,907-player list used by the already locked playing-time model. Of those players, 3,720 have a 2025 batting record and receive the five-model batting forecast. The other 187 are retained rather than dropped: their batting value is the frozen playing-time forecast multiplied by the development-population value rate.

The selected partial-WAR forecast adds four pieces:

- batting plus replacement, from the equal-weight five-model ensemble;
- positional value, based on the player's 2025 fielding-position mix and projected playing time;
- baserunning, using the previously selected steal and advancement shrinkage models;
- catcher throwing, blocking, and framing, for players with catcher evidence.

General non-catcher defense is explicitly zero. That is intentional: the tested public-data defense challenger did not earn inclusion. Consequently, this is a partial-WAR forecast and must not be described as complete player WAR.

The only batting challenger carried into the confirmation is the routed version. It uses the stats-only models for the chance of reaching MLB, while retaining detailed contact information for value conditional on reaching MLB. The selected model remains the incumbent unless the routed forecast clears every gate written in the JSON contract.

After the 2026 regular season is complete, construct one target row for every frozen player. A player with no MLB appearance must still have a row with zero outcomes. Then run the locked evaluator once. Do not tune the models, change the population, add late-season information, or choose new subgroups after seeing 2026 results.

The confirmation will answer three separate questions:

1. Did the routed batting architecture beat the selected architecture on batting and total partial WAR?
2. How well did the already frozen playing-time model perform against its two locked benchmarks?
3. Which value components and player groups remain the largest sources of error for the next development cycle?

The integrity verifier can be run at any time because it reads only the frozen package and its pre-2026 inputs.
