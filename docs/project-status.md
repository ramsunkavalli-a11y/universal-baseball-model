# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, defensive exposure, positional adjustment, run conversion, WAR/value, and final ranking separate.

## Frozen upstream stages

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.

## Defense v1 status — FINAL SKILL HIERARCHY FROZEN

Defense v1 skill selection/confirmation is complete after repairing concrete Savant catcher-source failures. General range was never reopened. Prior invalid-source catcher/framing artifacts remain in the repo as audit evidence but are not production evidence.

### General range — unchanged and binding

Binding result: `docs/defense-v1-2025-confirmation-result.json`.

- U1 universal range confirmed vs B0 on 161 players: MSE `1.01019 -> 0.97817`, Spearman `0.2167`.
- T1 tracked MLB increment confirmed vs U1 on 135 eligible tracked players: MSE `0.91639 -> 0.91558`, Spearman `0.2375 -> 0.2747`.
- Final hierarchy:
  1. eligible MLB + eligible certified tracking -> T1;
  2. otherwise eligible MLB or affiliated MiLB -> U1;
  3. insufficient U1 evidence -> explicit neutral B0.
- Tracked MiLB T1 remains closed for v1 because transfer evidence was insufficient.
- Age and rejected traditional-feature challengers remain closed.

**Do not reopen or rerun general range.**

### Repaired catcher throwing — C2 confirmed

Binding repaired development/freeze/confirmation:

- `docs/defense-v1-catcher-repair-development-result.json`
- `docs/defense-v1-catcher-repair-parameters.json`
- `docs/defense-v1-catcher-repair-2025-confirmation-result.json`

Corrected year-specific Savant targets changed the original result. The exact preregistered C1/C2 search selected **C2** and the one-shot repaired 2025 confirmation passed on 79 catchers:

- B0 MSE `1.00000` -> C2 `0.88575`;
- B0 MAE `0.77838` -> C2 `0.70392`;
- C2 Spearman `0.35827`.

Final throwing: **C2 when eligible; otherwise B0 neutral.**

Important implementation note: the frozen repaired parameter JSON has a metadata-only label `exposure: fielding_outs` for throwing. The actual preregistered C2 implementation used to fit and confirm the frozen coefficients weights the two-season feature by **steal attempts** and requires >=10 prior-season steal attempts. The parameter hash was not changed after 2025 access. Production/scoring code must follow the fitted `_catcher_matrix` semantics, not that one mislabeled metadata field.

### Repaired catcher blocking — C2 confirmed

The exact repaired C1/C2 development search selected **C2** and the one-shot repaired 2025 confirmation passed on 78 catchers:

- B0 MSE `1.00000` -> C2 `0.83563`;
- B0 MAE `0.73114` -> C2 `0.67740`;
- C2 Spearman `0.35975`.

Final blocking: **C2 when eligible; otherwise B0 neutral.**

### Repaired catcher framing — MLB F1 confirmed

The original framing evidence was also invalidated by the generic SportsDataverse `year=...` catcher-framing query. Repair used Baseball Savant's framing-specific `seasonStart` / `seasonEnd` source semantics while keeping the original F0/F1 model/gates unchanged.

Binding files:

- `docs/defense-v1-framing-repair-development-result.json`
- `docs/defense-v1-framing-repair-parameters.json`
- `docs/defense-v1-2024-framing-predictor-source-result.json`
- `docs/defense-v1-2025-framing-target-source-result.json`
- `docs/defense-v1-framing-2025-confirmation-result.json`

Repaired pre-2025 F1 passed and was frozen before 2025 access. The certified 2024 MLB predictor contained 84 eligible framing-z rows. The one-shot 2025 confirmation then passed on 48 eligible catchers:

- F0 MSE `0.96655` -> F1 `0.63129`;
- F0 MAE `0.75272` -> F1 `0.66683`;
- F1 Spearman `0.55145`.

Final framing hierarchy:

- eligible MLB catcher + eligible certified tracked framing -> **F1**;
- MLB without eligible tracking -> **F0 neutral**;
- affiliated MiLB -> **F0 neutral** because the frozen MiLB transfer sample was insufficient.

No additional framing tuning or second confirmation attempt is authorized.

### Defense source-repair audit history

The old catcher throwing/blocking selections and old framing failure remain useful only as evidence of what the invalid source produced. Do not delete or overwrite them, but do not use them for production decisions.

The repaired source contract is `docs/defense-v1-catcher-source-repair-contract.md`. The framing repair/confirmation contract is `docs/defense-v1-framing-2025-confirmation-contract.md`.

## Player Value v1 architecture

Architecture contract: `docs/player-value-v1-architecture-contract.md`.
Defense exposure contract: `docs/player-value-v1-defense-exposure-contract.md`.

The downstream architecture remains frozen:

- reuse the existing Performance RE24/bin-value infrastructure for batting;
- Defense skill and defensive runs are separate layers;
- no arbitrary `runs per z` conversion;
- use frozen Playing Time + Position/Role only through separately validated exposure mappings;
- positional adjustment remains separate from position-relative Defense skill;
- replacement level and runs per win remain separate later decisions;
- preserve each value component separately in final outputs.

### Defensive exposure — total-outs diagnostic complete

The canonical observed defensive exposure unit is official Stats API `fielding_outs` over `C, 1B, 2B, 3B, SS, LF, CF, RF`.

The first predeclared total-outs development diagnostic is complete:

- contract: `docs/player-value-v1-defensive-exposure-diagnostic-contract.md`;
- binding result: `docs/player-value-v1-defensive-exposure-diagnostic-result.json`;
- workflow run: `32261447127`;
- folds: 2022 -> 2023 and 2023 -> 2024;
- 2025 accessed: false.

Candidates were raw prior-year defensive-outs persistence (B0), frozen Playing Time projected PA times one global source-year outs/PA scale (P1), and a fixed 50/50 hybrid (H1). **B0 was retained under the frozen recommendation rule.**

Equal-fold means:

- B0: MAE `151.8143`, RMSE `473.4592`;
- P1: MAE `180.2195`, RMSE `427.4569`;
- H1: MAE `152.5628`, RMSE `430.7028`.

P1 and H1 improved RMSE and entrant error but failed the preregistered overall-MAE requirements. H1 narrowly missed the 2022 -> 2023 fold guardrail: its MAE was about 2.20% worse than B0 versus an allowed 2%. **Do not retune the gate or blend weight after result access.**

This does **not** freeze the full exposure bridge. Position allocation and component-native opportunities are still open.

## ACTIVE STAGE

**Defensive position allocation, then Defense native run conversion / positional-adjustment work.**

Defense skill development is closed. Total defensive-outs development retains raw prior-year persistence. The next gate is how projected total outs are distributed across defensive positions without pretending the frozen start-share Position/Role vector is already an outs-share forecast.

### Immediate next batch

1. Predeclare and run a by-position defensive-out-share allocation diagnostic on pre-2025 folds, comparing prior defensive-out-share persistence against a deterministic mapping from frozen Position/Role forecasts and any fixed predeclared hybrid.
2. Keep total exposure volume fixed to the retained B0 total-outs baseline while separately scoring share allocation and resulting per-position outs.
3. After position allocation is resolved, define and validate native-unit run conversion separately for range, throwing, blocking, and framing; do not use an arbitrary runs-per-z constant.
4. Keep positional adjustment separate from position-relative Defense skill.
5. Only after those pieces are frozen should replacement level / runs-per-win / WAR-value aggregation be opened.

## Binding boundaries

- **Defense v1 skill models are frozen.**
- No catcher or framing refit, new feature, family, threshold, recalibration, or rescue.
- Do not use 2025 confirmation residuals for tuning.
- Do not refit Current Talent, Projection, Playing Time, or Position/Role.
- Preserve invalid-source artifacts as audit history.
- Total defensive-outs development baseline is `B0_raw_persistence`; do not reopen its thresholds after result access.
- Full defensive exposure is not frozen until position allocation is selected.
- Run-conversion and positional-adjustment work are authorized next.
- **WAR/value calculation is not authorized yet.**

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-development-checkpoint.md`
3. `docs/defense-v1-catcher-repair-2025-confirmation-result.json`
4. `docs/defense-v1-framing-2025-confirmation-result.json`
5. `docs/defense-v1-2025-confirmation-result.json` — binding for general range only; old catcher portion is invalid-source audit history
6. `docs/defense-v1-catcher-repair-parameters.json`
7. `docs/defense-v1-framing-repair-parameters.json`
8. `docs/defense-v1-catcher-source-repair-contract.md`
9. `docs/defense-v1-framing-2025-confirmation-contract.md`
10. `docs/player-value-v1-architecture-contract.md`
11. `docs/player-value-v1-defense-exposure-contract.md`
12. `docs/player-value-v1-defensive-exposure-diagnostic-contract.md`
13. `docs/player-value-v1-defensive-exposure-diagnostic-result.json`
14. `docs/player-value-v1-defense-native-scale-audit.json`
15. `docs/position-role-2025-confirmation-result.json`
16. `docs/playing-time-v1-confirmation-result.json`
17. `docs/projection-batting-v1-development-result.json`
18. `docs/current-talent-results-only-baseline-freeze.md`
19. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure.
- Repair only the scope affected by a verified implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance, including invalid-source artifacts for audit history.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening a held-out confirmation period.
