# Player Value v1 — Defense native run-conversion selection contract

Last updated: 2026-08-19

Status: **PREDECLARED PRODUCTION RUN-CONVERSION SELECTION FROM PRE-2025 DIAGNOSTICS.**

## Purpose

Freeze the Player Value v1 conversion from each already-frozen standardized Defense skill output
to public seasonal defensive runs per native opportunity, without refitting Defense skill.

The only empirical input to this selection is
`docs/player-value-v1-defense-native-run-rate-calibration-result.json`, produced from 2022-2024
targets under the preregistered calibration diagnostic. No 2025 confirmation residual may be used.

## Common form

Every retained conversion has a zero intercept:

`component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity`.

This preserves the frozen neutral fallback: `skill_z = 0` maps to zero modeled component runs.

The production scale is the **median of the three year-specific through-origin slopes** whenever the
stability guardrails below pass. No coefficient is refit in this gate.

## General range

Native production opportunity is the already-frozen projected MLB defensive outs at the relevant
position.

Candidate scale hierarchy for each position:

1. use that position's median 2022-2024 slope if:
   - all three slopes are positive;
   - coefficient of variation <= 0.15; and
   - max/min slope ratio <= 1.50;
2. otherwise use the corresponding IF or OF pooled-group median slope if that group satisfies the
   same guardrails;
3. if the required group also fails, leave that position's run conversion unresolved and fail this
   freeze.

Groups:
- IF = `1B, 2B, 3B, SS`;
- OF = `LF, CF, RF`.

This hierarchy is allowed because the frozen target is standardized within target season x
position, while the public Statcast range-run methodology distinguishes infield from outfield.
The same rule applies to T1 and U1; family does not change the scale.

For a multi-position player, calculate range runs separately by projected position outs and sum.
Do not apply a primary-position scale to all defensive exposure.

## Catcher throwing

Native opportunity: projected stolen-base throw opportunities / `sb_attempts`.

Select the median 2022-2024 throwing slope if:
- all slopes are positive;
- coefficient of variation <= 0.10; and
- max/min slope ratio <= 1.25.

The source identity
`caught_stealing_above_average = cs_aa_per_throw * sb_attempts`
and the public run identity
`catcher_stealing_runs = 0.65 * caught_stealing_above_average`
must remain recorded as provenance.

## Catcher blocking

Native opportunity: projected Baseball Savant blocking `pitches`.

Do not use `n_pbwp` as the opportunity denominator. The calibration diagnostic showed that the
predeclared `n_pbwp / 40` reconstruction fails materially, while the public Savant methodology
defines Blocks Above Average / game from an average 40 blocking chances and treats each received
pitch as a blocking opportunity.

Select the median 2022-2024 `pitches` slope if:
- all slopes are positive;
- coefficient of variation <= 0.10;
- max/min slope ratio <= 1.25; and
- its run RMSE is lower than the `n_pbwp` calibration in every development year.

The public source conversion of 0.25 runs per block remains provenance, not a separately tuned
coefficient.

## Catcher framing

Native opportunity: projected framing pitches.

Select the median 2022-2024 framing slope if:
- all slopes are positive;
- coefficient of variation <= 0.10; and
- max/min slope ratio <= 1.25.

The repaired raw target `1000 * rv_tot / pitches` and direct seasonal run field `rv_tot` remain
the native-source provenance.

## Required frozen parameter output

Persist:
- exact calibration diagnostic source run/SHA and artifact provenance;
- selected scale for every general position;
- whether each general position used its own or a group fallback scale;
- selected throwing, blocking, and framing run-rate constants;
- native opportunity unit for each component;
- formula and zero-intercept semantics;
- all gate outcomes;
- explicit unresolved-component flag.

## Boundaries

- No 2025 data or confirmation residuals.
- No Defense refit or rescore.
- No Playing Time or Position/Role refit.
- General defensive outs/allocation remain frozen.
- Catcher native-opportunity **forecasting** remains a separate next gate; this contract only
  identifies their units and run-rate constants.
- Positional adjustment remains separate.
- Replacement level, runs per win, WAR/value aggregation, and final ranking remain unauthorized.
