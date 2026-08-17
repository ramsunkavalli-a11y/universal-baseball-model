# Current Talent Baseline 0 / Baseline 1 checkpoint

Last updated: 2026-08-16  
Status: **implementation primitives complete and unit-tested; real chronological future-target scoring not yet run.**

This checkpoint records the first results-only Current Talent estimators required by `docs/current-talent-validation-contract.md`. It does **not** promote either baseline as the final Current Talent model.

## Scope

Implemented:

- exact age-as-of enrichment from the pinned Chadwick Register identity source;
- recency-weighted player × level predictor evidence;
- translation of each level segment to the common MLB latent profile scale **before** multi-level aggregation;
- Baseline 0: leave-one-out age + current-level population prior;
- Baseline 1: empirical-Bayes shrinkage of translated player evidence toward Baseline 0;
- deterministic regression tests for translation direction, level aggregation, leave-one-out prior construction, fallback behavior, and shrinkage.

Not yet implemented or validated in this checkpoint:

- materialized real 2021 Baseline 0/1 predictions;
- mapping latent MLB-scale predictions into each actual future target environment for likelihood scoring;
- 90-day log loss, Brier score, calibration, and transition-stratified validation;
- rolling-origin comparison across multiple cutoffs/seasons;
- tuning or freezing the age-band width, peer threshold, recency window, or prior strength;
- Baseline 2 or richer process/tracking/scouting features.

## Age-as-of dependency

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — manual-only after bootstrap

Age is derived from Chadwick `birth_year`, `birth_month`, and `birth_day` at the explicit snapshot cutoff. A mutable current-age field is not stored.

Failure policy:

- complete, valid DOB -> exact age-as-of;
- partial/missing DOB -> age remains unavailable; no silent imputation;
- duplicate requested MLBAM identities -> fail closed;
- invalid complete DOB -> fail closed.

### 2021-08-01 universal training-population audit

Run: `31992658592`

- training players: **4,315**
- exact DOB / exact age-as-of: **4,315**
- exact-age coverage: **100.0%**
- missing exact age: **0**
- observed age range: approximately **16.93–41.54 years**

Therefore the first 2021 baseline fit does not require an age-imputation branch.

## Common latent reporting scale

Baseline evidence is represented on the 12-component core profile defined by the Current Talent contract:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

The candidate environment translation remains `matched_adjacent_stint_clr_wls_v1`, fitted from training-only evidence with MLB as the zero-effect anchor.

A critical ordering rule is now explicit in code:

> **Translate each player × level segment to MLB scale before pooling a player's evidence across levels.**

Applying one level adjustment after AAA/AA/etc. evidence has already been combined would use the wrong environment for at least part of the evidence and is not compositionally valid.

Implementation:

- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_translation.py`

Translation of a player × level profile:

1. recency-weight eligible pre-cutoff core-profile counts;
2. aggregate at player × level × core-bin grain;
3. apply the same symmetric CLR pseudocount used by the translation candidate (`0.5`);
4. convert observed level profile to CLR;
5. subtract the fitted environment effect for that level;
6. softmax back to MLB-scale component probabilities;
7. retain the segment's effective core-event total;
8. combine already-translated segments by effective evidence.

## Baseline 0 — leave-one-out age + current-level population prior

Method ID: `loo_age_level_population_prior_v1`

Purpose: provide a transparent population prior without using the predicted player's own recent Performance.

Current primitive:

- exact age-as-of;
- actual unambiguous as-of level;
- default age-band width: **2.0 years**;
- preferred peer pool: same current level + same age band;
- minimum preferred leave-one-out peers: **12**;
- if the preferred pool is too small, fall back to all other players at the same current level;
- if the level has no other eligible player, fall back to all other eligible players;
- the predicted player is explicitly excluded from every peer pool;
- peer evidence is already translated to the common MLB latent scale.

The fallback source and peer count are retained in the output so sparse-prior behavior is observable rather than hidden.

This is the first implementation of the contract's environment prior. The defaults are **candidate hyperparameters**, not frozen choices. Explicit league/season/context residual terms have not yet earned inclusion through out-of-time validation.

## Baseline 1 — translated recency empirical Bayes

Method ID: `translated_recency_empirical_bayes_v1`

Purpose: add the player's own simple results-only evidence while remaining interpretable and universally available.

Current primitive:

- player's eligible pre-cutoff core Performance only;
- recency weighting supplied by the chosen `EvidenceWindow`;
- per-level translation to MLB latent scale before aggregation;
- empirical-Bayes shrinkage toward Baseline 0;
- default prior strength: **100 effective core events**.

For component `k`:

`Baseline1_k = (translated_player_count_k + prior_strength * Baseline0_k) / (player_effective_core_events + prior_strength)`

The 12 Baseline 0 probabilities and 12 Baseline 1 probabilities are required to sum to one for each player.

No pitch tracking, bat/swing metrics, scouting grades, playing-time variables, projection aging, WAR, or ranking inputs are allowed in this baseline.

## Tests / CI

Regression tests: `tests/test_current_talent_baselines.py`

Covered behaviors include:

- zero environment effect preserves the smoothed profile and evidence total;
- fitted level effect is removed in the correct translation direction;
- already-translated level segments aggregate by effective evidence;
- Baseline 0 is genuinely leave-one-out;
- age-level fallback occurs only when required;
- Baseline 1 lies between the population prior and sufficiently different player evidence under positive shrinkage;
- component probabilities reconcile to one.

Baseline implementation CI: **`31992880494` — passed.**

## Interpretation

This milestone closes an implementation gap, not a model-selection gate.

We now have deterministic machinery to produce the two simple predictors the governing contract requires advanced models to beat. We **do not yet know** whether:

- the candidate MLB translation improves future prediction;
- Baseline 1 beats Baseline 0 out of time;
- the current recency weighting or 100-event prior strength is appropriate;
- age bands add meaningful predictive value beyond level;
- noisy contact-shape translation components should remain in the same form.

Those questions must be answered with chronological future outcomes, not in-sample fit aesthetics.

## Next gate

1. Materialize real universal Baseline 0 / Baseline 1 predictions for `2021-08-01` using only pre-cutoff evidence and a translation fit trained only on eligible history.
2. Map each latent MLB-scale profile into the **actual future environment** in which each target observation occurs.
3. Score the next-90-day target with multinomial/component log loss, Brier score, and calibration; stratify by level, age, evidence, and promotion/demotion transition.
4. Compare at minimum environment-prior vs translated empirical-Bayes variants before changing model complexity.
5. Repeat at later chronological cutoffs before freezing any hyperparameter or promoting a baseline.
