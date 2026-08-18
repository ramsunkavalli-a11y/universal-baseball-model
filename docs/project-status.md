# Project status and handoff

Last updated: 2026-08-18

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active development branch: `source-certification-poc`
- `source-certification-poc` contains newer work than the latest integration into `main`.
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, positional adjustment, WAR/value, and final ranking separate.

## Frozen upstream stages

### Performance — DONE for current batting pipeline

Completed-2024 affiliated batting Performance materialization is production-shaped and retained.

Primary checkpoint: `docs/performance-2024-affiliated-checkpoint.md`.

### Current Talent — DONE / FROZEN

Retained model: `translated_multiseason_recency_empirical_bayes_v1`.

Richer Challenger 1 failed development. Challenger 2 passed development but failed its one-shot 2023 confirmation. Both are closed without rescue tuning.

### Projection v1 batting rate/profile — DONE / FROZEN

Retained model: `frozen_current_talent_carry_forward_v1`.

The explicit age/development challenger failed the pre-registered 2024 OOT primary gate and is closed. 2025 batting-rate/profile outcomes remain untouched for Projection v1.

### Playing Time v1 — DONE / FROZEN / CONFIRMED

Production model: `playing_time_recent_opportunity_40man_b2_hurdle_v1`.

Passed isolated one-shot 2025 confirmation; no confirmation refit/reselection/recalibration.

### Position / Role v1 — DONE / FROZEN / CONFIRMED

Production model: `primary_share_thresholded_transition_mean_v1`.

Historical source certification passed 64/64 season × league pairs. The selective transition model passed development and its untouched 2025 confirmation on 2,891 players.

## ACTIVE STAGE — Defense v1 confirmation source preparation

Primary handoff: `docs/defense-v1-development-checkpoint.md`.

Frozen confirmation contract: `docs/defense-v1-2025-confirmation-contract.md`.

Frozen parameter package: `docs/defense-v1-confirmation-parameters.json`.

**Pre-2025 Defense-v1 development and parameter fitting are closed. Do not refit or reselect Defense.**

### Final pre-2025 component set

Universal components:

- general range: **U1, lambda `0.0`**;
- catcher blocking: **C2**;
- catcher throwing: **C1**.

Incremental tracked result:

- MLB tracked range T1 = exact U1 + `tracked_range_z`: **passed Tier A**;
- tracked MiLB T1: **not accepted / insufficient transfer evidence**;
- tracked framing F1: **failed / closed**;
- age A1 and rejected traditional features: **closed**.

The independent Tier-B cohort audit confirmed the zero-player transfer population was a sparse-overlap consequence of the frozen eligibility contract, not a player/position join bug. It does not reopen the gate.

### Pre-2025 parameter freeze — COMPLETE

Binding result: `docs/defense-v1-confirmation-parameters.json`.

The retained forms were refit only on the already-authorized 2022–2024 development responses using 2021–2023 inputs.

Latest deterministic freeze run recorded by the parameter package: `32198603779` from SHA `f228bc1e3f8e8099f1c6054f6a551b8c5bff6fdb`.

Canonical parameter hash:

`sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5`

Frozen training rows:

- U1 general: 490;
- T1 MLB tracked: 414;
- C1 throwing: 197;
- C2 blocking: 193.

The package persists exact coefficients, universal normalization moments and fallback hierarchy, catcher normalization moments, training rows, development targets, tracked-range development moments, package versions, source provenance, and table hashes.

Boundary at freeze:

- 2024 confirmation tracking predictor **not accessed**;
- 2025 defensive target/source **not accessed**;
- no model reselection or threshold change;
- no run conversion / WAR/value.

### Frozen coverage hierarchy

General range:

1. eligible MLB + eligible MLB tracking -> T1;
2. eligible MLB without eligible tracking -> U1;
3. eligible affiliated MiLB -> U1;
4. insufficient U1 evidence -> explicit insufficient evidence / neutral position-relative B0 for this component.

Catcher:

- eligible throwing -> C1, otherwise neutral/insufficient B0;
- eligible blocking -> C2, otherwise neutral/insufficient B0;
- tracked framing remains closed and is not fabricated as average skill.

## Immediate next batch

The frozen parameter package authorizes source materialization, not model changes.

1. Materialize **2024 MLB tracked-range predictor evidence only** under the frozen confirmation contract. This is source-only: no fitting, no scorer, no MiLB tracking, no framing, no 2025 target.
2. Certify and persist its coverage/hashes.
3. Only after that source is clean, materialize completed-2025 Savant range/throwing/blocking targets in a separate source-only workflow.
4. Only after both source artifacts are certified, perform the frozen one-shot 2025 confirmation with no fitting.

The 2024 tracking-predictor workflow is staged on `source-certification-poc`; its binding source result is `docs/defense-v1-2024-tracking-predictor-source-result.json` once the source run succeeds.

## Binding one-shot confirmation order

- U1 vs neutral B0 first.
- Only if U1 confirms, T1 vs U1 on identical eligible MLB tracked rows; fewer than 75 is insufficient evidence.
- C1 throwing vs B0; fewer than 30 is insufficient evidence.
- C2 blocking vs B0; fewer than 30 is insufficient evidence.
- Failed/insufficient components use their frozen fallback. No rescue, alternate family, threshold movement, recalibration, or 2025 refit.

## Binding boundaries

- **Do not refit/reselect Defense v1.**
- **Do not calculate WAR/value yet.**
- No additional Defense-v1 development challenger.
- No rescue for tracked framing, age, rejected traditional features, or Tier-B tracked range.
- No proprietary MiLB validation claim.
- No accidental neutral/zero imputation for missing tracking; B0 is a declared component fallback, not observed talent evidence.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-development-checkpoint.md`
3. `docs/defense-v1-2025-confirmation-contract.md`
4. `docs/defense-v1-confirmation-parameters.json`
5. `docs/defense-v1-2024-tracking-predictor-source-result.json` — once materialized
6. `docs/defense-v1-tracked-challenger-result.json`
7. `docs/defense-v1-tier-b-cohort-audit.json`
8. `docs/defense-v1-tracked-challenger-contract.md`
9. `docs/defense-v1-tracked-source-result.json`
10. `docs/defense-v1-source-architecture-checkpoint.md`
11. `docs/defense-v1-universal-development-result.json`
12. `docs/defense-v1-age-challenger-result.json`
13. `docs/position-role-2025-confirmation-result.json`
14. `docs/playing-time-v1-confirmation-result.json`
15. `docs/projection-batting-v1-development-result.json`
16. `docs/current-talent-results-only-baseline-freeze.md`
17. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, Position/Role v1, or Defense development absent a concrete implementation failure.
- Do not tune rejected models against their held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting skill, opportunity, position/role, defensive skill, positional adjustment, and value separate.
- Treat source coverage/missingness as information, not as zero skill.
- Freeze exact model/source decisions before opening their held-out confirmation period.
- Update this handoff whenever the active stage or binding result changes.
