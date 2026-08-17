# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect the current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- **Pause at meaningful project junctures to update this handoff before continuing.** Update after a major gate, a material model/architecture decision, or a changed recommended next batch.

## Current stage

The project is in **chronological Current Talent model validation**. Source/data plumbing is no longer the active bottleneck.

Implemented/certified foundations include:

1. reuse-first canonical data/provenance/identity architecture;
2. production-shaped 2024 affiliated-MiLB batting Performance;
3. certified 2021–2023 affiliated-MiLB Current Talent evidence;
4. certified 2021–2023 MLB Current Talent evidence with official reconciliation;
5. leakage-safe predictor snapshots and future targets;
6. training-only MLB-anchored matched-transition environment translation candidate;
7. exact Chadwick DOB → age-as-of enrichment;
8. Baseline 0 / Baseline 1 results-only Current Talent estimators;
9. proper future-environment scoring, calibration diagnostics, and controlled translation ablation.

**No Current Talent estimator is frozen/promoted yet.**

## Baseline definitions

Core batting profile: 12 components — BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB.

**Baseline 0 — `loo_age_level_population_prior_v1`**

- no player-specific recent Performance;
- exact age-as-of + current unambiguous level;
- leave-one-out age+level population prior;
- candidate 2-year age band;
- minimum 12 preferred age+level peers;
- same-level then global fallback only when needed.

**Baseline 1 — `translated_recency_empirical_bayes_v1`**

- season-to-date player core-profile evidence;
- candidate 90-day recency half-life;
- player×level evidence handled before multi-level pooling;
- optional candidate level translation to MLB latent scale;
- empirical-Bayes shrinkage toward B0;
- candidate prior strength = 100 effective core events.

These remain candidate settings, not frozen hyperparameters.

## Fixed-setting B1 vs B0 chronology

Lower is better. The same candidate settings were used in every fold below.

### Common July 15

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2021-07-15 | 435,778 | **-0.013638** | **-0.003643** |
| 2022-07-15 | 375,163 | **-0.017258** | **-0.004476** |
| 2023-07-15 | 369,944 | **-0.017367** | **-0.004398** |

Runs: 2021 `31995116901`; 2022/2023 `31995251526`.

`2021-07-15` is the first tested 2021 date where all six levels have training-only translation support. `2021-07-01` correctly fails closed because no pre-cutoff `ROOKIE_COMPLEX` effect exists.

### Common Aug. 1

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

Runs: 2021 `31993773737`; 2022/2023 `31994079021`.

### Common Sep. 1 — late-season gate passed

Run: **`31995542018`**.

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2021-09-01 | 163,751 | **-0.018898** | **-0.004986** |
| 2022-09-01 | 124,141 | **-0.020860** | **-0.005166** |
| 2023-09-01 | 134,188 | **-0.018447** | **-0.004577** |

The future-event sample is much smaller in September because affiliated seasons wind down inside the 90-day target horizon. That reduced opportunity volume is a coverage property and is reported explicitly; it is not treated as poor talent.

### Core Baseline 1 conclusion

The B1 signal now survives **three seasons × three common calendar positions** (July 15, Aug. 1, Sep. 1), with unchanged settings. The player-specific recent-results + empirical-Bayes signal is therefore a robust baseline finding, not an Aug. 1 artifact.

This still does **not** freeze the exact half-life, prior strength, age-band width, peer threshold, or translation choice.

## Translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

Controlled ablation: replace fitted `clr_environment_effect` values with zero while leaving recency, B0 peer rules, B1 shrinkage, player/target coverage, and future scoring unchanged. B0 still knows current level through its peer prior.

### July 15 — B1 fitted translation minus zero offsets

| Cutoff | Log loss delta | Brier delta |
|---|---:|---:|
| 2021-07-15 | **+0.000997** | **+0.000336** |
| 2022-07-15 | **-0.000713** | **-0.000202** |
| 2023-07-15 | **-0.000727** | **-0.000218** |

At the same July 15 date, fitted translation loses in 2021 and wins modestly in 2022/2023. The three-season event-weighted effect is essentially zero.

### Aug. 1 — B1 fitted minus zero

| Cutoff | Log loss delta | Brier delta |
|---|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 |
| 2022-08-01 | **-0.000838** | **-0.000246** |
| 2023-08-01 | **-0.001093** | **-0.000263** |

Run: `31994550684`.

### Sep. 1 — B1 fitted minus zero

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-09-01 | **-0.000624** | **-0.000158** | 15/21 | 14/21 | 5/12 | 8/12 |
| 2022-09-01 | **-0.002478** | **-0.000742** | 19/20 | 18/20 | 5/12 | 12/12 |
| 2023-09-01 | **-0.002026** | **-0.000577** | 16/21 | 17/21 | 7/12 | 8/12 |

September translation effects are more favorable than July/August, but the earlier common-July instability still matters.

### Translation decision

- The much larger B1-vs-B0 gain is primarily **player-specific recent evidence + EB shrinkage**.
- Fitted level translation is a smaller second-order effect.
- Its aggregate benefit is usually favorable, especially later in-season, but its sign/magnitude is not stable enough across time/components to freeze it as required.
- **Keep fitted and zero-offset translation variants alive for formal chronological model selection.**
- Do not add a more complex translation merely to rescue the current one before the simple baseline is selected.

## Governing validation rules

`docs/current-talent-validation-contract.md` is authoritative.

Frozen rules include:

- Current Talent = latent rate/profile ability now, conditional on opportunity;
- predictor evidence strictly before cutoff;
- environment effects training-only;
- future outcomes scored in their realized environment;
- primary horizon = next 90 calendar days;
- zero future PA is not poor talent;
- chronological / rolling-origin validation only;
- proper scoring and calibration outrank correlation;
- richer evidence must beat simple baselines out of time.

## Key implementation / workflow files

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_translation.py`
- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `.github/workflows/current-talent-baseline-validation.yml`
- `.github/workflows/current-talent-july-validation.yml`
- `.github/workflows/current-talent-2021-july-probe.yml`
- `.github/workflows/current-talent-july15-confirmation.yml`
- `.github/workflows/current-talent-september-validation.yml`

All completed live workflows above are **manual-only**.

## Important boundaries / not complete

Still unresolved:

- multi-fold calibration stability across July 15 / Aug. 1 / Sep. 1;
- formal model selection between fitted translation and zero offsets;
- selected recency half-life;
- selected EB prior strength;
- selected age-band width / peer threshold;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not tune or add richer features yet.**

1. Build a reproducible **multi-fold calibration review** over the nine common July 15 / Aug. 1 / Sep. 1 folds, for B0/B1 and fitted/zero translation where available.
2. Add calibration intercept/slope diagnostics required by the validation contract, not only reliability-bin ECE.
3. Document whether B1's proper-score win is accompanied by acceptable calibration stability and which components are systematically over/under-confident.
4. Then define a small **predeclared chronological model-selection grid** for recency half-life, EB prior strength, and translation choice. Use earlier seasons for selection and a later season for confirmation rather than tuning to all nine folds.
5. Freeze the simple baseline only if proper scores and calibration justify it.
6. Only after freeze test Baseline 2 or richer inputs.

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect current `source-certification-poc` head.
5. Continue with the **multi-fold calibration review across July 15 / Aug. 1 / Sep. 1**. Do not tune hyperparameters or re-audit closed source/certification work first.

<!-- BEGIN AUTO CURRENT TALENT DEVELOPMENT SELECTION -->
## Development-grid candidate selected — awaiting 2023 confirmation

The predeclared 18-candidate simple-baseline grid has been evaluated on **2021–2022 only**. Alternative grid configurations have not been evaluated on 2023.

Preselected candidate: **`hl180_ps100_fitted`** — half-life **180 days**, prior strength **100**, translation **`fitted_translation`**.

Development equal-fold mean B1 log loss: **2.255543**; Brier: **0.869233**.

Versus the prior 90/100/fitted reference, selected-minus-reference mean log loss is **-0.000262** and Brier is **-0.000133**.

Detailed checkpoint: `docs/current-talent-development-selection-checkpoint.md`.

**Next gate:** evaluate this preselected candidate on the three 2023 folds only; compare to B0 and the existing 90/100/fitted reference. Do not run the full alternative grid on 2023 and do not reselect using 2023 if confirmation fails.
<!-- END AUTO CURRENT TALENT DEVELOPMENT SELECTION -->
