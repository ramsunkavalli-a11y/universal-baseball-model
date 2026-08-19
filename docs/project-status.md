# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Integrated branch: `main`
- Active branch: `source-certification-poc`
- Work in small verified batches and inspect the active branch head before editing.
- Prefer certified/reusable public data and existing adapters over rebuilding source cleanup.
- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, batting runs, baserunning, positional adjustment, MLB-reference centering, replacement level, runs per win, WAR/value, and final ranking as explicit layers.

## Current downstream status

A broader public WAR-methodology review was completed **before final WAR aggregation**. It identified a material correction to replacement level and two missing required layers.

Binding literature record:

- `docs/player-value-v1-war-literature-review.md`

Current state:

- **Performance:** DONE / FROZEN
- **Current Talent:** DONE / FROZEN
- **Projection v1 batting:** DONE / FROZEN
- **Playing Time v1:** DONE / FROZEN
- **Position / Role v1:** DONE / FROZEN
- **Defense v1:** DONE / FROZEN
- **Positional adjustment:** DONE / FROZEN / VERIFIED
- **Batting projected runs:** DONE / FROZEN / VERIFIED
- **Runs per win method:** DONE / FROZEN / VERIFIED
- **Replacement level:** **REOPENED / ACTIVE** after literature review
- **Baserunning / GIDP:** **REQUIRED / NOT YET FROZEN**
- **MLB-reference centering:** **REQUIRED / NOT YET FROZEN**
- **Park-neutrality audit:** **REQUIRED**; correction only if residual context is demonstrated
- **WAR/value aggregation:** **CLOSED**
- **Final ranking:** **CLOSED**

## Frozen upstream stages

- **Current Talent:** `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** `playing_time_recent_opportunity_40man_b2_hurdle_v1`, frozen and 2025-confirmed.
- **Position / Role v1:** `primary_share_thresholded_transition_mean_v1`, frozen and 2025-confirmed.

Do not reopen these stages absent a concrete implementation failure.

## Defense v1 — DONE / FROZEN

Defense skill, exposure, native opportunity forecasts, and run conversion are frozen.

Final skill hierarchy:

- **General range:** eligible tracked MLB -> T1; otherwise eligible MLB/affiliated MiLB -> U1; otherwise neutral B0.
- **Catcher throwing:** repaired C2 when eligible; otherwise neutral B0.
- **Catcher blocking:** repaired C2 when eligible; otherwise neutral B0.
- **Framing:** eligible tracked MLB catcher -> F1; otherwise F0 neutral; MiLB framing remains F0.

Important throwing implementation note: repaired C2 uses **steal attempts** for its two-season feature weighting/eligibility even though an old parameter artifact contains a metadata-only `exposure: fielding_outs` label. Follow fitted `_catcher_matrix` semantics.

General defensive exposure:

- projected total defensive outs = prior-season MLB defensive outs;
- projected position shares = prior defensive-out shares;
- projected position outs therefore equal prior-season position outs algebraically.

Catcher native opportunities:

- throwing `sb_attempts`: `H1_fixed_50_50_hybrid`;
- blocking Savant `pitches`: `H1_fixed_50_50_hybrid`;
- framing Savant `pitches`: `B0_raw_persistence`.

Common run conversion:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`

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

Binding FanGraphs 162-game schedule:

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

DH exposure remains prior-season DH role-event persistence. Do not renormalize player exposure or league-center inside the positional component; any aggregate imbalance belongs in the separate MLB-reference centering layer.

Implementation: `src/universal_baseball/player_value_positional_adjustment.py`.

Verification: `docs/player-value-v1-positional-adjustment-verification.json`, Actions run `32270697293`.

Baseball-Reference's current raw positional schedule remains a required non-binding sensitivity before final WAR.

## Batting projected runs — DONE / FROZEN / VERIFIED

Binding contract: `docs/player-value-v1-batting-runs-contract.md`.

Implementation: `src/universal_baseball/player_value_batting_runs.py`.

Verification: `docs/player-value-v1-batting-runs-verification.json`, Actions run `32275192829`.

The frozen 12-bin batting Projection is a **mutually exclusive simplex conditional on a core event**. It is not directly a set of PA shares.

Player Value uses one pooled certified MLB reference environment:

`coverage_mlb = aggregate MLB core_profile_event_count / aggregate MLB PA`

`P_ref[b] = aggregate MLB occurrence_count[b] / aggregate MLB core events`

`RV_ref_core = sum_b(P_ref[b] * V_mlb[b])`

`RV_i_core = sum_b(P_i[b] * V_mlb[b])`

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

The same MLB coverage is applied to every player; source/taxonomy coverage is not an authorized talent term.

## Runs per win — DONE / FROZEN / VERIFIED

Binding contract: `docs/player-value-v1-runs-per-win-contract.md`.

Binding method:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Implementation verification: `docs/player-value-v1-runs-per-win-verification.json`, Actions run `32275833614`.

The certified 2024 MLB reference environment contains **21,343 runs over 43,116 1/3 innings**, approximately **9.68263 runs per win**. Production should use the exact persisted value rather than this rounded documentation value.

The literature review retained this common FanGraphs/Tango position-player RPW method. Baseball-Reference/PythagenPat remains a sensitivity.

## Replacement level — REOPENED / ACTIVE

Binding contract: `docs/player-value-v1-replacement-level-contract.md`.

The earlier `20.5 runs / 600 projected MLB PA` convention was implemented and mechanically verified in Actions run `32275638045`, but is **superseded for final WAR**.

Why: Baseball-Reference does not simply stop at 20.5/600; it works from a league replacement framework and fine-tunes/re-centers replacement runs to a target league WAR total. FanGraphs directly derives position-player replacement credit from its league WAR allocation, league PA, and RPW.

Predeclared binding candidate:

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

This uses FanGraphs' 57% / 570-WAR position-player allocation. Required sensitivities include Baseball-Reference's 59% / 590-WAR allocation and the legacy 20.5/600 result.

The replacement gate is not refrozen until completed-reference-season MLB games, MLB PA, RPW, and the resulting run rate are materialized and verified.

## Baserunning / GIDP — REQUIRED

The literature review confirmed that both major public position-player WAR systems include baserunning; Baseball-Reference also preserves GIDP runs separately.

Preferred evidence hierarchy to investigate:

1. MLB Statcast Baserunning Run Value / underlying public opportunity data;
2. comparable affiliated MiLB advancement evidence where available;
3. SB/CS-based run value as a lower-information fallback;
4. neutral fallback where evidence is insufficient.

GIDP avoidance must be audited for a clean, non-double-counted implementation.

Do not silently omit baserunning from a final metric called WAR.

## MLB-reference centering — REQUIRED

FanGraphs explicitly applies a league adjustment, and Baseball-Reference likewise ensures an average-relative baseline. Our independently constructed run components cannot be assumed to sum exactly to zero.

Use a fixed certified MLB reference population, **not the loaded universal ranking population**.

Candidate form:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdp_if_separate + Rdef + Rpos)`

`centering_runs_per_pa = -Ravg_raw_ref / aggregate_reference_MLB_PA`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

This is especially relevant in the universal-DH era because the fixed positional schedule is not automatically zero-sum after DH exposure is included.

## Park-neutrality audit — REQUIRED

Traditional WAR park-adjusts observed batting. Our frozen batting projection already values a common projected core-event composition in one pooled MLB RE24 environment, so blindly applying a conventional park factor risks double adjustment.

Before any park term is added:

- test frozen batting/current-talent outputs for systematic park/team residuals;
- document the result;
- add an explicit correction only if residual context is demonstrated.

## ACTIVE STAGE

**Replacement-level revision/refreeze.**

### Immediate next batches

1. Materialize/certify completed-reference-season MLB **games + position-player PA** and combine them with frozen RPW.
2. Calculate and verify the FanGraphs 570-WAR replacement rate and required 590-WAR / legacy-20.5 sensitivities; refreeze replacement if clean.
3. Open the baserunning/GIDP source-and-model audit.
4. Freeze MLB-reference centering after relevant components are available.
5. Complete the park-neutrality audit.
6. Run required positional, batting-reference, replacement, and RPW sensitivities.
7. Only then authorize WAR aggregation and ranking QA.

## Binding boundaries

- Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, batting projected runs, positional adjustment, and the RPW method are frozen.
- **Replacement level is reopened. Do not use the superseded 20.5/600 implementation for final WAR.**
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not use 2025 as an allegedly untouched holdout for a newly designed downstream gate where relevant outcomes were already opened.
- Do not add an arbitrary universal Defense `runs per z` constant.
- Do not make source/taxonomy coverage a player batting-talent term.
- Keep positional adjustment separate from position-relative Defense skill.
- Do not center against the universal ranking population.
- Do not add a park correction without evidence of residual park context.
- **WAR/value aggregation and final ranking remain unauthorized.**

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-war-literature-review.md`
3. `docs/player-value-v1-architecture-contract.md`
4. `docs/player-value-v1-replacement-level-contract.md`
5. `docs/player-value-v1-runs-per-win-contract.md`
6. `docs/player-value-v1-batting-runs-contract.md`
7. `docs/player-value-v1-batting-runs-verification.json`
8. `docs/player-value-v1-positional-adjustment-contract.md`
9. `docs/player-value-v1-positional-adjustment-verification.json`
10. `docs/player-value-v1-defense-production-handoff.md`
11. `docs/player-value-v1-defense-exposure-contract.md`
12. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
13. `docs/player-value-v1-catcher-native-opportunity-selection-result.json`
14. `docs/projection-batting-v1-development-result.json`
15. `docs/current-talent-results-only-baseline-freeze.md`
16. `docs/performance-2024-affiliated-checkpoint.md`

## Working rules

- Do not redo settled work absent a concrete implementation failure or a documented methodology correction such as the replacement-level reopening above.
- Repair only the scope affected by a verified failure or literature-driven architecture issue.
- Do not tune rejected models against held-out failure periods.
- Preserve immutable raw/source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening any genuinely unopened confirmation period.
