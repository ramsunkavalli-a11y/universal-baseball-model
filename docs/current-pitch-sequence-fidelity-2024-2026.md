# Minor-league pitch-sequence fidelity

Last updated: 2026-09-12  
Status: **CURRENT PROCESS EVIDENCE FEASIBLE; HISTORY LIMITED**

Official StatsAPI game feeds were sampled across August at every affiliated level.
The test looks for outcome-minimal entry: nearly every strikeout recorded as exactly
three pitches, walk as four, and ball in play as one.

| Season | AAA through Single-A | Rookie/complex |
|---|---|---|
| 2015 | AAA/AA normal; High-A and Single-A partly synthetic | Not promoted |
| 2016–17 | Mixed historical transition; not promoted | Not promoted |
| 2018–19 | Normal-looking sampled sequences | Not needed for current test |
| 2021 | Normal-looking sampled sequences | Synthetic in ACL, FCL and DSL |
| 2022 | Normal-looking sampled sequences | Synthetic in ACL, FCL and DSL |
| 2023 | Normal-looking sampled sequences | Synthetic in ACL, FCL and DSL |
| 2024 | Normal-looking sampled sequences | Synthetic: 89% K at 3 pitches, 100% BB at 4, 91% BIP at 1 |
| 2025 | Normal-looking sampled sequences | Normal-looking: 23%, 27%, 20% |
| 2026 | Normal-looking sampled sequences | Normal-looking: 21%, 26%, 22% |

The added 2021–2023 audits used 20 games spread across August at each level and
covered all 11 actual full-season leagues each year. The 2021–22 pooled exact-minimum
K/BB/BIP shares were roughly 10%–23%, compared with 86%–98% for Rookie/complex.
The full 2023 repeat produced the same normal full-season/synthetic Rookie split.
This certifies the full-season leagues for 2018–19 and 2021–24 pitch-process work while
explicitly rejecting the synthetic Rookie rows. The uneven 2015–17 feeds remain
uncertified and are excluded rather than patched or imputed.

The 2025-2026 DSL result marks a real feed change from 2024. Current swing, whiff and
called-strike features can be built from StatsAPI even though velocity, movement and
pitch type remain absent below AAA. This audit establishes source plausibility, not
forecast value.

Use these fields only as optional supporting evidence until a chronological forecast
test passes. Never backfill 2024 DSL whiff rates, mix synthetic and physical sequences,
or treat a missing process field as favorable talent. Other actual leagues were spread
across the level sample and have fewer than 20 games each, so their result remains a
strong probe rather than final league-by-league certification.
