# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches and inspect the active branch head before editing.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense skill, defensive exposure, defensive run conversion, positional adjustment, replacement level, WAR/value, and final ranking separate.

## Frozen upstream stages

- **Performance:** completed-2024 affiliated batting materialization retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.

Do not reopen these stages absent a concrete implementation failure.

## Defense v1 skill — DONE / FROZEN

Defense skill selection/confirmation is complete. The repaired Savant catcher-source path is binding; old invalid-source artifacts remain audit history only.

Final hierarchy:

- **General range:** T1 for eligible certified tracked MLB player-position; otherwise U1 for eligible MLB/affiliated MiLB player-position; otherwise neutral B0.
- **Catcher throwing:** repaired C2 when eligible; otherwise neutral B0.
- **Catcher blocking:** repaired C2 when eligible; otherwise neutral B0.
- **Framing:** MLB F1 when eligible for certified tracked framing; otherwise F0 neutral. MiLB framing remains F0 neutral.

Key records:

- `docs/defense-v1-development-checkpoint.md`
- `docs/defense-v1-2025-confirmation-result.json` — general range only
- `docs/defense-v1-catcher-repair-2025-confirmation-result.json`
- `docs/defense-v1-framing-repair-2025-confirmation-result.json`
- `docs/defense-v1-catcher-repair-parameters.json`
- `docs/defense-v1-framing-repair-parameters.json`
- `docs/player-value-v1-defense-production-handoff.md`

Important throwing implementation note: the repaired parameter JSON contains a metadata-only `exposure: fielding_outs` label, but fitted/confirmed C2 weights its two-season feature by **steal attempts** and requires the original steal-attempt eligibility. Production scoring must follow fitted `_catcher_matrix` semantics.

**Do not refit, rescue, recalibrate, or reopen Defense skill.**

## Player Value v1 architecture

Architecture contract: `docs/player-value-v1-architecture-contract.md`.

Binding boundaries:

- reuse existing Performance RE24/bin-value infrastructure for batting;
- Defense skill, exposure, run conversion, and positional adjustment are separate layers;
- no arbitrary universal `runs per z` conversion;
- positional adjustment is separate from position-relative Defense skill;
- replacement level and runs per win remain later decisions;
- preserve each component separately in outputs.

## Defensive exposure — DONE / FROZEN

Canonical observed general exposure is official Stats API `fielding_outs` over `C, 1B, 2B, 3B, SS, LF, CF, RF`.

### General defensive outs

Binding total-outs result: `docs/player-value-v1-defensive-exposure-diagnostic-result.json`, run `32261447127`.

Selected total form: **`B0_raw_persistence`** = prior-season MLB defensive outs.

Binding position-allocation result: `docs/player-value-v1-defensive-position-allocation-result.json`, run `32266007594`.

Selected allocation form: **`S0_prior_defensive_share_persistence`** = prior-season position fielding outs / prior-season total defensive outs.

Therefore:

- projected total defensive outs = prior-season MLB defensive outs;
- projected position shares = prior-season defensive-out shares;
- projected position outs = projected total x projected share;
- algebraically, v1 projected position outs equal prior-season position outs.

Do not retune rejected PA-scaled, Position/Role-normalized, or 50/50 challengers.

### Catcher native opportunities

Contract: `docs/player-value-v1-catcher-native-opportunity-selection-contract.md`.

Binding result: `docs/player-value-v1-catcher-native-opportunity-selection-result.json`, run `32269076231`, artifact digest `sha256:edc6c4fef7f0d17e063917f3defca48243ae60466a0e665c200c7989bfb42486`.

Development folds were 2022->2023 and 2023->2024; 2025 stayed closed.

Selected forward forms:

- **throwing / `sb_attempts`: `H1_fixed_50_50_hybrid`**
  - `0.5 * prior_sb_attempts + 0.5 * prior_sb_attempts * projected_expected_mlb_pa / source_year_mlb_pa`;
- **blocking / Savant blocking `pitches`: `H1_fixed_50_50_hybrid`**
  - `0.5 * prior_blocking_pitches + 0.5 * prior_blocking_pitches * projected_expected_mlb_pa / source_year_mlb_pa`;
- **framing / Savant framing `pitches`: `B0_raw_persistence`**
  - prior framing pitches.

For P1/H1, source-year MLB PA <= 0 falls safely back to raw persistence. The development folds had zero such fallbacks.

Framing's hybrid improved overall MAE/RMSE but failed the preregistered continuing-catcher MAE guardrail in 2022->2023, so persistence remained binding. Do not retune the 2% guardrail or 50/50 weight.

## Defensive run conversion — DONE / FROZEN

Source-semantics audit: `docs/player-value-v1-defense-native-semantics-audit-result.json`, run `32266817048`.

Run-rate calibration diagnostic: `docs/player-value-v1-defense-native-run-rate-calibration-result.json`, run `32267920355`, artifact digest `sha256:d78d857ebe608d5fe86e29cc57db66bb2d1e68fd0636683148ff97e0f4ffb934`.

Binding selection contract: `docs/player-value-v1-defense-native-run-conversion-selection-contract.md`.

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`, run `32268659408`, artifact digest `sha256:9bb18bcb62d1e8b9521a502a2a19ae1143897f2b7a177b9592ec5bc70fadb5dc`.

Common zero-intercept formula:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`.

Neutral `z = 0` maps to zero modeled runs.

### General range run rates

Apply separately by projected position outs and sum across positions. T1 and U1 use the same rule.

- 1B: `0.0014221370829147768` runs per `z x fielding_out`;
- 2B: `0.002430213267969069`;
- 3B: `0.0018120617732267537`;
- SS: `0.002042627635059078`;
- LF: `0.0021198415668483013`;
- CF: `0.0022070977120912877` — OF-group stability fallback;
- RF: `0.0022070977120912877` — OF-group stability fallback.

CF/RF position-specific three-year slopes failed the predeclared stability gate; the pooled OF calibration passed. Do not substitute their unstable position-specific scales.

### Catcher run rates

- throwing: `0.05862747110425751` runs per `z x projected_sb_attempt`;
- blocking: `0.0006466287170316754` runs per `z x projected_blocking_pitch`;
- framing: `0.001189541187787062` runs per `z x projected_framing_pitch`.

Blocking uses Savant `pitches`, not `n_pbwp`, as the native opportunity. `n_pbwp` failed the predeclared denominator identity; pitch-based calibration was more accurate and more stable.

**Defense skill -> exposure -> seasonal defensive runs is now fully specified for v1. Do not reopen it absent a concrete implementation failure.**

## ACTIVE STAGE

**Positional adjustment, with the batting projected-runs reuse audit still open in parallel.**

### Immediate next batch

1. Research established public positional-adjustment conventions and their current formulas from authoritative/public methodology sources.
2. Audit what the frozen Position/Role and defensive-exposure surfaces can support without conflating batting role with defensive exposure.
3. Predeclare a transparent v1 positional-adjustment selection/weighting rule before calculating player values.
4. Separately finish the batting projected-runs reuse audit using the already-certified Performance RE24/bin-value infrastructure; do not rebuild batting run values.
5. Only after batting runs and positional adjustment are frozen should replacement level, runs per win, and WAR/value aggregation open.

## Binding boundaries

- Current Talent, Projection, Playing Time, Position/Role, Defense skill, general defensive exposure, catcher native-opportunity forecasts, and defensive run conversion are frozen.
- Do not tune any Defense downstream decision to 2025 Defense confirmation residuals.
- Do not use 2025 as an allegedly untouched holdout for a newly designed downstream gate when its relevant outcomes were already accessed upstream.
- No arbitrary universal Defense `runs per z` constant.
- Positional adjustment remains separate from Defense skill/runs.
- **Replacement level, runs per win, WAR/value aggregation, and final ranking are not authorized yet.**

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-architecture-contract.md`
3. `docs/player-value-v1-defense-production-handoff.md`
4. `docs/player-value-v1-defense-exposure-contract.md`
5. `docs/player-value-v1-defensive-exposure-diagnostic-result.json`
6. `docs/player-value-v1-defensive-position-allocation-result.json`
7. `docs/player-value-v1-defense-native-semantics-audit-result.json`
8. `docs/player-value-v1-defense-native-run-rate-calibration-result.json`
9. `docs/player-value-v1-defense-native-run-conversion-selection-contract.md`
10. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
11. `docs/player-value-v1-catcher-native-opportunity-selection-contract.md`
12. `docs/player-value-v1-catcher-native-opportunity-selection-result.json`
13. `docs/defense-v1-development-checkpoint.md`
14. `docs/position-role-2025-confirmation-result.json`
15. `docs/playing-time-v1-confirmation-result.json`
16. `docs/projection-batting-v1-development-result.json`
17. `docs/current-talent-results-only-baseline-freeze.md`
18. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure.
- Repair only the scope affected by a verified implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening any genuinely unopened confirmation period.
