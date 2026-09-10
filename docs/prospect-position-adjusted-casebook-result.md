# Position-adjusted prospect casebook

Status: diagnostic complete; no production value changed.

The casebook holds the passing private position sensitivity fixed, then reviews every
remaining top-50 disagreement player by player. It contains 68 disagreements and 12
agreements among the 42 FanGraphs players who were still pre-MLB at the model cutoff.

## What remains

| Main model-side issue | Players |
|---|---:|
| Opportunity outweighs below-average translated batting | 28 |
| Pitcher translated skill | 12 |
| Advanced-level proximity and opportunity | 2 |
| Low-level upside or cumulative model | 10 |
| Sparse hitter evidence | 10 |
| Strong translated batting or cumulative model | 6 |

The clearest hitter pattern is not position anymore. Twenty-eight model-only top-50
hitters have below-average translated batting but enough arrival probability and
expected workload to create positive WAR above replacement. That can be sound for an
excellent defender or premium-position player, but it is too common to accept from
individual inspection alone.

This agrees with the existing linked hitter replay: the cutoff-reconstructed current
method predicted 0.211 mean four-year batting-plus-replacement WAR versus 0.144
observed. A linked-path alternative reduced MAE by moving predictions toward zero but
missed the positive tail and did not pass RMSE. The viewed 25% blend is not eligible
for promotion.

## Next gate

Build a chronology-safe next-season joint hitter test on completed 2022-to-2025
cohorts. Score expected batting-plus-replacement WAR with non-arrivals retained, and
report the exact high-arrival/below-average-batting subgroup. The candidate must
improve overall MAE/RMSE and preserve the positive MLB tail. Do not retest arbitrary
constant-hazard haircuts: the declining-hazard challenger was already rejected.

The generated player rows are in
`reports/generated/prospect-position-adjusted-casebook/2026-09-08/casebook.csv`.
No public FV or rank enters any issue label or model calculation.

