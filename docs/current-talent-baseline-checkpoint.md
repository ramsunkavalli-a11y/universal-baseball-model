# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **fixed-parameter Aug. 1 predictive gate passed independently in 2021, 2022, and 2023; translation ablation, additional cutoffs, hyperparameter selection, and calibration stability remain required before promotion.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md` and their chronological future-outcome validation. It does **not** promote either baseline as the final Current Talent model.

## Current conclusion

Using the **same candidate settings without retuning between seasons**, Baseline 1 beats Baseline 0 on both event-weighted multinomial log loss and multinomial Brier at Aug. 1 cutoffs in 2021, 2022, and 2023.

| Cutoff | Future core events | B0 log loss | B1 log loss | B1-B0 | B0 Brier | B1 Brier | B1-B0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | 2.268828 | **2.252931** | **-0.015896** | 0.872730 | **0.868446** | **-0.004284** |
| 2022-08-01 | 280,640 | 2.274821 | **2.256301** | **-0.018520** | 0.874528 | **0.869822** | **-0.004706** |
| 2023-08-01 | 275,511 | 2.269383 | **2.251158** | **-0.018226** | 0.874000 | **0.869362** | **-0.004638** |

Lower is better.

In **every season**, Baseline 1 also improves both proper scores in:

- 21 / 21 separate fixed descriptive strata: 6 target levels + 5 transition classes + 5 age bands + 5 evidence bands;
- 12 / 12 core profile components.

This is strong evidence that player-specific recent translated results add predictive information beyond the age+level population prior. It is **not yet a model-freeze decision** because these are all Aug. 1 cutoffs and the value of the translation layer itself has not yet been ablated.

Runs:

- 2021 primary diagnostic: `31993773737`
- 2022/2023 fixed-parameter confirmation matrix: **`31994079021`**

The permanent single-season workflow is `.github/workflows/current-talent-baseline-validation.yml` and is manual-only. The one-time 2022/2023 matrix workflow was removed after the confirmation gate.

## Model contract

### Common latent reporting scale

The model preserves the 12-component core profile:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

The current observation-layer candidate is `matched_adjacent_stint_clr_wls_v1`, trained only on pre-cutoff matched-player transitions with MLB as the zero-effect anchor.

Critical ordering rule:

> **Translate each player × level segment to MLB scale before pooling a player's evidence across levels.**

For future scoring, the direction is reversed:

`CLR(observed target profile at L) = CLR(latent MLB-scale profile) + beta[L]`

then softmax back to target-level probabilities.

### Baseline 0

Method: `loo_age_level_population_prior_v1`

- no player-specific recent Performance;
- exact age-as-of + actual unambiguous current level;
- preferred same-level + same-2-year-age-band leave-one-out peer pool;
- minimum preferred peers = 12;
- fallback to same level, then global other-player pool;
- predicted player excluded from every peer pool.

### Baseline 1

Method: `translated_recency_empirical_bayes_v1`

Current candidate settings, unchanged across the three confirmation folds:

- season-to-date eligible pre-cutoff evidence;
- **90-day half-life**;
- player×level translation before pooling;
- **100 effective core events** of prior strength toward Baseline 0.

For component `k`:

`B1_k = (translated_player_count_k + prior_strength * B0_k) / (player_effective_core_events + prior_strength)`

The 12 Baseline 0 and Baseline 1 probabilities each sum to one per player.

**The 90-day half-life, 100-event prior strength, 2-year age band, and 12-peer threshold remain candidate settings, not frozen choices.**

## Age-as-of coverage

Age is derived from pinned Chadwick `birth_year/month/day` at each cutoff. Partial/missing DOB is not silently imputed; duplicate requested MLBAM identities or invalid complete DOBs fail closed.

Exact age coverage:

- 2021-08-01: **4,315 / 4,315**
- 2022-08-01: **3,756 / 3,756**
- 2023-08-01: **3,853 / 3,853**

## Predictive validation implementation

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `tests/test_current_talent_baselines.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`

Each gate:

1. loads certified MLB + all five affiliated-MiLB level evidence;
2. fits translation only on events strictly before cutoff;
3. derives exact age at cutoff;
4. builds B0/B1 from pre-cutoff evidence only;
5. maps latent predictions into the actual future target level;
6. scores every eligible core event in the next 90 days;
7. persists aggregate, level, transition, age-band, evidence-band, component, and reliability diagnostics.

Temporal label:

`retrospective_event_cutoff_corrected_history_not_vintage_information_set`

## Three-year fold details

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

The 14 predictor exclusions are fail-closed ambiguous current environments; 8 otherwise had future scoreable evidence.

### 2022-08-01

- predictor/Baseline players: 3,756
- scored players: 3,357
- scored target environments: 4,134
- future core events: 280,640
- B1-B0 log loss: **-0.018520**
- B1-B0 Brier: **-0.004706**
- fixed-strata wins: 21/21
- component wins: 12/12
- Baseline 0 peer pools: 3,676 age+level; 80 same-level fallback; 0 global fallback

### 2023-08-01

- predictor/Baseline players: 3,853
- scored players: 3,418
- scored target environments: 4,154
- future core events: 275,511
- B1-B0 log loss: **-0.018226**
- B1-B0 Brier: **-0.004638**
- fixed-strata wins: 21/21
- component wins: 12/12
- Baseline 0 peer pools: 3,771 age+level; 82 same-level fallback; 0 global fallback

## Calibration

The 2021 gate showed mixed reliability behavior:

- BB/HBP calibration improved materially under B1;
- several contact components improved slightly;
- K expected calibration error worsened slightly even though K proper-score contribution improved;
- several other contact bins also had small calibration deterioration.

The 2022/2023 artifacts persist the same fixed reliability diagnostics, but multi-year calibration has **not yet been promoted to a summarized/frozen conclusion**. Review calibration across folds before any model freeze or post-hoc recalibration.

## What is established

- Universal MLB-through-Rookie data can support a real chronological Current Talent comparison.
- B1 adds predictive signal beyond B0 at three independent seasons with unchanged candidate settings.
- The gain is not confined to MLB, one transition class, one age band, one evidence band, or one profile component.
- Promotions/demotions/MLB transitions can be scored in realized future environments.
- The baseline machinery is production-shaped enough for repeated folds and ablations.

## What is not established

- That the candidate translation layer itself improves predictive scoring versus a simpler/no-translation treatment.
- That the model behaves similarly at May/June/July/September cutoffs.
- That the current half-life/prior-strength/age-band/peer threshold are optimal or should be frozen.
- That calibration is acceptable across years/components.
- That actual-league/season residual effects add value beyond level-only translation.
- That richer process/tracking/scouting evidence is warranted.

## Next gate

1. Implement a clean **translation ablation** while keeping the rest of B0/B1/scoring unchanged.
2. Run translated vs no-translation/simple-observation variants on the fixed 2021–2023 Aug. 1 folds.
3. Then add additional in-season cutoffs with the current fixed baseline settings.
4. Only after those stability gates, compare a small predeclared hyperparameter set chronologically.
5. Freeze the simple baseline before adding Baseline 2 or richer evidence.

Do not skip directly to Projection, playing time, WAR/value, or ranking.
