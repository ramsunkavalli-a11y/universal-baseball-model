# Pitcher value uncertainty result

Date: 2026-09-22
Status: **use for development uncertainty; point forecast unchanged**

## Question

How uncertain is the leading next-season pitcher projection, and can the ranges stay
honest for established MLB pitchers, upper-minors pitchers, lower-minors pitchers,
starters, and relievers?

## Method

For each historical forecast season, the interval uses only errors from earlier
out-of-fold seasons. Residual ranges are calibrated separately by forecast-time player
stage and by whether at least half of the pitcher's recent appearances were starts.
Cells with fewer than 200 prior errors fall back to all earlier players. No 2026
outcome is used, and the role-enhanced point forecast is not changed.

## Result

Across 24,514 later pitcher-seasons:

| Published range | Intended coverage | Observed coverage | Mean width |
|---|---:|---:|---:|
| Middle 50% | 50% | 45.4% | 0.112 WAR |
| Middle 80% | 80% | 79.7% | 0.306 WAR |
| Middle 90% | 90% | 89.8% | 0.469 WAR |

The broader stage-only calibration looked acceptable overall but badly understated
starter uncertainty: its 80% and 90% ranges covered only 67.4% and 81.8% of starter
outcomes. Crossing stage with recent role improved starter coverage to **77.7%** and
**89.1%**. Reliever coverage is **80.6%** and **90.1%**, respectively.

The ranges also behave sensibly by player stage. Current MLB pitchers have much wider
80% ranges (about 1.6 WAR) than upper-minors pitchers (about 0.08 WAR) or lower-minors
pitchers (about 0.005 WAR), because most minor-league outcomes are zero next-season
MLB value while established pitchers have a much wider performance and workload
distribution.

## Decision

Use the role-aware 80% and 90% ranges as the development uncertainty layer for the
leading pitcher forecast. Treat the 50% range cautiously because it remains too
narrow overall. These ranges cover the current defense-independent pitcher component,
not complete pitcher WAR. Refit the offsets from all completed historical errors when
the final 2026 forecast is assembled, without inspecting 2026 outcomes.
