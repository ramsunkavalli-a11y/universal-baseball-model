# Player Value v1 architecture contract

Last updated: 2026-08-18

## Purpose

Define the downstream value architecture now that batting Performance/Current Talent/Projection, Playing Time, Position/Role, and Defense v1 are frozen.

This document freezes **layer boundaries and evidence reuse**. It does **not** yet freeze defensive run-conversion constants, positional-adjustment constants, replacement level, runs per win, or WAR.

## Status

**ARCHITECTURE FROZEN — RUN-CONVERSION / POSITIONAL-ADJUSTMENT RESEARCH NEXT.**

WAR/value is not yet authorized.

## Frozen upstream inputs

Player Value v1 may consume frozen outputs from these stages without refitting them:

1. batting Performance / Current Talent / Projection;
2. Playing Time v1;
3. Position / Role v1;
4. Defense v1.

No downstream value decision may alter an upstream model coefficient, threshold, fallback, confirmation result, or evidence eligibility rule.

## 1. Batting value channel

The existing Performance value infrastructure is the retained run-value foundation for batting.

- contextual event value is based on RE24/state-transition reconstruction;
- league-season core-bin values are direct contextual run-value means;
- certified level-specific pooling/direct policies remain as frozen upstream evidence;
- player talent/projection remains separate from league-bin value estimation.

Player Value v1 should **reuse** this infrastructure rather than invent a second batting run-value system.

This architecture decision does not yet specify the exact production transform from frozen projected batting talent + projected playing time into projected batting runs. That transform must preserve the frozen Current Talent/Projection semantics and be documented separately before use.

## 2. Defensive skill and defensive runs are separate layers

Defense v1 is frozen as a **skill-prediction layer**, not a run-value layer.

Final Defense v1 policy:

- eligible MLB with eligible tracking: tracked MLB range model;
- otherwise eligible general defense: universal range model;
- insufficient general evidence: neutral component fallback;
- eligible catcher throwing: catcher throwing model;
- catcher blocking: neutral component fallback because the blocking challenger failed confirmation;
- tracked framing and tracked MiLB range remain closed.

The frozen defensive outputs are on standardized target scales. Player Value v1 must not assign an arbitrary `runs per z` constant.

A defensive run-conversion method must be separately specified and justified using either:

1. native target units plus opportunity/exposure conversion; or
2. a predeclared calibration to an independently defined public run-valued defensive target using evidence that does not reopen the 2025 Defense confirmation period.

The conversion must be common to the corresponding target scale. In particular, tracked MLB range and universal range predict the same general-range target scale, so they do not receive different run scales merely because their predictor families differ.

## 3. Defensive exposure

Defensive skill must be converted to seasonal value using **frozen projected opportunity/exposure**, not by treating a rate/skill score as a full-season total.

Permitted exposure inputs come from frozen Playing Time and Position/Role outputs. No new playing-time or role model may be fitted inside Player Value.

If a needed defensive-opportunity exposure is not directly produced upstream, the mapping from projected playing time / position share to defensive opportunities must be separately estimated and frozen before value calculation.

## 4. Position / Role and positional adjustment

Positional adjustment is **separate from Defense**.

Reason: the general Defense target is standardized within position, so the defensive model measures performance relative to peers at the same position. Position scarcity/difficulty must therefore not be hidden inside the defensive skill score.

Position / Role v1 produces a probability/share profile over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

Player Value v1 should use the projected position-share vector and projected exposure to calculate an exposure-weighted positional adjustment. It should not normally collapse a multi-position player to one primary-position constant.

The positional-adjustment schedule itself is **not yet frozen**. It must be researched/estimated under a separate gate before use.

## 5. Neutral Defense fallback semantics

A neutral Defense fallback means **zero adjustment for that specific defensive component on its defined position-relative scale**.

It does not mean:

- proof that the player is an average defender;
- zero uncertainty;
- permission to recreate a failed component downstream.

Therefore:

- catcher blocking contributes no modeled blocking adjustment in v1;
- framing contributes no modeled framing adjustment in v1;
- missing eligible tracking falls back to the validated universal range model where eligible, not to a fabricated tracked value.

## 6. Confirmation-period firewall

The completed 2025 Defense confirmation is not a new development sample.

Player Value v1 may use the **frozen confirmation decision** to know which Defense components survived. It may not tune defensive run-conversion coefficients against 2025 confirmation errors or search for a scaling constant that makes 2025 Defense look better.

If empirical defensive run calibration is required, preferred evidence is:

1. authorized pre-2025 development-era source/target data; or
2. an externally defined public run-value mapping chosen and frozen independently of the 2025 confirmation outcomes.

Any new held-out validation period must be identified before its outcomes are opened.

## 7. Replacement level remains closed

Replacement level must remain separate from:

- batting skill;
- defensive skill;
- positional adjustment;
- playing time.

No replacement-run or replacement-win credit may be added until batting runs, defensive runs, and positional adjustment have independently frozen production definitions.

## 8. Runs per win remains closed

No WAR calculation is authorized until:

1. batting run conversion is fixed;
2. defensive run conversion is fixed;
3. positional adjustment is fixed;
4. replacement level is fixed;
5. the runs-per-win convention is fixed.

The eventual WAR equation must expose each component separately so the final ranking can be audited.

## 9. Required final Player Value output decomposition

At minimum, the future player-season output must keep separate fields for:

- projected batting runs above the chosen baseline;
- projected general-defense runs;
- projected catcher-throwing runs;
- projected catcher-blocking runs (v1 expected to be zero modeled adjustment under the frozen fallback);
- projected framing runs (v1 expected to be absent/zero modeled adjustment under the frozen closed component);
- positional adjustment runs;
- replacement runs;
- runs above replacement;
- runs-per-win convention;
- WAR;
- projected playing-time exposure;
- projected position-share profile;
- component coverage/fallback flags and provenance.

Do not collapse these into one opaque value before persistence.

## 10. Immediate research gates

### Gate A — batting projected-runs reuse audit

Determine exactly how the frozen projected batting profile should consume the already-certified Performance league-bin run values. Prefer existing production transforms if present. Do not rebuild RE24 or bin calibration.

### Gate B — defensive run conversion

For each retained defensive target scale, document its native units and test principled conversions to runs using only authorized evidence:

- general range target: Savant `diff_success_rate_formatted`;
- catcher throwing target: Savant `cs_aa_per_throw`.

Catcher blocking and framing remain closed for v1.

### Gate C — positional adjustment

Research a transparent position-share-weighted schedule. Compare established public WAR conventions with an empirical public-data estimate where feasible. Freeze the method before calculating player value.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- Do not tune Defense run scaling to 2025 confirmation residuals.
- Do not assign arbitrary defensive `runs per z` values.
- Do not hide positional difficulty inside the Defense score.
- Do not replace a position-share vector with a primary-position shortcut unless a later explicit validation supports it.
- Do not calculate WAR yet.
- Do not add replacement level yet.
- Do not select a runs-per-win constant yet.
