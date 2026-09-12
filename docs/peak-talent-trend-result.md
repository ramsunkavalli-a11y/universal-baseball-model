# Peak-talent skill-direction result

Last updated: 2026-09-12  
Status: **HITTERS PROMOTED; PITCHERS REJECTED**

The frozen challenger adds one fact to the existing peak model: how the player's
translated, regressed component profile changed from the prior cutoff to the current
cutoff. It does not use public ranks, playing time, contracts or future results.

## Result

| Player type | Player log loss | Player Brier | Event log loss | Event Brier | Uncertainty | Decision |
|---|---:|---:|---:|---:|---:|---|
| Hitters | 5/5 wins | 5/5 | 5/5 | 5/5 | 4/5 | Promote |
| Pitchers | 4/5 wins | 3/5 | 3/5 | 3/5 | 2/5 | Reject |

The hitter gain grows in the later groups. Equal-player log-loss improvement versus
the prior peak model is 0.00014 in 2018, 0.00029 in 2019, 0.00068 in 2023, 0.00046 in
2024 and 0.00087 in 2025. Small gains are accepted because the direction is fixed in
advance, repeats across time, and does not damage event-weighted scoring.

The existing hitter run-scale correction remains valid after the change: it improves
RMSE in 5/5 and MAE in 4/5 later groups. No new calibration value was fitted.

The current hitter peak board now uses trend. The pitcher board remains unchanged.
`recent_component_direction_runs` is exposed as an explanation field, not used as a
separate manual bonus. A missing prior profile means exactly zero trend.

