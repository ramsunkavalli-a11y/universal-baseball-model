# ADR 007: Use Gameday field coordinates for universal batted-ball direction

- Status: Accepted for the universal PBP evidence layer
- Date: 2026-08-15

## Context

The FaBIO-inspired Performance layer needs Pull / Center / Opposite direction for ground balls, line drives, and outfield fly balls. The project charter requires that we evaluate existing public implementations before inventing our own transformation.

Public precedent already solves the coordinate conversion:

- Matt Collier's public FaBIO descriptions divide batted-ball direction into thirds of the field and adjust for batter handedness.
- FanGraphs describes Pull / Center / Opposite as three equal 30-degree field sections.
- `pybaseball` implements the established Bill Petti / Zimmerman Gameday/Statcast spray-angle transform:

  `atan2(hc_x - 125.42, 198.27 - hc_y) * 180/pi * 0.75`

- Bill Petti's published Statcast database code uses the same home-plate constants and `0.75` calibration.

A current SportsDataverse helper cites the same public precedent but omits the `0.75` factor and has a sign-description inconsistency. We therefore reuse the established Petti/pybaseball transform directly in Polars rather than importing that helper.

The key empirical question was whether `hc_x/hc_y` behaves like optional Statcast sensor data or like broadly available Gameday/stringer field-location evidence.

## Certification evidence

The reusable MiLB source's direct batted-ball fields were first compared with current official MLB Stats API `hitData` in five AAA games. All 349 current official in-play pitch keys were present. `hc_x`, `hc_y`, trajectory, fielding location, distance, exit velocity, launch angle, and batter side agreed whenever both snapshots had values except one later launch-angle revision. This established that source `hc_x/hc_y` is a direct official-feed field rather than a locally derived estimate.

Cross-level and cross-era coverage then showed that coordinates are nearly universal among physical in-play pitch keys:

| Slice | In-play keys | `hc_x + hc_y` coverage |
|---|---:|---:|
| 2005 Sep AAA | 3,696 | 99.0% |
| 2015 Sep AAA | 5,221 | 98.8% |
| 2023 Aug AAA | 11,938 | ~100.0% |
| 2023 Aug AA | 11,978 | ~100.0% |
| 2023 Aug High-A | 11,524 | 100.0% |
| 2023 Aug Single-A | 11,210 | ~100.0% |
| 2023 Aug Rookie/complex/DSL | 17,967 | ~100.0% |
| 2024 Rookie/complex/DSL | 21,652 | ~100.0% |
| 2025 AAA | 1,291 | 100.0% |
| 2025 AA | 9,952 | ~100.0% |
| 2025 High-A | 10,159 | ~100.0% |
| 2025 Single-A | 10,113 | ~100.0% |

No audited `type`, `bb_type`, `hit_location`, `hc_x`, `hc_y`, or `stand` conflicts occurred on a natural pitch key in these tested assets after repeated source observations were handled deterministically.

This is materially different from pitch tracking such as velocity/spin/launch measurements. Field coordinates behave like a near-universal Gameday/stringer field-position signal and belong in the universal PBP evidence tier.

## Decision

### Field-relative angle

Use the established public transform exactly:

`field_spray_angle = atan2(hc_x - 125.42, 198.27 - hc_y) * 180/pi * 0.75`

Canonical sign convention:

- negative = left field;
- zero = straightaway center;
- positive = right field.

Coordinates are explicitly cast to numeric because sparse historical/lower-level CSV columns can infer as strings. Invalid or blank values become null rather than failing or being imputed.

### Direction thirds

Split the approximately 90-degree fair field into equal thirds:

- left field: angle < -15°;
- center: -15° through +15°, inclusive;
- right field: angle > +15°.

Then adjust by the batter's event-level batting side:

| Batter side | Left field | Center | Right field |
|---|---|---|---|
| R | Pull | Center | Opposite |
| L | Opposite | Center | Pull |

A switch hitter uses the event-level `stand` value. If coordinates or a usable L/R batting side are absent, direction is **unknown**.

### No automatic `hit_location` fallback

Do **not** use fielder/location code as the automatic direction fallback.

A diagnostic handedness-adjusted mapping of standard fielding locations agreed with coordinate-derived thirds only about 73–82% overall in the tested slices. Agreement was much better for fly balls (~87–99%) but only about 65–76% for ground balls and similarly weak for popups. This is consistent with `hit_location` describing a fielder/location outcome rather than the ball's geometric spray direction; defensive positioning can separate those concepts.

Because coordinate coverage is already ~99%+ even in old and Rookie/DSL data, the small coverage gain from a noisy fallback is not worth contaminating the universal feature. Missing coordinate direction remains `unknown` and carries reduced effective evidence.

## Implementation

The candidate implementation lives in:

- `src/universal_baseball/batted_ball_direction.py`
- `src/universal_baseball/direction_coverage.py`

Tests cover:

- public Petti/pybaseball calibration fixtures;
- handedness-adjusted thirds;
- exact ±15° boundary behavior;
- null/invalid evidence;
- sparse string coordinate columns;
- deterministic repeated-source collapse and conflict quarantine.

## Consequences

- Pull / Center / Opposite can be part of the universal PBP/Profile layer rather than an optional tracking tier.
- FaBIO-like directional event bins can be constructed for essentially the entire affiliated historical universe without imputing Statcast data.
- Missing coordinate direction is explicit and rare, not filled from a weaker proxy.
- `hit_location` remains useful raw/context evidence and a diagnostic signal, but it is not treated as geometric spray direction.
- Rich sensor measurements such as exit velocity, launch angle, pitch velocity, and spin remain separate evidence tiers with structural coverage metadata.

## Remaining related work

This ADR accepts **direction**, not the full FaBIO event taxonomy. Before the 12-bin Performance profile is productionized, the project still needs to certify the mapping of source `bb_type` vocabulary into IFFB / OFFB / LD / GB, especially how `popup` and bunt trajectories should be handled, and define the treatment of rare/unknown batted-ball types.
