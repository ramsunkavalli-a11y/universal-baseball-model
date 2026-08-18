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

## ACTIVE STAGE — Defense v1 final refit / parameter freeze

Primary handoff: `docs/defense-v1-development-checkpoint.md`.

Source/architecture checkpoint: `docs/defense-v1-source-architecture-checkpoint.md`.

**Pre-2025 Defense-v1 feature/model development is now closed.**

### Universal Defense-v1 components already selected

- general range: **U1, lambda `0.0`**;
- catcher blocking: **C2**;
- catcher throwing: **C1**;
- age challenger A1: failed / closed;
- traditional feature search: closed.

### Frozen tracked source gate — PASSED

Binding source record: `docs/defense-v1-tracked-source-result.json`.

Workflow run `32182019495` succeeded from source SHA `5438e905d24e2167432a52253320ccbc978186b8` and hash-pinned the 2021–2023 MLB tracked range/framing evidence plus 2023 tracked MiLB transfer evidence.

No 2025 source/target was accessed and no model was fit during source materialization.

### Final tracked challenger — COMPLETE

Governing contract: `docs/defense-v1-tracked-challenger-contract.md`.

Binding result: `docs/defense-v1-tracked-challenger-result.json`.

Workflow run `32196115227` completed successfully from scoring SHA `ace1df97001b83b91a1a1021637c604ebdea6399` after verifying the pinned tracked-source hashes.

#### General tracked range

**Tier A / MLB: PASSED.** T1 = exact U1 + `tracked_range_z`.

- 2022 MSE: `0.83749 -> 0.80983` — 3.30% better, n=140;
- 2023: `0.86863 -> 0.85218` — 1.89% better, n=133;
- 2024: `0.97975 -> 0.97191` — 0.80% better, n=141;
- pooled MSE improvement: **1.93%**;
- pooled Spearman delta: **+0.01180**;
- all frozen Tier-A gates passed.

**Tier B / tracked MiLB: NOT ACCEPTED.** The predeclared 2023-MiLB -> 2024-MLB transfer diagnostic produced `0` eligible players and therefore `insufficient_transfer_evidence`. Under the frozen contract that is not a pass and has no rescue path.

Retain T1 for Tier-A MLB only; Tier B/C range stays on U1.

#### Tracked catcher framing

**FAILED / CLOSED.** F1 beat neutral F0 in 2 of 3 folds, improved pooled MSE 9.37%, and had pooled Spearman 0.2410, but its 2022 fold was **8.35% worse** than F0. That breaches the frozen maximum 5.0% fold-degradation guardrail.

The Tier-A failure is binding. MiLB transfer was not attempted. Tracked framing is not retained for Defense v1 and may not be rescued or retuned.

### Retained Defense-v1 evidence by tier entering final freeze

- **Tier A — MLB tracked:** T1 tracked range; universal C2 blocking/C1 throwing where eligible; no tracked framing.
- **Tier B — tracked MiLB:** U1 universal range; universal C2/C1 where eligible; no tracked framing.
- **Tier C — untracked affiliated MiLB:** U1 universal range; universal C2/C1 where eligible.

Missing tracking remains missing evidence, not observed average/zero defensive skill.

## Immediate next batch

The tracked result explicitly authorizes **final refit and parameter freeze next**. It does **not** authorize 2025 confirmation or WAR/value.

1. Refit only retained Defense-v1 components on all authorized 2022–2024 development responses.
2. Freeze exact normalization moments, coefficients, coverage/fallback rules, package versions, parameter hashes, and component provenance.
3. Freeze the exact one-shot 2025 Defense-v1 confirmation contract before any completed-2025 defensive source/target is opened.

Stop after that freeze. A separate source-only workflow may materialize completed-2025 defensive targets only afterward.

## Binding boundaries

- **No 2025 defensive source/target access yet.**
- **No WAR/value calculation yet.**
- No additional Defense-v1 development challenger.
- No rescue/reselection for tracked framing, age, rejected traditional features, or Tier-B tracked range.
- No proprietary MiLB validation claim.
- No accidental neutral/zero imputation for missing tracking.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-development-checkpoint.md`
3. `docs/defense-v1-tracked-challenger-result.json`
4. `docs/defense-v1-tracked-challenger-contract.md`
5. `docs/defense-v1-tracked-source-result.json`
6. `docs/defense-v1-source-architecture-checkpoint.md`
7. `docs/defense-v1-universal-development-result.json`
8. `docs/defense-v1-age-challenger-result.json`
9. `docs/position-role-2025-confirmation-result.json`
10. `docs/playing-time-v1-confirmation-result.json`
11. `docs/projection-batting-v1-development-result.json`
12. `docs/current-talent-results-only-baseline-freeze.md`
13. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled Current Talent, Projection v1, Playing Time v1, or Position/Role v1 absent a concrete implementation failure.
- Do not tune rejected models against their held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Keep batting skill, opportunity, position/role, defensive skill, positional adjustment, and value separate.
- Treat source coverage/missingness as information, not as zero skill.
- Freeze exact model/source decisions before opening their held-out confirmation period.
- Update this handoff whenever the active stage or binding result changes.
