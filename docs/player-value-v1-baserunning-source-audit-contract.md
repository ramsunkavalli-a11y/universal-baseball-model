# Player Value v1 baserunning source / overlap audit contract

Status: **SOURCE SEMANTICS FROZEN FOR AUDIT — MODEL NOT YET FROZEN — WAR CLOSED**

This document fixes the evidence hierarchy and double-counting boundaries for the Player Value v1 baserunning gate before any baserunning model is selected or any final Player Value rankings are inspected.

## 1. Why this gate exists

The frozen batting component is not a conventional linear-weights batting line. It projects a player's 12-bin core-event composition and values each bin using league-season mean PA-level RE24. That architecture creates an important overlap question for ground-into-double-play value and requires baserunning to be added only where it represents value not already embedded in batting.

The goal of this gate is therefore to identify additive baserunning information, not to reproduce FanGraphs or Baseball-Reference component names mechanically.

## 2. GIDP overlap ruling

### 2.1 Raw GIDP run value is not additive

The Performance pipeline computes PA-level RE24 from the actual before/after base-out transition:

`RE24 = runs_scored + RE(after) - RE(before)`.

Direct batting-bin values are then the mean of those PA-level run values within each core bin. A ground ball that becomes a double play therefore contributes its additional out and resulting base-state change to the league mean run value of its ground-ball bin.

**Binding audit ruling:** do not add a raw `GIDP * run_penalty` or conventional unmodified wGDP term to Player Value v1. Doing so would count the baseline double-play cost once inside the frozen batting-bin run value and again inside baserunning.

### 2.2 A residual GIDP skill may still be additive

The frozen batting projection uses each player's projected ground-ball-bin composition multiplied by league mean bin values. It does not separately carry forward a player's individual tendency to ground into a double play conditional on a double-play opportunity.

Accordingly, the only GIDP candidate allowed into diagnostics is an **opportunity-adjusted, league-centered residual** measuring whether a player creates more or fewer double plays than expected given his opportunities. If retained, its run conversion must represent only the incremental value relative to the double-play incidence already embedded in the batting-bin reference value; it may not use the full raw RE24 of a double-play PA.

If that residual does not show stable out-of-sample signal under the predeclared validation design, Player Value v1 will omit a separate GIDP component.

## 3. Source hierarchy

### 3.1 Steal channel

Preferred universal evidence:

1. official MLB Stats API season-player batting counts for MLB;
2. the already-certified armstjc affiliated season-player releases for MiLB;
3. neutral fallback when the required evidence is unavailable.

Required source fields are stolen bases and caught stealing. They must remain raw observed counts at the evidence layer; no missing count may be silently filled with zero.

### 3.2 GIDP residual candidate

Preferred evidence:

1. official MLB Stats API season-player GIDP and GIDP-opportunity counts, **only if the live API proves both fields are present and semantically usable**;
2. armstjc affiliated season-player `batting_GiDP` and `batting_GiDP_Opp` for MiLB;
3. no residual candidate for a level/season where a defensible opportunity denominator is unavailable.

The MiLB release extractor explicitly exposes `stolenBases`, `caughtStealing`, `gidpOpp`, and `groundIntoDoublePlay`; the local standardized adapter maps these as `batting_stolen_bases`, `batting_caught_stealing`, `batting_gidp_opportunities`, and `batting_ground_into_double_play`.

### 3.3 Non-steal advancement channel

For MLB, the preferred evidence is the public Baseball Savant / Statcast baserunning advancement value or its public opportunity-level inputs. This source must be captured through a dedicated baserunning adapter with exact provenance rather than mixed into the existing pitch-detail Savant adapter.

The frozen source-audit surface is the public runner-level regular-season CSV from:

`https://baseballsavant.mlb.com/leaderboard/baserunning-run-value`

Use one season per request with runner type, minimum one opportunity, no year split, and the CSV response. The implementation may use a thin `requests` adapter rather than taking a package dependency, but it must follow the already-public reusable client semantics documented by SportsDataverse / Savant helper projects instead of reverse-engineering a new event model.

Normalize CSV header case only. Required fields for this gate are:

- `player_id`;
- `runner_runs_tot`;
- `runner_runs_xb`;
- `runner_runs_sbx`;
- `n_runner_moved`;
- `n_runner_moved_xb`;
- `n_runner_moved_sbx`.

`runner_runs_xb` and `n_runner_moved_xb` are the candidate **non-steal advancement** evidence. `runner_runs_sbx` remains source-validation evidence only at this stage because the portable steal channel is selected separately. Do not add `runner_runs_tot` to the portable steal component; that would double-count stolen-base value.

Audit completed seasons **2019 through 2024**. This window is source certification only; it is wide enough to support a later three-prior-season chronological diagnostic for a 2022 target without opening 2025 evidence.

No comparable public affiliated-MiLB advancement-value source has been certified. Until one is found and validated, MiLB-only players receive **no invented non-steal advancement differentiation**. A neutral fallback is preferable to a weak proxy chosen after looking at player rankings.

## 4. Candidate decomposition

The audit may evaluate the following additive structure:

`Rbr = Rsteal + Radvance + Rgidp_residual`

where:

- `Rsteal` is the portable MLB/MiLB steal component;
- `Radvance` is the MLB Statcast non-steal advancement component, with neutral fallback outside supported evidence;
- `Rgidp_residual` is optional and must satisfy the overlap restriction in Section 2.

A candidate component may be dropped after predeclared predictive diagnostics. No omitted component may be restored because final rankings look more intuitive.

## 5. Development / confirmation firewall

Baserunning candidate selection must be completed without using final Player Value rankings as an objective.

The diagnostic plan must declare development and confirmation seasons before fitting. Evidence from a held-out confirmation season may determine whether a predeclared candidate passes its gate, but it may not be used iteratively to tune coefficients after inspection. The existing project rule against using 2025 to tune newly invented parameters remains binding unless an earlier contract explicitly authorized that use.

## 6. Required source audit before modeling

Before fitting any baserunning candidate, persist a machine-readable source audit proving, for each supported source/season:

- field presence and exact source names;
- integer-like, nonnegative observed counts;
- `GIDP <= GIDP opportunities` wherever both exist;
- exact season/league/level provenance;
- missingness rates and supported player-season counts;
- no silent zero-filling;
- explicit result for whether MLB `gidpOpp` is actually available from the official bulk source.

For the Savant advancement surface also persist:

- exact request parameters and season;
- response byte count and SHA-256;
- normalized required-field coverage;
- finite run values;
- nonnegative integer opportunity counts;
- duplicate `player_id` diagnostics;
- diagnostic-only checks of total-vs-component run values and opportunity counts.

The Savant source gate passes a season only when all required fields are complete, runner IDs are unique, and non-steal advancement opportunity evidence is present. Arithmetic decomposition is recorded as a diagnostic because displayed/served component rounding may differ; it is not silently repaired.

The source audit may expand the evidence schema. It may not select baserunning model coefficients.

## 7. What remains open

The following are intentionally **not frozen** by this document:

- steal run weights / centering convention;
- whether to project steal attempts and success separately or project a centered run rate directly;
- MLB advancement current-talent / projection method;
- whether the GIDP residual is predictive enough to retain;
- any shrinkage strengths, history windows, or exposure thresholds;
- final baserunning run aggregation.

Those choices must be resolved through the next predeclared diagnostic/selection gate.

## 8. Downstream boundary

WAR remains closed until baserunning is frozen and verified, MLB-reference centering is resolved, the park-neutrality audit is complete, and all required sensitivities have been recorded. This gate must not alter already-frozen batting, defense, positional-adjustment, replacement, or runs-per-win methodology except to document a demonstrated double-counting conflict.
