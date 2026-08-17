# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **first real 2021 chronological predictive gate passed; rolling-origin stability and hyperparameter/translation ablation remain required before promotion.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md` and their first real future-outcome test. It does **not** promote either baseline as the final Current Talent model.

## Current conclusion

At the `2021-08-01` cutoff, using only eligible pre-cutoff evidence and a translation fit trained only on pre-cutoff history, **Baseline 1 beats Baseline 0 on both event-weighted log loss and multinomial Brier over 344,391 realized future core events in the next 90 days**.

The gain is broad:

- all 6 target levels;
- all 5 aggregate transition classes represented;
- all 5 fixed age bands;
- all 5 fixed evidence-volume bands;
- all 12 core profile components.

But calibration is not uniformly better component-by-component, and this is still only one cutoff. Therefore the correct status is **first chronological gate passed, not model frozen**.

Primary diagnostic run: **`31993773737`**  
First successful scoring run: `31993534180`  
Workflow: `.github/workflows/current-talent-baseline-validation.yml` — **manual-only** after bootstrap cleanup.

## Scope implemented

- exact age-as-of enrichment from the pinned Chadwick Register;
- recency-weighted player × level predictor evidence;
- training-only MLB-anchored environment translation;
- translation of each player × level segment before multi-level aggregation;
- Baseline 0 leave-one-out age + current-level population prior;
- Baseline 1 empirical-Bayes shrinkage of translated player evidence toward Baseline 0;
- forward mapping from latent MLB scale into each realized future target level;
- exact aggregate-event multinomial log loss and multinomial Brier;
- fixed reliability-bin calibration diagnostics;
- target-level, transition, age-band, evidence-band, and component diagnostics;
- deterministic regression tests for estimator and scoring contracts.

Implementation:

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `tests/test_current_talent_baselines.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`

## Age-as-of dependency

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — manual-only

Age is derived from Chadwick `birth_year`, `birth_month`, and `birth_day` at the explicit snapshot cutoff. A mutable current-age field is not stored.

Failure policy:

- complete valid DOB -> exact age-as-of;
- partial/missing DOB -> unavailable, no silent imputation;
- duplicate requested MLBAM identities -> fail closed;
- invalid complete DOB -> fail closed.

### 2021-08-01 coverage

Run: `31992658592`

- predictor players: **4,315**
- exact age: **4,315**
- exact-age coverage: **100.0%**
- missing exact age: **0**

## Common latent reporting scale

The model preserves the 12-component core profile:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

The candidate environment translation is `matched_adjacent_stint_clr_wls_v1`, fitted from training-only matched-player transitions with MLB as the zero-effect anchor.

Critical ordering rule:

> **Translate each player × level segment to MLB scale before pooling a player's evidence across levels.**

Applying one environment adjustment after AAA/AA/etc. evidence has already been pooled is not compositionally valid.

Player × level translation:

1. recency-weight eligible pre-cutoff core-profile counts;
2. aggregate at player × level × core-bin grain;
3. apply symmetric CLR pseudocount `0.5`;
4. convert observed level profile to CLR;
5. subtract the fitted environment effect for that level;
6. softmax back to MLB-scale component probabilities;
7. retain the segment's effective core-event total;
8. combine already-translated segments by effective evidence.

For future scoring, the direction is reversed:

`CLR(observed future profile at L) = CLR(latent MLB-scale profile) + fitted_beta[L]`

then softmax back to target-level probabilities.

## Baseline 0 — leave-one-out age + current-level prior

Method ID: `loo_age_level_population_prior_v1`

Purpose: transparent population prior without using the predicted player's own recent Performance.

Current candidate settings:

- exact age-as-of;
- actual unambiguous as-of level;
- age-band width: **2.0 years**;
- preferred peer pool: same current level + same age band;
- minimum preferred leave-one-out peers: **12**;
- fallback to other players at same level, then global others only if necessary;
- predicted player explicitly excluded from every peer pool;
- peer evidence already translated to the MLB latent scale.

2021 real gate peer usage:

- age + level pool: **4,256 players**;
- same-level fallback: **45 players**;
- global fallback: **0**.

The fallback source and peer count are persisted per player.

## Baseline 1 — translated recency empirical Bayes

Method ID: `translated_recency_empirical_bayes_v1`

Current candidate:

- season-to-date eligible pre-cutoff Performance;
- **90-day half-life** recency weighting;
- per-level translation to MLB latent scale before aggregation;
- empirical-Bayes shrinkage toward Baseline 0;
- **100 effective core events** of prior strength.

For component `k`:

`Baseline1_k = (translated_player_count_k + prior_strength * Baseline0_k) / (player_effective_core_events + prior_strength)`

The 12 Baseline 0 and Baseline 1 probabilities must each sum to one per player.

No pitch tracking, bat/swing metrics, scouting grades, playing-time variables, projection aging, WAR, or ranking inputs enter these baselines.

**The 90-day half-life, 100-event prior strength, 2-year age band, and 12-peer threshold remain candidate hyperparameters.** They were not selected by searching the 2021 future target.

## First real chronological gate

### Design

Cutoff: `2021-08-01`  
Primary future horizon: next 90 calendar days.

The live materializer:

1. loads certified 2021 evidence for MLB + AAA + AA + High-A + Single-A + Rookie/complex;
2. combines it into one universal player-game surface;
3. fits environment translation on games strictly before `2021-08-01`;
4. builds leakage-safe predictor and future-target surfaces;
5. derives exact age at the cutoff;
6. builds Baseline 0 and Baseline 1 from pre-cutoff evidence;
7. maps each latent prediction into the actual future target level;
8. scores every realized eligible future core event;
9. persists all inputs, predictions, scores, reliability tables, and diagnostics.

Temporal label remains:

`retrospective_event_cutoff_corrected_history_not_vintage_information_set`

### Coverage

Universal evidence loaded:

- **4,715 players**
- **231,999 player-games**
- **886,178 PA**
- **863,851 core events**

Pre-cutoff predictor population:

- **4,315 players**
- exact age for all 4,315
- **4,301** receive Baseline 0 / Baseline 1 profiles
- 14 are excluded because current environment is ambiguous under the fail-closed as-of rule

Future target / scoring:

- target players: **4,130**
- target players without predictor evidence: **400** — coverage only, not poor talent
- raw validation players with predictor + future target: **3,730**
- baseline-scored players: **3,722**
- 8 of the otherwise-scoreable players are among the 14 ambiguous-environment exclusions
- scored target-environment rows: **4,634**
- future core events scored: **344,391**

### Aggregate proper scores

| Model | Event-weighted log loss | Multinomial Brier |
|---|---:|---:|
| Baseline 0 | 2.268828 | 0.872730 |
| Baseline 1 | **2.252931** | **0.868446** |

Baseline 1 minus Baseline 0:

- log loss: **-0.015896**
- Brier: **-0.004284**

Lower is better.

### Breadth of gain

The diagnostic run persists four separate descriptive strata rather than relying only on sparse cross-products.

Baseline 1 improves both log loss and Brier in **21 / 21 separate strata**:

- target level: **6 / 6**;
- transition class: **5 / 5**;
- fixed age band: **5 / 5**;
- fixed effective-evidence band: **5 / 5**.

Transition classes represented:

- `SAME_LEVEL`
- `PROMOTION`
- `DEMOTION`
- `MLB_DEBUT`
- `MLB_TO_MILB`

It also improves both proper-score contributions in **12 / 12 core profile components**.

Largest log-loss contribution improvements include K, center-groundball, pull-groundball, opposite-groundball, and BB/HBP. Every remaining component is still positive for Baseline 1.

The evidence-volume pattern is directionally sensible for empirical Bayes: Baseline 1's advantage is smallest below 25 effective core events and increases with player evidence.

Do **not** translate this into a claim that every tiny level × transition cell wins. Sparse cross-product cells are noisy; the persisted 21/21 claim refers to the separate fixed strata above.

## Calibration

Reliability uses fixed 10-bin component calibration diagnostics.

The first gate shows a mixed calibration result:

- BB/HBP calibration improves materially under Baseline 1;
- several contact components improve slightly;
- K expected calibration error worsens slightly even though K proper-score contribution improves;
- several other contact bins also show small calibration deterioration.

This is why Baseline 1 is **not yet frozen**. Proper-score gains are broad, but calibration behavior must survive later chronological folds and may require different shrinkage/translation choices rather than a post-hoc cosmetic fix.

## Tests / CI

Baseline primitive CI: `31992880494` — passed.

The live diagnostic gate also ran the targeted regression suite:

- baseline tests;
- target-environment scoring tests;
- score-diagnostic tests;
- translation tests;
- Chadwick age tests.

Diagnostic run `31993773737`: **21 targeted tests passed before live materialization**, then the full real gate completed successfully and uploaded its artifact.

## What this gate does and does not establish

Established:

- the universal data surfaces can support a real chronological Current Talent comparison;
- Baseline 1 adds predictive information beyond Baseline 0 at this cutoff;
- the gain is not confined to MLB, one transition class, one age band, one evidence band, or one profile component;
- the scoring direction for promotions/demotions works on real data;
- the baseline machinery is production-shaped enough for repeated folds.

Not established:

- that 90-day half-life is optimal;
- that 100 effective events is the right EB prior strength;
- that age-band width / peer threshold are optimal;
- that the translation candidate adds value versus a simpler/no-translation treatment;
- that Baseline 1 wins in later seasons/cutoffs;
- that calibration is acceptable enough to freeze the baseline;
- that richer inputs are warranted.

## Next gate

1. Repeat the exact baseline gate on **independent later chronological cutoffs/seasons**, using the certified 2022/2023 evidence.
2. Compare a small **predeclared** set of simple recency windows / prior strengths inside chronology instead of tuning to 2021-08-01.
3. Add a translation ablation so the predictive value of the observation layer is measured directly.
4. Require stable proper-score and calibration behavior across years, levels, evidence bands, and transitions.
5. Freeze the simple baseline only after those gates pass.
6. Only then test Baseline 2 or richer process/tracking/scouting evidence.

Do not skip directly to Projection, playing time, WAR/value, or ranking.
