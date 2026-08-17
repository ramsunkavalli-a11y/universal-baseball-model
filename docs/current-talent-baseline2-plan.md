# Current Talent Baseline 2 challenger plan

Last updated: 2026-08-16  
Status: **PREDECLARED BEFORE BASELINE 2 OUT-OF-TIME EVALUATION.**

## Purpose

Baseline 2 is the final simple **results-only** Current Talent baseline required by `docs/current-talent-validation-contract.md` before process / tracking / scouting evidence is added.

It answers one narrow baseball question:

> Does carrying a player's prior-season results forward improve our estimate of his present batting talent beyond the frozen season-to-date Baseline 1?

This gate must not add Statcast, swing, pitch-level, scouting, projection, playing-time, defense, or WAR information.

## Frozen comparator

Comparator: **`hl180_ps100_fitted`** from `docs/current-talent-simple-baseline-freeze.md`.

Keep unchanged:

- 12-component batting profile;
- 180-day recency half-life;
- fitted training-only level translation;
- Baseline 0 age+level prior construction;
- 100 effective-core-event empirical-Bayes prior strength;
- 90-day future target;
- observation, identity, source-authority, scoring, calibration, and target-environment rules.

The comparator remains season-to-date because its certified validation inputs were one season at a time. Do not silently give Baseline 1 prior-season evidence.

## Baseline 2 challenger

Working method name: **`translated_multiseason_recency_empirical_bayes_v1`**.

The only intended modeling change is the predictor evidence history:

- Baseline 1: eligible evidence from the current season only;
- Baseline 2: eligible evidence from the current season plus prior certified seasons, up to a maximum 1,095-day lookback;
- every event is still weighted by the frozen 180-day exponential half-life;
- player × level evidence is translated before pooling exactly as in Baseline 1;
- the same fold-specific fitted translation offsets used by the comparator are used for the challenger, so this test does not simultaneously test a new translation model;
- the same frozen Baseline 0 prior is used for both comparator and challenger, so the only difference is player-specific historical evidence;
- the same 100-event prior strength is used after evidence aggregation.

For a player with no eligible prior-season evidence, Baseline 2 must equal Baseline 1 to numerical tolerance.

### Why 1,095 days

The governing contract called for a recency-weighted 2–3 year history where available. A three-year calendar cap makes the historical boundary explicit while the 180-day half-life naturally gives much less weight to old performance. This is not a new tuned hyperparameter in this gate; no alternate lookback caps will be searched before confirmation.

## Data / reuse policy

No new raw baseball source is required for this challenger.

Reuse the already certified universal player-game Current Talent evidence for 2021–2023 and concatenate seasons before predictor construction. `combine_universal_player_game_evidence` already accepts an explicit set of expected seasons, and the existing recency-weighted evidence builder operates on game dates rather than assuming one season.

Do not rebuild play-by-play parsing for Baseline 2.

## Coverage and league policy

Baseline 2 remains a **universal MLB-through-affiliated-minors baseline**. It uses only the same results evidence family available across the universal surface.

League-specific richer evidence is deliberately deferred to the next gate. When process / tracking evidence is introduced later, missing lower-level features must not be imputed from MLB distributions. A future richer model may therefore be tiered by source capability, but its fallback for players without richer evidence should be the best validated universal results-only baseline.

## Chronological evaluation

### Development

Use only the three 2022 folds:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

Predictor evidence may use certified 2021 evidence plus pre-cutoff 2022 evidence. Future 2022 target events remain forbidden from predictors.

The 2021 folds are not informative for the incremental historical question because the certified bundle begins in 2021. They may be used only as an implementation invariant showing that the challenger collapses to the frozen comparator when no prior season is supplied.

### Confirmation

Hold the three 2023 folds untouched while implementing and assessing the 2022 development result:

- 2023-07-15;
- 2023-08-01;
- 2023-09-01.

For confirmation, predictor evidence may use certified 2021–2022 history plus pre-cutoff 2023 evidence. Do not search alternative historical windows, half-lives, priors, or translation variants on 2023.

If the predeclared challenger fails confirmation, reject it. Do not reselect a nearby historical weighting using 2023.

## Primary comparison

Compare **Baseline 2 directly with the frozen Baseline 1 comparator** on identical scored players, target environments, and future core events.

Primary metric:

1. equal-fold mean event-weighted multinomial log loss.

Secondary proper score:

2. equal-fold mean event-weighted multinomial Brier score.

Also retain component, level, age, evidence-volume, prior-MLB-evidence, and promotion/demotion diagnostics under the existing scoring contract.

## Development promotion rule

Proceed to 2023 confirmation only if all of the following hold on the three 2022 development folds:

1. Baseline 2 has lower equal-fold mean log loss than Baseline 1;
2. Baseline 2 has no worse equal-fold mean Brier score than Baseline 1;
3. Baseline 2 wins log loss in at least 2 of 3 folds;
4. scored coverage is identical between the two models;
5. the aggregate gain is not solely an MLB artifact: a non-MLB level is considered meaningfully supported when it contributes at least **1,000 future core events across the three development folds**; no such level may show Baseline 2 worse than Baseline 1 on both proper scores in at least 2 of 3 folds;
6. all component calibration fits converge, and Baseline 2's equal-fold mean absolute calibration-intercept error and absolute calibration-slope error are each no more than **25% worse** than Baseline 1. Fixed-bin ECE is reported but is not a hard gate because the frozen-baseline calibration review already showed that ECE can move differently from intercept/slope calibration.

If these conditions fail, Baseline 2 is not promoted and the frozen Baseline 1 remains the universal results-only baseline.

## 2023 confirmation rule

Confirmation passes only if:

1. Baseline 2 retains lower equal-fold mean log loss than Baseline 1;
2. Baseline 2 retains no worse equal-fold mean Brier score than Baseline 1;
3. coverage remains identical;
4. for non-MLB levels with at least **1,000 future core events across the three confirmation folds**, no level shows Baseline 2 worse on both proper scores in at least 2 of 3 folds;
5. all component calibration fits converge, and Baseline 2's equal-fold mean absolute calibration-intercept and slope errors are each no more than **25% worse** than Baseline 1;
6. component diagnostics show no new broad failure that overturns the aggregate result.

A tiny confirmation edge may still be rejected on simplicity grounds if it is unstable across folds or concentrated in one narrow stratum. Baseline 2 is not entitled to promotion merely because it has more history.

## Implementation invariants

Before a live development run, deterministic tests must establish:

- cross-season events before the cutoff are included;
- events after the cutoff are excluded regardless of season label;
- 180-day weighting is continuous across December/January rather than resetting at Opening Day;
- the 1,095-day cap excludes older evidence;
- player × level translation still precedes cross-level pooling;
- Baseline 0 prior is shared between comparator and challenger;
- players lacking prior-season evidence receive identical B1/B2 profiles;
- candidate score coverage cannot change merely because historical evidence was added.

## What comes after Baseline 2

Only after this gate is resolved should the project test richer evidence such as exit velocity / contact quality, swing decisions, whiff/contact process, bat speed, pitch-level information, or scouting data.

Those inputs may have materially different coverage by league. The richer-evidence design should therefore start with a source-capability inventory and explicitly decide whether the architecture is:

- universal feature set only;
- tiered richer model with Baseline 2 fallback;
- or separate validated challengers for evidence-rich populations.

Do not force unavailable lower-level tracking features into a universal matrix through synthetic imputation.
