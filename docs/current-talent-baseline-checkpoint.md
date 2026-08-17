# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **Baseline 1 has repeated fixed-setting predictive wins at common July 15, Aug. 1, and Sep. 1 cutoffs in 2021–2023; full-strength level translation remains a candidate rather than a frozen requirement.**

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

## Fixed-setting chronology

Lower is better.

| Cutoff | 2021 B1-B0 LL / Brier | 2022 B1-B0 LL / Brier | 2023 B1-B0 LL / Brier |
|---|---|---|---|
| Jul. 15 | **-0.013638 / -0.003643** | **-0.017258 / -0.004476** | **-0.017367 / -0.004398** |
| Aug. 1 | **-0.015896 / -0.004284** | **-0.018520 / -0.004706** | **-0.018226 / -0.004638** |
| Sep. 1 | **-0.018898 / -0.004986** | **-0.020860 / -0.005166** | **-0.018447 / -0.004577** |

Future core-event volume:

| Cutoff | 2021 | 2022 | 2023 |
|---|---:|---:|---:|
| Jul. 15 | 435,778 | 375,163 | 369,944 |
| Aug. 1 | 344,391 | 280,640 | 275,511 |
| Sep. 1 | 163,751 | 124,141 | 134,188 |

The September sample is smaller because affiliated seasons wind down within the 90-day horizon. That is opportunity/censoring coverage, not a bad-talent target.

Runs:

- Jul. 15: 2021 `31995116901`; 2022/2023 `31995251526`
- Aug. 1: 2021 `31993773737`; 2022/2023 `31994079021`
- Sep. 1: **`31995542018`**

`2021-07-15` is the first tested 2021 date with a six-level training-only translation graph. `2021-07-01` correctly fails closed because no `ROOKIE_COMPLEX` offset exists yet.

### Core conclusion

B1's player-specific recent-results + empirical-Bayes signal survives **nine common season/date folds** with unchanged candidate settings. That signal is now much more stable than the current translation effect.

## Translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

Ablation rule: set learned `clr_environment_effect` values to zero while leaving B0 peer rules, recency, B1 shrinkage, player coverage, and scoring unchanged. B0 still knows current level through its peer prior.

### B1 fitted translation minus zero offsets

| Cutoff | 2021 LL / Brier | 2022 LL / Brier | 2023 LL / Brier |
|---|---|---|---|
| Jul. 15 | **+0.000997 / +0.000336** | **-0.000713 / -0.000202** | **-0.000727 / -0.000218** |
| Aug. 1 | **-0.000328 / +0.000003** | **-0.000838 / -0.000246** | **-0.001093 / -0.000263** |
| Sep. 1 | **-0.000624 / -0.000158** | **-0.002478 / -0.000742** | **-0.002026 / -0.000577** |

Negative favors fitted translation.

September translation breadth:

- 2021: fitted wins 15/21 LL strata, 14/21 Brier strata; 5/12 LL components, 8/12 Brier components.
- 2022: 19/20 LL strata, 18/20 Brier strata; 5/12 LL components, 12/12 Brier components.
- 2023: 16/21 LL strata, 17/21 Brier strata; 7/12 LL components, 8/12 Brier components.

### Translation decision

The stable B1 signal is **player-specific recent evidence + EB shrinkage**. Full-strength level-only translation is a much smaller second-order effect:

- unfavorable at 2021 Jul. 15;
- usually modestly favorable at Aug. 1;
- more favorable at Sep. 1;
- not universal by component/stratum.

Therefore:

- keep fitted and zero-offset variants alive through formal model selection;
- **do not freeze fitted translation as required**;
- do not add a more complex translation merely to rescue the current one before the simple baseline is selected.

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

B1 proper-score gains are broad, but component reliability is not uniformly better. Existing fixed-bin ECE diagnostics show mixed component behavior. The validation contract also calls for calibration intercept/slope, which are not yet implemented.

**Calibration is now the next gate.** Do not tune hyperparameters or apply post-hoc recalibration first.

## What is established

- B1 adds meaningful predictive signal beyond B0 across 2021–2023 and three common dates.
- The signal is much larger and more stable than the current translation effect.
- Real promotions/demotions/MLB transitions can be scored in realized future environments.
- Fail-closed translation topology rules correctly prevent unsupported early universal claims.

## What remains

- multi-fold calibration review, including intercept/slope;
- translation choice: fitted vs zero offsets;
- recency half-life selection;
- EB prior-strength selection;
- age-band / peer-threshold selection;
- uncertainty model;
- Baseline 2 / richer evidence;
- Projection, playing time, defense, WAR/value, ranking.

## Next gate

1. Build a reproducible calibration review across the nine Jul. 15 / Aug. 1 / Sep. 1 folds.
2. Add component calibration intercept/slope alongside reliability ECE.
3. Only after that define a small predeclared chronological hyperparameter-selection grid.
4. Freeze the simple baseline only after proper-score and calibration stability justify it.
5. Only then test richer inputs.
