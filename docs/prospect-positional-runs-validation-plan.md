# Prospect positional-runs validation plan

Status: frozen before first score.

## Question

For minor-league hitters who reach MLB, does the already selected position-transition
model predict actual MLB positional runs per 600 better than carrying their current
minor-league position usage forward?

## Frozen comparison

- Outer population: the 576 hitters with a 2023 minor-league position origin and
  official MLB fielding usage in 2024 or 2025.
- Baseline: 2023 minor-league games-started-weighted positional runs per 600 using the
  frozen FanGraphs schedule.
- Candidate: the previously selected 2021-2022-trained transition probabilities times
  the previously derived destination-group positional runs.
- Target: games-started-weighted actual 2024-2025 MLB positional runs per 600.

Use games played only where games started is zero, matching the source certification.
Score MAE, RMSE, and signed error. Use a fixed 2,000-resample paired player bootstrap
for candidate-minus-baseline MAE and RMSE.

## Decision

The candidate passes only if both MAE and RMSE improve on the untouched outer players.
Report every origin group; subgroup results cannot rescue an overall failure. A pass
supports the positional-run component only, not the full FV model or publication.

No outside FV, current player value, organization depth, or subjective position rule
is allowed.
