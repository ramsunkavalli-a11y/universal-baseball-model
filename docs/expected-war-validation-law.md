# Expected-WAR validation law

Status: active methodology rule as of 2026-09-10.

## Correction

The product needs expected WAR and expected surplus value, not the median player's
WAR. Squared error is consistent for a conditional mean. Absolute error is consistent
for a conditional median. In a prospect cohort where most players record zero future
MLB WAR, an all-zero forecast can therefore win MAE by construction even while it is
wrong for expected value.

Reference: Tilmann Gneiting, *Making and Evaluating Point Forecasts*, Journal of the
American Statistical Association 106 (2011), 746–762,
<https://doi.org/10.1198/jasa.2011.r10138>.

MAE remains a useful description of a median forecast, but it is no longer a veto for
an expected-WAR or expected-value model.

## Required gate

A future linked career model must pass all of these, in time order and on identical
players:

1. arrival probabilities: Brier score and log loss;
2. complete zero-inclusive predictive distribution: a proper distribution score such
   as CRPS, including the exact zero mass;
3. expected WAR: paired squared-error improvement and an absolute-bias check;
4. supported predeclared subgroup review; and
5. genuinely fresh confirmation.

This does not retroactively promote the linked pitcher path. Its existing paired MSE
interval against the historical incumbent crosses zero, it lacks a scored predictive
distribution, and the cohort is not fresh. It only removes MAE as an invalid reason
for rejection and states the correct next test.

## First distribution result

The cutoff-safe 2021 pitcher replay now scores the exact zero-plus-historical-path
mixture. Its CRPS is 0.1035, versus 0.1134 for an all-zero point distribution and
0.1496 when the historical incumbent mean is treated as a point distribution. The
candidate-minus-zero paired interval is [-0.0138, -0.0061]. This supports the linked
distribution structure.

The fair common-distribution comparison is also complete. A tiered incumbent with the
same cutoff-valid workload paths scores 0.1077; adding its frozen event and posterior
rate uncertainty improves it to 0.1048. The linked candidate remains slightly better
at 0.1035, but candidate-minus-incumbent is -0.00133 with a 95% interval of
[-0.00311, +0.00041]. The methods are not reliably different. The cohort is exposed
and the expected-WAR MSE interval also crosses zero, so no promotion is authorized.

The protected 2026 hitter and pitcher aging contracts were corrected before any 2026
outcome was loaded. Their selection gates now use component log loss, paired zero-
inclusive squared error, aggregate bias and supported age-band squared-error
guardrails. MAE remains descriptive only. The frozen predictions themselves did not
change; their reports were regenerated solely to bind the amended contract hashes.

The protected 2026 opportunity confirmation follows the same rule. Its full hurdle-
count negative log likelihood remains the primary distribution score, while expected
PA/BF is guarded by mean squared error and aggregate bias. MAE is descriptive only.
The already-frozen 2026 opportunity predictions did not change.
