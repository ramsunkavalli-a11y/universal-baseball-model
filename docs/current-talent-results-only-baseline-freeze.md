# Current Talent universal results-only baseline freeze

Last updated: 2026-08-16  
Status: **FROZEN as the universal results-only Current Talent comparator.**

## Decision

Freeze **Baseline 2 `translated_multiseason_recency_empirical_bayes_v1`** as the results-only comparator that richer process, tracking, or scouting Current Talent models must beat out of time.

Frozen settings:

- core batting profile: the existing 12 Current Talent components;
- player-specific history: up to **1,095 calendar days** of eligible certified results evidence;
- recency half-life: **180 days**;
- environment translation: the existing fitted training-only MLB-anchored translation;
- empirical-Bayes prior strength: **100 effective core events**;
- Baseline 0 prior: existing leave-one-out age + current-level prior with 2-year age band and minimum 12 preferred peers;
- target: existing 90-day future eligible event profile;
- all existing observation, identity, source-authority, temporal, translation, target-environment, and scoring rules remain unchanged.

The prior frozen season-to-date B1 `hl180_ps100_fitted` remains a useful simpler reference but is no longer the strongest required results-only comparator for richer challengers.

## Evidence for freeze

### 2022 development

B2 versus frozen B1:

- mean log-loss delta: **-0.002622**;
- mean Brier delta: **-0.000491**;
- fold wins: **3/3** on both proper scores;
- no meaningfully supported non-MLB level reversal;
- calibration intercept and slope improved materially.

Development checkpoint: `docs/current-talent-baseline2-development-checkpoint.md`.

### Held-out 2023 confirmation

The exact fixed challenger then confirmed without parameter search or reselection:

- mean log-loss delta: **-0.003005**;
- mean Brier delta: **-0.000574**;
- fold wins: **3/3** on both proper scores;
- no meaningfully supported non-MLB level reversal;
- component Brier wins: **36/36**;
- component log-loss wins: **25/36**;
- calibration intercept and slope again improved materially.

Confirmation checkpoint: `docs/current-talent-baseline2-confirmation-checkpoint.md`.

### Combined six-fold view

Across 2022 development plus 2023 confirmation:

- B2 beats B1 in **6/6** folds on log loss;
- B2 beats B1 in **6/6** folds on Brier;
- mean log-loss delta: **-0.002814**;
- mean Brier delta: **-0.000532**;
- component log-loss wins: **51/72**;
- component Brier wins: **72/72**;
- mean absolute calibration-intercept error improves **0.5233 -> 0.3676**;
- mean absolute calibration-slope error improves **0.1917 -> 0.1386**;
- fixed-bin ECE is effectively unchanged overall (**0.002560 vs 0.002563**).

## What the freeze means

The project now has two stable results-only reference points:

1. **B1 — simple season-to-date reference:** `hl180_ps100_fitted`;
2. **B2 — required universal results-only comparator:** multi-season 1,095-day history with the same 180-day decay / 100-event shrinkage / fitted translation.

Richer models must be judged primarily against B2. B1 remains useful for attribution: it can show whether a richer model is merely recovering information that prior-season results already capture.

## Freeze boundary

Do **not** tune B2 in response to a process/tracking/scouting challenger. Proposed changes to:

- historical lookback;
- half-life;
- prior strength;
- component-specific shrinkage;
- recalibration;
- translation;
- age/level prior construction;

are separate challengers and require their own leakage-safe chronological validation.

This freeze still does not complete Current Talent or the overall ranking system. Unresolved work includes:

- richer process / tracking / scouting evidence;
- final uncertainty model;
- Projection / aging / development;
- playing time / role;
- defense;
- WAR / value;
- final ranking.

## Next gate

Inventory mature reusable public sources/packages for the first richer evidence family before building raw-source cleanup.

Because feature availability can differ materially by league, the next design must explicitly measure source capability by MLB / AAA / AA / High-A / Single-A / Rookie Complex / DSL where applicable. Do not fabricate missing lower-level tracking inputs from MLB distributions.

Preferred architecture if coverage is heterogeneous:

- B2 remains the universal fallback for every eligible player;
- richer evidence is applied only where genuinely observed and validated;
- incremental validation is reported both on the richer-evidence eligible population and by league/source-capability tier;
- a richer model is promoted only if its gain is not merely an MLB-only artifact and its missing-data behavior is explicit.
