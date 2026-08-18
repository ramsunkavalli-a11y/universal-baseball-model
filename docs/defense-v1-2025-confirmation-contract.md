# Defense v1 — untouched 2025 confirmation contract

Last updated: 2026-08-18

Status: **FROZEN BEFORE 2024 TRACKING CONFIRMATION-PREDICTOR MATERIALIZATION AND BEFORE 2025 DEFENSIVE-TARGET ACCESS.**

Governing development contracts:

- `docs/defense-v1-development-contract.md`
- `docs/defense-v1-tracked-challenger-contract.md`

Binding pre-2025 development results:

- `docs/defense-v1-universal-development-result.json`
- `docs/defense-v1-tracked-challenger-result.json`
- `docs/defense-v1-tier-b-cohort-audit.json` (diagnostic only; does not change selection)

The final pre-2025 parameter artifact must be persisted before any source workflow authorized by this contract is run.

## Fixed confirmation question

On untouched 2025 public Savant defensive outcomes, do the already-selected and already-refit Defense-v1 components retain next-season defensive-skill signal under the exact frozen hierarchy?

No feature, family, penalty, recency weight, eligibility threshold, normalization rule, fallback rule, source rule, or confirmation threshold may be changed after 2025 defensive targets are opened.

No failed or closed development path may be rescued by 2025.

## Frozen component hierarchy entering confirmation

### General range

Universal incumbent:

- `U1`, lambda `0.0`.

Tracked MLB increment:

- `T1 = exact U1 + tracked_range_z`, lambda `0.0`.

Coverage hierarchy:

1. an eligible MLB input row with eligible MLB `tracked_range_z` uses T1;
2. an otherwise eligible MLB input row without eligible tracking falls back to U1;
3. eligible affiliated MiLB input rows use U1 regardless of public tracking availability;
4. a row without sufficient U1 evidence is explicit `insufficient_evidence` and receives the neutral position-relative B0 skill estimate for this component.

The failed 2023-MiLB -> 2024-MLB Tier-B transfer gate is not reopened. Tracked MiLB does not receive T1 in Defense v1.

### Catcher components

- throwing: `C1`, current-season `caught_stealing_pct_z` only;
- blocking: `C2`, frozen two-season recency/exposure `passed_balls_per_9_z` model;
- tracked framing: closed / not retained.

A catcher without the frozen component-specific evidence minimum is explicit `insufficient_evidence` and receives the neutral B0 estimate for that component.

Missing framing remains missing evidence; this contract does not manufacture a framing skill value or reopen F1.

## Frozen pre-2025 refit

Before any confirmation source is opened, refit only the retained forms on all authorized development responses:

- input 2021 -> target 2022;
- input 2022 -> target 2023;
- input 2023 -> target 2024.

The refit must persist:

- exact coefficients and intercepts;
- exact universal normalization moments and fallback hierarchy;
- exact catcher normalization moments;
- exact tracked-range source-standardization rule;
- exact eligibility and coverage/fallback rules;
- training row counts;
- package versions;
- source artifact/run identifiers and hashes;
- a canonical parameter hash;
- this confirmation contract's byte-level SHA-256 hash.

The refit workflow may use only the already-certified historical fielding artifact and the already-frozen 2021-2023 tracked aggregate plus already-opened 2022-2024 Savant development targets. It may not access 2024 tracking or any 2025 defensive target.

## Frozen predictor source for the 2025 fold

### Universal / catcher predictors

Reuse the already-certified official 2024 fielding evidence from historical source run `32148467330`.

No 2025 fielding information may enter predictors.

### MLB tracked-range predictor

T1 confirmation requires a 2024 MLB tracking predictor because the untouched target is 2025.

After the parameter freeze succeeds, a separate source-only workflow may materialize **2024 regular-season MLB tracking only** using the exact portable range construction frozen in the tracked-development contract:

- pinned `sportsdataverse==0.0.75`;
- 2024 regular-season MLB Statcast only;
- same SportsDataverse `mlb_fielding_oaa` implementation;
- `tracked_oaa_per_100 = 100 * oaa / opportunities`;
- positions 1B, 2B, 3B, SS, LF, CF, RF;
- at least 100 OAA opportunities;
- standardize within 2024 × MLB × position;
- require at least 20 eligible players and a finite nondegenerate SD in the position cell.

This workflow must contain no model coefficients, no 2025 target query, and no model scorer. It must persist raw-source/query evidence, derived row counts, and output hashes before the tracked predictor is used.

No 2024 MiLB tracking is required or authorized for Defense-v1 confirmation because T1 is not retained for Tier B.

## Frozen 2025 target source

Completed-2025 defensive targets must be materialized in a separate source-only workflow after the parameter freeze.

The source workflow may query only the public Savant leaderboard surfaces required by this contract for completed 2025 regular-season outcomes:

### General range target

Use `diff_success_rate_formatted` from the 2025 Outs Above Average leaderboard when:

- player ID is valid;
- target is finite;
- Savant `primary_pos_formatted` is one of 1B, 2B, 3B, SS, LF, CF, RF.

Within 2025 × target position, standardize to mean 0 / population SD 1. This creates `range_target_z`.

### Catcher throwing target

Use 2025 `cs_aa_per_throw` with target `sb_attempts >= 10` and finite value. Standardize within 2025 to `throwing_target_z`.

### Catcher blocking target

Use 2025 `blocks_above_average_per_game` with target `pitches >= 500` and finite value. Standardize within 2025 to `blocking_target_z`.

The target-source workflow must:

- contain no frozen model parameters and no model scorer;
- persist the exact package version and query surface;
- persist canonical target rows, counts, and hashes;
- fail on missing required columns, duplicate player-position keys where prohibited, nonfinite target construction, or an empty required target surface.

No 2025 outcome may be interpreted until source certification succeeds.

## Frozen confirmation populations

### Universal general U1 confirmation

Use 2024 input evidence under the frozen U1 eligibility rules:

- 2024 primary position is 1B, 2B, 3B, SS, LF, CF, or RF;
- fielding outs at that primary position >= 300;
- chances >= 100;
- all four U1 raw features are present;
- current level group is available;
- a 2025 Savant range target exists at **exactly the same position**.

Apply only the frozen pre-2025 universal normalizer and U1 coefficients. Do not normalize from the 2024 predictor distribution.

Baseline B0 predicts `0.0` target z for the identical population.

### MLB tracked T1 incremental confirmation

This comparison is evaluated only if U1 confirms.

Start from the exact U1 confirmation population, then require:

- 2024 `current_level_group == MLB`;
- eligible certified 2024 MLB `tracked_range_z` at the same 2024 primary position.

Score T1 and U1 on exactly identical rows. T1 uses the frozen pre-2025 coefficients; only the target-free 2024 tracked feature standardization described above is newly materialized.

If the tracked confirmation population is fewer than 75 players, record `insufficient_confirmation_evidence`; do not call T1 confirmed. Tier A then falls back to confirmed U1 if U1 passed.

### Catcher throwing C1 confirmation

Use 2024 catcher evidence with:

- catcher fielding outs >= 300;
- steal attempts >= 10;
- finite `caught_stealing_pct`;
- eligible 2025 throwing target.

Apply the frozen pre-2025 catcher normalizer and C1 coefficients. B0 predicts zero on identical rows.

### Catcher blocking C2 confirmation

Use 2024 catcher evidence with:

- catcher fielding outs >= 300;
- finite `passed_balls_per_9`;
- eligible 2025 blocking target.

Apply the frozen pre-2025 catcher normalizer and C2 coefficients. The C2 prior-season contribution may use only eligible 2023 catcher evidence under the already-frozen 0.5 recency/exposure rule. B0 predicts zero on identical rows.

For each catcher component, fewer than 30 scored catchers is `insufficient_confirmation_evidence`, not a pass.

## Frozen scores

For every comparison report on identical rows:

- player count;
- MSE (primary);
- MAE;
- Pearson correlation;
- Spearman correlation;
- calibration intercept/slope from `target ~ prediction` where estimable;
- finite-value checks.

Also persist the exact scored player IDs and positions/components in the confirmation artifact for auditability.

## Binding one-shot confirmation rules

### U1 vs B0

U1 confirms as the universal general-range component only if all are true:

1. U1 MSE is strictly lower than B0;
2. U1 MAE is no more than 5.0% worse than B0;
3. U1 Spearman is at least `0.10`;
4. all coefficients, predictions, and required metrics are finite;
5. U1 and B0 coverage is exactly identical.

If U1 fails, general range freezes at B0 for Defense v1 and T1 is not eligible to rescue it.

### T1 vs U1

Only if U1 confirms, T1 confirms for eligible MLB tracked rows only if all are true:

1. at least 75 tracked confirmation players exist;
2. T1 MSE is strictly lower than U1;
3. T1 MAE is no more than 5.0% worse than U1;
4. T1 Spearman is no more than `0.005` lower than U1;
5. all coefficients, predictions, and required metrics are finite;
6. T1 and U1 coverage is exactly identical.

If T1 fails or evidence is insufficient, Tier-A MLB range falls back to confirmed U1. No retuning or alternate tracked form is allowed.

### Catcher throwing C1 vs B0

C1 confirms only if all are true:

1. at least 30 scored catchers exist;
2. C1 MSE is strictly lower than B0;
3. C1 MAE is no more than 7.5% worse than B0;
4. C1 Spearman is at least `0.10`;
5. all coefficients, predictions, and required metrics are finite;
6. candidate and B0 coverage is exactly identical.

Failure or insufficient evidence freezes catcher throwing at B0 for Defense v1. No C2 substitution or retuning is allowed.

### Catcher blocking C2 vs B0

C2 confirms only if all are true:

1. at least 30 scored catchers exist;
2. C2 MSE is strictly lower than B0;
3. C2 MAE is no more than 7.5% worse than B0;
4. C2 Spearman is at least `0.10`;
5. all coefficients, predictions, and required metrics are finite;
6. candidate and B0 coverage is exactly identical.

Failure or insufficient evidence freezes catcher blocking at B0 for Defense v1. No C1 substitution or retuning is allowed.

## Binding outcome and fallback

After the one-shot 2025 confirmation, each retained component is independently frozen according to the rules above.

- U1 failure closes modeled general range at B0 for v1.
- U1 pass + T1 pass retains T1 for eligible MLB tracking and U1 elsewhere.
- U1 pass + T1 fail/insufficient retains U1 for all eligible general-range rows.
- C1 throwing failure/insufficient uses B0 throwing.
- C2 blocking failure/insufficient uses B0 blocking.
- tracked framing remains closed regardless of 2025 outcomes.
- tracked MiLB T1 remains closed regardless of 2025 outcomes.

No failed component may be rescued by another family, altered threshold, alternate source, post-hoc subgroup, recalibration, or refit to 2025.

## Binding boundaries

- no 2025 defensive target access before the pre-2025 parameter package is persisted successfully;
- no 2025 predictor may enter the model;
- no 2025 refit, reselection, recalibration, or threshold movement;
- no age rescue;
- no traditional feature search;
- no tracked framing rescue;
- no Tier-B tracked-range rescue;
- no position-specific coefficients;
- no proprietary MiLB validation claim;
- no run conversion / WAR/value;
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
