# League playing-time allocation: do not adopt this version

Completed 2026-09-22 under the [predeclared screen](hitter-league-allocation-v1-plan.md).
One stage/expected-PA allocation adjustment, no tuning after scoring. Original
2026 freeze, delivered 2026–2028 forecasts, and explorer are unchanged.

## What the test found

Matching the league total does not fix who should receive the playing time.
Across 8,319 player/origin rows forecasting ordinary seasons 2023/2024:

| Measure (lower is better) | Accepted PA | Uniform budget | Group allocation |
|---|---:|---:|---:|
| Individual PA RMSE | 90.028 | 90.001 | 89.475 |
| Fixed-rate partial-value RMSE | 0.49548 | 0.49814 | 0.49686 |
| Top-50 PA RMSE | 202.69 | 216.48 | 211.44 |
| Top-50 partial-value RMSE | 2.0384 | 2.0976 | 2.0724 |
| Under-26 top-50 PA RMSE | 161.49 | 168.57 | 164.16 |

Overall PA improves in both ordinary origins; paired MSE difference -99.16,
player-cluster 95% interval [-168.15, -18.41]. Fixed-rate value worsens slightly:
MSE difference +0.001363, interval [-0.000380, +0.003332]. Top-50 PA and value
worsen in both years, with positive paired intervals. Young-top-player results
are small/uncertain (26 rows), not a validated gain. There are only two ordinary
evaluation origins, fewer than the three required for promotion anyway.

All means/losses weight origins equally. The independently estimated batting-plus-
replacement rate is identical across the three opportunity forms. These are not
full WAR and not replacements for the separately fitted delivered value model
(ordinary-scope direct-value RMSE 0.50519, shown separately in the package).
Its comparison with the anchor diagnostic was already exposed; do not substitute
the better-looking diagnostic after this test.

## Where PA is misplaced

The accepted baseline overprojects current-MLB players as a group by 21 PA per
player, yet underprojects its preselected top 50 by 131 PA. Those observations
are compatible: too much opportunity can be spread across weaker/less-established
MLB players while stars get too little. Upper-minors players are underprojected
by about 9 PA per player. The adjustment partly corrects broad groups but cuts
star opportunity further: top-50 bias becomes -140 PA. Uniform scaling is worse.
Grouping only by level and forecast PA does not adequately resolve this mismatch.

The pandemic stress tests remain distinct: target-2020 PA RMSE 79.48 -> 76.61
and partial value 0.3891 -> 0.3857, but 2021 PA 73.86 -> 73.91 and value
0.4727 -> 0.4762. No hindsight schedule scaling was used.

## A concrete reserve problem found after scoring

The frozen candidate reserved about 7,403/7,282 PA for players outside the named
cohort in target seasons 2023/2024. Actual outside use was 2,147/2,981 PA.
The excess reserve reduced the named-player pool too far. This is a failed
assumption in this experiment, not an accepted production change.

A separately saved **post-score descriptive audit** shows why old outside-cohort
totals cannot be treated as an unchanged hitter-entrant reserve. In target seasons
2015–2019, outside-cohort players who also faced at least 100 batters as pitchers
accounted for 5,052–5,382 batting PA annually. In 2023/2024 they accounted for only
5/2 PA. Same-season pitching is used only to describe this composition, not as
a forecast feature; the threshold is not a definitive position classifier.

This is consistent with the [universal DH introduced in both leagues for 2022](https://www.mlb.com/news/mlb-rule-changes-for-2022).
The diagnostic does not prove that subtracting pitcher PA would repair individual
errors. It also does not justify assuming the 2022 rule at the end of 2021.
No second candidate was fitted and no result was replaced after this discovery.

## Next bounded checkpoint

Separate outside-cohort **pitcher batting** from **unlisted hitters**, respecting
rules known at each cutoff and changes in population coverage. Then predeclare
a new opportunity test that distinguishes batting quality within comparable
playing-time groups, rather than retuning these aggregate multipliers. Reconstruct
more chronological opportunity replays before any deployment claim. Preserve
an outside-player reserve, top-player guards, and partial-value accuracy gates.
The league budget remains an accounting check, not a reason to force partial WAR
to 570 or to overwrite independently modeled value means.

## Reproduction and checks

Artifact: `model_artifacts/hitter-league-allocation-v1-2026-09-22/` contains
17,419 scored rows, per-origin/group results, reserve/calibration ledgers,
source hashes and the separately labeled reserve-composition audit.

Run `scripts/test_hitter_league_allocation_v1.py` and
`scripts/audit_league_allocation_reserve_v1.py`; both accept `--verify`.
Eight focused unit tests cover maturity, future-data isolation, pandemic exclusion,
shrinkage, fallback, budget conservation, caps, zero capacity and order invariance.
The broader focused suite passes 65 tests. Original freeze and v2-forecast hash
checks also pass. Results are exposed development evidence, not a new holdout;
bootstrap intervals condition on historical years and fitted calibration.
