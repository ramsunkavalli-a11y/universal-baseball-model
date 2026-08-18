# Defense SportsDataverse reuse POC contract

Last updated: 2026-08-18

Status: **SOURCE / REUSE FEASIBILITY ONLY — NO DEFENSE MODEL PROMOTION.**

## Question

Can the project reuse SportsDataverse `0.0.75` and public Baseball Savant data for a useful defensive range / outs-above-average evidence tier, rather than building a new defensive-event parser or OAA implementation from scratch?

This POC may execute SportsDataverse's existing OAA estimator to test the reusable implementation. It does **not** authorize a production defense model, a universal MiLB defense score, catcher value, throwing value, team allocation, WAR, or final ranking.

## Upstream implementation frozen for this POC

- package: `sportsdataverse==0.0.75`
- inspected upstream commit: `1dafadb38c5240d8e29a0f818efbabe04cd6c417`
- OAA implementation: `sportsdataverse/mlb/mlb_fielding_oaa.py`
- Statcast transport: `sportsdataverse/mlb/mlb_statcast_extra.py`

The upstream OAA implementation fits a per-position smooth logistic catch/out probability using public landing distance, launch angle, exit velocity, and spray angle, then sums `is_out - p_catch` by responsible fielder. Public Statcast does not expose proprietary fielder starting coordinates, so this is an approximation of Savant OAA rather than a reproduction of the proprietary model.

## Source windows

### MLB oracle slice

- 2024-06-01 through 2024-06-30, regular season
- derive balls in play from the returned Statcast pitch table (`type == "X"` when available)
- compare the reusable OAA output to the official Savant 2024 OAA leaderboard

This deliberately mirrors the upstream package's committed month-vs-season oracle design rather than selecting a new favorable sample.

### Tracked MiLB feasibility slices

Use 2024-06-10 through 2024-06-16, regular season:

- `hfLevel=AAA|`
- `hfLevel=A|`

These are tracking-coverage tiers, not claims of universal affiliated coverage. Missing AA, High-A, complex, or DSL evidence must remain missing rather than being imputed from this POC.

## Required public fields

For each balls-in-play sample require the columns used by the upstream OAA implementation:

- `hc_x`
- `hc_y`
- `hit_distance_sc`
- `launch_angle`
- `launch_speed`
- `hit_location`
- `events`
- `fielder_1` through `fielder_9`

## Frozen checks

### MLB implementation/oracle gate

Pass only if all are true:

1. all required columns are present;
2. the June MLB BIP sample is non-empty;
3. reusable OAA produces at least 50 matched fielders against the Savant 2024 OAA leaderboard;
4. Pearson correlation between June reusable OAA and full-season Savant OAA is **>= 0.30**, matching the upstream package's frozen month-vs-season oracle gate.

Do not lower the correlation gate after seeing the result.

### MiLB execution/coverage gate, separately for AAA and Single-A

Pass a tracked level slice only if all are true:

1. all required columns are present;
2. at least 100 balls in play are returned;
3. the OAA implementation produces at least 100 total scored fielder opportunities;
4. scored opportunities / returned BIP is at least 0.50.

These checks establish technical/source feasibility only. They do not validate MiLB OAA against an unavailable proprietary MiLB OAA oracle.

## Interpretation

Possible outcomes:

- MLB passes, AAA/A pass: SportsDataverse is a viable reusable **tracked-defense evidence tier**; next work should define chronology, shrinkage/projection, coverage fallback, and non-range defensive components before production use.
- MLB passes, one or both MiLB slices fail: retain SportsDataverse as an MLB implementation candidate and explicitly limit MiLB use to demonstrated coverage; investigate source coverage only, not model rescue tuning.
- MLB fails: do not promote this OAA implementation. Diagnose package/source/version behavior before considering a custom model.

Regardless of outcome:

- `universal_defense_authorized = false`;
- `catcher_defense_authorized = false`;
- `war_value_authorized = false`;
- Position/Role v1 and Playing Time v1 remain frozen and untouched.

## Provenance

Persist:

- exact package version;
- date windows and filters;
- returned row/BIP counts;
- required-field missingness/non-null coverage;
- OAA opportunity counts and coverage rates;
- MLB Savant join count and correlation;
- a machine-readable decision record.
