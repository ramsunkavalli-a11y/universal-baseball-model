# Current Talent richer challenger 2 — contact-value residual plan

Status: **FROZEN BEFORE DEVELOPMENT SCORING**  
Date frozen: 2026-08-17

This document predeclares the second richer Current Talent challenger. It is a new candidate, not a rescue or retune of the rejected contact-shape challenger.

## Why this candidate exists

The first richer challenger, `baseline2_plus_ev_sweet_spot_contact_residual_v1`, asked whether observed mean exit velocity and sweet-spot share improved prediction of B2's ten future contact-direction/trajectory probabilities. It failed its fixed 2022 development gate.

The governing first-challenger plan explicitly reserved a later alternative: use batted-ball quality as a separate **contact-quality/value latent target** rather than silently changing the failed protocol. This document freezes that alternative before any second-candidate 2022 score is computed.

## Candidate identity

Comparator foundation:

`translated_multiseason_recency_empirical_bayes_v1` (frozen Baseline 2)

Incremental candidate:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

The candidate does **not** alter B2's 12-component Current Talent profile. It adds a separate scalar expected value per non-bunt contact for richer-eligible hitters. If the richer term is unavailable, the adjustment is exactly zero.

This development gate is deliberately conditional: it tests whether observed EV/LA predicts future contact value **after conditioning on the future contact's B2 shape bin and level environment**. It is not yet a full Current Talent proper-score comparison and it does not authorize Player Value integration.

## Frozen observed features

Reuse the already-certified challenger-1 tracking layer without a new feature search:

1. **180-day recency-weighted mean exit velocity**;
2. **180-day recency-weighted sweet-spot share**, launch angle 8–32 degrees inclusive.

Rules remain unchanged:

- tracking source epoch: `2021-01-01`;
- 180-day exponential recency half-life;
- observed canonical BBE only;
- no hard-hit rate;
- no barrel rate;
- no xwOBA;
- no max EV / EV90;
- no bat speed or swing length;
- no pitch-process features;
- no scouting/projection inputs;
- no defense, playing-time or WAR input;
- no missing-tracking imputation.

Primary richer eligibility remains **>=20 complete observed canonical tracked BBE before cutoff**.

## Canonical contact universe

Use the already-frozen canonical non-bunt result-producing contact identity:

- valid game / batter / PA / pitch identity;
- result-producing terminal contact;
- bunt excluded;
- one result-producing contact per PA;
- regular-season games only.

For this value gate, a future contact must additionally have:

- a complete frozen B2 core contact bin: `IFFB` or Pull/Center/Oppo × `OFFB`/`LD`/`GB`;
- a terminal official outcome that maps to one of the frozen value groups below;
- a supported level group.

Ambiguous/special terminal outcomes are excluded from the value target for **both** comparator and richer candidate and are reported diagnostically. They may not be silently mapped after development scores are observed.

## Frozen terminal-outcome groups

Map official result events to these context-neutral terminal groups:

- `1B`: `single`
- `2B`: `double`
- `3B`: `triple`
- `HR`: `home_run`
- `ROE`: `field_error`
- `FC_REACH`: `fielders_choice`
- `SF`: `sac_fly`
- `MULTI_OUT`: `double_play`, `grounded_into_double_play`, `sac_fly_double_play`, `triple_play`
- `OUT`: `field_out`, `fielders_choice_out`, `force_out`

Bunts remain excluded. A new/unmapped terminal contact event fails closed for target construction and is surfaced in the source report.

## Fixed contact-value scale

Actual per-event RE24 is contextual and is **not** a player-talent target.

Instead, build one context-neutral MLB-scale terminal-outcome value table:

1. use the project's frozen state-transition/RE24 mechanics;
2. use **2021 MLB regular-season state-transition evidence strictly before 2021-07-15**;
3. compute event RE24 from the pre-cutoff MLB run-expectancy matrix;
4. for each frozen terminal-outcome group above, take the event-weighted mean RE24;
5. freeze those nine terminal-group values for the entire 2022 development gate.

The table is an outcome-value scale, not a fitted player model. It must not use any event on or after 2021-07-15 and is not re-estimated from 2022 outcomes.

Reuse the repo's existing state replay and `run_expectancy.py` implementation. Retrosheet is the preferred MLB source for this narrow value-scale job because player identity is unnecessary: only date, regular-season terminal outcome and state transition are needed. If the existing Retrosheet path cannot reproduce the frozen transition semantics, stop at a source-feasibility report rather than substituting a new source silently.

## Conditional B2 contact-value baseline

For each as-of cutoff, fit a deterministic **pre-cutoff-only** contact baseline from certified historical contacts:

`terminal_value ~ contact_bin + level_group`

where:

- `terminal_value` is the fixed MLB-scale value assigned from the frozen terminal-outcome table;
- `contact_bin` is the ten-bin B2 non-bunt contact shape;
- `level_group` is the project's canonical level group;
- all terms are categorical fixed effects;
- event weighting is one weight per contact;
- ordinary least squares only;
- no interactions;
- no player terms;
- no shrinkage or regularization;
- no penalty search.

Reference coding is deterministic:

- reference contact bin: `IFFB`;
- reference level group: `MLB`;
- intercept included.

The fit uses all eligible regular-season historical contact events with event date strictly before the snapshot cutoff and source epoch >= `2021-01-01`.

This baseline is not a replacement for B2. It is an evaluation control that conditions on the future event's realized contact shape and environment so the richer gate isolates **within-shape contact value**.

## Future target

For each eligible future contact event in the fixed 90-day Current Talent target window:

- assign `terminal_value` from the frozen MLB-scale terminal-outcome table;
- compute `baseline_contact_value` from that cutoff's pre-cutoff `contact_bin + level_group` baseline using the event's realized core bin and level group;
- define

`contact_value_residual = terminal_value - baseline_contact_value`.

Comparator event prediction:

`baseline_contact_value`

Richer event prediction:

`baseline_contact_value + player_contact_value_residual`.

The comparator and richer candidate therefore have identical target-event coverage. The use of realized future contact bin is intentional: this is a controlled incremental test of value conditional on contact shape, not a claim that B2 knew the future bin.

## Richer residual fit

Fit exactly two coefficients from the frozen 2021 training snapshot.

Training snapshot:

`2021-07-15`

Feature standardization:

- use richer-eligible training players only;
- standardize weighted mean EV and sweet-spot share to z-scores using the same deterministic player-level standardization convention as challenger 1;
- save means/scales in the artifact;
- zero-variance feature fails closed.

Model:

`player_contact_value_residual = beta_EV * z_EV + beta_SS * z_SS`

Rules:

- no intercept;
- no interactions;
- no polynomial terms;
- no regularization;
- no coefficient search;
- weighted least squares, with each training player's weight equal to its number of supported future target contacts;
- mathematically equivalent event-level squared-error fitting because a player's predictors are constant within snapshot;
- require finite full-rank solution; otherwise candidate fails development structurally.

No 2022 future outcome may enter this fit.

## 2022 development chronology

Fit the richer coefficients once from `2021-07-15` + its fixed future target.

Evaluate unchanged on exactly:

- `2022-07-15`
- `2022-08-01`
- `2022-09-01`

At each 2022 cutoff:

- construct features strictly before the cutoff;
- construct that cutoff's `contact_bin + level_group` baseline strictly from pre-cutoff contacts;
- apply the unchanged 2021 richer coefficients;
- score the fixed 90-day future target;
- do not search thresholds, features, groupings, baseline forms or coefficients.

## Primary paired cohort

Primary development scoring includes only future target events for players where the richer adjustment applies at the cutoff:

- player has >=20 complete tracked BBE before cutoff;
- both frozen features are finite;
- target event has supported terminal outcome, core contact bin and level group.

B2/contact-baseline and richer predictions are scored on the exact same event rows.

## Proper scores

Primary score:

**event-weighted mean squared error (MSE)** on `terminal_value`.

Secondary score:

**event-weighted mean absolute error (MAE)**.

For each fold, compute one event-weighted score. Selection across the three folds is the arithmetic mean of fold scores; do not pool all fold events before computing the selection statistic.

MSE is the primary proper loss for the conditional mean target. MAE is a robustness guardrail, not a tuning objective.

## Calibration

For each fold and model, fit the event-weighted calibration regression:

`terminal_value = intercept + slope * predicted_terminal_value`.

Ideal calibration is intercept 0, slope 1.

All required fits must be finite and identifiable.

Report:

- fold intercept/slope;
- mean absolute intercept error across folds;
- mean absolute slope error across folds.

## Capability / MiLB transport

Reuse the tracked-evidence provenance from materialization run `32046012977`.

Report at minimum:

- overall primary paired cohort;
- any-observed-MiLB-richer-evidence cohort;
- each exact non-MLB `source_capability_tier` represented in the paired cohort.

Do not generalize partial 2022 AAA tracking to all AAA.

## Frozen 2022 promotion rule

The candidate is eligible for one fixed 2023 confirmation only if **all** checks pass:

1. richer has lower equal-fold mean event-weighted MSE than the conditional B2 contact-value baseline;
2. richer equal-fold mean MAE is no worse than baseline, tolerance `1e-12`;
3. richer MSE wins at least **2 of 3** development folds;
4. comparator and richer have identical paired event coverage in every fold;
5. the any-observed-MiLB-evidence cohort has at least **1,000 future target contacts** and richer has lower equal-fold mean MSE in that cohort;
6. for every exact non-MLB capability tier with at least **1,000 future target contacts**, fail if richer is worse on **both MSE and MAE in at least 2 of 3 folds**;
7. richer coefficient fit is finite/full-rank;
8. all required calibration fits converge;
9. richer mean absolute calibration-intercept error is <= `1.25 ×` baseline;
10. richer mean absolute calibration-slope error is <= `1.25 ×` baseline.

No ECE threshold is used for this continuous target.

A failed check closes this candidate. Do not alter the feature threshold, outcome groups, OLS baseline, fitting form, or promotion thresholds after seeing 2022 scores.

## If development passes

Only then:

1. refit the unchanged two-coefficient richer form using annual training snapshots `2021-07-15` and `2022-07-15`;
2. refit feature standardization using those training rows under the same convention;
3. keep the frozen terminal-outcome value scale unchanged;
4. confirm exactly once on `2023-07-15`, `2023-08-01`, `2023-09-01`;
5. perform no 2023 search/reselection.

Do not build or run this confirmation before the 2022 gate passes.

## Production boundary

Even if this candidate passes development and confirmation, the resulting scalar initially remains a **separate Current Talent contact-quality dimension**.

It does not automatically:

- modify the frozen B2 12-component probability vector;
- become wOBA/xwOBA;
- change Performance;
- change Projection;
- enter defense/playing time/WAR;
- enter Player Value / Overall Ranking.

A later integration contract must define how a validated scalar contact-value residual combines with B2's predicted contact mixture and target-environment bin values.

## Reuse requirements

Prefer existing solved infrastructure:

- canonical B2/Performance contact-bin classification;
- `src/universal_baseball/run_expectancy.py` and frozen state-transition mechanics;
- existing Retrosheet capture/parser path for the narrow MLB value-scale table;
- `armstjc/milb-data-repository` historical 2021/2022 PBP assets for MiLB contact/outcome history;
- retained/certified historical MLB contact evidence already in the repo where it can supply contact bin + terminal outcome;
- challenger-1 tracked EV/LA feature materialization and capability metadata.

Do not rebuild raw official MiLB PBP cleanup unless a concrete gap in these reusable sources is proven.

## Stop conditions before scoring

Before any 2022 score is run, deterministic tests must prove:

- terminal-event mapping is exhaustive for the accepted target universe and fails closed otherwise;
- frozen outcome values use only pre-2021-07-15 MLB state transitions;
- baseline contact-value fits contain no post-cutoff events;
- future target contains only post-cutoff events inside the fixed target window;
- bunts and unsupported/special events are excluded symmetrically;
- comparator/richer event coverage is identical;
- richer feature eligibility/fallback is exact;
- no 2023 input is present anywhere in the development evaluator.
