# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream Player Value architecture while preserving the already-frozen upstream batting, playing-time, role, and Defense decisions.

This document freezes **layer boundaries and evidence reuse**. Batting projected runs, Defense runs/exposure, and positional adjustment are now frozen. Replacement level is the active gate. Runs per win and WAR/value aggregation remain closed.

## Status

**ARCHITECTURE FROZEN — BATTING RUNS / DEFENSE / POSITIONAL ADJUSTMENT FROZEN AND VERIFIED — REPLACEMENT-LEVEL GATE ACTIVE.**

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

The existing Performance value infrastructure remains the run-value foundation:

- contextual event value uses the frozen RE24/state-transition definition;
- certified league-season core-bin values remain upstream evidence;
- frozen Projection v1 supplies a 12-part mutually exclusive core-bin composition;
- frozen Playing Time v1 supplies expected MLB PA.

Projection probabilities are conditional on a core event, not shares of all PA. Player Value therefore creates one pooled certified MLB reference environment from the latest certified MLB Performance materialization available to the snapshot:

`coverage_mlb = aggregate MLB core events / aggregate MLB PA`

`V_mlb[b] = occurrence-weighted pooled AL/NL certified run value for bin b`

`P_ref[b] = aggregate MLB occurrence_count[b] / aggregate MLB core events`

`RV_ref_core = sum_b(P_ref[b] * V_mlb[b])`

For player `i`:

`RV_i_core = sum_b(P_i[b] * V_mlb[b])`

`Rbat_i = projected_expected_mlb_pa_i * coverage_mlb * (RV_i_core - RV_ref_core)`

The same MLB coverage is applied to every player. Do not project player-specific `core_events / PA` in v1; source/taxonomy coverage is not an authorized talent dimension.

Batting runs are above the pooled MLB reference only. Replacement credit, position, league centering, and runs-per-win are not part of this layer.

## 2. Defensive skill -> runs — FROZEN

Defense skill hierarchy remains frozen:

- general range: eligible tracked MLB -> T1; otherwise eligible MLB/affiliated MiLB -> U1; insufficient evidence -> B0 neutral;
- catcher throwing: repaired C2 when eligible; otherwise B0 neutral;
- catcher blocking: repaired C2 when eligible; otherwise B0 neutral;
- catcher framing: eligible tracked MLB catcher -> F1; otherwise F0 neutral; MiLB framing F0.

Tracked MiLB range/framing remain closed for v1.

The common frozen conversion form is:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`.

Each component/position has its own pre-2025 calibration to a public run-valued target. There is no arbitrary universal `runs per z` constant. Neutral B0/F0 skill maps to zero modeled component runs.

Binding parameters: `docs/player-value-v1-defense-native-run-conversion-parameters.json`.

## 3. Defensive exposure — FROZEN

Observed general defensive exposure is official `fielding_outs` over:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

Forward bridge:

- projected total defensive outs = `B0_raw_persistence` = prior-season MLB defensive outs;
- projected position shares = `S0_prior_defensive_share_persistence` = prior-season defensive-out shares;
- projected position outs = frozen total x frozen position share.

Catcher opportunities are independently frozen:

- throwing `sb_attempts`: fixed 50/50 raw-persistence / frozen-Playing-Time-ratio hybrid;
- blocking Savant `pitches`: fixed 50/50 raw-persistence / frozen-Playing-Time-ratio hybrid;
- framing Savant `pitches`: raw persistence.

Do not reopen rejected projected-PA general-outs, Position/Role-normalized defensive-share, or catcher-opportunity challengers.

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

For non-DH positions:

`Rpos[p] = schedule_runs[p] * projected_position_fielding_outs[p] / 4374`

For DH:

`Rpos[DH] = -17.5 * projected_DH_role_events / 162`

DH role events use frozen raw prior-season persistence. Do not renormalize player exposure and do not league-center inside Rpos.

Position-relative Defense skill must remain separate from positional difficulty.

## 5. Neutral Defense fallback semantics

B0/F0 neutral means zero modeled adjustment for that specific defensive component on its defined position-relative skill scale. It does not mean the player is certainly average, does not erase uncertainty, and does not authorize a downstream rescue model.

## 6. Confirmation-period firewall

Completed 2025 confirmation periods are not new development samples.

Player Value may use frozen confirmation decisions to know which upstream components survived. It may not tune new downstream coefficients to already-accessed 2025 residuals or relabel those outcomes as untouched holdouts.

Any genuinely new held-out period must be identified before outcomes are opened for that downstream gate.

## 7. Replacement level — ACTIVE

Replacement level is separate from batting skill, defensive skill/runs, positional adjustment, and playing-time forecasting.

The replacement-level gate may now open because batting runs, Defense runs/exposure, and positional adjustment all have frozen production definitions.

The gate must:

1. research established public replacement-level conventions and authoritative methodology;
2. predeclare the v1 replacement form and exposure/population assumptions before final ranking outcomes are inspected;
3. implement and verify replacement runs separately from the runs-per-win choice;
4. preserve replacement runs as an explicit output field.

No replacement-level choice may retroactively alter batting, Defense, position, or Playing Time.

## 8. Runs per win remains closed

Runs per win opens only after replacement level is frozen. It must remain an explicit convention and must not be hidden inside replacement credit or component scales.

## 9. WAR/value remains closed

No WAR calculation is authorized until:

1. batting run conversion — **DONE**;
2. defensive run conversion — **DONE**;
3. defensive/catcher opportunity forecasts — **DONE**;
4. positional adjustment — **DONE**;
5. replacement level — **ACTIVE / NOT YET FROZEN**;
6. runs per win — **CLOSED**.

## 10. Required final Player Value decomposition

Future player-season output must preserve separate fields for at least:

- projected batting runs above MLB reference;
- projected general-defense runs;
- projected catcher-throwing runs;
- projected catcher-blocking runs;
- projected catcher-framing runs;
- positional adjustment runs;
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

## 11. Required sensitivities before final WAR freeze

The final pre-WAR QA must include, without retuning the binding choices:

- positional adjustment under the current raw Baseball-Reference schedule versus the binding FanGraphs schedule;
- batting runs under an alternate recent certified MLB reference season when available;
- any sensitivity explicitly required by the eventual replacement-level contract.

Sensitivities are diagnostics, not a license to choose the version that produces preferred player rankings.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- Do not reopen batting run conversion or positional adjustment absent a concrete implementation failure.
- Do not tune downstream decisions to already-accessed 2025 confirmation residuals.
- Do not assign arbitrary defensive `runs per z` values.
- Do not make Performance source/taxonomy coverage a player batting-talent term.
- Do not hide positional difficulty inside Defense skill.
- Do not calculate WAR yet.
- Replacement-level research/selection is authorized now.
- Runs-per-win selection opens only after replacement level freezes.
