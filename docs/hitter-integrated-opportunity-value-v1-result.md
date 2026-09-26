# Playing time improves; the value connection still fails

2026-09-25. Completed the [fixed integration test](hitter-integrated-opportunity-value-v1-plan.md).
**No live model or explorer changed.** The combined candidate improves individual
playing-time forecasts, but fails cohort-total/lower-minors checks and does not
improve the full value forecast against the strongest reference. Keep the
component improvements as research evidence; do not deploy the combination.

## What was built

One predeclared H candidate uses repaired F participation and detailed D
conditional workload for never-debuted prospects, the existing E ensemble for
players with prior MLB debuts, and B for remaining inactive/unknown players.
There are no name-specific exceptions, new fits, tuning or outcome-based routes.

The safe component connector distinguishes benchmark **rates**, direct **totals**,
and neutral predictions. Only explicit rate heads change with expected PA.
Direct totals remain unchanged; they are never divided by tiny old PA. All
seven original components and the earlier model-selection decisions are replayed.
This removes the known amplification error, but is not a claim that all
component totals now respond coherently to opportunity.

Controls: L is the original component release; B is accepted opportunity;
D is the retained prospect-only research update; E is universal ensemble PA.
B/D/E/H share the same marginal batting correction and safe component rules.
N uses the same E PA but its independently archived batting-rate product, with
the same safe component rules. N is a mandatory reference, not a newly selected
rescue model. Its batting forecast already existed; its safe expanded ledger
is assembled in this experiment and is not a deployed full-WAR forecast.

## Playing time: a real accuracy gain, not a complete solution

All starting players, including zero-MLB outcomes; equal-origin PA RMSE:

| Horizon | Retained prospect update D | Existing ensemble E | Combined H |
|---|---:|---:|---:|
| Year 1 | 67.83 | 62.33 | 61.95 |
| Year 2 | 82.99 | 78.85 | 78.31 |
| Year 3 | 93.39 | 89.63 | 89.17 |
| Three-year total | 208.12 | 193.22 | 190.97 |

Three-year H vs E MSE change is -863.77, paired 95% interval
[-1377.56, -349.50]; H improves two of three origins, with a slight loss in
2016. Against D it improves all three origins, interval [-8387.36, -5379.20].
Cumulative MAE also improves: D 82.38, E 76.16, H 74.65 PA.

The expected baseball mechanism is visible. Across all five Year-1 origins,
prior 100–399 MLB PA players' mean overprediction falls from 45.72 to 1.40 PA.
Prior 400+ players' underprediction falls from 41.39 to 9.83 PA. Young players
with brief MLB debuts improve from 29.14 to 16.92 PA underprediction. These
are cutoff-known groups, not groups selected by future success. Returners
after lost seasons remain difficult and the recent-regular subset is small.

Two predeclared checks fail:

- **Cohort totals:** average absolute three-year PA-total error is 38,524 for H,
  versus 38,132 for E and 21,639 for D. D's better total does not imply better
  individual allocations: offsetting group errors can cancel. Conversely H's
  better RMSE does not excuse missing aggregate opportunity.
- **Lower minors:** next-year PA RMSE rises 9.01 (E) to 9.25 (H), a 5.50% MSE
  worsening, just beyond the fixed 5% guard. This is inherited from the prospect
  D recipe, not caused by changing existing MLB players. We do not change the
  threshold or choose a lower-minors exception after seeing this result.

Probability guards pass. Aggregate totals refer to each starting cohort, not
the entire future MLB league; future entrants absent from the database are not
invented. 2021 and other origins are reported separately; the 2021-origin H
three-year PA shortfall remains about 72,770 (predicted 468,259 vs 541,029).

## Better playing time does not automatically give better player value

Three-year RMSE in the project's component-wins units:

| Target | Original release L | Prospect update D | Ensemble reference N | Combined H |
|---|---:|---:|---:|---:|
| Batting plus replacement | 1.216 | 1.207 | 1.140 | 1.210 |
| Expanded component ledger | 1.277 | 1.264 | 1.213 | 1.270 |

These are separate targets on different complete-label support, not interchangeable
published WAR measurements. Expanded totals have only two complete origins
(2021/22), versus three for batting/PA; no six-year claim is supported.

H does not improve batting or expanded value beyond D. N beats H in every
cumulative origin: H-minus-N MSE intervals are [+0.11556, +0.22042] for batting
and [+0.07921, +0.21186] for expanded value. N also has lower annual errors in
all three horizons. Many supported value safety checks fail, including older
MLB players. H's expanded cohort-total error is 183.11 wins versus N's 67.98.

The diagnosis is specific: **the preserved direct batting forecast plus a
marginal PA correction is not the strongest way to connect these pieces.**
E and N have identical PA and nonbatting components, but N's existing batting
product has much lower cumulative error (1.140 vs 1.209). That comparison
isolates the batting construction as a block; it does not isolate the choice
of rate anchor from the choice of product versus marginal correction. Those
both differ, so neither can be credited alone without a separate test.

## Accounting fixes and remaining consistency limits

The earlier Maikel Garcia/Edward Olivares explosions are not reproduced:
H gives Garcia (2021 origin, Year 1) about 104 PA and 0.29 component wins,
and Olivares (2018 origin, Year 1) about 59 PA and 0.11 wins. These are outputs
of a rejected integrated candidate, not new live forecasts or tuned fixes.

16,831 player/horizon/component records use direct totals; 9,814 have H PA
below one. Their largest absolute direct total is 0.720 runs. There is no
old-PA ratio explosion, but holding totals fixed does not resolve role/exposure
consistency. Future component refits need cutoff-safe nested opportunity inputs
or explicit relevant opportunities, not a retrospectively chosen cap.

Another inherited limitation: E's PA mixes four hurdle members plus one direct
PA member, while E's participation probability averages four classifiers. These
are not one exact hurdle product. In 285 E records (two retained by H), expected
PA exceeds 750 times reported participation probability. That is incompatible
with treating the two outputs as one distribution under the model's own 750-PA
bound. Do not derive a conditional PA distribution by dividing them. No ad hoc
probability correction was applied. This is an additional reason not to call
the combined system ready for joint career-path simulation.

## Decision and next milestone

Both full promotion gates fail. Retain the positive PA evidence, the safe
component-assembly code, and the stronger N reference; preserve the existing
live outputs. No retrospective candidate switching or extra tuning was done.

Next work should use the stronger existing batting product as a mandatory
control and explicitly separate (a) which conditional talent anchor is used,
(b) how opportunity and production are connected, and (c) how consistent annual
participation/workload distributions are obtained. Fit any reconciliation only
on older, genuinely out-of-time forecasts. Judge player errors and cohort totals
together. Before another fit, audit source support for nested annual PA/rate
predictions; do not train a meta-model on its own fitted outcomes.

This is a more targeted task than another engine tournament or a blanket age,
repeater, COVID or prospect boost. Full direct-component reconciliation,
joint career uncertainty, Years 4–6 and control/trade value remain open.

## Verification

52,181 annual player/horizon rows, 365,267 component records, 12,891 complete
three-year player/origin records. Original component release and seven-component
target accounting recompose; original earlier-fold choices and inherited fit
cutoffs are checked. Assembly cannot access outcomes; mutation replay is exact.
Independent NumPy score/recomposition checks and 39 focused regression/unit
tests pass (13 new integration cases). The prior workload and transfer packages
also verify unchanged. Historical results remain exposed development evidence; overlapping
cohorts and few independent years limit inference from player bootstrap intervals.

The original 3,907-player, 31-file 2026 forecast verifies unchanged. No protected
outcomes were opened. Sources, code, decisions and output hashes are preserved in
`model_artifacts/hitter-integrated-opportunity-value-v1-2026-09-25/`.

Reproduce from the repository root with the archived source packages present:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/build_hitter_integrated_opportunity_value_v1.py --freeze
.venv/Scripts/python.exe -X utf8 scripts/build_hitter_integrated_opportunity_value_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_integrated_opportunity_value_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_integrated_opportunity_value_v1.py
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_hitter_integrated_opportunity_value.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_full_2026_freeze.py
```

The freeze command is for a fresh output directory only; an existing manifest
is verified and reused, never overwritten to disguise a changed experiment.
