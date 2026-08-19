# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream value architecture now that batting Performance/Current Talent/Projection, Playing Time, Position/Role, Defense v1 skill, and the general defensive-out exposure bridge are frozen.

This document freezes **layer boundaries and evidence reuse**. It does **not** yet freeze defensive run conversion, component-native catcher opportunity forecasts, positional-adjustment constants, replacement level, runs per win, or WAR.

## Status

**ARCHITECTURE FROZEN — GENERAL DEFENSIVE EXPOSURE FROZEN — NATIVE RUN-CONVERSION / POSITIONAL-ADJUSTMENT RESEARCH ACTIVE.**

WAR/value is not yet authorized.

Current downstream contracts/evidence:

- `docs/player-value-v1-defense-production-handoff.md` — binding Defense skill hierarchy/interface;
- `docs/player-value-v1-defense-exposure-contract.md` — binding observed exposure semantics and selected general defensive-out bridge;
- `docs/player-value-v1-defensive-exposure-diagnostic-result.json` — total-outs selection;
- `docs/player-value-v1-defensive-position-allocation-result.json` — position-share selection;
- `docs/player-value-v1-defense-native-scale-audit.json` — diagnostic pre-2025 target-scale evidence only;
- `docs/player-value-v1-defense-native-semantics-audit-contract.md` — current source-semantics audit gate.

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

## 2. Defensive skill and defensive runs are separate layers

Defense v1 is frozen as a **skill-prediction layer**, not a run-value layer.

Final hierarchy:

- general range: eligible tracked MLB -> T1; otherwise eligible general defense -> U1; insufficient evidence -> B0 neutral;
- catcher throwing: repaired C2 when eligible; otherwise B0 neutral;
- catcher blocking: repaired C2 when eligible; otherwise B0 neutral;
- catcher framing: eligible tracked MLB catcher -> F1; MLB without eligible tracking and affiliated MiLB -> F0 neutral.

Tracked MiLB range/framing remain closed for v1 because transfer evidence was insufficient.

The frozen outputs are standardized skill-target predictions. Player Value v1 must not assign an arbitrary universal `runs per z` constant.

A defensive run-conversion method must be separately justified using either:

1. native target units plus component-appropriate opportunity/exposure conversion; or
2. a predeclared calibration to an independently defined public run-valued defensive target using evidence that does not reopen the 2025 Defense confirmation period.

T1 and U1 predict the same general-range target scale and therefore share the same downstream native/run conversion.

## 3. Defensive exposure

Observed general defensive exposure is official MLB/affiliated `fielding_outs` over:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

The general forward bridge is now frozen under `docs/player-value-v1-defense-exposure-contract.md`:

- projected total defensive outs = `B0_raw_persistence` = prior-season MLB defensive outs;
- projected position shares = `S0_prior_defensive_share_persistence` = prior-season defensive-out shares;
- projected position outs = frozen total x frozen position share.

The total-outs selection is recorded in `docs/player-value-v1-defensive-exposure-diagnostic-result.json`; the allocation selection is recorded in `docs/player-value-v1-defensive-position-allocation-result.json`.

Do not reopen rejected projected-PA or frozen-Position/Role exposure challengers after result access.

This bridge solves general defensive-out volume/allocation only. It does **not** imply the denominators for catcher throwing, blocking, or framing. If a component needs throws, games, pitches, takes, or another native opportunity count, that mapping must be separately documented and frozen.

## 4. Position / Role and positional adjustment

Positional adjustment is **separate from Defense** because general Defense skill is position-relative.

Frozen Position/Role forecasts a probability/share profile over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

The defensive-allocation gate empirically rejected direct use of that role vector as defensive-out share for v1. That result does not make Position/Role irrelevant to positional adjustment: positional adjustment is a separate question with a separate exposure basis.

The positional-adjustment schedule and exact weighting basis are not yet frozen. They must be researched under a separate gate before Player Value aggregation.

## 5. Neutral Defense fallback semantics

B0/F0 neutral means zero modeled adjustment for that specific defensive component on its defined position-relative skill scale. It does not mean the player is certainly average, does not erase uncertainty, and does not authorize a downstream rescue model.

## 6. Confirmation-period firewall

The completed 2025 Defense confirmation is not a development sample.

Player Value may use frozen confirmation decisions to know which components survived. It may not tune run-conversion coefficients, future standardization constants, opportunity mappings, or scaling rules against 2025 confirmation residuals.

The 2025 Position/Role outcomes have also already been accessed upstream and may not be relabeled as an untouched holdout for a newly designed downstream question.

Any genuinely new held-out period must be identified before outcomes are opened for that specific downstream gate.

## 7. Replacement level remains closed

Replacement level remains separate from batting skill, defensive skill/runs, positional adjustment, and playing time. No replacement-run credit may be added until batting runs, defensive runs, and positional adjustment have frozen production definitions.

## 8. Runs per win remains closed

No WAR calculation is authorized until:

1. batting run conversion is fixed;
2. defensive run conversion is fixed;
3. needed component-native defensive opportunities are fixed;
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
- component-native opportunity counts used by defensive run conversion;
- component coverage/fallback flags and provenance.

Do not collapse these into one opaque value before persistence.

## 10. Active research gates

### Gate A — batting projected-runs reuse audit

Determine how frozen projected batting talent consumes the certified Performance league-bin run values. Prefer existing transforms; do not rebuild RE24 or bin calibration.

### Gate B — defensive exposure

**General defensive-out volume and position allocation are complete/frozen.** Component-native catcher opportunities remain open only where needed for run conversion.

### Gate C — defensive run conversion

For each retained target scale, establish exact native source semantics first, then predeclare a conversion separately:

- general range: Savant `diff_success_rate_formatted` / Success Rate Added;
- catcher throwing: Savant `cs_aa_per_throw`;
- catcher blocking: Savant `blocks_above_average_per_game`;
- catcher framing: repaired raw target `1000 * rv_tot / pitches`.

The current source-semantics diagnostic is defined by `docs/player-value-v1-defense-native-semantics-audit-contract.md`. It may identify algebraic/native identities but may not itself select a conversion.

### Gate D — positional adjustment

Research a transparent position-share-weighted schedule, comparing established public WAR conventions with an empirical public-data estimate where feasible. Freeze the method before calculating Player Value.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- General defensive exposure is frozen at B0 total-outs persistence plus S0 defensive-share persistence.
- Do not tune Defense run scaling to 2025 confirmation residuals.
- Do not assign arbitrary defensive `runs per z` values.
- Do not hide positional difficulty inside Defense skill.
- Do not calculate WAR yet.
- Do not add replacement level yet.
- Do not select runs per win yet.
