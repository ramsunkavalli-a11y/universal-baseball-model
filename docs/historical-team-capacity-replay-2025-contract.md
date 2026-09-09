# Historical team-capacity replay — 2025 contract

Status: frozen before scoring capacity-adjusted forecasts against 2025 outcomes.

## Question

When applied to the already frozen 2025 Opening Day workload forecasts, do the conservative team, hitter-position, and pitcher-role capacity layers improve player-level workload accuracy?

## Chronology and inputs

- Forecast cutoff: 2025-03-27.
- Forecasts: the existing historical hitter and pitcher paths; no refit.
- Opening organization: the existing dated historical control-owner table.
- Capacity development: 2021-2024 MLB team workload, hitter-position, and pitcher-role evidence only.
- Outcomes: full-season 2025 MLB PA and BF, including explicit zero for forecast players with no MLB workload.
- A player's full-season outcome follows the player even after a transaction. Opening organization is used only to determine the crowding visible at forecast time.

The 2025 data has already been used for other descriptive confirmation work, so this is available historical confirmation, not an untouched final holdout.

## Fixed comparisons

Hitters:

1. Original expected MLB PA.
2. Team-cap expected PA.
3. Team plus primary-position-cap expected PA.

Pitchers:

1. Original expected MLB BF.
2. Team-cap expected BF.
3. Team plus fractional-role-cap expected BF.

No layer may increase a player's workload. Missing outcome rows are zero, never dropped. Players without a resolved Opening Day organization are reported and excluded because a team constraint cannot be assigned honestly.

## Scores

For each player type and comparison:

- player-level RMSE;
- player-level MAE;
- mean forecast minus actual workload;
- total forecast divided by total actual workload;
- the same scores among players whose forecast was actually reduced;
- paired bootstrap 95% intervals for RMSE and MAE changes, resampling Opening Day organizations as clusters with a fixed seed.

Also report changes by hitter position group and the forecast's highest-probability pitcher role as diagnostics. The capacity calculation itself remains fractional. Subgroups do not select or tune the method.

## Decision rule

- Promote a capacity layer toward the displayed team-fit view only if it does not materially worsen all-player RMSE or MAE and improves the affected-player overprediction problem.
- If RMSE and MAE disagree, intervals span zero, or a major group is harmed, keep the layer as research and diagnose it without tuning on 2025.
- Regardless of outcome, the replay cannot change organization-neutral skill, WAR rate, or trade value.
