# Calibrate overseas forecasts to event counts

2026-10-05. Test one repair to the saved overseas translation. The earlier
direct-conversion test already failed and is not repeated unchanged. Its event
probabilities were poorly calibrated in arithmetic frequencies, especially HR.
The old calibration minimizes squared error in centered log ratios; applying
softmax to that conditional estimate need not produce a conditional arithmetic
mean. That is a design concern, not an established explanation of every miss.

## Locked repair and comparison

Keep the old source histories, identities, event order, smoothing, 5/4/3 recency,
27 qualified foreign movers, domestic consecutive pairs, chronology and player
exclusions. Do not retrieve outcomes after 2025. The new 2025 foreign source is
preserved but is not used to revise or evaluate a new 2026 forecast.

Replace transformed-response least squares with penalized multinomial count
likelihood. Domestic source coordinates remain relative CLR deviations. For
eight events jointly fit intercept a and event-specific slope b in
`logits = log(target_MLB_reference) + a + b * source_coordinates`.
Fit to unsmoothed observed target frequencies. Slopes remain bounded [0,2];
penalty is `2 * sum(a*a + b*b) / 2`, centered at zero as before. No sweep.

Each pair's effective count is harmonic source/target PA capped at 300, divided
by its person's number of retained pairs. This is the old relative weight
multiplied by 300, now interpreted as count exposure. The response loss and
prior-to-data scale both change; this is not a causal contrast of loss alone.
The effective count is a regularization design, not 300 independently verified
observations. Repeated people, selection and season shocks remain limitations.

With domestic slopes/intercepts fixed, fit one eight-event offset d per foreign
league using the same count likelihood, mover weights and penalty `sum(d*d)`.
No league movers means unsupported prediction, not an invented mean.
Use the existing coherent profile pooling and origin MLB reference. Every
actual fit excludes the evaluated player's fold and completes targets no later
than the origin. All thirty-five historical evaluation cells are preflighted
before any fit. No new supervised downstream head or nested tuning is used.

The [Stan multinomial documentation](https://mc-stan.org/docs/2_38/functions-reference/multivariate_discrete_distributions.html)
supports the logit count likelihood. Bound-constrained optimization uses the
documented [SciPy L-BFGS-B interface](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html).
Neither source establishes baseball transportability. Analytic gradients must
match numerical gradients; all optima must have projected gradient per effective
PA below 1e-7. Verify saved coefficient predictions independently.

## Full forecast contrast without rebuilding domestic routes

Keep all 30,506 original forecasts and thirteen separately qualified additions.
Original baseline probability, conditional PA, expected PA and talent are the
unchanged current benchmark. Additions have no current prediction; their fixed
comparison anchor is the earlier dated-context domestic forecast, explicitly
labeled rather than represented as current UBM or zero. Both candidate and this
addition anchor use that same opportunity forecast.

Use a direct converted overseas rate only where an observed NPB/KBO season
within the last three years has at least 30 PA and is later than every observed
domestic season with at least 30 PA. A domestic promotion/debut cameo below
30 PA does not erase substantial overseas evidence. Same-year substantial
domestic/foreign work is ambiguous and keeps the anchor. The floor matches
calibration coverage, not an optimized talent threshold. This route includes
both newcomers and MLB returners and ignores future arrival when selecting.

For a supported routed case, rate is the existing event-value dot product of
`new_translated_probability - held_origin_MLB_reference`, in batting wins per
600 PA. There is no extra blend or fitted scalar regression. Unsupported cases
retain the fixed anchor and a warning. All other domestic/current talent is
unchanged. This does not assume older MLB evidence is worthless: dropping it
from routed returner talent is an explicit risk to inspect, not approval.

Expected contribution is unchanged expected PA times
`(rate/600 + origin_replacement_rate)`. It is custom batting plus replacement,
not full WAR, six control years or trade value. Non-arrivals stay in value
scoring; their observed rate is missing. No employment correction, eligibility
expansion, explorer promotion or new 2026 forecast occurs here.

## Scores and review before disposition

Primary full-forecast questions are whether conditional actual-PA-weighted
hitting MSE and delivered batting-contribution MSE improve among origin-defined
route-eligible original forecasts. Retain unsupported fallbacks in that scope.
Report complete original-cohort effects, each origin, newcomers/returners,
non-arrivals, lower/upper minors and the thirteen additions separately.
Unchanged groups provide integrity controls, not evidence of a modeling gain.
Report all fixed predicted/actual PA and contribution totals and paired
player-cluster intervals with 2,000 draws, seed 84 and fixed origin weights.
These are exposed historical development results, not independent confirmation.

Compare new versus saved borrowed probabilities on identical supported active
foreign profiles using log loss, one-hot Brier, actual-PA-weighted event
frequencies, HR/K errors and direct-rate MSE. Preserve the original 253-source
component ledger as a diagnostic, but do not confuse stale overseas-only
diagnostics after MLB play with the fresh-source route. Rate outcomes for exits
remain unobserved. Proper probability gains are not automatic value gains.
The scalar incumbent does not define eight probabilities; do not invent them.

Retain the qualified matched 2,627 public-system original forecasts and their
snapshot/park/environment limits. Report any actual route overlap rather than
calling unchanged public scores a new benchmark win. Additions do not silently
enter that matched public scope. A genuine preseason 2026 export remains missing.

Fixed walks are Thames before 2017, Ohtani before 2018, Suzuki before 2022,
Yoshida before 2023, Lee before 2024, Hyeseong before 2025 and Henry Ramos before
2023. Keep absent/unrouted cases with their reason. Add a stable-source-ID ordinary
non-arrival, largest routed gain and harm, false high/low and ordinary active
case. Select three same-origin peers from age, foreign PA, debut status and dated
job evidence without future outcomes. Walk actual annual counts, source pooling,
coefficients, event-value terms, unchanged opportunity, contribution, future
counts and foreign/profile support. Include the previous direct-conversion
results where matched. Complete readable review before choosing the next test.

A useful candidate requires improvement in both primary losses without an
unexplained origin/group or total failure. Sparse support still qualifies it;
no automatic deployment. If it fails, retain the old benchmark and identify
whether mean calibration, transport, returner history or opportunity remains
the problem. Do not optimize another constant from these player results.
