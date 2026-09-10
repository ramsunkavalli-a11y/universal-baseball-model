# Prospect positive-WAR hurdle plan

**Status:** frozen before scoring

## Question

Can a separate, strongly regressed probability of producing at least `0.25` MLB
component WAR over two seasons distinguish the positive tail without sacrificing the
majority of non-arrivals and low-value arrivals?

The threshold is fixed from the previously committed support inventory, not from
candidate performance. It supplies 69 hitter and 114 pitcher positives in the 2018
arrived-player training cohort and at least 51 / 68 in each later cohort. Higher impact
thresholds are deferred because support is thinner.

## Frozen construction

- Fit once on 2018 pre-MLB players who record MLB workload in 2019-2020.
- Binary target: two-year component WAR at least `0.25`.
- Predictors: the same core age, level, role, affiliated workload, dated 40-man and
  four production-rate design used by the bridge, with rates regressed by `200`
  opportunities.
- Standardize on the 2018 arrived-player training rows only.
- Fit one logistic model with fixed `C=0.1`, no class weights and no search.
- Estimate conditional WAR as predicted positive-tail probability times the 2018
  positive-tail mean plus its complement times the 2018 below-threshold mean.
- Multiply by the unchanged core arrival probability for the all-player expectation.

No demographics, physical measurements, draft/FV opinions, organization, depth chart,
recentered outer outcomes or WAR clipping are allowed. Negative below-threshold WAR is
retained. The candidate is a transparent two-part mean, not a full distribution.

## Frozen evaluation

Apply the unchanged 2018 fit to the 2021, 2022 and 2023 snapshots and their following
two MLB seasons. Do not refit between cohorts.

1. Among observed arrivals, compare tail probability with the constant 2018 tail rate
   using log loss, Brier error, calibration and paired player intervals.
2. On all players, compare pooled versus hurdle expected WAR using bias, MAE, RMSE and
   paired player intervals; non-arrivals remain zero.
3. Report arrived-player continuous error and supported level, role, evidence and hand
   diagnostics. Subgroups cannot select a separate model.

The hurdle passes retrospective stability only if both probability scores improve at
the point estimate in all three cohorts, all-player RMSE and MAE do not worsen,
absolute bias does not worsen, and arrived-player RMSE does not worsen. Uncertainty and
subgroup damage remain required interpretation. These cohorts are already general
development data; even a pass cannot change production without fresh confirmation.

