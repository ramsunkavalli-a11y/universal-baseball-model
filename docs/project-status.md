# Project status and handoff

Last updated: 2026-08-19

This is the **canonical start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Active branch: `source-certification-poc`
- `main` is behind active work; use the active branch.
- Work in small verified batches and inspect branch head before editing.
- Prefer certified/reusable public data, mature parsers, and existing adapters over rebuilding raw-source cleanup.
- Preserve every Player Value component as an explicit layer with provenance.

## Governing methodology record

`docs/player-value-v1-war-literature-review.md`

A broader WAR literature review was completed before final aggregation. It caused one material course correction: fixed 20.5 replacement runs/600 PA was superseded by a FanGraphs league-WAR-pool construction. It also promoted baserunning, MLB-reference centering, and a park-neutrality audit to required pre-WAR gates.

## Current state

- **Performance:** DONE / FROZEN
- **Current Talent:** DONE / FROZEN
- **Projection v1 batting:** DONE / FROZEN
- **Playing Time v1:** DONE / FROZEN
- **Position / Role v1:** DONE / FROZEN
- **Defense v1:** DONE / FROZEN
- **Positional adjustment:** DONE / FROZEN / VERIFIED
- **Batting projected runs:** DONE / FROZEN / VERIFIED
- **Runs per win:** DONE / FROZEN / VERIFIED
- **Replacement level:** DONE / REFROZEN / VERIFIED
- **Baserunning:** **DONE / FROZEN / VERIFIED**
- **GIDP:** **RAW TERM NON-ADDITIVE; RESIDUAL OMITTED FOR v1**
- **MLB-reference centering:** **ACTIVE**
- **Park-neutrality audit:** REQUIRED NEXT
- **WAR/value aggregation:** CLOSED
- **Final ranking:** CLOSED

## Frozen upstream models

- Current Talent: `translated_multiseason_recency_empirical_bayes_v1`
- Projection batting: `frozen_current_talent_carry_forward_v1`
- Playing Time: `playing_time_recent_opportunity_40man_b2_hurdle_v1`
- Position / Role: `primary_share_thresholded_transition_mean_v1`
- Steal attempt propensity: `B2_k5`
- Steal success skill: `B2_k45`
- Non-steal advancement: `A2_k25`

Do not reopen these absent a concrete implementation failure.

## Defense v1 — frozen

Final skill hierarchy:

- general range: tracked MLB T1 -> affiliated U1 -> neutral B0;
- catcher throwing: repaired C2 -> B0;
- catcher blocking: repaired C2 -> B0;
- framing: eligible MLB F1 -> F0; MiLB framing remains F0.

Important catcher throwing implementation: fitted repaired C2 weights by **steal attempts** and requires original steal-attempt eligibility, despite an older metadata-only `fielding_outs` label.

General defensive exposure is prior-season MLB defensive-out persistence with prior-position shares. Catcher opportunity forecasts remain:

- throwing `sb_attempts`: fixed 50/50 persistence / Playing-Time-ratio hybrid;
- blocking pitches: fixed 50/50 hybrid;
- framing pitches: raw persistence.

Native run conversion:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`.

Key verification records include runs `32266007594`, `32266817048`, `32267920355`, `32268659408`, and `32269076231`.

## Positional adjustment — frozen / verified

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

Verification: Actions run `32270697293`.

Do not center inside the positional layer. Baseball-Reference's raw current schedule remains a final sensitivity.

## Batting projected runs — frozen / verified

The 12 projected batting bins are a mutually exclusive simplex conditional on a core event. Player Value uses one pooled certified MLB reference environment and common core-event coverage:

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

Verification: Actions run `32275192829`.

Do not add player-specific taxonomy/source coverage as talent.

## Runs per win — frozen / verified

Binding method:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

2024 certified MLB reference:

- runs: `21343`
- innings: `43116.333333333336`
- RPW: `9.682629939156854`

Verification: Actions run `32275833614`.

Baseball-Reference/PythagenPat remains a non-binding sensitivity.

## Replacement level — refrozen / verified

Binding contract: `docs/player-value-v1-replacement-level-contract.md`.

Binding convention: `fangraphs_570_war_pool_projected_pa_v1`.

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

2024 certified reference:

- completed MLB games: `2429`
- MLB PA: `182449`
- RPW: `9.682629939156854`
- prorated position-player replacement pool: `569.7654320987654 WAR`
- replacement runs/PA: `0.030237643566893475`
- replacement runs/600 PA: `18.142586140136086`

Materialization: `docs/player-value-v1-replacement-level-2024.json`.

Verification: Actions run `32280808517`.

Required replacement sensitivities already materialized:

- 590-WAR position-player allocation: `18.779168109965422` runs/600 PA;
- legacy fixed convention: `20.5` runs/600 PA.

The earlier 20.5 implementation remains in history/provenance but is **not authorized for final WAR**.

## Baserunning / GIDP — frozen / verified

### Source / overlap gate

Binding source/overlap contract: `docs/player-value-v1-baserunning-source-audit-contract.md`.

The live source audit established:

- official 2024 MLB season hitting output has complete `groundIntoDoublePlay` counts but **no `gidpOpp` field in any of 780 pooled AL/NL player rows**;
- therefore the preferred official bulk source cannot directly support an opportunity-adjusted MLB GIDP residual;
- public Baseball Savant runner-level baserunning-run-value CSV is certified for **2019–2024** with all required advancement fields complete, zero duplicate runner IDs, and internally consistent component opportunity counts;
- certified Savant runner-row counts by season are `659, 517, 680, 625, 611, 608` for 2019 through 2024;
- raw GIDP run value is **not additive** because PA-level RE24 already feeds the frozen ground-ball bin values used in `Rbat`.

Source materialization: `docs/player-value-v1-baserunning-source-audit-result.json`.

### Portable steal projection

The chronological steal gate used 2022–2023 development targets and held out 2024. Frozen methods:

- attempt propensity: `B2_k5` — three-season recency empirical Bayes, prior strength 5;
- success skill: `B2_k45` — three-season recency empirical Bayes, prior strength 45.

Both beat the neutral baseline in development and confirmed on 2024. Result: `docs/player-value-v1-steal-projection-selection-result.json`.

### Non-steal advancement projection

The predeclared Savant persistence gate used 2019–2024 source seasons, 2022–2023 development targets, and held out 2024. Frozen method:

- advancement rate: `A2_k25` — up to three prior MLB Savant seasons with `1.00 / 0.50 / 0.25` recency weights and a prior of 25 non-steal advancement opportunities.

Development equal-year primary score improved from `0.0035781987760809303` for `A0_neutral` to `0.0026695655379876298` for `A2_k25`. On held-out 2024 it improved from `0.0032647343977582704` to `0.0023445732494996718`, so the preselected player-specific method confirmed without opening alternative 2024 candidates.

Result: `docs/player-value-v1-advancement-projection-selection-result.json`.

### Run conversion and final v1 baserunning definition

Binding contract: `docs/player-value-v1-baserunning-run-conversion-contract.md`.

Materialization: `docs/player-value-v1-baserunning-run-conversion-2024.json`.

Verified 2024 reference constants include:

- MLB PA: `182449`;
- steal opportunity proxy: `42342`;
- steal attempts: `4578`;
- stolen bases: `3617`;
- caught stealing: `961`;
- common steal opportunity rate: `0.2320758129669113` per MLB PA;
- common steal attempt rate: `0.1081195975627037` per portable steal opportunity;
- MLB steal success probability: `0.790083005679336`;
- Savant non-steal advancement opportunities: `12931`;
- common advancement opportunity rate: `0.0708746005733109` per MLB PA.

Frozen production form:

`Rbr_i = Rsteal_i + Radvance_i`

Steal opportunity exposure and advancement opportunity exposure both scale from **common fixed MLB reference rates per projected MLB PA**, not from the player's projected batting outcomes.

The steal conversion uses the public wSB-style opportunity-centering convention with `runSB = +0.2` and the certified 2024 MLB runs/out environment. Mechanical verification shows a neutral steal player produces `-2.220446049250313e-16` runs at 600 PA, effectively zero within the `1e-10` tolerance.

For advancement, the source-defined frozen `A2_k25` rate is multiplied by the common reference advancement-opportunity rate. MiLB-only/unsupported advancement history remains neutral rather than receiving an invented proxy.

### GIDP decision for v1

Do **not** build a conventional raw GIDP penalty. It would double-count value already present inside the frozen RE24 ground-ball bins.

The separate opportunity-adjusted residual is also now **omitted for v1**:

`Rgidp_residual_i = 0`

The preferred official MLB bulk opportunity denominator is unavailable, and this project will not create a custom play-by-play denominator solely to force a familiar WAR component into the model. Reopen only through a new predeclared gate if a mature, reproducible direct source or reusable implementation is certified first.

## ACTIVE STAGE — fixed-reference MLB centering

Use a fixed certified MLB reference population, not the loaded universal ranking population.

With the v1 GIDP residual omitted, the intended above-average reference total is:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdef + Rpos)`

Then:

`centering_runs_per_pa = -Ravg_raw_ref / aggregate_reference_MLB_PA`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

Before materializing a centering constant, identify and reuse the existing frozen component/reference assembly rather than building a parallel ranking-specific population. Replacement runs are **not** part of this centering total.

### After centering — park-neutrality audit

Test whether frozen batting/current-talent outputs retain systematic park/team residuals. Add an explicit park correction only if evidence demonstrates remaining context; do not blindly copy a conventional park adjustment and risk double-correction.

## WAR remains closed

Intended final decomposable form:

`RAR = Rbat + Rbr + Rdef + Rpos + Rlg + Rpark_if_required + Rrep`

`WAR = RAR / RPW`

Before final WAR freeze also complete:

- Baseball-Reference positional sensitivity;
- alternate recent certified MLB batting reference when available;
- replacement sensitivities above;
- PythagenPat run-to-win sensitivity if practical;
- any baserunning/centering sensitivities predeclared before outcomes.

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-war-literature-review.md`
3. `docs/player-value-v1-architecture-contract.md`
4. `docs/player-value-v1-replacement-level-contract.md`
5. `docs/player-value-v1-replacement-level-2024.json`
6. `docs/player-value-v1-replacement-level-verification.json`
7. `docs/player-value-v1-runs-per-win-contract.md`
8. `docs/player-value-v1-mlb-run-environment-2024.json`
9. `docs/player-value-v1-batting-runs-contract.md`
10. `docs/player-value-v1-positional-adjustment-contract.md`
11. `docs/player-value-v1-defense-production-handoff.md`
12. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
13. `docs/player-value-v1-baserunning-source-audit-contract.md`
14. `docs/player-value-v1-baserunning-source-audit-result.json`
15. `docs/player-value-v1-steal-projection-selection-contract.md`
16. `docs/player-value-v1-steal-projection-diagnostic-thresholds.md`
17. `docs/player-value-v1-steal-projection-selection-result.json`
18. `docs/player-value-v1-advancement-projection-selection-contract.md`
19. `docs/player-value-v1-advancement-projection-selection-result.json`
20. `docs/player-value-v1-baserunning-run-conversion-contract.md`
21. `docs/player-value-v1-baserunning-run-conversion-2024.json`
22. `docs/projection-batting-v1-development-result.json`
23. `docs/current-talent-results-only-baseline-freeze.md`

## Working rules

- Work in small verified batches.
- Preserve immutable source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening genuinely unused confirmation evidence.
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not center against the universal ranking population.
- Do not add park adjustment without evidence of residual park context.
- Do not calculate final WAR yet.
