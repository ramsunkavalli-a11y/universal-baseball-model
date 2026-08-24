# Hitter v2 Stage 2c unscored implementation checkpoint

Status: **IMPLEMENTED AND VERIFIED WITHOUT CANDIDATE FIT OR SCORE**  
Date: 2026-08-24  
Generated report SHA-256:
`47d069f33dece03bf163eeefcc90f3a687d9f82453e240cbea82766d9161ae1a`

## Outcome

The narrow Stage 2c candidate machinery is implemented. It does not load an
offensive target and cannot score or promote a candidate.

The power surface separately estimates `OFFB / classified contact` and
`pulled OFFB / OFFB`. Its residual can change only `HR / contact` and
`2B-or-3B / hit`; it preserves upstream K, UBB, HBP, total-contact structure,
and the 2B-to-3B mix. The ground surface separately estimates `GB / classified
contact` and `opposite GB / GB`. Its residual can change only reach versus out
within non-HR contact.

## Pre-fit clarification

Contract schemas 0.2-0.3 freeze the multiseason operation and exact nested
reach scope before any fit or score.
Within each player-season-league-level, the feature is the difference between
the player's Beta-posterior log odds and that context's log odds. These
residuals are averaged using component opportunities times the fixed two-season
recency weight. The 100-event Beta prior performs the shrinkage; the reported
reliability is not multiplied into the feature a second time.

## Unscored coverage

| Fold | Forecast players | Shape-supported | Exact fallback |
|---|---:|---:|---:|
| V2022 | 4,705 | 4,481 | 224 |
| V2023 | 5,568 | 5,323 | 245 |
| V2024 | 6,381 | 6,132 | 249 |

Among shape-supported players, pulled-OFFB opportunity is positive for 4,154,
4,986, and 5,794 players; the remaining supported players receive a literal
zero centered pulled-OFFB feature because they have classified contact but no
OFFB opportunity. This is not a zero-valued observation: the first-stage OFFB
feature and its evidence remain present, while the conditional pull component
stays at its context prior.

## Invariants

- future shape rows cannot change features at an earlier cutoff;
- zero-increment fits reproduce every base probability exactly;
- players without classified shape evidence take the exact base fallback;
- empirical-Bayes shrinkage is applied once, not twice;
- only the contract-authorized conditional contrasts can change;
- the ground residual rejects any base other than E1;
- 2B/3B composition is preserved by the power contrast;
- terminal probabilities remain exhaustive and normalized; and
- the feature builder and materializer have no target, tracking, 2026,
  leaderboard, or WAR input.

The generated report reproduced byte-for-byte across consecutive executions.
The next gate is review and explicit authorization to freeze a scorer and run
the disclosed Stage 2c development folds. Protected 2026, tracking, Stage 3,
and WAR remain unauthorized.
