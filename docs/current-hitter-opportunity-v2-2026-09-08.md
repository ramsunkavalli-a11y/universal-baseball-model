# Current hitter opportunity v2 integration

**As of:** 2026-09-08  
**Status:** provisional development scenario, not production-confirmed  
**2026 outcomes used for evaluation:** no

The durable universal hitter package now scores all 3,940 current hitters for 2027.
It uses broad level, age, current MLB and minor-league PA, and exact-date 40-man
membership. It does not use team depth or a future team.

## Current score

- 600 players were on an exact-date 40-man roster.
- 223 players were inactive and retained rather than dropped.
- 212 players had missing age and used the model's explicit missing-age path.
- Mean expected 2027 PA is 44.84, versus 40.48 from the historical cohort fallback.
- The player-level difference has a median of 0.33 PA, with a 5th-to-95th percentile
  span of -68.29 to +104.53 PA.

The current prediction file SHA-256 is
`dfe4c3d73c175cd66f34c165bd321810adfbc896506ceb2b4fec4ad075774a56`.

## Downstream effect

The model replaces only the 2027 hitter opportunity input. Hitter horizons 2028-2032
and all pitcher horizons retain the existing labeled historical fallbacks.

Relative to the retained baseline, the provisional scenario adds 101.46 expected WAR
to the full future player universe. The contract-controlled annual rows add 108.72 WAR,
all in 2027. The isolated hitter-only checkpoint contained 51,070 rows,
calculates 8,362 player paths, and leaves the same 16 annual contract reviews across
11 players. Its discounted point total is $3.01 billion, versus $1.66 billion in the
retained baseline. The later combined hitter-and-pitcher result is documented in
`current-universal-opportunity-v2-2026-09-08.md`.

The $1.35 billion difference is a model sensitivity, not a validated increase in
league value. It is amplified by player-level market tiers and control status. The
retained production baseline is not overwritten.

## Boundary

This run proves that the selected package can score the current universe and pass
through WAR, uncertainty, current rights, and contract economics without hidden
fallbacks. It does not provide an untouched outcome confirmation. Completed 2026 MLB
PA remains the first protected confirmation target.
