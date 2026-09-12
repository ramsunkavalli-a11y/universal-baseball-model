# Peak-talent run-scale calibration and uncertainty

Last updated: 2026-09-12  
Status: **POINT CALIBRATION PROMOTED; RANGES REMAIN DIAGNOSTIC**

The component model predicts strikeouts, walks, hit batters and hit outcomes better
than unchanged talent. Converting those forecasts to runs left a consistent bias:
hitter peak rates were too low and pitcher peak rates were too optimistic.

One fixed correction was estimated from peak-window end years 2015-2017 only, using
the median actual-minus-predicted run rate within each origin age band. It was then
applied unchanged to 2018, 2019, 2023, 2024 and 2025.

| Player type | Under 20 | Age 20-21 | Age 22-23 |
|---|---:|---:|---:|
| Hitter runs / 600 PA | +5.03 | +6.22 | +4.88 |
| Pitcher runs prevented / 800 BF | -5.63 | -2.02 | -1.19 |

The correction improved equal-player MAE and RMSE in all five later groups for both
hitters and pitchers. It also beat unchanged present rate on both measures in all five
groups. The frozen values are in
`model_artifacts/peak-talent-run-calibration-v1.json`. Component projections remain
unchanged and visible separately.

Historical 10th-to-90th-percentile errors remain diagnostic, not formal player ranges.
Hitter cohort coverage was 73%-83%. Pitcher coverage ranged from 60%-86%, including a
clear 2023 failure.

The pitcher model intentionally remains the validated five outcomes: SO, unintentional
walk, HBP, HR and other. An earlier frozen test separated singles, doubles and triples
from official data. Even with heavier Tango-style regression, no richer candidate beat
the five-outcome incumbent on both development scores. Availability alone is not a
reason to add it.
