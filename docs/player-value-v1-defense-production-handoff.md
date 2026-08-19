# Player Value v1 — Defense production handoff

Last updated: 2026-08-19

Status: **FROZEN HANDOFF OF DEFENSE SKILL ONLY.**

This document reconciles the final repaired Defense v1 decisions into one downstream interface for Player Value v1. It does not refit Defense, convert any skill score to runs, select defensive exposure, calculate positional adjustment, or calculate WAR.

## Binding inputs

General range remains governed by `docs/defense-v1-2025-confirmation-result.json`.

Repaired catcher throwing/blocking are governed by:

- `docs/defense-v1-catcher-repair-parameters.json`;
- `docs/defense-v1-catcher-repair-2025-confirmation-result.json`.

Repaired framing is governed by:

- `docs/defense-v1-framing-repair-parameters.json`;
- `docs/defense-v1-framing-2025-confirmation-result.json`.

Prior invalid-source catcher/framing artifacts remain audit history only and must not override the repaired binding results.

## Final production hierarchy

### 1. General range

Target scale: the frozen standardized Savant general-range target derived from `diff_success_rate_formatted` / Success Rate Added, standardized within target season x position.

Production policy:

1. eligible MLB player-position with eligible certified tracking -> **T1**;
2. otherwise eligible MLB or affiliated MiLB player-position with sufficient universal evidence -> **U1**;
3. insufficient U1 evidence -> **B0 neutral** for the general-range component.

T1 and U1 predict the same target scale. They must therefore share one downstream run-conversion rule; T1 does not receive a different runs-per-unit scale merely because it has tracked inputs.

Tracked MiLB T1 remains closed for v1 because transfer evidence was insufficient.

### 2. Catcher throwing

Target scale: repaired year-specific Savant `cs_aa_per_throw`, standardized within target year.

Production policy:

- eligible catcher -> repaired **C2**;
- otherwise -> **B0 neutral** for throwing.

Binding parameter hash: `sha256:f4790bc1cb4df63d2ba65757455a4b6753e98d25fe552208d893958bdd19f328`.

Implementation note: the persisted repaired parameter JSON has a metadata label `exposure: fielding_outs`, but the frozen fitted/scored C2 construction for throwing weights the two-season feature by **steal attempts** and requires the original steal-attempt eligibility. Production scoring must reproduce the fitted `_catcher_matrix` semantics; do not reinterpret the metadata label as fitted-model exposure.

The feature-weighting exposure above is part of skill estimation. It is not yet the Player Value seasonal run-exposure denominator.

### 3. Catcher blocking

Target scale: repaired year-specific Savant `blocks_above_average_per_game`, standardized within target year.

Production policy:

- eligible catcher -> repaired **C2**;
- otherwise -> **B0 neutral** for blocking.

The fitted C2 two-season construction uses fielding outs as its historical feature-weighting exposure. That does not by itself select the downstream run-exposure denominator.

Binding parameter hash: `sha256:f4790bc1cb4df63d2ba65757455a4b6753e98d25fe552208d893958bdd19f328`.

### 4. Catcher framing

Raw repaired target before standardization: `1000 * rv_tot / pitches` from the year-specific Baseball Savant catcher-framing leaderboard, with the frozen minimum-pitch rule. The Defense model predicts the within-target-year standardized version of that target.

Production policy:

- eligible MLB catcher with eligible certified tracked framing -> **F1**;
- MLB catcher without eligible tracking -> **F0 neutral** for framing;
- affiliated MiLB catcher -> **F0 neutral** because tracked MiLB framing transfer evidence was insufficient.

Binding parameter hash: `sha256:e75ebd58d868b6cb6d51f2d0e48d49c1735a4cfa80661b6280269311a7875086`.

The raw framing target is already expressed as run value per 1,000 pitches before standardization. Player Value must recover/use principled native units and exposure rather than assign an arbitrary runs-per-z constant.

## Required downstream skill interface

Any production Defense handoff table used by Player Value must preserve, at minimum, these fields or their exact equivalents:

- player identifier;
- projection season;
- level/scope needed to apply MLB-vs-MiLB eligibility;
- position;
- `general_range_skill` plus `general_range_family` in `{T1,U1,B0}`;
- `catcher_throwing_skill` plus family/fallback flag in `{C2,B0}`;
- `catcher_blocking_skill` plus family/fallback flag in `{C2,B0}`;
- `catcher_framing_skill` plus family/fallback flag in `{F1,F0}`;
- source/parameter provenance sufficient to recover the binding artifact and hash;
- component eligibility/coverage flags.

Do not collapse components into one Defense score before run conversion. Do not silently impute a failed/missing component with another component.

## Neutral fallback semantics

A B0/F0 neutral fallback means zero modeled adjustment for that component on its defined position-relative skill scale. It does not assert that the player is truly average, does not eliminate uncertainty, and does not authorize a downstream rescue model.

## Downstream boundary

Authorized next:

1. map projected defensive exposure without refitting Playing Time or Position/Role;
2. define native-unit run conversion separately for range, throwing, blocking, and framing;
3. define positional adjustment separately from Defense skill.

Still unauthorized:

- changing any Defense model/feature/threshold;
- tuning run conversion to 2025 Defense confirmation residuals;
- reopening tracked MiLB range or framing;
- replacement level;
- runs per win;
- WAR/value aggregation.
