# Project status and handoff

Last updated: 2026-08-20

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
- **MLB-reference centering:** **DONE / FROZEN / VERIFIED**
- **Park-neutrality audit:** **DONE / FROZEN / VERIFIED — `Rpark = 0`**
- **Required pre-WAR sensitivities:** **DONE / VERIFIED OR CONTRACTUALLY UNAVAILABLE**
- **WAR/value aggregation:** **ACTIVE — pre-outcome method/population frozen**
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

## COMPLETED STAGE — fixed-reference MLB centering

Binding contract: `docs/player-value-v1-mlb-centering-contract.md`.

### Membership / exposure gate — VERIFIED

The fixed reference population is now anchored to the certified pooled 2024 MLB Stats API population, not to the Playing Time validation target:

- official positive-PA reference players: **651**;
- official pooled MLB PA membership anchor: **182,449**;
- frozen Playing Time 2023-10-15 snapshot rows: **3,985**;
- Playing Time target players with positive observed 2024 PA: **645**;
- Playing Time observed-PA diagnostic total: **181,190**;
- aggregate frozen projected reference PA after membership reconciliation: **148,948.26306286638**.

Six official 2024 MLB hitters are outside the frozen eligible Playing Time/B2 snapshot and therefore have no authorized chronology-safe Playing Time prediction row: `543518`, `593934`, `622491`, `656555`, `666158`, `808982`. They remain in the official 651-player reference cohort with the predeclared structural fallback `projected_expected_mlb_pa = 0.0`; realized 2024 PA is not used to backfill exposure.

Binding membership materialization: `docs/player-value-v1-mlb-centering-2024-membership.json`.

Verification Actions run: **`32320525700`**. Tests, source-artifact download, membership materialization, and artifact upload all passed.

### Numerical centering reference — FROZEN / VERIFIED

With the v1 GIDP residual omitted, assemble the existing frozen historical 2024 component surfaces for the fixed 651-player membership:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdef + Rpos)`

Then:

`centering_runs_per_pa = -Ravg_raw_ref / 148948.26306286638`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

Do **not** use 182,449 observed official PA as the centering denominator; it is the membership/accounting anchor. The numerical centering denominator is frozen projected reference PA.

Before freezing the constant, reuse the existing frozen batting/B2, baserunning, Defense, defensive-position allocation, and DH-role artifacts. Do not build a ranking-specific player population, refit an upstream model, or use 2024 realized component outcomes as projected values. The six outside-snapshot members must remain explicit zero-exposure/fallback rows rather than being dropped.

The concrete numerical materializer and immutable input/column map are now present:

- `scripts/materialize_player_value_v1_mlb_centering_2024.py`;
- `src/universal_baseball/player_value_defense_projection.py`;
- `docs/player-value-v1-mlb-centering-source-map-2024.json`;
- `.github/workflows/player-value-v1-mlb-centering-materialize-2024.yml`.

Verified artifact-only component aggregates for the 651-player reference are:

- `Rbat = 258.49014809587965` runs;
- `Rdef = 75.99916554129656` runs;
- `Rpos = -470.90992226794697` runs;
- projected centering exposure remains exactly `148948.26306286638` PA.

The Savant byte drift was resolved through the narrow, predeclared source re-certification in `docs/player-value-v1-advancement-source-recertification-contract.md`. Actions run **`32378956567`** froze 3,700 projection-relevant player-season rows in artifact **`9410189065`** with canonical model-input SHA-256 `dfbd52dfaccd1cc20d2bf710c27755f169a7873fcd0efb45339debbb3ad4bbc8`. The largest primary-score relative drift was `0.0002302112248237264`, below the `0.001` gate; `A2_k25` remained the unique development winner and retained its 2024 confirmation verdict. No model was refit or reselected.

Final numerical materialization Actions run **`32379246845`** passed every workflow step and froze `docs/player-value-v1-mlb-centering-2024.json`. Its component artifact is **`9410315587`**, digest `sha256:d4180d36e78cd46b0e3df4479c8c708e855cb2ebf7b5ec6c49a21ed3d8955597`. The verified reference is:

- `Rbat = 258.49014809587965` runs;
- `Rbr = 35.008603291041524` runs;
- `Rdef = 75.99916554129656` runs;
- `Rpos = -470.90992226794697` runs;
- raw total `Ravg_raw_ref = -101.41200533972923` runs;
- `centering_runs_per_pa = 0.0006808538968791225`;
- aggregate `Rlg = 101.41200533972925` runs;
- post-centering residual `= 1.4210854715202004e-14` runs, within the binding `1e-10` tolerance.

All 651 component rows are explicit. The six outside-snapshot members remain present with projected exposure and all four components equal to zero. Replacement and realized 2024 player components are excluded, and the official `182,449` PA accounting anchor is preserved without being used as the centering denominator. The obsolete fail-closed blocker was removed by the verified workflow.

Legacy advancement-selection run **`32378956317`**, triggered by the shared projection-helper edit, failed at its intentional original-byte hash lock for the already-adjudicated 2019 Savant drift. Its 18 code tests passed before that source lock fired. This does not supersede or invalidate the successful re-certification; the frozen model remains `A2_k25`.

## COMPLETED STAGE — park-neutrality audit

Binding pre-outcome contract: `docs/player-value-v1-park-neutrality-audit-contract.md`.

Verified result: `docs/player-value-v1-park-neutrality-audit-result.json`.

Actions run **`32381035435`** passed all workflow steps, downloaded the four exact frozen source artifacts, and uploaded diagnostic artifact **`9411024828`** with digest `sha256:9a85d711b2d68ac553df35055b0d7c74edd90c07563b00925e6f911ba2171738`.

The predeclared primary test compared each same-team incumbent's 2023 home-minus-away signal with the frozen B2 projection minus 2024 away-only performance. It retained 251 players, 28 teams, and 55,988 away PA after all player/team exposure gates. Results were decisively below every material retained-context threshold:

- full-season retention slope: `-0.012703125674` versus required `>= 0.25`;
- fitted retained-context weighted SD: `0.072080770764` runs/600 PA versus required `>= 1.0`;
- one-sided 10,000-permutation p-value: `0.549945005499` versus required `<= 0.05`;
- first-/second-half slopes: `-0.047819950981` / `0.05284180674`, failing the same-positive-sign gate.

Realized 2024 venue context remained visible as expected: the 30 primary venues had a weighted residual SD of `3.799161849204` runs/600 PA. That secondary diagnostic does not show retained prior-park bias because it uses realized venue outcomes; it was predeclared as non-decisional. The primary out-of-time away-only retention test failed four of five gates, so no park-correction design gate opens and **`Rpark = 0` is frozen for Player Value v1**.

The audit reproduced the binding 645-player / 181,190-PA positive-observed-PA diagnostic before context assignment. One four-PA player-game for MLBAM `643376` was excluded because its frozen rows map the batter to both teams, making a single batting-team assignment false; the final contextual diagnostic surface is 645 players / 181,186 PA. This exclusion affects only the park audit, not the 651-player centering cohort or its frozen denominator.

No live Savant source was fetched, no B2 probability was changed, realized 2024 data were used only as audit targets, numerical centering was unchanged, and no 2025 data or WAR result was accessed.

## ACTIVE STAGE — required pre-WAR sensitivities

Park neutrality is resolved. WAR remains closed until the already-listed positional, batting-reference, replacement, runs-per-win, and baserunning/centering sensitivity obligations are either completed from comparable frozen surfaces or explicitly documented as unavailable under their contracts.

### Baseball-Reference positional schedule — DONE / VERIFIED

`docs/player-value-v1-positional-adjustment-sensitivity-2024.json` applies the documented Baseball-Reference raw schedule to the exact frozen 3,046-player position/DH exposure surface. Actions run **`32381604496`** passed and uploaded artifact **`9411231308`**, digest `sha256:8f16bd1e4686c306e70586c103824ac85749fd01655952a29ee5385191756aa1`.

- binding FanGraphs aggregate: `-473.74028349337` positional runs;
- Baseball-Reference sensitivity aggregate: `-440.9744444444445` runs;
- aggregate difference: `+32.76583904892546` runs;
- player median / mean absolute difference: `0.0` / `0.06353248512895247` runs;
- player range: `-2.1774759945130313` to `+2.1908367626886136` runs.

This is diagnostic only. The binding `fangraphs_fixed_162_game_v1` schedule and all frozen exposures remain unchanged. Companion implementation verification run **`32381604402`** also passed.

### Baseball-Reference player-aware/PythagenPat conversion — DONE / VERIFIED

`docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json` applies the pre-outcome method in `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-contract.md` to the exact 651-player numerical-centering component surface. Actions run **`32382624096`** passed and uploaded artifact **`9411624967`**, digest `sha256:a08d7ce0129d1db736c979fcc971fca61da52778ccdf3efd18f0337cb10586d9`.

- binding common-divisor aggregate: `465.1468161753402` WAR;
- player-aware PythagenPat aggregate: `477.9803621205956` WAR;
- aggregate sensitivity difference: `+12.833545945255509` WAR;
- player median / mean absolute difference: `+0.013543074681223954` / `0.022448545991792267` WAR;
- player range: `-0.06846760327663248` to `+0.1277806560791115` WAR;
- all 651 rows, the `148948.26306286638` projected-PA denominator, and the six explicit zero-exposure rows reconciled.

This is diagnostic only. The binding `9.682629939156854` common RPW, frozen components, centering, and replacement rate remain unchanged.

Replacement sensitivities were already completed in `docs/player-value-v1-replacement-level-2024.json`. Remaining sensitivity work is the alternate recent MLB batting/centering reference only if a full comparable frozen surface exists, plus any other explicitly predeclared baserunning/centering sensitivity that is actually feasible from frozen inputs.

## WAR aggregation — ACTIVE

Intended final decomposable form:

`RAR = Rbat + Rbr + Rdef + Rpos + Rlg + Rpark_if_required + Rrep`

`WAR = RAR / RPW`

Completed before the final WAR freeze:

- Baseball-Reference positional sensitivity;
- alternate recent certified MLB batting reference when available;
- replacement sensitivities above;
- PythagenPat run-to-win sensitivity if practical;
- any baserunning/centering sensitivities predeclared before outcomes.

The alternate recent centering sensitivity was closed as unavailable by
`docs/player-value-v1-alternate-centering-sensitivity-feasibility.json`; Actions run
**`32383260384`** passed and uploaded artifact **`9411870714`**, digest
`sha256:0755279274cfa0440f29cf48db4186d70b0cc28f99a71afaf0c287f76e03cc18`.
The frozen surface has 2023 B2, baserunning, defense, position, and DH machinery,
but lacks both a certified official 2023 positive-PA cohort/outside-snapshot audit
and the certified 2023 MLB batting run-reference tables. The centering contract
forbids manufacturing a partial alternative, so no alternate constant was computed.

The pre-outcome final method and 3,051-player complete-component population are
now frozen in `docs/player-value-v1-final-aggregation-contract.md`. Final numerical
materialization and Actions verification are the active gate.

## Governing read order

1. `docs/project-status.md`
2. `docs/player-value-v1-war-literature-review.md`
3. `docs/player-value-v1-architecture-contract.md`
4. `docs/player-value-v1-mlb-centering-contract.md`
5. `docs/player-value-v1-mlb-centering-2024-membership.json`
6. `docs/player-value-v1-mlb-centering-2024.json`
7. `docs/player-value-v1-park-neutrality-audit-contract.md`
8. `docs/player-value-v1-park-neutrality-audit-result.json`
9. `docs/player-value-v1-mlb-centering-verification.json`
10. `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-contract.md`
11. `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json`
12. `docs/player-value-v1-alternate-centering-sensitivity-feasibility.json`
13. `docs/player-value-v1-final-aggregation-contract.md`
14. `docs/player-value-v1-replacement-level-contract.md`
15. `docs/player-value-v1-replacement-level-2024.json`
16. `docs/player-value-v1-replacement-level-verification.json`
17. `docs/player-value-v1-runs-per-win-contract.md`
18. `docs/player-value-v1-mlb-run-environment-2024.json`
19. `docs/player-value-v1-batting-runs-contract.md`
20. `docs/player-value-v1-positional-adjustment-contract.md`
21. `docs/player-value-v1-defense-production-handoff.md`
22. `docs/player-value-v1-defense-native-run-conversion-parameters.json`
23. `docs/player-value-v1-baserunning-source-audit-contract.md`
24. `docs/player-value-v1-baserunning-source-audit-result.json`
25. `docs/player-value-v1-steal-projection-selection-contract.md`
26. `docs/player-value-v1-steal-projection-diagnostic-thresholds.md`
27. `docs/player-value-v1-steal-projection-selection-result.json`
28. `docs/player-value-v1-advancement-projection-selection-contract.md`
29. `docs/player-value-v1-advancement-projection-selection-result.json`
30. `docs/player-value-v1-baserunning-run-conversion-contract.md`
31. `docs/player-value-v1-baserunning-run-conversion-2024.json`
32. `docs/projection-batting-v1-development-result.json`
33. `docs/current-talent-results-only-baseline-freeze.md`

## Working rules

- Work in small verified batches.
- Preserve immutable source evidence and provenance.
- Reuse certified artifacts where scope matches.
- Freeze exact model/source decisions before opening genuinely unused confirmation evidence.
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not center against the universal ranking population.
- Do not add park adjustment without evidence of residual park context.
- Do not revise the frozen final aggregation method or population from ranking outcomes.
