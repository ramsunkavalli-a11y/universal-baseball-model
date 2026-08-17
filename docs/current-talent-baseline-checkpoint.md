# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **Baseline 1 has repeated fixed-setting predictive wins at common July 15 and Aug. 1 cutoffs in 2021–2023; full-strength level translation is not temporally stable enough to freeze.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md`. It does **not** promote a final Current Talent model.

## Baselines

Core profile: BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB (12 components).

**B0 — `loo_age_level_population_prior_v1`**

- exact age-as-of + current unambiguous level;
- leave-one-out population prior;
- no player-specific recent Performance;
- candidate 2-year age bands and minimum 12 preferred age+level peers.

**B1 — `translated_recency_empirical_bayes_v1`**

- season-to-date player core-profile evidence;
- candidate 90-day half-life;
- player×level evidence before multi-level pooling;
- empirical-Bayes shrinkage toward B0;
- candidate prior strength = 100 effective core events;
- optional candidate fitted level translation to MLB latent scale.

All settings remain candidates.

## Common July 15 confirmation

Same settings in all three seasons:

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2021-07-15 | 435,778 | **-0.013638** | **-0.003643** |
| 2022-07-15 | 375,163 | **-0.017258** | **-0.004476** |
| 2023-07-15 | 369,944 | **-0.017367** | **-0.004398** |

Lower is better.

Runs:

- 2021: `31995116901`
- 2022/2023: `31995251526`

`2021-07-15` is the first tested 2021 date with a six-level training-only translation graph. `2021-07-01` correctly fails closed because no `ROOKIE_COMPLEX` offset exists yet.

## Aug. 1 confirmation

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** |

At every Aug. 1 fold B1 also wins both proper scores in all 21 separate descriptive strata and all 12 profile components.

Runs:

- 2021: `31993773737`
- 2022/2023: `31994079021`

## Translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

Ablation rule: set learned `clr_environment_effect` values to zero while leaving B0 peer rules, recency, B1 shrinkage, player coverage, and scoring unchanged. B0 still knows current level through its peer prior.

### Common July 15 — B1 fitted minus zero

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-07-15 | **+0.000997** | **+0.000336** | 10/21 | 10/21 | 7/12 | 5/12 |
| 2022-07-15 | **-0.000713** | **-0.000202** | 18/21 | 14/21 | 4/12 | 9/12 |
| 2023-07-15 | **-0.000727** | **-0.000218** | 17/21 | 16/21 | 6/12 | 8/12 |

Negative favors fitted translation. The three-season event-weighted net effect is essentially zero (~`-0.000086` log loss / `-0.000008` Brier).

### Aug. 1 — B1 fitted minus zero

- 2021: **-0.000328 log loss / +0.000003 Brier**
- 2022: **-0.000838 / -0.000246**
- 2023: **-0.001093 / -0.000263**
- Run: `31994550684`.

### Translation decision

The stable B1 signal is **player-specific recent evidence + EB shrinkage**. The current full-strength level-only translation contributes a much smaller effect whose sign is not stable at the common July 15 cutoff.

Therefore:

- keep fitted and zero-offset variants alive through the remaining baseline-selection work;
- **do not freeze fitted translation as a required layer**;
- do not add a more complex translation merely to rescue it before broader chronological selection.

## Predictive validation implementation

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `scripts/materialize_current_talent_translation_ablation.py`

Each gate:

1. loads certified MLB + five MiLB levels;
2. fits environment effects only on events strictly before cutoff;
3. derives exact age at cutoff;
4. builds B0/B1 from pre-cutoff evidence;
5. maps predictions into actual future target environments;
6. scores all eligible core events in the next 90 days;
7. persists aggregate, stratum, component, and reliability diagnostics.

Temporal label: `retrospective_event_cutoff_corrected_history_not_vintage_information_set`.

## Calibration

B1 proper-score gains are broad, but component reliability is not uniformly better. The 2021 Aug. fold, for example, improved BB/HBP calibration while K ECE worsened slightly despite a better K proper-score contribution.

Calibration across multiple seasons/cutoffs remains a model-selection requirement. Do not apply cosmetic post-hoc calibration yet.

## What is established

- B1 adds meaningful predictive signal beyond B0 across 2021–2023 and multiple dates.
- The signal is much larger and more stable than the current translation effect.
- Real promotions/demotions/MLB transitions can be scored in realized future environments.
- Fail-closed translation topology rules correctly prevent unsupported early universal claims.

## What remains

- one more meaningfully separated common cutoff;
- translation choice: fitted vs zero offsets;
- recency half-life selection;
- EB prior-strength selection;
- age-band / peer-threshold selection;
- multi-fold calibration review;
- uncertainty model;
- Baseline 2 / richer evidence;
- Projection, playing time, defense, WAR/value, ranking.

## Next gate

1. Run **September 1** in 2021–2023 with the same fixed settings and both translation variants.
2. Review calibration across July 15 / Aug. 1 / September 1.
3. Define a small predeclared chronological selection grid rather than tuning ad hoc.
4. Freeze the simple baseline only after proper-score and calibration stability justify it.
5. Only then test richer inputs.
