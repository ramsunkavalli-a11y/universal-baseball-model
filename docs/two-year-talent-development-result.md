# Direct two-year talent development result

Last updated: 2026-09-12  
Status: **PROMISING HISTORICAL REPLAY; CURRENT RANKING NOT YET CHANGED**

The one-year development adjustment was not repeated twice. The same historical
framework was fit directly against translated component quality two seasons later.
Training, model selection, level translation, minimum future evidence and missing-
season rules remain the same. Every path touching the nonexistent 2020 minor-league
season is excluded.

## Result versus unchanged talent

The development-selected richer form beat carry-forward on both proper scores in all
three later two-year replays.

| Target | Hitter log-loss change | Hitter Brier change | Pitcher log-loss change | Pitcher Brier change |
|---|---:|---:|---:|---:|
| 2023 | -0.00528 | -0.00162 | -0.03073 | -0.00813 |
| 2024 | -0.00768 | -0.00281 | -0.02938 | -0.00763 |
| 2025 | -0.01014 | -0.00358 | -0.02954 | -0.00816 |

## Complexity decision

- Hitters: the richer component form also beats age/level alone on both scores in all
  3/3 replays. Retain it as the research two-year hitter form.
- Pitchers: the richer form beats age/level alone on Brier in 3/3, but log loss in only
  2/3. Prefer the simpler age/level two-year pitcher form under the fixed 80% breadth
  rule.

This gives the development layer a logical shape instead of one universal adjustment:

- one-year hitters and pitchers can use current component shape after heavy shrinkage;
- two-year hitters retain that component-specific signal;
- two-year pitchers use the simpler age/level path until richer detail proves broader.

Both horizons remain rate-only and conditional on a later observed season. Playing
time, position, arrival, contracts, public rank and public FV are absent.

## Next gate

Add player-cluster uncertainty and age/level subgroup checks. If the broad gains remain,
fit the frozen forms through completed 2025 and generate current one- and two-year
talent medians and ranges. Only then compare the current results player by player with
the external top 50.
