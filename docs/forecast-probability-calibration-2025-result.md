# Forecast probability calibration: 2025 result

**Status:** diagnostic complete; no recalibration or production change.

The frozen March 27, 2025 forecasts were scored in fixed forecast-time probability
bands. All forecast players stayed in the denominator, including players with no MLB
workload. The audit now also reports a proper interval score, which penalizes ranges
that are wide as well as ranges that miss.

## Participation probability

| Component | Predicted active | Observed active | Brier | Log loss | Calibration error |
|---|---:|---:|---:|---:|---:|
| Hitters | 16.74% | 17.14% | 0.0444 | 0.1516 | 0.0145 |
| Pitchers | 15.41% | 15.74% | 0.0579 | 0.1958 | 0.0122 |

The overall levels are close, but the middle bands reveal shape errors:

- hitters forecast at 30%–60% averaged **44.5%** predicted versus **55.9%** observed;
- pitchers in that band averaged **44.8%** versus **53.3%** observed;
- the highest pitcher band averaged **91.2%** versus **87.0%**, a smaller error in the
  opposite direction.

This supports an eventual monotone probability-calibration challenger, but one 2025
season is not enough to fit and validate it. Build it on earlier rolling origins and
freeze the mapping before a later score.

## Range implication

The prior conclusion is unchanged: the current symmetric WAR bounds are sensitivity
ranges, not calibrated probability intervals. Zero outcomes make full-universe
coverage look strong, while active-player misses are asymmetric. The Phase 2 range
must combine a discrete inactivity probability with conditional workload and skill
draws, then validate fixed quantiles with proper interval scores.
