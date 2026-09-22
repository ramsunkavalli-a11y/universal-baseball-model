# Hitter gradient feature-ablation result

Status: **full model passes the development gate and becomes the leading hitter
candidate; 2026 remains protected for final confirmation**

## Plain-language conclusion

The improvement is not merely caused by switching from a linear model to a tree.
The detailed contact type by outcome information adds a clear improvement beyond
the tree control. Opponent quality adds a smaller gain, and park information adds
another clear gain. The complete model beats the contact-only projection with its
entire paired 95% interval on the favorable side for RMSE, log loss, and Brier.

All comparisons use 6,799 next-season forecasts and resample 3,613 players as
whole career clusters 5,000 times. This keeps repeated seasons from the same player
together instead of pretending they are independent.

## What contributed to the RMSE improvement

| Cumulative model | RMSE | Added improvement | Approx. share of full gain |
|---|---:|---:|---:|
| Contact-only incumbent | 0.014597 | — | — |
| Tree control: age, level, workload | 0.014477 | -0.000120 | 43% |
| Add detailed contact type × result | 0.014379 | -0.000098 | 35% |
| Add prior opponent quality and handedness | 0.014362 | -0.000017 | 6% |
| Add park effects and reliability | 0.014318 | -0.000044 | 16% |

These shares describe this fixed cumulative ordering; they are not claims that the
families are perfectly separable. The important result is that contact detail still
improves the same tree after the basic control is present.

## Statistical checks

Candidate-minus-baseline values below zero are better.

| Comparison | RMSE change | Paired 95% interval | Chance candidate is better |
|---|---:|---:|---:|
| Contact detail vs tree control | -0.000098 | [-0.000140, -0.000057] | 100.0% |
| Opponent context vs contact detail | -0.000017 | [-0.000032, -0.000002] | 98.8% |
| Park context vs opponent model | -0.000044 | [-0.000061, -0.000028] | 100.0% |
| Full model vs contact-only | -0.000279 | [-0.000343, -0.000215] | 100.0% |

For the full model versus contact-only, the paired intervals also exclude zero for
log loss [-0.000276, -0.000160] and Brier [-0.000063, -0.000026].

Opponent context's incremental log-loss and Brier intervals narrowly cross zero,
so its strongest evidence is RMSE. Park context has clear incremental RMSE and
Brier gains, while its incremental log-loss interval crosses zero. The complete
model nevertheless clears all three measures decisively against the incumbent.

## Decision

The complete gradient tree is now the leading **development** hitter base model.
The old contact-only forecast remains the production reference until the protected
2026 confirmation is available. No 2026 outcome was used here.

A subsequent identical-feature comparison tested XGBoost and LightGBM with limited
nested chronological tuning. Neither beat the scikit-learn histogram-gradient
engine across the complete scoring rule; see
`hitter-gradient-engine-comparison-v1-result.md`.

The next useful work is to freeze the training recipe and produce 2026 predictions
without fitting against 2026 results. Further feature or hyperparameter searching
against these same 2022-2025 outcomes would weaken the evidence rather than improve
it.
