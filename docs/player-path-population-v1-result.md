# Historical snapshot repair: result

2026-09-23. Fixed experiment from [the pre-fit plan](player-path-population-v1-plan.md).
Decision: **reject_population_repair_as_replacement**. No delivered player forecasts or explorer changed.
No 2026 outcomes opened. Historical results remain exposed development evidence.

## What the audit found

Keeping only each player's latest eligible snapshot discards many young career states.
The repair restores every mature historical snapshot, with each player receiving total weight one.
Counts below use age <=23 and 1–99 current MLB PA; effective support accounts for repeated identities.

| Fit cutoff / horizon | Latest snapshots | Restored snapshots / identities | Effective identities |
|---|---:|---:|---:|
| 2016 / 3 | 30 | 114 / 102 | 91.8 |
| 2019 / 3 | 31 | 196 / 172 | 144.6 |
| 2021 / 3 | 31 | 196 / 172 | 144.6 |
| 2022 / 3 | 31 | 196 / 172 | 144.6 |
| 2025 / 3 | 45 | 264 / 235 | 155.6 |
| 2016 / 6 | 22 | 41 / 39 | 37.4 |
| 2017 / 6 | 27 | 68 / 61 | 54.4 |
| 2018 / 6 | 18 | 85 / 77 | 70.2 |
| 2019 / 6 | 30 | 114 / 102 | 91.8 |
| 2025 / 6 | 30 | 114 / 102 | 91.8 |

Exact promotion timing is not identified by this annual panel; partial-season exposure is available,
but cannot be relabeled as a dated late-season promotion. Missing timing remains unknown.
No earlier matched delivered forecasts were available for 2012–15. No extra evaluation origins added.

## Normal three-year results

Same players at origins 2016, 2021 and 2022. Lower is better. Targets are batting plus replacement,
**not whole WAR**. These are exact fitted-distribution scores, so v1 finite-sample scores differ slightly.

| Model | Cumulative CRPS | Mean RMSE |
|---|---:|---:|
| Age/stage comparisons | 0.363579 | 1.644024 |
| Age/level/workload forest | 0.296199 | 1.365719 |
| Full-feature latest snapshots | 0.289130 | 1.333203 |
| Full-feature identity-balanced snapshots | 0.266062 | 1.222144 |
| Delivered mean forecast | — | 1.213781 |

Restoring snapshots reduces distribution error by 8.0% versus F1.
That isolates a useful historical-population improvement. It does not establish a better production
point forecast: the delivered model still has lower mean error. Passing the 5% mean-error guard
means the candidate stays reasonably close; it is not a claim to beat the delivered model.

Paired player-cluster CRPS differences (A1 minus reference; negative favors repair):

- B0: -0.097517, 95% interval [-0.115413, -0.080713].
- F0: -0.030137, 95% interval [-0.037962, -0.022702].
- F1: -0.023068, 95% interval [-0.029574, -0.017362].

## Young players and prospect success

| Group | Rows | Actual regular-workload paths | F1 expected | A1 expected |
|---|---:|---:|---:|---:|
| Never-debuted minors | 9845 | 44 | 28.80 | 23.47 |
| Recent debut | 641 | 102 | 74.27 | 89.84 |
| Young brief MLB | 98 | 16 | 6.65 | 9.83 |

For young brief-MLB cases, predicted no-further-MLB paths fall from 46.7 to 25.1, versus 10 observed.
That is an improvement, but still too pessimistic. Among never-debuted prospects, the expected
number of regular-workload paths moves farther below the observed count, and its Brier score
does not beat either forest control. This is a substantive supported failure, not merely a failure
to collect enough rare-star examples. Counts are player-origin outcomes, not distinct careers.

Regular-workload means at least 450 PA in two of three years. Other fixed events:
no MLB play, six cumulative batting/replacement wins, and two four-win batting/replacement seasons.
They overlap and are not scouting grades or All-Star probabilities. The exposed 98-row young brief-MLB
group remains diagnostic, not fresh confirmation. Full event counts and calibration are in the package.

## Acceptance checks

- three_normal_origins: PASS.
- crps_improvement: PASS.
- majority_origins: PASS.
- mean_error: PASS.
- event_scores: PASS.
- starting_group_crps: PASS.
- supported_success_checks: NOT PASSED.
- broad_success_support: NOT PASSED.

Simulation checks: stable; 0 acceptance checks change across sampled runs.
Five fixed 400-draw seeds and one 1600-draw run reuse fitted models. CRPS, Brier and mean-MSE
sampling estimates remove their IID finite-draw bias; log loss has a common fixed clipping rule.
Exact means/probabilities/CRPS determine the main comparisons. Joint energy and intervals remain
simulation diagnostics. Small negative corrected loss estimates are possible, not negative true risks.
Whole-player bootstrapping does not remove common-season shocks. Nonoverlapping 2016/2021 results,
fully player-disjoint 2022 sensitivity and pandemic stress tests are separately reported.
With test identities excluded from training, CRPS improves from 0.3430 to 0.2731. The inherited delivered reference is not player-disjoint,
so its error in that diagnostic is not an equally disjoint comparator.
All historical H6 windows cross 2020 and cannot confirm ordinary six-year accuracy.

In that separate six-year stress test, mean RMSE is 2.284 for F1, 2.182 for A1, and 2.173 for the delivered reference.
The repair improves this weaker path benchmark too, but does not beat the delivered mean.

## Projection-anchored follow-up readiness

Cutoff-safe H1 conditional batting/replacement-rate anchors from 2012; H2 development challenger; H1-H3 opportunity replays from 2016; unconditional H1-H3 quantiles from 2012.

The conditional anchors are selected-MLB rate estimates, not universal latent ability. No accepted joint rate/opportunity path is archived at early donor cutoffs. The earliest normal outer fold has zero donors with both existing H1 anchor and complete H1-H3 opportunity replay. H6 2016/2017 has no eligible H1 anchors at all. Unconditional quantiles cannot be divided by expected PA and called talent, or independently sampled into coherent careers.

The raw annual panel is available. Earlier vintage models and a coherent transition design can be rebuilt in a separately specified follow-up. This is an archive/readiness gate, not proof that anchoring cannot work.

Next prerequisites:

- Rebuild cutoff-specific conditional-rate and opportunity baseline states at donor origins, starting with H3. Preserve inactive and never-debuted rows and unknown rates.
- Freeze how baseline ability, development and availability interact before residual-path scoring; do not use a failed H2 challenger as an accepted anchor.
- Verify vintage training cutoffs and predictive support for young brief-MLB and never-debuted states, then freeze one C1 experiment.
- Keep six-year calibration explicitly pandemic-limited; do not synthesize a normal H6 test or full control tail.

See the [dated-anchor rebuild checklist](projection-path-anchor-rebuild-checklist.md) for the bounded next step.

Prior direct prospect-tail and component-tail tests were inspected and remain rejected;
no new threshold search was added. Dollar valuation still needs whole-WAR accounting, dated rights/costs,
and the beyond-six-calendar-year control/liability tail. No failures are rescued with a post-hoc blend.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_player_path_population_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_player_path_population_v1.py
.venv/Scripts/python.exe -X utf8 scripts/audit_projection_path_feasibility_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_player_path_population_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_player_path_population_v1.py
```

The pre-fit manifest is immutable; do not refreeze it after fitting. All 44 fitted distributions,
264 simulated prediction sets and their local hashes are recorded. Exact predictions and compact
diagnostics are packaged; the larger simulation files remain locally reproducible.
