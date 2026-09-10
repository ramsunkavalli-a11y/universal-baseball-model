# Prospect conditional-WAR bridge stability plan

**Status:** frozen before 2022/2023 bridge scoring

Keep the exact model already fit under the conditional-WAR bridge plan:

- 2018 training cohort and 2019-2020 outcomes;
- core two-year arrival model;
- standardized core conditional-WAR ridge with penalty `100`;
- four production rates regressed with `200` opportunities;
- no clipping, demographics-as-talent, outside FV, organization or calibration.

Do not refit, reselect, blend or recenter anything. Apply that unchanged fit to:

1. the 2022 snapshot and 2023-2024 component-WAR outcomes;
2. the 2023 snapshot and 2024-2025 component-WAR outcomes.

Retain all non-arrivals as zero. Compare the same pooled-conditional baseline and
ridge candidate on identical players. Report end-to-end and arrived-player mean,
bias, MAE, RMSE, paired player intervals, supported level/role/evidence/hand groups,
and hashes for each cohort.

The extension is stable only if both later cohorts improve end-to-end RMSE and MAE,
do not worsen absolute bias, and do not worsen arrived-player RMSE for both hitters
and pitchers. A failed condition rejects stability; it may not be repaired by tuning
on one year. These seasons have been inspected elsewhere, so even a pass is
retrospective robustness evidence rather than fresh production confirmation.

