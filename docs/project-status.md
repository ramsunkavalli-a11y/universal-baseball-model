# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- **Pause at meaningful project junctures to update this handoff before continuing.** Update after a major gate, a material model/architecture decision, or a changed recommended next batch.

## Current stage

The project is in **chronological Current Talent model validation**. Source/data plumbing is no longer the active bottleneck.

Implemented/certified foundations include the canonical public-data layer, 2024 affiliated batting Performance, certified 2021–2023 MLB + affiliated-MiLB Current Talent evidence, leakage-safe snapshots/future targets, exact age-as-of, candidate environment translation, Baseline 0 / Baseline 1, and proper future-environment scoring/diagnostics.

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
- candidate level translation to MLB latent scale;
- empirical-Bayes shrinkage toward B0;
- candidate prior strength = 100 effective core events.

These remain candidate settings, not frozen hyperparameters.

## Fixed-setting B1 vs B0 results

Lower is better. Candidate settings are unchanged across every fold below.

### Common July 15 cutoff — all three seasons

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2021-07-15 | 435,778 | **-0.013638** | **-0.003643** |
| 2022-07-15 | 375,163 | **-0.017258** | **-0.004476** |
| 2023-07-15 | 369,944 | **-0.017367** | **-0.004398** |

Runs:

- 2021 probe: `31995116901`
- 2022/2023 confirmation: **`31995251526`**

The 2021 July 15 date is the first tested 2021 cutoff where the training-only matched-transition graph supports all six levels. `2021-07-01` fails closed because no pre-cutoff `ROOKIE_COMPLEX` offset exists; do not weaken support rules to force an earlier universal fitted-translation fold.

### Aug. 1 cutoff — all three seasons

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

Runs:

- 2021 diagnostic: `31993773737`
- 2022/2023 confirmation: `31994079021`

### July 1 where structurally supported

- 2022: B1-B0 **-0.015154 log loss / -0.003995 Brier** over 448,049 future core events.
- 2023: B1-B0 **-0.015839 / -0.004079** over 444,276 events.
- Run: `31994814042`.

**Conclusion on the core B1 signal:** player-specific recent results + empirical-Bayes shrinkage beat the age+level population prior consistently across seasons and more than one calendar position. This is now a robust baseline finding, though hyperparameters/calibration are not yet frozen.

## Translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

The controlled ablation replaces fitted `clr_environment_effect` values with zero while leaving recency, B0 peer rules, B1 shrinkage, player/target coverage, and future scoring unchanged. B0 still knows current level through its peer prior.

### Common July 15 — B1 fitted translation minus zero offsets

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-07-15 | **+0.000997** | **+0.000336** | 10/21 | 10/21 | 7/12 | 5/12 |
| 2022-07-15 | **-0.000713** | **-0.000202** | 18/21 | 14/21 | 4/12 | 9/12 |
| 2023-07-15 | **-0.000727** | **-0.000218** | 17/21 | 16/21 | 6/12 | 8/12 |

Negative is better for fitted translation. At the same July 15 date, fitted translation is worse in 2021 and modestly better in 2022/2023. Event-weighting the three season-level deltas gives an effect very close to zero (~`-0.000086` log loss / `-0.000008` Brier), so **full-strength level-only translation has not earned a freeze decision**.

### Aug. 1 — B1 fitted minus zero

- 2021: **-0.000328 log loss / +0.000003 Brier**
- 2022: **-0.000838 / -0.000246**
- 2023: **-0.001093 / -0.000263**
- Run: `31994550684`.

### Translation decision

- The large B1-vs-B0 gain is primarily **player-specific recent evidence + EB shrinkage**.
- Current fitted level translation adds only a small incremental effect.
- Its sign is not stable at the common July 15 cutoff.
- **Do not freeze fitted translation as required.** Keep zero-offset and fitted variants as model-selection candidates for now.
- Do not add a more complicated translation merely to rescue the current one before broader chronology/hyperparameter selection.

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

All completed live workflows above are **manual-only**.

## Important boundaries / not complete

Still unresolved:

- another meaningfully separated common cutoff beyond July 15/Aug. 1;
- model selection between fitted translation and zero offsets;
- selected recency half-life;
- selected EB prior strength;
- selected age-band width / peer threshold;
- multi-year/multi-cutoff calibration stability;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not tune or add richer features yet.**

1. Run a common **September 1** fixed-setting fold in 2021–2023, carrying fitted and zero-offset translation variants. This gives a more separated calendar position than July 15 vs Aug. 1; interpret lower-minor opportunity coverage explicitly because seasons wind down inside the 90-day horizon.
2. Document the September gate and review calibration across July 15 / Aug. 1 / September 1 before selecting hyperparameters.
3. Then define a small **predeclared chronological model-selection grid** for recency half-life, EB prior strength, and translation choice; use earlier seasons for selection and later seasons for confirmation rather than tuning to all folds.
4. Freeze the simple baseline only if proper scores and calibration justify it.
5. Only after freeze test Baseline 2 or richer inputs.

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect current `source-certification-poc` head.
5. Continue with the **September 1 fixed-setting three-year validation**, keeping fitted and zero-offset translation variants. Do not re-audit closed source/certification work or weaken translation support rules.
