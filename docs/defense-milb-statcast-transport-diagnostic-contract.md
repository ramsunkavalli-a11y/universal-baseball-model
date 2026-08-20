# MiLB Statcast defense transport diagnostic contract

Last updated: 2026-08-18

Status: **SOURCE-TRANSPORT DIAGNOSTIC ONLY — NO DEFENSE MODEL PROMOTION.**

## Why this diagnostic exists

The frozen SportsDataverse defense reuse POC established that its public OAA implementation reproduces its own MLB oracle gate, but `mlb_statcast_search_minors()` returned zero rows for the tested 2024 AAA and Single-A requests even after explicit season scoping.

This diagnostic tests a known-working Savant MiLB CSV request semantic without altering any statistical gate:

- use SportsDataverse `0.0.75` for date-chunked MiLB CSV retrieval and OAA calculation;
- add the raw Savant parameter `minors=true`;
- do **not** rely on a server-side `hfLevel` filter;
- split the returned tracked pool client-side.

## Frozen source window

- 2024-06-10 through 2024-06-16
- regular season
- season 2024

## Client-side level split

1. Fetch the complete tracked MiLB pool for the frozen week with `minors=true`.
2. Fetch official Stats API Triple-A team abbreviations for 2024 (`sportId=11`).
3. Rows whose `home_team` abbreviation is in the official AAA set are the AAA slice.
4. Remaining tracked rows are recorded separately as the non-AAA tracked slice. For 2024, Baseball Savant documents the public non-AAA tracked coverage as Florida State League Single-A games; nevertheless, the report must retain the observed home-team abbreviations rather than silently relabel unknown rows.

No row may be assigned to AAA from player identity, velocity, or other baseball characteristics.

## Required OAA fields

Require:

- `hc_x`
- `hc_y`
- `hit_distance_sc`
- `launch_angle`
- `launch_speed`
- `hit_location`
- `events`
- `fielder_2` through `fielder_9`

`fielder_1` remains optional because the public CSV does not expose it in the already-certified MLB sample and the upstream OAA implementation dynamically uses available responsible-fielder columns.

## Frozen feasibility checks

For AAA and the tracked non-AAA slice separately, pass only if:

1. required fields are present;
2. at least 100 balls in play exist;
3. SportsDataverse OAA produces at least 100 scored fielder opportunities;
4. scored opportunities / returned BIP >= 0.50.

These are execution/coverage gates only. There is no public proprietary MiLB OAA oracle, so this diagnostic cannot validate MiLB OAA accuracy.

## Interpretation boundary

- This diagnostic may establish that the SportsDataverse **OAA implementation** is reusable on tracked MiLB data even if its default minor-search transport parameters are incomplete.
- It does not authorize universal defense, defensive projection, catcher defense, WAR/value, or untracked-level imputation.
- The prior MLB oracle result remains binding and is not rerun or retuned here.
