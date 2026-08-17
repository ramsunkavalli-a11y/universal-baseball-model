# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **fixed-parameter Aug. 1 predictive gate passed independently in 2021–2023; controlled translation ablation completed; additional cutoffs, hyperparameter selection, and calibration stability remain required before promotion.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md` and their chronological future-outcome validation. It does **not** promote either baseline as the final Current Talent model.

## Current conclusion

Using the **same candidate settings without retuning**, Baseline 1 beats Baseline 0 on both event-weighted multinomial log loss and multinomial Brier at Aug. 1 cutoffs in 2021, 2022, and 2023.

| Cutoff | Future core events | B0 log loss | B1 log loss | B1-B0 | B0 Brier | B1 Brier | B1-B0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | 2.268828 | **2.252931** | **-0.015896** | 0.872730 | **0.868446** | **-0.004284** |
| 2022-08-01 | 280,640 | 2.274821 | **2.256301** | **-0.018520** | 0.874528 | **0.869822** | **-0.004706** |
| 2023-08-01 | 275,511 | 2.269383 | **2.251158** | **-0.018226** | 0.874000 | **0.869362** | **-0.004638** |

In every season, Baseline 1 improves both proper scores in all 21 separate fixed descriptive strata and all 12 core profile components.

A controlled translation ablation now shows that the **large B1-vs-B0 gain is mostly the value of player-specific recent evidence + empirical-Bayes shrinkage**, not the current level-only translation layer. Translation adds a small aggregate log-loss benefit to Baseline 1, but its Brier/component/stratum results are mixed.

There is still **no model-freeze decision**.

Runs:

- 2021 baseline diagnostic: `31993773737`
- 2022/2023 fixed-parameter baseline confirmation: `31994079021`
- three-year fitted-vs-zero translation ablation: **`31994550684`**

## Model contract

### Core profile

The model preserves the 12-component profile:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

### Baseline 0

Method: `loo_age_level_population_prior_v1`

- no player-specific recent Performance;
- exact age-as-of + actual unambiguous current level;
- preferred same-level + same-2-year-age-band leave-one-out peers;
- minimum preferred peers = 12;
- fallback to same level, then global other-player pool;
- predicted player excluded from every peer pool.

### Baseline 1

Method: `translated_recency_empirical_bayes_v1`

Candidate settings unchanged across the three confirmation folds:

- season-to-date eligible pre-cutoff evidence;
- **90-day half-life**;
- player×level evidence handled before pooling;
- **100 effective core events** of prior strength toward Baseline 0.

For component `k`:

`B1_k = (player_count_k + prior_strength * B0_k) / (player_effective_core_events + prior_strength)`

When fitted translation is active, each player×level segment is first converted to the MLB latent scale. When the zero-offset ablation is active, the same machinery runs with all learned CLR level effects set to zero.

**The half-life, prior strength, age-band width, peer threshold, and translation choice remain candidate settings.**

## Age-as-of coverage

Age is derived from pinned Chadwick DOB at each cutoff. Partial/missing DOB is not silently imputed.

Exact age coverage at Aug. 1:

- 2021: **4,315 / 4,315**
- 2022: **3,756 / 3,756**
- 2023: **3,853 / 3,853**

## Predictive validation implementation

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `tests/test_current_talent_baselines.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`

Each gate:

1. loads certified MLB + five affiliated-MiLB level evidence;
2. fits any environment translation only on events strictly before cutoff;
3. derives exact age at cutoff;
4. builds B0/B1 from pre-cutoff evidence;
5. maps latent predictions into the actual future target level;
6. scores every eligible core event in the next 90 days;
7. persists aggregate, level, transition, age-band, evidence-band, component, and reliability diagnostics.

Temporal label:

`retrospective_event_cutoff_corrected_history_not_vintage_information_set`

## Three-year Baseline 1 stability

### 2021-08-01

- predictor players: 4,315
- Baseline profiles: 4,301
- scored players: 3,722
- scored target environments: 4,634
- future core events: 344,391
- B1-B0 log loss: **-0.015896**
- B1-B0 Brier: **-0.004284**
- fixed-strata wins: 21/21
- component wins: 12/12

### 2022-08-01

- predictor/Baseline players: 3,756
- scored players: 3,357
- scored target environments: 4,134
- future core events: 280,640
- B1-B0 log loss: **-0.018520**
- B1-B0 Brier: **-0.004706**
- fixed-strata wins: 21/21
- component wins: 12/12

### 2023-08-01

- predictor/Baseline players: 3,853
- scored players: 3,418
- scored target environments: 4,154
- future core events: 275,511
- B1-B0 log loss: **-0.018226**
- B1-B0 Brier: **-0.004638**
- fixed-strata wins: 21/21
- component wins: 12/12

## Controlled translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

Run: **`31994550684`**.

### Question

Does the learned training-only level observation layer add predictive value if every other part of the Baseline 0/1 pipeline remains identical?

The ablation replaces fitted `clr_environment_effect` values with zero. It does **not** remove level from Baseline 0's age+level peer prior. It therefore isolates the learned cross-level translation.

### Baseline 1 result

Fitted translation minus zero-offset:

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 | 13/21 | 12/21 | 9/12 | 6/12 |
| 2022-08-01 | **-0.000838** | **-0.000246** | 17/21 | 17/21 | 3/12 | 9/12 |
| 2023-08-01 | **-0.001093** | **-0.000263** | 16/21 | 15/21 | 6/12 | 8/12 |

Lower is better.

### Baseline 0 result

Translation is inconsistent for the population-prior baseline:

- 2021 fitted translation is worse than zero offsets on both aggregate metrics;
- 2022 fitted translation is slightly better on both;
- 2023 fitted translation is worse on both.

### Interpretation / decision

- B1's aggregate log loss benefits from fitted translation in **all three Aug. 1 folds**, but the effect is small.
- Brier is essentially flat/slightly worse in 2021 and modestly better in 2022/2023.
- The translation gain is not universal across profile components or descriptive strata.
- The much larger B1-vs-B0 gain (~0.016–0.019 log loss; ~0.0043–0.0047 Brier) is overwhelmingly the player-evidence/shrinkage signal rather than translation.
- **Keep fitted translation as a candidate, but do not freeze it or require it yet.** Carry fitted and zero-offset variants into additional cutoff tests and let chronology decide whether the small gain is worth the complexity.

The temporary three-season workflow used for this ablation was removed after the gate. Artifacts remain on run `31994550684`.

## Calibration

The original 2021 B1-vs-B0 gate showed mixed reliability behavior: BB/HBP improved materially, while K expected calibration error worsened slightly despite better K proper score. The translation ablation likewise does not show universal component-level improvement.

Multi-year calibration remains a model-selection requirement before freeze; do not apply post-hoc cosmetic recalibration yet.

## What is established

- Universal MLB-through-Rookie data support real chronological Current Talent scoring.
- B1 adds substantial predictive signal beyond B0 in three independent seasons with unchanged settings.
- The B1 gain is broad across levels/transitions/ages/evidence bands/components.
- The current fitted translation contributes a small incremental B1 log-loss benefit, not the main signal.
- The pipeline is production-shaped enough for repeated cutoff tests and controlled ablations.

## What is not established

- Whether fitted translation retains its small advantage at other dates.
- Whether zero offsets ultimately win on parsimony after more folds.
- Whether the model behaves similarly at June/July/September cutoffs.
- Whether the current half-life/prior strength/age-band/peer threshold should be frozen.
- Whether calibration is acceptable across years/components.
- Whether a partial/component-specific translation or actual-league/season residual layer adds value.
- Whether richer process/tracking/scouting evidence is warranted.

## Next gate

1. Run **July 1** cutoffs in 2021–2023 with the same fixed Baseline 0/1 settings.
2. Carry **both fitted and zero-offset translation variants**.
3. If July 1 is structurally supported and consistent, add another earlier cutoff, likely June 1.
4. Only then compare a small predeclared hyperparameter set chronologically.
5. Freeze the simple baseline before adding Baseline 2 or richer evidence.

Do not skip directly to Projection, playing time, WAR/value, or ranking.
