# ADR 023 — Use modest AL/NL peer pooling for MLB Performance-bin values

**Status:** Accepted  
**Date:** 2026-08-16

## Decision

For MLB batting Performance contextual bin values, estimate each AL/NL league-season-bin mean from the fixed canonical RE24 definition and shrink it toward the same bin in the *other MLB league* by **5 prior-equivalent occurrences**.

No MiLB, adjacent-season, or broader fallback prior is allowed. If the peer MLB league/bin is unavailable, retain the direct estimate but mark it uncertified.

This is contextual Performance-bin value stabilization. It is **not** player-talent shrinkage and must not be reused as a Current Talent prior.

## Evidence

The primary 2024 MLB audit used:

- the independently validated 24-state RE24 definition;
- 45 deterministic spread intraleague AL games and 45 NL games;
- the frozen screened 12-bin Performance taxonomy;
- bidirectional split-half and five-fold held-out scoring;
- direct estimates versus a pre-declared prior-strength grid.

Positive strengths 5, 10, 25, 50, and 75 matched or improved the direct baseline on every required split-half and five-fold metric. Per the pre-specified selection rule, the **smallest robust positive strength, 5**, was nominated for independent confirmation.

The independent 2023 confirmation then froze lambda=5 before examining that season and reran the identical 45-game-per-league design. Lambda=5 improved every required metric in both tests:

### 2023 split-half

- cell MAE: 0.054825 -> 0.052430
- cell RMSE: 0.072208 -> 0.068439
- event MAE: 0.285772 -> 0.285558
- event RMSE: 0.433185 -> 0.432830
- occurrence-weighted cell MAE: 0.038810 -> 0.037375

### 2023 five-fold

- cell MAE: 0.063179 -> 0.062578
- cell RMSE: 0.098133 -> 0.097318
- event MAE: 0.285541 -> 0.285491
- event RMSE: 0.433158 -> 0.433051
- occurrence-weighted cell MAE: 0.047338 -> 0.046958

No alternative strength was considered after observing the confirmation season.

## Rationale

AL and NL run-value environments are already highly similar, so a strong pooling prior would add unnecessary bias. The held-out evidence supports only a small amount of stabilization, and the independent-season confirmation shows that the direction is reproducible rather than a one-season artifact.

The same-level peer rule also preserves the architecture used in the affiliated model: environment values may borrow only from directly comparable environments when held-out evidence supports doing so.

## Consequences

- MLB can now use the same stable Performance output contract as affiliated MiLB while retaining a separately certified environment policy.
- The existing affiliated league map remains unchanged; MLB is not treated as an affiliated level merely to reuse code.
- Historical/forward Current Talent validation must still freeze environment/run-value tables using only training-period information when a true predictive claim is made. This ADR certifies the descriptive Performance estimator form; it does not waive chronological leakage rules.
