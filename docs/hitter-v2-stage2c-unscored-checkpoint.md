# Hitter v2 Stage 2c schema 0.4 unscored implementation checkpoint

Status: **IMPLEMENTED AND VERIFIED WITHOUT CANDIDATE FIT OR SCORE**  
Date: 2026-08-24  
Generated report SHA-256:
`2ed7ceb2fde23d2da46dd2b5b47c3c7339200ec3dab93e8a9fab88c366a7c901`

## Outcome

The schema 0.4 ladder is implemented in the predeclared order. The module has
no source loader, scorer, promotion path, tracking route, leaderboard, or WAR
assembly, and the materializer loads no offensive target.

1. `E1_NESTED_PULLED_OFFB_POWER` uses the two shrunk pulled-air features and
   can change only `P(HR | contact)`.
2. `E2_PULLED_OFFB_XBH_ABLATION` reuses the same features, requires E1 as its
   base during both fitting and prediction, and can change only
   `P(2B/3B | non-HR hit)`.
3. `E3_SEPARATE_GROUND_DIRECTION` requires an E1 or E2 air candidate as its
   base during fitting and prediction and can change only reach versus out
   within non-HR contact.

This supersedes the schema 0.3 implementation before any Stage 2c candidate fit
or score. It does not erase the earlier checkpoint or its hashes.

## Unscored coverage

| Fold | Forecast players | Shape-supported | Exact fallback |
|---|---:|---:|---:|
| V2022 | 4,705 | 4,481 | 224 |
| V2023 | 5,568 | 5,323 | 245 |
| V2024 | 6,381 | 6,132 | 249 |

E1 and E2 intentionally have identical evidence coverage because they use the
same pulled-air features. They remain separate models because their permitted
outcome contrasts, base requirements, fitted coefficients, diagnostics, and
advance rules differ.

Among shape-supported players, pulled-OFFB opportunity is positive for 4,154,
4,986, and 5,794 players. A supported player with no OFFB opportunity retains
the first-stage OFFB feature while the conditional pull residual remains at
the context prior; missingness is not treated as observed zero talent.

## Invariants

- future shape rows cannot change features at an earlier cutoff;
- the chained E1/E2/E3 zero-increment ladder reproduces every C0 probability;
- players without classified shape evidence take the exact current-base
  fallback at each step;
- empirical-Bayes shrinkage is applied once, not twice;
- E1 cannot change XBH composition or any non-HR conditional branch;
- E2 cannot change HR, reach, or 2B-versus-3B composition;
- E2 rejects a non-E1 base during fitting and prediction;
- E3 cannot change HR or hit composition and rejects a non-air base;
- terminal probabilities remain exhaustive and normalized; and
- distance, EV/LA, target outcomes, evaluation membership, and protected 2026
  outcomes are absent from this gate.

The generated report reproduced byte-for-byte across consecutive executions.
The next gate is review. Freezing or running a scorer is not authorized by this
checkpoint. Protected 2026, tracking, Stage 3, and WAR remain unauthorized.
