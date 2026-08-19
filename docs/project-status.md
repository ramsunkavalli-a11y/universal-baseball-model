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
- **Projection v1 batting:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.

## Defense v1 status — GENERAL RANGE FROZEN; CATCHER CHANNEL QUARANTINED

A concrete source implementation failure was discovered while beginning Player Value run-conversion work.

### General range remains valid and frozen

Binding general-range confirmation remains in `docs/defense-v1-2025-confirmation-result.json`:

- universal general range confirmed on 161 rows;
- tracked MLB range confirmed incrementally on 135 eligible tracked rows;
- final general hierarchy remains tracked MLB range when eligible, otherwise universal range, then declared neutral fallback when universal evidence is insufficient;
- tracked MiLB range, tracked framing, age, and rejected traditional-feature paths remain closed.

**Do not reopen or rerun general range.**

### Catcher source failure

The pre-2025 Defense target artifact contained exactly the same catcher-throwing target distribution for 2022, 2023, and 2024. It also matched the subsequently materialized nominal 2025 target distribution. Historical blocking pulls likewise returned the same 70-row payload for every requested year.

Direct source diagnostic: `docs/savant-catcher-year-filter-diagnostic.json`.

The diagnostic showed that both Savant catcher leaderboards returned identical 2022-2025 payloads when queried with the legacy/generated `year=...` form used by the pinned SportsDataverse catcher wrapper and with tested camelCase season parameters.

The current Savant UI instead uses snake_case `season_start` / `season_end` plus the current catcher leaderboard parameters. A second diagnostic run is testing that exact query shape now.

### Quarantined catcher results

Until the repair completes, the following are **historical audit evidence, not binding production evidence**:

- prior catcher-throwing development selection;
- prior catcher-blocking development selection;
- catcher portions of `docs/defense-v1-confirmation-parameters.json`;
- prior 2025 catcher throwing confirmation pass;
- prior 2025 catcher blocking confirmation failure.

This does not imply those model ideas are wrong. Their target source was not year-specific, so the evidence is invalid.

### Catcher source repair contract

Binding repair contract: `docs/defense-v1-catcher-source-repair-contract.md`.

The repair is source-only in scope:

1. certify truly year-specific Savant catcher query semantics;
2. materialize corrected 2022-2024 catcher targets only;
3. rerun the **exact original preregistered C1/C2 catcher development search and gates** with no new features/families/thresholds;
4. refit/freeze any surviving catcher component on corrected pre-2025 targets;
5. only then materialize corrected 2025 catcher targets separately;
6. run one-shot catcher confirmation under the original frozen confirmation rules.

No repaired 2025 catcher outcome may enter development/refit.

## Player Value v1 architecture

Architecture contract: `docs/player-value-v1-architecture-contract.md`.

The downstream architecture is frozen even while the catcher source is repaired:

- reuse the existing Performance RE24/bin-value infrastructure for batting;
- Defense skill and defensive runs are separate layers;
- no arbitrary `runs per z` conversion;
- use frozen Playing Time + full Position/Role share vector for exposure;
- positional adjustment remains separate from position-relative Defense skill;
- replacement level and runs per win remain separate later decisions;
- preserve each value component separately in final outputs.

### Defensive run conversion research

Public Statcast methodology supports a native-unit route rather than arbitrary z-score scaling:

- range: convert predicted position-relative success-rate skill to cumulative OAA-like value using projected opportunities, then use Statcast fielding run values;
- catcher throwing: convert predicted CS-above-average-per-throw skill using projected steal attempts, then use Statcast throwing run value;
- catcher blocking already has a native Statcast blocks-to-runs convention, but its model channel cannot be used until the source repair decides whether a blocking model survives.

The pre-2025 native-scale audit is persisted at `docs/player-value-v1-defense-native-scale-audit.json`. General-range scale diagnostics are usable; catcher scale diagnostics are quarantined because they exposed the source failure.

## ACTIVE STAGE

**Defense catcher source repair + Player Value exposure/positional-adjustment research.**

These can proceed in parallel where independent, but WAR/value aggregation remains closed.

### Immediate next batch

1. Resolve the current-UI snake_case Savant catcher query diagnostic.
2. If it certifies, materialize corrected 2022-2024 catcher targets under the repair contract and rerun the original catcher development gate.
3. In parallel, finish the audit of frozen Playing Time output semantics and define the pre-2025 defensive-opportunity exposure mapping.
4. Do not open repaired 2025 catcher targets until repaired catcher development and parameter freeze are complete.

## Binding boundaries

- **General Defense remains frozen.**
- **Catcher Defense is quarantined pending source repair.**
- No new catcher features, model families, thresholds, or rescue tuning.
- Do not use prior invalid catcher confirmation residuals for tuning.
- Do not refit Current Talent, Projection, Playing Time, or Position/Role.
- General-range run-conversion research and positional-adjustment research may continue.
- Catcher run conversion is blocked until repaired confirmation completes.
- **WAR/value calculation is not authorized yet.**

## Governing read order

1. `docs/project-status.md`
2. `docs/defense-v1-catcher-source-repair-contract.md`
3. `docs/savant-catcher-year-filter-diagnostic.json`
4. `docs/player-value-v1-architecture-contract.md`
5. `docs/player-value-v1-defense-native-scale-audit.json`
6. `docs/defense-v1-2025-confirmation-result.json` — general result remains binding; catcher portion quarantined
7. `docs/defense-v1-development-contract.md`
8. `docs/defense-v1-2025-confirmation-contract.md`
9. `docs/defense-v1-confirmation-parameters.json` — general parameters binding; catcher portion quarantined
10. `docs/position-role-2025-confirmation-result.json`
11. `docs/playing-time-v1-confirmation-result.json`
12. `docs/projection-batting-v1-development-result.json`
13. `docs/current-talent-results-only-baseline-freeze.md`
14. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure.
- Repair only the scope affected by a verified implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance, including invalid-source artifacts for audit history.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening a held-out confirmation period.
