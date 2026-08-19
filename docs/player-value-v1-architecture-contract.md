# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream value architecture now that batting Performance/Current Talent/Projection, Playing Time, Position/Role, Defense v1 skill, defensive exposure, and Defense run conversion are frozen.

This document freezes **layer boundaries and evidence reuse**. It does **not** yet freeze batting projected-runs conversion, positional-adjustment constants, replacement level, runs per win, or WAR.

## Status

**ARCHITECTURE FROZEN — DEFENSE SKILL / EXPOSURE / RUN CONVERSION FROZEN — POSITIONAL-ADJUSTMENT AND BATTING-RUN REUSE RESEARCH ACTIVE.**

WAR/value is not yet authorized.

Current downstream records:

- `docs/player-value-v1-defense-production-handoff.md` — binding Defense skill hierarchy/interface;
- `docs/player-value-v1-defense-exposure-contract.md` — binding general and catcher exposure semantics;
- `docs/player-value-v1-defensive-exposure-diagnostic-result.json` — total-outs selection;
- `docs/player-value-v1-defensive-position-allocation-result.json` — position-share selection;
- `docs/player-value-v1-defense-native-semantics-audit-result.json` — pre-2025 native source semantics;
- `docs/player-value-v1-defense-native-run-rate-calibration-result.json` — pre-2025 run-rate diagnostic;
- `docs/player-value-v1-defense-native-run-conversion-selection-contract.md` — binding run-conversion selection rule;
- `docs/player-value-v1-defense-native-run-conversion-parameters.json` — frozen Defense run rates;
- `docs/player-value-v1-catcher-native-opportunity-selection-result.json` — frozen catcher opportunity forecasts.

## Frozen upstream inputs

Player Value v1 may consume frozen outputs from:

1. batting Performance / Current Talent / Projection;
2. Playing Time v1;
3. Position / Role v1;
4. Defense v1.

No downstream value decision may alter an upstream coefficient, threshold, fallback, confirmation result, or evidence-eligibility rule.

## 1. Batting value channel

The existing Performance value infrastructure is the retained run-value foundation for batting:

- contextual event value uses RE24/state-transition reconstruction;
- league-season core-bin values are direct contextual run-value means;
- certified level-specific pooling/direct policies remain frozen upstream evidence;
- player talent/projection remains separate from league-bin value estimation.

Player Value v1 should reuse this infrastructure rather than invent a second batting run-value system. The exact production transform from frozen projected batting talent plus projected playing time into projected batting runs must still be documented separately before use.

## 2. Defensive skill -> runs — FROZEN

Defense v1 skill hierarchy remains frozen:

- general range: eligible tracked MLB -> T1; otherwise eligible general defense -> U1; insufficient evidence -> B0 neutral;
- catcher throwing: repaired C2 when eligible; otherwise B0 neutral;
- catcher blocking: repaired C2 when eligible; otherwise B0 neutral;
- catcher framing: eligible tracked MLB catcher -> F1; MLB without eligible tracking and affiliated MiLB -> F0 neutral.

Tracked MiLB range/framing remain closed for v1.

The frozen Defense outputs are standardized skill-target predictions. Their production run conversion is now frozen in `docs/player-value-v1-defense-native-run-conversion-parameters.json` using the common zero-intercept form:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`.

This is not a universal arbitrary `runs per z` scale. Each component/position has a pre-2025 calibration to its public run-valued target and its own native opportunity.

Neutral B0/F0 skill maps to zero modeled component runs.

T1 and U1 use the same general-range conversion rule; family does not change the run rate.

## 3. Defensive exposure — FROZEN

Observed general defensive exposure is official MLB/affiliated `fielding_outs` over:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

General forward bridge:

- projected total defensive outs = `B0_raw_persistence` = prior-season MLB defensive outs;
- projected position shares = `S0_prior_defensive_share_persistence` = prior-season defensive-out shares;
- projected position outs = frozen total x frozen position share.

Catcher native opportunities are frozen independently under `docs/player-value-v1-catcher-native-opportunity-selection-result.json`:

- throwing `sb_attempts`: fixed 50/50 raw-persistence / frozen-Playing-Time-ratio hybrid;
- blocking Savant `pitches`: fixed 50/50 raw-persistence / frozen-Playing-Time-ratio hybrid;
- framing Savant `pitches`: raw persistence.

Do not reopen rejected projected-PA general-outs, Position/Role-normalized defensive-share, or catcher-opportunity challengers after result access.

## 4. Position / Role and positional adjustment

Positional adjustment is **separate from Defense** because general Defense skill is position-relative.

Frozen Position/Role forecasts a probability/share profile over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

The defensive-allocation gate empirically rejected direct use of that batting-role vector as defensive-out share. That does not make Position/Role irrelevant to positional adjustment: positional adjustment is a separate question and may need a deliberately chosen weighting basis.

Two exposure surfaces now exist and must not be conflated:

1. frozen **defensive-out shares**, appropriate for actual fielding exposure;
2. frozen **Position/Role batting-role profile**, which includes DH and may be useful where a positional-adjustment convention assigns value by batting role rather than fielding outs.

The positional-adjustment schedule and exact weighting basis are not yet frozen. They must be researched under a separate gate before Player Value aggregation.

## 5. Neutral Defense fallback semantics

B0/F0 neutral means zero modeled adjustment for that specific defensive component on its defined position-relative skill scale. It does not mean the player is certainly average, does not erase uncertainty, and does not authorize a downstream rescue model.

## 6. Confirmation-period firewall

The completed 2025 Defense confirmation is not a development sample.

Player Value may use frozen confirmation decisions to know which components survived. It may not tune downstream coefficients or scaling rules against 2025 Defense confirmation residuals.

The 2025 Position/Role outcomes have also already been accessed upstream and may not be relabeled as an untouched holdout for a newly designed downstream question.

Any genuinely new held-out period must be identified before outcomes are opened for that specific downstream gate.

## 7. Replacement level remains closed

Replacement level remains separate from batting skill, defensive skill/runs, positional adjustment, and playing time. No replacement-run credit may be added until batting runs and positional adjustment have frozen production definitions.

## 8. Runs per win remains closed

No WAR calculation is authorized until:

1. batting run conversion is fixed;
2. defensive run conversion is fixed — **DONE**;
3. needed component-native defensive opportunities are fixed — **DONE**;
4. positional adjustment is fixed;
5. replacement level is fixed;
6. the runs-per-win convention is fixed.

## 9. Required final Player Value decomposition

Future player-season output must preserve separate fields for at least:

- projected batting runs above the chosen baseline;
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

## 10. Active research gates

### Gate A — batting projected-runs reuse audit

Determine how frozen projected batting talent consumes the certified Performance league-bin run values. Prefer existing transforms; do not rebuild RE24 or bin calibration.

### Gate B — defensive exposure

**COMPLETE / FROZEN.** General defensive outs, position allocation, and catcher native-opportunity forecasts are selected.

### Gate C — defensive run conversion

**COMPLETE / FROZEN.** Use `docs/player-value-v1-defense-native-run-conversion-parameters.json`; do not refit or substitute ad hoc scales.

### Gate D — positional adjustment

**ACTIVE.** Research a transparent schedule and weighting basis. Compare established public WAR conventions with an empirical/public-data estimate where feasible, but do not allow position-relative Defense skill to absorb positional difficulty. Freeze the method before Player Value aggregation.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- General defensive exposure and catcher native-opportunity forecasts are frozen.
- Defense run conversion is frozen.
- Do not tune any downstream Defense decision to 2025 confirmation residuals.
- Do not assign arbitrary defensive `runs per z` values.
- Do not hide positional difficulty inside Defense skill.
- Do not calculate WAR yet.
- Do not add replacement level yet.
- Do not select runs per win yet.
