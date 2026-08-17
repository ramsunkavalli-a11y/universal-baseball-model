# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **fixed-parameter Aug. 1 predictive gate passed in 2021–2023; July 1 passed in 2022/2023 but 2021 correctly fails closed because Rookie/complex translation is not yet supported; fitted-vs-zero translation remains a small incremental effect.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md` and their chronological future-outcome validation. It does **not** promote either baseline as the final Current Talent model.

## Current conclusion

Using unchanged candidate settings, Baseline 1 beats Baseline 0 at Aug. 1 in 2021–2023 and at July 1 in 2022–2023.

Aug. 1:

| Cutoff | Future core events | B0 log loss | B1 log loss | B1-B0 | B0 Brier | B1 Brier | B1-B0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | 2.268828 | **2.252931** | **-0.015896** | 0.872730 | **0.868446** | **-0.004284** |
| 2022-08-01 | 280,640 | 2.274821 | **2.256301** | **-0.018520** | 0.874528 | **0.869822** | **-0.004706** |
| 2023-08-01 | 275,511 | 2.269383 | **2.251158** | **-0.018226** | 0.874000 | **0.869362** | **-0.004638** |

July 1:

| Cutoff | Future core events | B0 log loss | B1 log loss | B1-B0 | B0 Brier | B1 Brier | B1-B0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022-07-01 | 448,049 | 2.275096 | **2.259942** | **-0.015154** | 0.874479 | **0.870483** | **-0.003995** |
| 2023-07-01 | 444,276 | 2.272685 | **2.256846** | **-0.015839** | 0.874743 | **0.870664** | **-0.004079** |

The candidate settings were unchanged:

- season-to-date eligible pre-cutoff evidence;
- **90-day half-life**;
- **100 effective core events** of B1 prior strength;
- 2-year B0 age bands;
- minimum 12 preferred age+level peers.

The July result strengthens the conclusion that the player-specific evidence/shrinkage signal is not an Aug. 1 artifact.

**2021-07-01 is not a valid universal fitted-translation fold.** Before that cutoff, the matched-transition fitter has no `ROOKIE_COMPLEX` level effect. When actual Rookie predictor evidence is reached, the pipeline raises `ValueError: no fitted translation offsets for level ROOKIE_COMPLEX`. This is correct fail-closed behavior. Do not lower the translation support threshold, omit Rookie, or manufacture a level bridge just to create a July 1 fold.

There is still **no model-freeze decision**.

Runs:

- 2021 Aug. baseline diagnostic: `31993773737`
- 2022/2023 Aug. confirmation: `31994079021`
- Aug. fitted-vs-zero translation ablation: `31994550684`
- July 1 matrix: **`31994814042`**

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

For component `k`:

`B1_k = (player_count_k + prior_strength * B0_k) / (player_effective_core_events + prior_strength)`

When fitted translation is active, each player×level segment is first converted to the MLB latent scale. In the zero-offset ablation, the same machinery runs with all learned CLR level effects set to zero.

**The half-life, prior strength, age-band width, peer threshold, and translation choice remain candidate settings.**

## Translation observation layer

Candidate implementation:

- `src/universal_baseball/current_talent_translation.py`
- method `matched_adjacent_stint_clr_wls_v1`

Critical rule:

> Translate each player × level segment before pooling multi-level evidence, and require every observed level to have a supported path to the MLB anchor.

Historical support is cutoff-dependent. A universal validation fold may exist in August but not earlier in the same season.

## Age-as-of coverage

Age is derived from pinned Chadwick DOB at each cutoff. Partial/missing DOB is not silently imputed.

Exact age coverage at Aug. 1:

- 2021: 4,315 / 4,315
- 2022: 3,756 / 3,756
- 2023: 3,853 / 3,853

## Predictive validation implementation

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_baselines.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`
- `tests/test_current_talent_ablation.py`

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

## Fixed-parameter Aug. 1 stability

In all three seasons:

- Baseline 1 improves aggregate log loss and Brier;
- all 21 separate fixed descriptive strata favor B1 on both scores;
- all 12 core components favor B1 on both score contributions.

See `docs/project-status.md` for coverage counts and exact run references.

## Controlled translation ablation

Run: `31994550684`.

The ablation changes only fitted `clr_environment_effect` values to zero. Baseline 0 still uses current level in its peer prior.

Baseline 1 fitted-minus-zero at Aug. 1:

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 | 13/21 | 12/21 | 9/12 | 6/12 |
| 2022-08-01 | **-0.000838** | **-0.000246** | 17/21 | 17/21 | 3/12 | 9/12 |
| 2023-08-01 | **-0.001093** | **-0.000263** | 16/21 | 15/21 | 6/12 | 8/12 |

At July 1:

- 2022: **-0.000409 log loss / -0.000130 Brier**; translation wins 16/21 log-loss strata, 17/21 Brier strata, 6/12 component LL contributions, 8/12 component Brier contributions.
- 2023: **-0.000566 log loss / -0.000160 Brier**; translation wins 15/21 strata on both metrics and 7/12 components on both metrics.

### Interpretation / decision

- B1's large advantage over B0 is primarily player-specific recent evidence + EB shrinkage.
- Fitted translation has a **small but generally favorable aggregate effect** for B1 in every successful July/August fold tested so far.
- The translation benefit is not universal across components or descriptive strata.
- Keep fitted translation as a candidate, but do not freeze it or require it yet.

## July 1 validation boundary

Run: `31994814042`.

- 24 targeted regression tests passed in all three matrix jobs before live materialization.
- 2022 and 2023 complete successfully.
- 2021 stops before scoring because `ROOKIE_COMPLEX` is not yet in the pre-cutoff fitted level set.
- The 2021 failure is therefore a **support/topology boundary**, not evidence that B0/B1 failed predictively.
- `.github/workflows/current-talent-july-validation.yml` is now **manual-only**. A connector safety block prevented deleting the one-time workflow file, so it remains reproducible without auto-triggering.

## Calibration

The original 2021 B1-vs-B0 fold showed mixed reliability behavior: BB/HBP improved materially, while K expected calibration error worsened slightly despite better K proper score. Translation ablations likewise do not show universal component-level improvement.

Multi-year/multi-cutoff calibration remains a model-selection requirement before freeze; do not apply post-hoc cosmetic recalibration yet.

## What is established

- Universal MLB-through-Rookie data support real chronological Current Talent scoring once the cutoff has enough support for all levels present.
- B1 adds substantial predictive signal beyond B0 in multiple years and at both July 1 and Aug. 1 where structurally supported.
- The B1 gain is broad at the Aug. folds.
- The current fitted translation contributes a small incremental aggregate B1 benefit, not the main signal.
- The fitter's fail-closed topology rules correctly prevent unsupported early-season universal claims.

## What is not established

- Earliest 2021 cutoff where all six levels are supported.
- A common July cutoff validated across all three years.
- Whether the current half-life/prior strength/age-band/peer threshold should be frozen.
- Whether calibration is acceptable across years/components/cutoffs.
- Whether a simpler/partial translation or actual-league/season residual layer adds value.
- Whether richer process/tracking/scouting evidence is warranted.

## Next gate

1. Probe **2021-07-15** with unchanged translation support and B0/B1 settings.
2. If Rookie is still unsupported, move later in July; do **not** weaken the 20-core-event stint threshold or graph-connectivity rules.
3. Once a universal 2021 July date is found, run that same date in 2022/2023 for an apples-to-apples three-year comparison, carrying fitted and zero-offset translation variants.
4. Document that gate before hyperparameter selection.
5. Only then compare a small predeclared parameter set chronologically.

Do not skip directly to Projection, playing time, WAR/value, or ranking.
