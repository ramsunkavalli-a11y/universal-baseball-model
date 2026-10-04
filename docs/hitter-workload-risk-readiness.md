# Playing time uncertainty training readiness

2026-10-03. The [locked comparison](hitter-workload-risk-contract.md) has its
actual training and validation memberships saved. No new models have been
fitted and no predictive result is claimed.

All 30,506 existing forecasts and 35 outer cells remain. The setup prepares 95
internal conditional-PA fits, with both the outer tested player group and the
inner validation player group excluded from training. Internal labels are
available by the outer cutoff, and each internal predictor fit uses only labels
available at its own earlier cutoff. Actual scouting release dates are checked.
The 2020 target exclusion leaves two rather than three eligible internal origins
for each 2021 and 2022 cell; there is no invented validation year.

Each outer cell has 153–217 distinct active calibration players. Repeated seasons
are not counted as distinct people. No cell needs an unestimated fallback. The
maximum observed source target is 753 PA, within the declared engineering support
bound of 800; this does not establish a physical limit of 800.

Important qualification: 8,420 outer forecasts have no matching earlier active
player in the refined age/stage/rank/draft/sample intersection, and 12,820 have
fewer than 20. Internal validation has 38,137 absent and 56,035 sparse profile
rows across the 95 contexts; these rows can recur across outer contexts and are
not unique players. The global dispersion estimate is supported by active
calibration outcomes, not by direct analogues for every lower-minors prospect.
Keep all those forecasts in scoring and report their support warnings. A passing
execution check cannot justify calibrated risk for the entire population.

Two new regression tests reproduce the nested selection and reject outer-player
contamination. Eleven related handoff/source-review tests also pass. The earlier
source review and browser checks are complete; the new model's player walks
remain pending because it has not been fitted.

Authoritative local artifacts:

- `reports/generated/hitter-workload-risk/preflight.json`
- `reports/generated/hitter-workload-risk/support.parquet`
- `reports/generated/hitter-workload-risk/profile-support.parquet`
- `reports/generated/hitter-workload-risk/calibration-memberships.parquet`

The preflight receipt SHA256 is
`57a88cd4de2724a88d3cc699c1b7621facca57699d18bd1c0c1b6c960a4f448e`.
Run the declared fits and proper distribution scoring next, then the required
actual player reviews before any retention decision. Current forecast means,
public benchmark errors, frozen 2026 and deployed explorers remain unchanged.
