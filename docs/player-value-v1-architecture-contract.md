# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream Player Value architecture while preserving frozen upstream batting, playing-time, role, Defense, position, replacement, and runs-per-win decisions.

Binding literature record: `docs/player-value-v1-war-literature-review.md`.

## Status

**ARCHITECTURE FROZEN — BATTING / DEFENSE / POSITION / REPLACEMENT / RUNS PER WIN FROZEN — BASERUNNING ACTIVE — CENTERING / PARK AUDIT REQUIRED — WAR CLOSED.**

WAR/value aggregation is not yet authorized.

## Frozen upstream inputs

Player Value v1 consumes frozen outputs from:

1. batting Performance / Current Talent / Projection;
2. Playing Time v1;
3. Position / Role v1;
4. Defense v1.

No downstream value decision may alter an upstream coefficient, threshold, fallback, confirmation result, or evidence-eligibility rule.

## 1. Batting runs — FROZEN / VERIFIED

Contract: `docs/player-value-v1-batting-runs-contract.md`.

Implementation: `src/universal_baseball/player_value_batting_runs.py`.

Verification: `docs/player-value-v1-batting-runs-verification.json`, Actions run `32275192829`.

Binding form:

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

The 12 projected batting probabilities are a mutually exclusive composition conditional on a core event. One pooled certified MLB coverage/value environment is applied to every player; source/taxonomy coverage is not a talent term.

## 2. Defense — FROZEN

Defense skill, exposure, catcher opportunities, and native run conversion are frozen.

Common conversion:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`.

General defensive exposure remains prior-season MLB fielding-out persistence with prior-position shares. Catcher throwing/blocking use their frozen 50/50 opportunity hybrids; framing uses raw opportunity persistence.

## 3. Positional adjustment — FROZEN / VERIFIED

Contract: `docs/player-value-v1-positional-adjustment-contract.md`.

Verification: `docs/player-value-v1-positional-adjustment-verification.json`, Actions run `32270697293`.

Binding FanGraphs full-season schedule:

- C +12.5
- 1B -12.5
- 2B +2.5
- 3B +2.5
- SS +7.5
- LF -7.5
- CF +2.5
- RF -7.5
- DH -17.5

Non-DH:

`Rpos[p] = schedule_runs[p] * projected_position_fielding_outs[p] / 4374`

DH:

`Rpos[DH] = -17.5 * projected_DH_role_events / 162`

Do not center inside this component. Aggregate imbalance belongs in the later MLB-reference centering layer.

## 4. Replacement level — FROZEN / VERIFIED

Contract: `docs/player-value-v1-replacement-level-contract.md`.

Materialization: `docs/player-value-v1-replacement-level-2024.json`.

Verification: `docs/player-value-v1-replacement-level-verification.json`, Actions run `32280808517`.

Binding convention: `fangraphs_570_war_pool_projected_pa_v1`.

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

Frozen 2024 reference:

- MLB games `2429`;
- MLB PA `182449`;
- RPW `9.682629939156854`;
- replacement runs/600 PA `18.142586140136086`.

Required sensitivities are already materialized:

- 590-WAR allocation `18.779168109965422` runs/600;
- legacy 20.5/600 comparison.

The prior fixed 20.5/600 implementation is superseded for final WAR but retained for provenance.

## 5. Runs per win — FROZEN / VERIFIED

Contract: `docs/player-value-v1-runs-per-win-contract.md`.

Verification: `docs/player-value-v1-runs-per-win-verification.json`, Actions run `32275833614`.

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Frozen 2024 reference RPW: `9.682629939156854`.

Use one common position-player divisor for the snapshot. Baseball-Reference/PythagenPat remains a non-binding sensitivity.

## 6. Baserunning / GIDP — ACTIVE

Both major public position-player WAR systems include baserunning; Baseball-Reference also preserves a separate GIDP term. Player Value v1 must resolve these before final WAR.

The gate must audit mature public evidence and predeclare a universal hierarchy before ranking outcomes are inspected. Preferred investigation order:

1. MLB Statcast Baserunning Run Value / underlying public opportunity data;
2. comparable affiliated MiLB advancement evidence where available;
3. SB/CS-based run value as a lower-information fallback;
4. neutral fallback where evidence is insufficient.

GIDP avoidance must be audited separately for source quality and overlap. Do not double-count it with batting or baserunning.

## 7. MLB-reference centering — REQUIRED AFTER BASERUNNING

Average-relative components cannot be assumed to aggregate exactly to zero.

Use a fixed certified MLB reference population, never the loaded universal ranking population.

Candidate form:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdp_if_separate + Rdef + Rpos)`

`centering_runs_per_pa = -Ravg_raw_ref / aggregate_reference_MLB_PA`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

The exact reference population and exposure semantics must be predeclared before this gate freezes.

## 8. Park-neutrality audit — REQUIRED

Traditional WAR park-adjusts observed offense, but the frozen batting projection already values one projected core-event composition in a common pooled MLB RE24 environment.

Before adding any park term:

1. test frozen batting/current-talent outputs for systematic park/team residuals;
2. document the result;
3. add an explicit correction only if a material residual-context problem is demonstrated.

Avoid double-adjusting a projection that is already effectively park-neutral.

## 9. Confirmation-period firewall

Completed 2025 confirmation periods are not new development samples. Downstream gates may consume frozen decisions but may not retune new coefficients to already-accessed 2025 residuals or relabel those outcomes as untouched holdouts.

## 10. WAR/value remains closed

No final WAR calculation is authorized until:

1. batting run conversion — **DONE**;
2. Defense run conversion/exposure — **DONE**;
3. positional adjustment — **DONE**;
4. replacement level — **DONE**;
5. runs per win — **DONE**;
6. baserunning/GIDP — **ACTIVE / NOT FROZEN**;
7. MLB-reference centering — **REQUIRED**;
8. park-neutrality audit — **REQUIRED**;
9. remaining sensitivities — **NOT COMPLETE**.

## 11. Required final decomposition

Persist separate fields for at least:

- projected batting runs;
- projected baserunning runs;
- projected GIDP runs if separate;
- general Defense runs;
- catcher throwing/blocking/framing runs;
- positional adjustment runs;
- MLB-reference centering runs;
- park adjustment if justified;
- replacement runs;
- runs above replacement;
- RPW;
- WAR;
- projected MLB PA and defensive/native opportunities;
- evidence coverage, fallback flags, and provenance.

Intended final form:

`RAR = Rbat + Rbr + Rdp_if_separate + Rdef + Rpos + Rlg + Rpark_if_required + Rrep`

`WAR = RAR / RPW`

## 12. Required sensitivities before final WAR freeze

Without retuning from rankings:

- Baseball-Reference positional schedule versus binding FanGraphs schedule;
- alternate recent certified MLB batting reference season when available;
- replacement 570 vs 590 WAR allocation and legacy 20.5/600 comparison;
- Baseball-Reference/PythagenPat run-to-win comparison if practical;
- sensitivities predeclared by baserunning and centering gates.

## Binding boundaries

- Do not refit frozen upstream stages absent a concrete implementation failure.
- Do not tune downstream decisions to already-accessed confirmation residuals.
- Do not center against the universal ranking population.
- Do not add a park correction without evidence of residual park context.
- Do not use superseded 20.5/600 replacement for final WAR.
- Do not calculate final WAR yet.
