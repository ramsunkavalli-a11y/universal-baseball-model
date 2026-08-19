# Project status and handoff

Last updated: 2026-08-18

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, positional adjustment, run conversion, WAR/value, and final ranking separate.

## Frozen upstream stages

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting rate/profile:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1:** **DONE / FROZEN / 2025-CONFIRMED**. See below.

## Defense v1 — DONE / FROZEN / 2025-CONFIRMED

Binding result: `docs/defense-v1-2025-confirmation-result.json`.

Frozen parameter package: `docs/defense-v1-confirmation-parameters.json`.

Frozen confirmation contract: `docs/defense-v1-2025-confirmation-contract.md`.

Canonical parameter hash:

`sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`

### Final retained Defense-v1 components

General range:

- **U1 confirmed** on 161 identical 2024-input -> 2025-target rows.
- U1 MSE `0.978170` vs B0 `1.010190`.
- U1 Spearman `0.216701`.
- **T1 confirmed** on 135 eligible MLB tracked rows.
- T1 MSE `0.915584` vs U1 `0.916394` on the identical tracked population.
- T1 Spearman `0.274737` vs U1 `0.237502`.
- Final hierarchy: eligible MLB with eligible tracking -> **T1**; otherwise eligible general-range row -> **U1**; insufficient U1 evidence -> declared neutral position-relative B0 fallback.

Catcher throwing:

- **C1 confirmed** on 71 catchers.
- C1 MSE `0.945481` vs B0 `1.002019`.
- C1 MAE `0.772223` vs B0 `0.810838`.
- C1 Spearman `0.246372`.
- Final throwing component: **C1** when eligible; otherwise neutral B0.

Catcher blocking:

- **C2 failed the frozen confirmation gate** on 69 catchers.
- C2 MSE improved (`0.973228` vs B0 `1.008113`) and MAE remained within tolerance (`0.784477` vs `0.774848`), but Spearman was `0.096639`, below the preregistered `0.10` minimum.
- No rescue tuning or threshold movement is allowed.
- Final blocking component: **B0 neutral**.

Closed paths remain closed:

- tracked framing F1;
- tracked MiLB T1;
- age A1;
- rejected traditional-feature search.

### Confirmation provenance

- historical fielding source run: `32148467330`;
- 2024 MLB tracking source run: `32198857540`;
- 2025 target-source run: `32201584187`;
- one-shot scoring run: `32205199301`;
- scoring SHA: `e4649a52fec59d6d70a15f18010db2804c1dc395`;
- scored-row artifact: 436 rows, SHA-256 `8468a619410068e4d37384e4af536e7231f695edc8d65f8b78ea5548cda63779`.

The scoring workflow completed successfully and performed no fitting, reselection, recalibration, threshold movement, live source query, run-value conversion, or WAR calculation.

### Important methodology note

The earlier Tier-B tracked-MiLB transfer gate returned zero qualifying players because the frozen candidate universe contained only three non-MLB players before tracking availability was applied; the >=30-player criterion was therefore impossible by construction. The independent audit confirmed this was not a join bug. Keep the result as `insufficient_transfer_evidence`; do not reinterpret it as evidence that tracked MiLB range is ineffective.

## ACTIVE STAGE — post-Defense run conversion / positional adjustment design

Defense development and confirmation are closed. **Do not refit, reselect, or rescue any Defense-v1 component.**

The binding confirmation result authorizes **run-value conversion next**, but **WAR/value is not yet authorized**.

### Immediate next batch

1. Inspect the repo for existing run-conversion and positional-adjustment contracts/scripts/data sources before implementing anything new.
2. Define and freeze the run-conversion / positional-adjustment methodology and source boundaries without changing frozen Defense skill estimates.
3. Only after that stage is certified should the project authorize WAR/value aggregation.

## Binding boundaries

- **Do not refit/reselect Defense v1.**
- No rescue for C2 blocking, tracked framing, tracked MiLB range, age, or rejected traditional features.
- Do not use 2025 confirmation outcomes to retune coefficients or thresholds.
- **Run-value conversion is authorized next; WAR/value calculation is not yet authorized.**
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
- Preserve missingness/coverage explicitly; neutral B0 is a declared fallback, not observed average talent evidence.

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-2025-confirmation-result.json`
3. `docs/defense-v1-2025-confirmation-contract.md`
4. `docs/defense-v1-confirmation-parameters.json`
5. `docs/defense-v1-2025-target-source-result.json`
6. `docs/defense-v1-2024-tracking-predictor-source-result.json`
7. `docs/defense-v1-development-checkpoint.md`
8. `docs/defense-v1-tracked-challenger-result.json`
9. `docs/defense-v1-tier-b-cohort-audit.json`
10. `docs/position-role-2025-confirmation-result.json`
11. `docs/playing-time-v1-confirmation-result.json`
12. `docs/projection-batting-v1-development-result.json`
13. `docs/current-talent-results-only-baseline-freeze.md`
14. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, Position/Role v1, or Defense absent a concrete implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting skill, opportunity, position/role, defensive skill, positional adjustment, run conversion, and value separate.
- Freeze exact model/source decisions before opening a held-out confirmation period.
