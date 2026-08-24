# Hitter v2 Stage 2 C1 unscored checkpoint

Date: 2026-08-24

## Scientific outcome

The frozen C1 implementation produced complete, unscored PBP-only forecasts
for all three predeclared forecast populations without loading target outcomes
or evaluation membership. All chronology, population, simplex, MLB-anchor,
zero-offset, and exact GIDP-fallback invariants passed. The generated report is
identified by SHA-256
`9263770a1ac7072344377b1c54519b3fcabd1077d86bf15caa93de1e7311afe4`.

The materialized configuration is a non-decisional conservative sentinel:
half-life `1`, component prior `800` PA, park prior
`2,000` PA, movement prior `500` mover PA, and age ridge `100`. These artifacts
prove implementation behavior; they do not select or promote a model.

## Fold findings

| Fold | Forecast players | Adjacent movement pairs | Explicit limitation |
| --- | ---: | ---: | --- |
| V2022 | 4,705 | 0 | Age is neutral; 3,923 non-MLB histories use disconnected-level translation fallback. |
| V2023 | 5,568 | 3,176 | No age or translation fallback; two players use exact GIDP fallback. |
| V2024 | 6,381 | 6,297 | No age or translation fallback; two players use exact GIDP fallback. |

V2022 cannot estimate adjacent-season movement or age effects because the
certified all-level outcome history begins in 2021 and its predictor cutoff is
2021. The implementation does not borrow 2022 or later rows. This is a real
early-fold source limitation, not an invariant failure, and must remain visible
in the scored fold diagnostics.

The maximum C1 simplex error in every fold was
`2.220446049250313e-16`. Missing GIDP evidence reproduced the pre-GIDP
prediction bit-for-bit. Zero park, age, and translation offsets reproduced C0
bit-for-bit in the sentinel identity check. All MLB level-offset components
were exactly zero.

## Gate decision

The unscored implementation gate passes. After this checkpoint is committed
locally, the already-authorized next gate is training-origin grid selection and
scoring on disclosed 2022–2024 validation outcomes. The grid cannot expand in
response to those results. Tracking, protected 2026 confirmation, Stage 3, and
full WAR remain closed.
