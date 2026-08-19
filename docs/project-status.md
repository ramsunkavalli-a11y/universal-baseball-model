# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches and inspect the active branch head before editing.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, batting runs, positional adjustment, replacement level, runs per win, WAR/value, and final ranking as explicit layers.

## Frozen upstream stages

- **Performance:** completed-2024 affiliated batting materialization retained; certified MLB Performance/RE24 bin-value infrastructure is the batting value foundation.
- **Current Talent:** `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** `playing_time_recent_opportunity_40man_b2_hurdle_v1`, frozen and 2025-confirmed.
- **Position / Role v1:** `primary_share_thresholded_transition_mean_v1`, frozen and 2025-confirmed.

Do not reopen these stages absent a concrete implementation failure.

## Defense v1 — DONE / FROZEN

Defense skill, exposure, native opportunity forecasts, and run conversion are fully frozen.

Final skill hierarchy:

- **General range:** eligible tracked MLB -> T1; otherwise eligible MLB/affiliated MiLB -> U1; otherwise neutral B0.
- **Catcher throwing:** repaired C2 when eligible; otherwise neutral B0.
- **Catcher blocking:** repaired C2 when eligible; otherwise neutral B0.
- **Framing:** eligible tracked MLB catcher -> F1; otherwise F0 neutral; MiLB framing remains F0.

Important throwing implementation note: repaired C2 uses **steal attempts** for its two-season feature weighting/eligibility even though an old parameter artifact contains a metadata-only `exposure: fielding_outs` label. Follow fitted `_catcher_matrix` semantics.

General defensive exposure:

- projected total defensive outs = `B0_raw_persistence` = prior-season MLB defensive outs;
- projected position shares = `S0_prior_defensive_share_persistence` = prior-season defensive-out shares;
- therefore projected position outs equal prior-season position outs algebraically.

Catcher native opportunities:

- throwing `sb_attempts`: `H1_fixed_50_50_hybrid`;
- blocking Savant `pitches`: `H1_fixed_50_50_hybrid`;
- framing Savant `pitches`: `B0_raw_persistence`.

Common run conversion:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`.

General range run rates per `z x fielding_out`:

- 1B `0.0014221370829147768`
- 2B `0.002430213267969069`
- 3B `0.0018120617732267537`
- SS `0.002042627635059078`
- LF `0.0021198415668483013`
- CF `0.0022070977120912877` — OF-group fallback
- RF `0.0022070977120912877` — OF-group fallback

Catcher run rates:

- throwing `0.05862747110425751` per `z x projected_sb_attempt`;
- blocking `0.0006466287170316754` per `z x projected_blocking_pitch`;
- framing `0.001189541187787062` per `z x projected_framing_pitch`.

Key records:

- `docs/player-value-v1-defense-production-handoff.md`
- `docs/player-value-v1-defense-exposure-contract.md`
- `docs/player-value-v1-defensive-exposure-diagnostic-result.json` — run `32261447127`
- `docs/player-value-v1-defensive-position-allocation-result.json` — run `32266007594`
- `docs/player-value-v1-defense-native-semantics-audit-result.json` — run `32266817048`
- `docs/player-value-v1-defense-native-run-rate-calibration-result.json` — run `32267920355`
- `docs/player-value-v1-defense-native-run-conversion-parameters.json` — run `32268659408`
- `docs/player-value-v1-catcher-native-opportunity-selection-result.json` — run `32269076231`

**Do not reopen Defense absent a concrete implementation failure.**

## Positional adjustment — DONE / FROZEN / VERIFIED

Binding contract: `docs/player-value-v1-positional-adjustment-contract.md`.

Binding schedule is the fixed FanGraphs 162-game convention:

- C `+12.5`
- 1B `-12.5`
- 2B `+2.5`
- 3B `+2.5`
- SS `+7.5`
- LF `-7.5`
- CF `+2.5`
- RF `-7.5`
- DH `-17.5`

Non-DH:

`Rpos[p] = schedule_runs[p] * projected_position_fielding_outs[p] / 4374`

DH:

`Rpos[DH] = -17.5 * projected_DH_role_events / 162`

DH exposure is frozen at `B0_raw_dh_role_event_persistence` = prior-season DH role events. Do not renormalize player exposure or league-center Rpos inside this layer.

Implementation: `src/universal_baseball/player_value_positional_adjustment.py`.

Verification: `docs/player-value-v1-positional-adjustment-verification.json`, Actions run `32270697293`.

A Baseball-Reference current raw schedule remains a required non-binding sensitivity before final WAR aggregation; it may not retune the binding schedule after ranking outcomes are seen.

## Batting projected runs — DONE / FROZEN / VERIFIED

Binding contract: `docs/player-value-v1-batting-runs-contract.md`.

Implementation: `src/universal_baseball/player_value_batting_runs.py`.

Verification: `docs/player-value-v1-batting-runs-verification.json`, Actions run `32275192829`, source SHA `0d054fe735f1f53eafad2fa880335067adc66ebe`.

Important semantic finding: the frozen 12-bin batting Projection is a **mutually exclusive simplex conditional on a core event**. It is not a set of overlapping probabilities and it is not directly a set of PA shares. Performance separately preserves core-taxonomy PA coverage.

Player Value v1 therefore uses one pooled certified MLB reference environment for every player rather than projecting player-specific `core_events / PA`.

For the latest certified MLB Performance materialization available to the Player Value snapshot:

- pool AL/NL certified bin values by their actual core-bin occurrence counts;
- `coverage_mlb = aggregate MLB core_profile_event_count / aggregate MLB PA`;
- `P_ref[b] = aggregate MLB occurrence_count[b] / aggregate MLB core events`;
- `RV_ref_core = sum_b(P_ref[b] * V_mlb[b])`.

For player `i`:

`RV_i_core = sum_b(P_i[b] * V_mlb[b])`

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

This places every player in the same MLB opportunity/reporting environment and prevents source coverage, excluded event classes, or MiLB/MLB coverage differences from becoming accidental projected batting talent.

No separate core-event-rate forecast is authorized for v1.

## ACTIVE STAGE

**Replacement level.**

Batting runs, Defense runs, and positional adjustment are now frozen and mechanically verified. Replacement level is the next unopened Player Value gate.

### Immediate next batch

1. Research established public replacement-level conventions from authoritative methodology sources and identify what is compatible with the frozen Playing Time/position architecture.
2. Predeclare the v1 replacement-level form and any necessary population/exposure assumptions **before** inspecting final ranking outcomes.
3. Validate/implement the replacement-run calculation independently of runs per win.
4. After replacement level freezes, select the runs-per-win convention.
5. Only then authorize WAR/value aggregation, required sensitivities, QA, and final ranking.

## Binding boundaries

- Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, batting projected runs, and positional adjustment are frozen.
- Do not tune downstream decisions to 2025 confirmation residuals that were already accessed upstream.
- Do not use 2025 as an allegedly untouched holdout for a newly designed downstream gate where relevant outcomes were already opened.
- Do not add an arbitrary universal Defense `runs per z` constant.
- Do not make source/taxonomy coverage a player batting-talent term.
- Keep positional adjustment separate from position-relative Defense skill.
- **Replacement level is now authorized for research/selection. Runs per win, WAR/value aggregation, and final ranking are not yet authorized.**

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-architecture-contract.md`
3. `docs/player-value-v1-batting-runs-contract.md`
4. `docs/player-value-v1-batting-runs-verification.json`
5. `docs/player-value-v1-positional-adjustment-contract.md`
6. `docs/player-value-v1-positional-adjustment-verification.json`
7. `docs/player-value-v1-defense-production-handoff.md`
8. `docs/player-value-v1-defense-exposure-contract.md`
9. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
10. `docs/player-value-v1-catcher-native-opportunity-selection-result.json`
11. `docs/defense-v1-development-checkpoint.md`
12. `docs/position-role-2025-confirmation-result.json`
13. `docs/playing-time-v1-confirmation-result.json`
14. `docs/projection-batting-v1-development-result.json`
15. `docs/current-talent-results-only-baseline-freeze.md`
16. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure.
- Repair only the scope affected by a verified implementation failure.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening any genuinely unopened confirmation period.
