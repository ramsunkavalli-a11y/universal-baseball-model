# Player Value v1 steal diagnostic thresholds

Status: **BINDING ADDENDUM — PREDECLARED BEFORE MODEL FITTING**

This addendum resolves the qualitative guardrails left open in `docs/player-value-v1-steal-projection-selection-contract.md`. It does not change the candidate grid, scoring objectives, or chronology.

## Sparse-environment fallback

For affiliated MiLB:

- use an actual `league_id × season` attempt baseline when that environment has at least **500** total portable steal-opportunity-proxy events;
- use an actual `league_id × season` success baseline when that environment has at least **25** total steal attempts;
- otherwise fall back to the corresponding `level × season` baseline;
- the level × season fallback itself must have positive exposure for the channel or the affected row is unscoreable.

MLB remains one pooled AL+NL baseline and is not subject to this fallback hierarchy.

These thresholds are source-quality guards, not hyperparameters in the candidate grid. They may not be changed after candidate results are visible.

## Meaningful tier and catastrophic reversal

For a given target year and channel, a major source tier is a meaningful guardrail stratum only when it contributes at least **5% of that year's scored channel exposure**:

- attempt channel exposure = portable steal-opportunity proxy;
- success channel exposure = steal attempts.

A selected player-specific candidate has a **catastrophic tier reversal** if its primary per-exposure proper score is at least **10% worse than B0** in any meaningful tier.

A candidate with a catastrophic development-tier reversal is not eligible for selection even if its aggregate score wins.

## Held-out 2024 confirmation

The selected development winner must beat B0 on the **aggregate 2024 primary proper score** for its channel. There is no post-hoc tolerance and no reselection on 2024.

If it does not beat B0 in 2024, the player-specific candidate fails confirmation and the channel falls back to B0 for v1 unless a separate predeclared gate is opened before any alternative 2024 candidate is inspected.

The selected candidate also fails confirmation if it has a catastrophic tier reversal under the definition above in 2024.

## Exact-score tie handling

Candidate primary scores are compared at **8 decimal places** for tie handling only.

If player-specific candidates are tied at that displayed precision:

1. prefer **B1** over B2;
2. within the same history family, prefer the stronger-shrinkage prior in the order **45, 15, 5**.

This is a deterministic simplicity rule, not permission to disregard a score difference visible beyond the declared tie precision.

## Numerical safeguards

Probability/log calculations may use a fixed numerical epsilon of `1e-9` solely to prevent `log(0)` or infinite logits. Candidate predictions may not be clipped to improve scoring or ranking behavior.

Poisson means must be strictly positive for scoreable rows; a structurally zero environment rate with positive target attempts is a source/environment failure, not a value to patch with an outcome-driven constant.