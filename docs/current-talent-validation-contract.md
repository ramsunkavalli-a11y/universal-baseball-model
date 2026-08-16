# Current Talent Validation Contract — Proposed

Last updated: 2026-08-16  
Status: **Proposed; do not promote a Current Talent model until these gates are implemented and passed.**

## Purpose

Current Talent is the second layer of the universal player model. It answers:

> **Given all eligible evidence available at an as-of date, what rate/profile ability does this player possess now, conditional on receiving baseball opportunities?**

It is not:

- observed Performance;
- a future aging/development projection;
- playing-time or role probability;
- WAR / roster value;
- prospect status;
- an overall ranking.

The separation is deliberate. Performance is what happened in context. Current Talent is a regressed, translated estimate of present latent ability. Projection later moves that ability through future time and separately models opportunity/role.

## Primary batting representation

The first batting Current Talent model should preserve the Performance profile rather than compressing all evidence into one noisy scalar.

### Core latent profile

Estimate a player-specific probability/rate profile over the frozen core Performance evidence:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

A scalar MLB-equivalent expected run value per 100 PA is derived from the profile and the frozen contextual value layer; it is **secondary to the component/profile fit**.

### Non-core / coverage channel

Bunts, confirmed foul-air exclusions, special events, and unknown/conflicted evidence remain outside the core talent profile and are reported separately. Missing/structurally unavailable evidence must never be redistributed across core bins merely to make probabilities sum over all PA.

At minimum expose:

- core-profile coverage;
- non-core event rate;
- unknown/conflict rate;
- effective evidence / sample size;
- participant-authority and source-coverage diagnostics.

## Common MLB-through-DSL scale

A universal Current Talent score cannot compare raw AA and MLB Performance directly. The baseline must learn an **observation/translation layer by competitive environment**.

Conceptually:

`observed core profile at environment L = latent player profile + environment/level effect + season/context effect + noise`

with MLB as the reporting anchor.

Initial translation policy:

1. estimate level/environment effects only from training-period data;
2. prefer matched-player transitions and repeated-player evidence across levels;
3. do not use a player's held-out future destination performance to construct that player's predictor at the earlier cutoff;
4. keep actual league/season environment effects available rather than replacing them with a single static level constant when data support that distinction;
5. never infer missing lower-level tracking/process features from MLB distributions;
6. report translation uncertainty, especially for sparse Rookie/DSL bridges.

The exact statistical form is a model choice to be validated. The contract only requires leakage-safe common-scale translation.

## As-of semantics

Every training/evaluation row has an explicit `as_of_date`.

### Initial validation mode

Use **retrospective event-cutoff** semantics first:

- predictors can use only baseball events whose `occurred_at <= as_of_date`;
- corrected historical source values are allowed where that is all the public history supports;
- results must be labeled retrospective event-cutoff, **not vintage/as-of information-set**.

### Strict vintage mode

Where source `known_at` history is proven, a stricter vintage-information-set evaluation can be added. Null/unknown historical source availability is ineligible for that stricter label.

No model comparison may mix the two semantics without an explicit flag.

## Snapshot cadence

Initial batting validation should use repeated in-season and offseason snapshots rather than season-end-only rows.

Recommended deterministic cadence:

- monthly in-season cutoffs, approximately the first day of May through September;
- one offseason / preseason cutoff where historical data coverage permits;
- multiple seasons in chronological rolling-origin folds.

A season-end-only benchmark should also be retained because it is simple and easy to reproduce, but it is insufficient by itself for a model intended to update during a season.

## Future targets

Current Talent is latent and cannot be observed directly. Validation therefore uses **subsequent rate/profile outcomes as noisy measurements of the earlier latent estimate**, not as a claim that future performance literally equals current talent.

### Primary short-horizon target

For each as-of snapshot, score future eligible batting opportunities during the next **90 calendar days**, capped at **200 PA per player** for the primary aggregate-rate diagnostic.

Why:

- short enough to reduce future aging/development contamination;
- long enough to accumulate useful evidence for many active players;
- calendar-defined so the validation window is known before observing future playing time;
- PA cap prevents everyday MLB players from dominating aggregate diagnostics.

All available eligible future PA inside the window contribute to event-likelihood scoring. The 200-PA cap applies only to player-aggregate secondary metrics.

### Secondary horizons

Also report:

- 30-day future outcomes — more "current", much noisier;
- 180-day future outcomes — more stable, more development/aging contamination;
- next-season / ~365-day outcomes — a bridge benchmark only, **not** the primary Current Talent objective because it begins to overlap Projection.

A model need not win every horizon, but tradeoffs must be visible.

## Playing time and censoring

Current Talent is **conditional on receiving opportunities**.

Therefore:

- a player with zero future PA is not assigned a bad batting target;
- injury, release, retirement, roster status, and manager opportunity are not silently treated as batting skill;
- rate-model metrics are computed on realized future opportunities;
- future-opportunity availability is reported separately by age, level, and talent/evidence strata;
- survivor/censoring sensitivity must be reported, especially for lower minors;
- a future Playing Time / Role model will explicitly model opportunity probability.

For player-aggregate metrics, always report the distribution of future PA and minimum-PA sensitivity (for example >=25, >=50, >=100) instead of selecting one flattering threshold.

## Promotion / demotion handling

Future outcomes are scored at the **environment in which they actually occur**. A promotion is not an error and a demotion is not a special target class.

The Current Talent model must predict a common latent profile and use the observation/translation layer to map that latent estimate to the target environment for likelihood scoring.

This is preferable to evaluating only players who remain at the same level, which would bias the sample toward organizational decisions and survivor status.

Stratified reports should still show:

- same-level future PA;
- promotion future PA;
- demotion future PA;
- MLB debut transitions;
- MLB-to-MiLB option transitions.

## Baselines that advanced models must beat

### Baseline 0 — environment prior

Age + competitive environment + season/context only. No player-specific recent performance.

Purpose: quantify how much information comes merely from knowing where/when a player is competing.

### Baseline 1 — Marcel-style player evidence

Simple, transparent empirical-Bayes baseline:

- recent Performance component rates;
- recency weighting;
- regression toward an age/environment prior;
- explicit sample/effective-evidence strength;
- leakage-safe environment translation to MLB reporting scale.

No pitch tracking, swing metrics, scouting grades, or complicated latent features.

### Baseline 2 — simple multi-season profile

Adds multiple prior windows / seasons but remains results-only.

Every richer process, pitch-level, tracking, or scouting enhancement must demonstrate incremental out-of-time value over these baselines.

## Player evidence windows

Do not decide a single recency half-life by intuition.

Candidate simple baselines should compare at least:

- current season / recent 90 days;
- rolling 365 days;
- recency-weighted 2–3 year history where available.

The selected form must be chosen inside training folds and confirmed on later chronological data. Current Talent may legitimately prefer different recency by component (for example K vs batted-ball direction), but extra complexity must earn its place.

## Age

Age may inform **present latent talent conditional on observed level/performance** because a 20-year-old and 30-year-old producing the same observed line at the same level need not carry identical priors.

However:

- Current Talent does not apply future aging curves;
- future age/development change belongs to Projection;
- age effects must be learned on training data only;
- age should not be allowed to dominate strong direct evidence merely because a player is atypical for his level.

## Evidence strength and uncertainty

Every Current Talent output must include uncertainty/evidence fields, not an opaque confidence score.

Minimum fields:

- raw eligible PA / core events;
- effective recency-weighted PA;
- core-profile coverage;
- number of seasons / time span contributing;
- source capability tier;
- level-translation evidence strength;
- posterior / bootstrap / model interval for scalar talent;
- component-profile uncertainty where computationally practical;
- flags for sparse or structurally unavailable evidence.

High uncertainty is an output property, not a reason to fabricate missing features.

## Validation folds

Use rolling-origin chronology. A fold may train/tune only on snapshots and outcomes strictly before its evaluation period.

Illustrative shape once sufficient historical Performance materialization exists:

- train through 2022 -> validate 2023 snapshots;
- train through 2023 -> validate 2024 snapshots;
- train through 2024 -> validate 2025 snapshots;
- final untouched confirmation on the latest completed eligible period.

Exact years depend on data coverage and the date the model is built. Do not randomly split player-seasons across time.

Players may appear in both train and test in later years; that is intentional for a live updating model. Future observations for that player remain forbidden at the earlier cutoff.

## Primary metrics

### Profile/event metrics

Primary:

- multinomial / component log loss on future core outcomes;
- Brier score or equivalent proper score by component;
- calibration intercept/slope and reliability plots by major component;
- weighted and unweighted player-level diagnostics.

### Scalar diagnostics

Derived MLB-equivalent expected-run-value talent:

- MAE and RMSE versus future contextualized Performance rate;
- rank correlation as a secondary diagnostic;
- calibration by predicted-talent decile;
- interval coverage.

Do not choose a model primarily because it has a prettier correlation if proper scoring/calibration deteriorates.

## Required stratification

Every serious validation report should break out at least:

- MLB / AAA / AA / High-A / Single-A / Rookie-complex / DSL where sample permits;
- age bands;
- evidence-volume bands;
- source capability tier;
- same-level vs promoted/demoted future outcomes;
- handedness where relevant;
- players with and without prior MLB evidence.

Aggregate wins that hide a material failure at a lower level do not qualify as universal improvement.

## Leakage prohibitions

At a snapshot cutoff, predictors may not use:

- events after the cutoff;
- season-end totals containing future events;
- future promotion/demotion level;
- future playing time;
- future scouting/public ranking updates;
- level translations estimated using held-out future periods;
- target-season league/bin values estimated using held-out target outcomes when the evaluation claims true forward prediction.

Environment/run-value tables used for evaluation must be frozen from training history or clearly labeled retrospective descriptive quantities.

## Model-selection rule

A richer Current Talent model is promoted only if it improves the simple baseline **out of time** and the gain is not confined to one evidence-rich level.

Prefer the simpler model when:

- average gains are tiny relative to fold variation;
- calibration worsens;
- lower-level coverage is materially harmed;
- benefits disappear on the latest chronological confirmation;
- the richer model relies on features structurally unavailable to most affiliated players without an explicit tiered architecture.

## First implementation sequence

1. Add MLB Performance to the same 2024 contract so the reporting anchor exists before common-scale talent fitting.
2. Materialize multiple historical seasons of player-game outcome/contact evidence needed for as-of snapshots.
3. Implement deterministic snapshot and future-window builders.
4. Estimate leakage-safe environment translations inside chronological training folds.
5. Fit Baseline 0 and Baseline 1 only.
6. Validate profile proper scores, scalar diagnostics, calibration, promotion transitions, and censoring.
7. Freeze the baseline before adding process/tracking evidence.
8. Add richer evidence in explicit tiers and retain it only if it beats the frozen baseline.

## Relationship to later layers

### Projection

Projection starts from Current Talent and adds:

- future aging/development;
- multi-horizon change;
- role/playing-time probability;
- uncertainty growth through time.

### Player Value

Player Value combines projected rate talent, playing time/role, position/defense, replacement level, and uncertainty into WAR/value-like outputs.

### Overall Ranking

The final ranking consumes Current Talent / Projection / Player Value outputs. It does not directly rank raw Performance tables.
