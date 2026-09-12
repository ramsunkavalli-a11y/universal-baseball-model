# Current minor-league pitch-sequence fidelity

Last updated: 2026-09-12  
Status: **CURRENT PROCESS EVIDENCE FEASIBLE; HISTORY LIMITED**

Official StatsAPI game feeds were sampled across August at every affiliated level.
The test looks for outcome-minimal entry: nearly every strikeout recorded as exactly
three pitches, walk as four, and ball in play as one.

| Season | AAA through Single-A | DSL |
|---|---|---|
| 2024 | Normal-looking sampled sequences | Synthetic: 89% K at 3 pitches, 100% BB at 4, 91% BIP at 1 |
| 2025 | Normal-looking sampled sequences | Normal-looking: 23%, 27%, 20% |
| 2026 | Normal-looking sampled sequences | Normal-looking: 21%, 26%, 22% |

The 2025-2026 DSL result marks a real feed change from 2024. Current swing, whiff and
called-strike features can be built from StatsAPI even though velocity, movement and
pitch type remain absent below AAA. This audit establishes source plausibility, not
forecast value.

Use these fields only as optional supporting evidence until a chronological forecast
test passes. Never backfill 2024 DSL whiff rates, mix synthetic and physical sequences,
or treat a missing process field as favorable talent. Other actual leagues were spread
across the level sample and have fewer than 20 games each, so their result remains a
strong probe rather than final league-by-league certification.
