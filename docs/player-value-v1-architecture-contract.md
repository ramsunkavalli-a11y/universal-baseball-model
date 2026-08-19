# Player Value v1 architecture contract

Last updated: 2026-08-19

## Purpose

Define the downstream value architecture now that batting Performance/Current Talent/Projection, Playing Time, Position/Role, and Defense v1 are frozen.

This document freezes **layer boundaries and evidence reuse**. It does **not** yet freeze defensive run-conversion constants, the forward defensive-exposure bridge, positional-adjustment constants, replacement level, runs per win, or WAR.

## Status

**ARCHITECTURE FROZEN — DEFENSIVE EXPOSURE / RUN-CONVERSION / POSITIONAL-ADJUSTMENT RESEARCH ACTIVE.**

WAR/value is not yet authorized.

Current downstream contracts:

- `docs/player-value-v1-defense-production-handoff.md` — binding Defense skill hierarchy/interface;
- `docs/player-value-v1-defense-exposure-contract.md` — binding observed exposure semantics; forward bridge still open;
- `docs/player-value-v1-defense-native-scale-audit.json` — pre-repair native-scale audit evidence; its catcher coverage is incomplete and must not override repaired Defense results.

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

Final Defense v1 production hierarchy is reconciled in `docs/player-value-v1-defense-production-handoff.md`:

- general range: eligible tracked MLB -> T1; otherwise eligible general defense -> U1; insufficient evidence -> B0 neutral;
- catcher throwing: repaired C2 when eligible; otherwise B0 neutral;
- catcher blocking: repaired C2 when eligible; otherwise B0 neutral;
- catcher framing: eligible tracked MLB catcher -> F1; MLB without eligible tracking and affiliated MiLB -> F0 neutral;
- tracked MiLB range and tracked MiLB framing remain closed for v1 because transfer evidence was insufficient.

The frozen defensive model outputs are standardized skill-target predictions. Player Value v1 must not assign an arbitrary `runs per z` constant.

A defensive run-conversion method must be separately specified and justified using either:

1. native target units plus opportunity/exposure conversion; or
2. a predeclared calibration to an independently defined public run-valued defensive target using evidence that does not reopen the 2025 Defense confirmation period.

The conversion must be common to the corresponding target scale. In particular, tracked MLB range and universal range predict the same general-range target scale, so they do not receive different run scales merely because their predictor families differ.

## 3. Defensive exposure

Defensive skill must be converted to seasonal value using frozen projected opportunity/exposure, not by treating a rate/skill score as a full-season total.

Observed defensive-exposure semantics are frozen in `docs/player-value-v1-defense-exposure-contract.md`:

- canonical observed position-player defensive exposure is official `fielding_outs` from the certified historical Position/Role fielding source;
- `fielding_outs` is distinct from batting Playing Time and from the frozen Position/Role `role_probability`;
- the frozen Position/Role vector is based on starts, with games-played fallback, and is not automatically a projected defensive-out-share vector;
- projected PA is not defensive outs.

Permitted inputs to a future exposure bridge include frozen Playing Time and Position/Role outputs plus already-certified historical fielding usage. No new general playing-time or role model may be fitted inside Player Value.

If a needed defensive-opportunity exposure is not directly produced upstream, the mapping to defensive outs/throws/pitches must be separately estimated, validated, documented, and frozen before value calculation. `projected PA x projected role share` is not a binding shortcut.

## 4. Position / Role and positional adjustment

Positional adjustment is **separate from Defense**.

Reason: the general Defense target is standardized within position, so the defensive model measures performance relative to peers at the same position. Position scarcity/difficulty must therefore not be hidden inside the defensive skill score.

Position / Role v1 produces a probability/share profile over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

For positional adjustment, Player Value v1 should use the frozen projected role-share vector together with the appropriate projected playing-time/exposure basis and calculate an exposure-weighted positional adjustment. It should not normally collapse a multi-position player to one primary-position constant.

The positional-adjustment schedule and exact exposure basis are **not yet frozen**. They must be researched/estimated under a separate gate before use.

## 5. Neutral Defense fallback semantics

A neutral Defense fallback means **zero modeled adjustment for that specific defensive component on its defined position-relative skill scale**.

It does not mean:

- proof that the player is an average defender;
- zero uncertainty;
- permission to recreate a missing/failed component downstream.

Final v1 examples:

- insufficient general-range evidence -> B0 for general range;
- ineligible catcher throwing/blocking evidence -> B0 for that catcher component;
- MLB catcher without eligible tracked framing -> F0 for framing;
- affiliated MiLB framing -> F0 because tracked transfer evidence was insufficient;
- missing eligible MLB range tracking falls back to validated U1 where U1 evidence is sufficient, not to a fabricated tracked value.

## 6. Confirmation-period firewall

The completed 2025 Defense confirmation is not a new development sample.

Player Value v1 may use the **frozen confirmation decisions** to know which Defense components survived. It may not tune defensive run-conversion coefficients against 2025 confirmation errors or search for a scaling constant that makes 2025 Defense look better.

If empirical defensive run calibration is required, preferred evidence is:

1. authorized pre-2025 development-era source/target data; or
2. an externally defined public run-value mapping chosen and frozen independently of the 2025 confirmation outcomes.

The 2025 Position/Role outcomes have also already been accessed in the upstream Position/Role confirmation. They may not be relabeled as an untouched holdout for a newly designed defensive-exposure bridge.

Any new held-out validation period must be identified before its outcomes are opened for that downstream question.

## 7. Replacement level remains closed

Replacement level must remain separate from:

- batting skill;
- defensive skill;
- positional adjustment;
- playing time.

No replacement-run or replacement-win credit may be added until batting runs, defensive runs, defensive exposure, and positional adjustment have independently frozen production definitions.

## 8. Runs per win remains closed

No WAR calculation is authorized until:

1. batting run conversion is fixed;
2. defensive run conversion is fixed;
3. defensive exposure/opportunity mapping is fixed;
4. positional adjustment is fixed;
5. replacement level is fixed;
6. the runs-per-win convention is fixed.

The eventual WAR equation must expose each component separately so the final ranking can be audited.

## 9. Required final Player Value output decomposition

At minimum, the future player-season output must keep separate fields for:

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
- projected total defensive exposure and by-position defensive exposure;
- frozen projected Position/Role profile;
- component-specific opportunity counts used by defensive run conversion;
- component coverage/fallback flags and provenance.

Do not collapse these into one opaque value before persistence.

## 10. Immediate research gates

### Gate A — batting projected-runs reuse audit

Determine exactly how the frozen projected batting profile should consume the already-certified Performance league-bin run values. Prefer existing production transforms if present. Do not rebuild RE24 or bin calibration.

### Gate B — defensive exposure bridge

Use the frozen observed-exposure contract and certified historical fielding outs to evaluate a simple forward mapping for:

- total defensive outs;
- by-position defensive allocation;
- any component-specific opportunity counts needed later.

Compare against simple persistence baselines, preserve level/multi-level provenance, and do not refit Playing Time or Position/Role. Freeze the mapping before converting Defense skill to seasonal totals.

### Gate C — defensive run conversion

For each retained defensive target scale, document native units and test principled conversions using only authorized evidence:

- general range: Savant `diff_success_rate_formatted` / Success Rate Added;
- catcher throwing: Savant `cs_aa_per_throw`;
- catcher blocking: Savant `blocks_above_average_per_game`;
- catcher framing: repaired raw target `1000 * rv_tot / pitches` before standardization.

Do not assign one universal runs-per-z or runs-per-out constant across components.

### Gate D — positional adjustment

Research a transparent position-share-weighted schedule. Compare established public WAR conventions with an empirical public-data estimate where feasible. Freeze the method before calculating player value.

## Binding boundaries

- Do not refit Current Talent, Projection, Playing Time, Position/Role, or Defense.
- Do not tune Defense run scaling to 2025 confirmation residuals.
- Do not relabel 2025 Position/Role outcomes as an untouched exposure holdout.
- Do not assign arbitrary defensive `runs per z` values.
- Do not hide positional difficulty inside the Defense score.
- Do not replace the frozen position-share vector with a primary-position shortcut unless a later explicit validation supports it.
- Do not calculate WAR yet.
- Do not add replacement level yet.
- Do not select a runs-per-win constant yet.
