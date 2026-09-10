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
