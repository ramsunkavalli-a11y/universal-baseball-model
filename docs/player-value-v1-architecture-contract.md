# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream Player Value architecture while preserving the already-frozen upstream batting, playing-time, role, and Defense decisions.

This document freezes **layer boundaries and evidence reuse**. It has been revised after a broader public WAR-methodology review identified three required pre-WAR corrections: replacement level must be reopened, baserunning must be modeled, and the average-relative components require an explicit MLB-reference centering layer. A park-neutrality audit is also required before adding any park correction.

Binding literature record: `docs/player-value-v1-war-literature-review.md`.

## Status

**ARCHITECTURE FROZEN — BATTING / DEFENSE / POSITION FROZEN — RUNS PER WIN FROZEN — REPLACEMENT REOPENED — BASERUNNING / CENTERING / PARK AUDIT REQUIRED — WAR CLOSED.**

WAR/value is not yet authorized.

## Frozen upstream inputs

Player Value v1 may consume frozen outputs from:

1. batting Performance / Current Talent / Projection;
2. Playing Time v1;
3. Position / Role v1;
4. Defense v1.

No downstream value decision may alter an upstream coefficient, threshold, fallback, confirmation result, or evidence-eligibility rule.

## 1. Batting value channel — FROZEN

Binding contract: `docs/player-value-v1-batting-runs-contract.md`.

Implementation: `src/universal_baseball/player_value_batting_runs.py`.

Verification: `docs/player-value-v1-batting-runs-verification.json`, Actions run `32275192829`.

The frozen batting conversion is:

`coverage_mlb = aggregate MLB core events / aggregate MLB PA`

`V_mlb[b] = occurrence-weighted pooled AL/NL certified run value for bin b`

`P_ref[b] = aggregate MLB occurrence_count[b] / aggregate MLB core events`

`RV_ref_core = sum_b(P_ref[b] * V_mlb[b])`

`RV_i_core = sum_b(P_i[b] * V_mlb[b])`

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

Projection probabilities are a 12-part mutually exclusive composition conditional on a core event. The same MLB coverage is applied to every player; source/taxonomy coverage is not a projected talent dimension.

Batting runs are average-relative inside the pooled MLB reference. Replacement, baserunning, position, centering, and runs per win remain separate layers.

## 2. Defensive skill -> runs — FROZEN

Defense skill hierarchy remains frozen:

- general range: eligible tracked MLB -> T1; otherwise eligible MLB/affiliated MiLB -> U1; insufficient evidence -> B0 neutral;
- catcher throwing: repaired C2 when eligible; otherwise B0 neutral;
- catcher blocking: repaired C2 when eligible; otherwise B0 neutral;
- catcher framing: eligible tracked MLB catcher -> F1; otherwise F0 neutral; MiLB framing F0.

The common frozen conversion is:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`.

## 3. Defensive exposure — FROZEN

Observed general defensive exposure uses official `fielding_outs` over `C, 1B, 2B, 3B, SS, LF, CF, RF`.

Forward bridge:

- projected total defensive outs = prior-season MLB defensive outs;
- projected position shares = prior defensive-out shares;
- projected position outs = frozen total x frozen position share.

Catcher native opportunities remain frozen:

- throwing `sb_attempts`: fixed 50/50 raw-persistence / frozen-Playing-Time-ratio hybrid;
- blocking Savant `pitches`: fixed 50/50 hybrid;
- framing Savant `pitches`: raw persistence.

## 4. Positional adjustment — FROZEN

Binding contract: `docs/player-value-v1-positional-adjustment-contract.md`.

Implementation: `src/universal_baseball/player_value_positional_adjustment.py`.

Verification: `docs/player-value-v1-positional-adjustment-verification.json`, Actions run `32270697293`.

Use the fixed FanGraphs 162-game schedule:

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

Do not league-center inside the positional layer itself. Any aggregate imbalance is handled by the separate MLB-reference centering layer.

## 5. Neutral Defense fallback semantics

B0/F0 neutral means zero modeled adjustment for that specific defensive component on its defined position-relative skill scale. It does not mean certainty of average ability and does not authorize a downstream rescue model.

## 6. Confirmation-period firewall

Completed 2025 confirmation periods are not new development samples.

Player Value may use frozen confirmation decisions to know which upstream components survived. It may not tune new downstream coefficients to already-accessed 2025 residuals or relabel those outcomes as untouched holdouts.

Any genuinely new held-out period must be identified before outcomes are opened for that downstream gate.

## 7. Replacement level — REOPENED / ACTIVE

Binding contract: `docs/player-value-v1-replacement-level-contract.md`.

The prior fixed `20.5 runs / 600 projected MLB PA` convention was implemented and verified in Actions run `32275638045`, but the literature review showed that it was too literal a representation of Baseball-Reference's final replacement accounting. That convention is superseded for final WAR while its implementation/verification remain as provenance.

Predeclared binding candidate:

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

This follows the FanGraphs position-player allocation. Baseball-Reference's 590-WAR / 59% allocation and the legacy 20.5/600 form are required sensitivities.

Replacement is not refrozen until completed-reference-season MLB games, PA, RPW, and the resulting rate are materialized and verified.

## 8. Runs per win — FROZEN METHOD

Binding contract: `docs/player-value-v1-runs-per-win-contract.md`.

Implementation verification: `docs/player-value-v1-runs-per-win-verification.json`, Actions run `32275833614`.

Binding convention:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Use one completed certified pooled MLB run environment and one common position-player RPW for the snapshot.

The 2024 certified MLB reference environment contains 21,343 runs over 43,116 1/3 innings, approximately `9.68263` runs per win; production should consume the exact persisted value rather than a rounded documentation number.

Baseball-Reference/PythagenPat remains a sensitivity, not the binding v1 divisor.

## 9. Baserunning / GIDP — REQUIRED / ACTIVE AFTER REPLACEMENT REFRESH

Both FanGraphs and Baseball-Reference include baserunning in position-player WAR. Baseball-Reference also preserves a separate GIDP run term.

Player Value v1 must not silently omit these components.

The baserunning gate must audit available public evidence and predeclare a universal hierarchy before final rankings are inspected. Preferred investigation order:

1. MLB Statcast Baserunning Run Value / underlying opportunities;
2. comparable affiliated MiLB advancement evidence where available;
3. SB/CS-based run value as a lower-information fallback;
4. neutral fallback when evidence is insufficient.

GIDP avoidance must be audited for whether it can be modeled separately without double-counting the frozen batting taxonomy or baserunning term.

## 10. MLB-reference centering — REQUIRED

The final average-relative components cannot be assumed to sum exactly to zero merely because each component was designed around an average baseline.

Use a fixed certified MLB reference population, never the loaded universal ranking population.

Candidate form after the relevant components freeze:

`Ravg_raw_ref = aggregate(Rbat + Rbr + Rdp_if_separate + Rdef + Rpos)`

`centering_runs_per_pa = -Ravg_raw_ref / aggregate_reference_MLB_PA`

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

The exact reference population and exposure semantics must be predeclared before this gate freezes.

This layer is especially important in the universal-DH era because a fixed positional schedule including DH is not automatically zero-sum.

## 11. Park-neutrality audit — REQUIRED

Traditional WAR batting is park-adjusted because observed offense inherits park context. Player Value v1 already translates a projected core-event composition through one pooled MLB RE24 value environment, so an additional park adjustment could double-correct context.

Before adding any park term:

1. test whether frozen batting/current-talent outputs retain systematic park/team residuals;
2. document the result;
3. add an explicit park correction only if a concrete residual-context problem is demonstrated.

No park correction is authorized merely because traditional WAR includes one.

## 12. WAR/value remains closed

No WAR calculation is authorized until:

1. batting run conversion — **DONE**;
2. defensive run conversion — **DONE**;
3. defensive/catcher opportunity forecasts — **DONE**;
4. positional adjustment — **DONE**;
5. runs per win method — **DONE**;
6. replacement level — **REOPENED / ACTIVE**;
7. baserunning/GIDP — **REQUIRED**;
8. MLB-reference centering — **REQUIRED**;
9. park-neutrality audit — **REQUIRED**;
10. required sensitivities — **NOT COMPLETE**.

## 13. Required final Player Value decomposition

Future player-season output must preserve separate fields for at least:

- projected batting runs above MLB reference;
- projected baserunning runs;
- projected GIDP runs if modeled separately;
- projected general-defense runs;
- projected catcher-throwing runs;
- projected catcher-blocking runs;
- projected catcher-framing runs;
- positional adjustment runs;
- MLB-reference centering/league-adjustment runs;
- explicit park adjustment if the audit justifies one;
- replacement runs;
- runs above replacement;
- runs-per-win convention;
- WAR;
- projected batting playing-time exposure;
- projected total defensive outs and by-position defensive outs;
- frozen projected Position/Role profile;
- projected catcher native opportunities;
- component coverage/fallback flags and provenance.

Do not collapse these into one opaque value before persistence.

Intended final form:

`RAR = Rbat + Rbr + Rdp_if_separate + Rdef + Rpos + Rlg + Rpark_if_required + Rrep`

`WAR = RAR / RPW`

## 14. Required sensitivities before final WAR freeze

Without retuning binding choices from player rankings, final QA must include:

- Baseball-Reference current raw positional schedule versus binding FanGraphs schedule;
- alternate recent certified MLB batting reference season when available;
- replacement 570-WAR vs 590-WAR allocation;
- legacy 20.5/600 replacement comparison;
- Baseball-Reference/PythagenPat runs-to-wins comparison if practical;
- any additional sensitivity predeclared by the baserunning or centering contracts.

Sensitivities are diagnostics, not a license to choose the version that produces preferred rankings.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, Defense, batting-run conversion, or positional adjustment absent a concrete implementation failure.
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not assign arbitrary defensive `runs per z` values.
- Do not make Performance source/taxonomy coverage a player batting-talent term.
- Do not hide positional difficulty inside Defense skill.
- Do not center against the universal ranking population.
- Do not add a park adjustment without evidence of residual park context.
- Do not use the superseded 20.5/600 replacement implementation for final WAR.
- Do not calculate WAR yet.
