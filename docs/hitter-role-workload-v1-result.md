# Playing-time research: a promising simpler model and a source correction

Completed 2026-09-22 under the [precommitted plan](hitter-role-workload-v1-plan.md),
commit `57c03a9`. No forecast or explorer changed; 2026 outcomes remain sealed.

## What actually helped

A fixed LightGBM participation/positive-PA model using existing performance, age,
level, workload and roster predictors improves on the PA model currently attached
to the multi-year report. It does not require new injury labels or workload bins.
The new role and mixture versions are not better than this base challenger.

Normal-calendar tests, lower error is better:

| Forecast | Current multi-year PA model | Base challenger | Add role history | Role + workload states |
|---|---:|---:|---:|---:|
| Next-year PA RMSE | 69.30 | **62.88** | 62.90 | 62.93 |
| Year-2 PA RMSE | 86.65 | **79.22** | 79.24 | 79.46 |
| Next-year fixed-rate value RMSE | 0.45752 | **0.44748** | 0.44833 | 0.44933 |
| Year-2 fixed-rate value RMSE | 0.50593 | **0.49779** | 0.49888 | 0.49958 |

The value calculation holds the independently predicted hitting rate identical
across workload versions. It is batting plus replacement, **not full WAR**, and
does not overwrite the delivered direct-value forecasts. The normal samples are
25,912 player/origin rows in six next-year folds and 21,564 in five Year-2 folds.
The experiment contains 61,328 rows including separately reported pandemic stress.
All means give each forecast origin equal weight.

Base versus current multi-year model, paired MSE differences with player-cluster
95% intervals (negative favors the challenger):

- Next-year PA: -848.58 [-985.37, -712.90], improves 6/6 origins.
- Year-2 PA: -1,232.39 [-1,449.98, -1,019.36], improves 5/5 origins.
- Next-year value: -0.009090 [-0.014417, -0.003837], improves 6/6 origins.
- Year-2 value: -0.008169 [-0.015588, -0.001156], improves 4/5 origins.

These comparisons change model family as well as using the richer existing inputs;
they do not isolate which existing feature causes the gain. The role-versus-base
comparison is the controlled feature ablation.

Intervals condition on these seasons and fitted models; they do not incorporate
model-training uncertainty or adjust for multiple comparisons. All are development
results. The existing panel uses official historical snapshots, not the older
workbook-based cohort extension discussed below.

## Does it help the players we care about?

| Group | Next-year PA error, current → base | Year-2 PA error, current → base |
|---|---:|---:|
| Current MLB | 161.10 → 146.24 | 179.42 → 165.15 |
| Upper minors | 59.85 → 54.11 | 92.51 → 83.15 |
| Top 50 by pre-existing forecast | 177.28 → 141.18 | 194.76 → 143.92 |
| Top 50, under age 26 | 166.26 → 159.04 | 149.51 → 139.88 |

Top-50 fixed-rate value also improves: 2.0178 → 1.8759 next year and
1.9494 → 1.8347 in Year 2. The top-50 PA and value improvement intervals exclude
zero in both horizons. Young-star point estimates improve, but their intervals
include no improvement: only 102 next-year and 79 Year-2 observations. Do not call
that subgroup solved. Year-2 MLB players age 30+ have better PA but slightly worse
value (0.99689 → 1.00681); overall gains are not universal gains.

## The stronger benchmark matters

The older single-season roster-aware five-model ensemble was already stronger
than the simpler PA model attached to the multi-year report. On the exact 20,272
common normal-season rows (five origins), its PA RMSE is 65.48 versus 64.85 for the
base challenger, **not** a six-PA advantage. Paired PA MSE difference is -81.83
[-162.97, -11.12], improving four of five origins.

Fixed-rate value is nearly tied: 0.45922 versus 0.45847, difference -0.000694
[-0.003193, +0.001806], improving only two origins. This is not evidence for a
large new whole-model improvement. There are 5,640 new-screen rows without a roster
match and 7,911 old-roster rows outside the screen. The raw old 60.816 RMSE comes
from a different population and must not be compared to this table.

This is an existing-recipe benchmark, not a controlled feature ablation: source
population, training history and feature representations differ. The old roster
facts are October 15 snapshots; the multi-year reconstruction uses year-end
cutoffs. A confirmation should harmonize these pipelines before promotion.

## What did not help

We added two years of official non-pitcher starts (including DH), positional start
shares, positional breadth and smoothed PA per start. The source covers 2004–2025,
has unique player/team/position/year rows, and a maximum of 163 summed starts.
Games played at multiple positions were not summed. These are MLB usage features;
minor-league starts and lineup position were not reconstructed here.

The added features improve participation probability scores slightly, but their
incremental PA MSE differences are +3.26 [-22.42, +27.39] next year and +4.13
[-37.06, +46.94] in Year 2. Fixed-rate value is slightly worse. There is no reason
to adopt them for expected workload from this test.

The four-state model (zero, 1–199, 200–449, 450+ PA) averages probabilities and
within-state means. It does not assume the most likely role will happen. It also
does not improve PA/value beyond the ordinary hurdle. The published state scores
do not establish calibrated uncertainty within the ranges. Neither this one set
of bins nor this source proves that all role-aware or distributional models fail.

Pandemic-crossing tests remain separate. The base challenger's next-year stress
value error worsens 0.39006 → 0.43453; Year-2 stress worsens 0.43293 → 0.44936.
No future shortened schedule was supplied. More normal-season PA is not robust
to an unforeseen league shutdown; this failure must remain visible.

## Important source correction: the human benchmarks are not historical

The private workbooks contain historical ages/control facts, but **all shared
nonnull PA and IP forecasts are exactly identical across different archive years**:

| Archive years | PA forecasts identical / shared | IP forecasts identical / shared |
|---|---:|---:|
| 2023 and 2024 | 451 / 451 | 460 / 460 |
| 2023 and 2025 | 462 / 462 | 467 / 467 |
| 2024 and 2025 | 532 / 532 | 558 / 558 |

For example, the 2023-labeled table assigns 630 projected PA to Jackson Merrill,
who has no 2023 MLB outcome row, and the same projected PA appears in the 2025
table. Invariance across hundreds of hitters **and** pitchers is the decisive
source warning, not a single unexpectedly optimistic projection.

The exact workload vintage remains unknown. A shared later lookup is consistent
with the evidence, but is not a confirmed description of the provider's internals.
Quarantine these PA/IP columns for historical fitting, selection and benchmarking.
Do not replace missing values with zero. Source-audit code now detects the
cross-year invariance and withholds accuracy scoring. No private bulk records are
published, and these values never entered this experiment's predictor matrices.

Corrections are added to the earlier source, projection-path and 2025 replay notes.
The old external FanGraphs accuracy claim is withdrawn. The old path builder also
used nonnull projection presence to extend cohorts, so those replay/cap results
need a dated-role cohort rebuild before cutoff-certification. They remain archived
conditional comparisons, not deleted. Independently checked service/options/role
controls are not automatically invalidated by this workload-field problem.

## Decision and next bounded step

Keep the **base gradient workload model** as the candidate for confirmation.
Do not add these role features or workload bins. Do not replace the original
2026 freeze or claim a full-WAR upgrade from the fixed-rate diagnostic.

Next, preregister a same-cohort/same-cutoff confirmation of this fixed recipe and
the existing roster ensemble across Years 1–3. Check older-player value and
young-star uncertainty, then evaluate whether replacing PA improves the actual
delivered value components. Include chronological and cold-start diagnostics;
do not tune away the exposed failures. Repair the old archived cohort source gate
separately, and obtain genuinely dated human forecasts before using that benchmark.

## Reproduction and validation

Run `scripts/test_hitter_role_workload_v1.py`; `--verify` checks the saved artifact
and input hashes, chronology, finite means and state-probability composition.
The implementation uses fixed LightGBM settings, no new tuning or post-score bins.
The protocol remains unchanged after the audit discovery; withholding unsafe human
scores implements its source gate. The model comparisons were rerun unchanged after
replacing the provisional archive scoring with the stricter invariance audit.

Package: `model_artifacts/hitter-role-workload-v1-2026-09-22/` contains keyed
predictions, aggregate results and source hashes. Tests cover mature horizons,
pandemic exclusion, source dates, DH inclusion/pitcher exclusion, duplicate starts,
missing sources, mixture arithmetic and projection-vintage quarantine. Both the
original 2026 freeze and the delivered multi-year v2 forecast verify unchanged.
