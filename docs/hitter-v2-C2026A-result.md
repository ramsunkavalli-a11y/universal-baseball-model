# C2026A result: output calibration is insufficient

Both prespecified candidates failed. The global correction improved active-year
PA-weighted RMSE by 0.32%, below the 1% practical threshold. The origin correction
worsened it by 0.60% and reversed supported AAA/demotion results in 2023. Both
failed calibration readiness. No parameters were retuned and no candidate shipped.

| PA-weighted wOBA RMSE | 2023 | 2024 | Pooled |
|---|---:|---:|---:|
| G0 | .038811 | .040796 | .039820 |
| Global calibration | .039338 | .040039 | .039692 |
| Origin calibration | .039836 | .040278 | .040059 |
| Marcel | .040338 | .044021 | .042227 |

Paired player-cluster bootstrap intervals for pooled RMSE change were
[-.000216, -.000039] for global and [.000100, .000386] for origin calibration.
The global gain is statistically discernible under this resampling scheme but
too small and insufficiently calibrated to satisfy the declared practical goal.

2024 upward movers had G0 mean wOBA error .03038, versus .01246 for clean
same-level players. The analysis also makes coverage explicit: the original G0
score does not include 863/813/671 target players without a forecast in
2022/2023/2024. It measures returning/forecast-eligible players, not every hitter.
This must remain visible in future prospect-model claims.

The next mechanism to examine is unadjusted history accumulated across levels.
H0's translation used adjacent years and bundled age/development/calibration;
same-season within-player level contrasts can isolate a different, simpler
translation question. It needs its own contract; C2026A remains closed.
