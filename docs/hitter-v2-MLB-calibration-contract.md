# C2026C: calibrate the explicit MLB batting target

Declared 2026-09-06 before fitting. This changes the task from the earlier all-level
aggregate to MLB-conditional batting ability. T2026B's aggregate failure remains final.
No website changes or new protected outcomes are part of this work.

## Inputs and chronology

Use the presaved T2026B MLB-scenario vectors and their original MLB target stints.
Bind their hashes in `hitter-v2-MLB-calibration-inputs.json` before fitting. Keep
the same original G0-overlap evaluation population. V2022 is an identity warm-up.
V2023 learns only from V2022; V2024 learns only from V2022+V2023. Save all current
forecast vectors before evaluating current-year outcomes. Earlier predictions
retain their own chronological cutoff; do not recreate them with a later fit.

## Two candidates; no search

**MLB_EVENT:** reuse the exact CAL_GLOBAL multinomial estimator, bounds, penalty,
and optimizer in `hitter_calibration_batch.py`, fitted to earlier MLB outcomes only.

**MLB_VALUE:** fit an affine wOBA calibration separately for known prior-MLB and
prior-minor origin groups. For x=predicted wOBA-.3188 and y=actual wOBA-.3188,
minimize PA-weighted mean (a+b*x-y)^2 + .01*a^2 + .0001*(b-1)^2.
Bounds: a in [-.05,.05], b in [.25,1.75]. Initialize a=0,b=1; L-BFGS-B analytic
gradient, maxiter1000, ftol1e-12, gtol1e-8. With no training rows use identity.
No age/evidence feature, additional interaction, or post-result retuning.

Desired wOBA is .3188+a+b*x, clipped to [.10,.60]. Convert to a coherent terminal
distribution q_j proportional to p_j*exp(lambda*wOBA_weight_j), using 64 bisection
steps for lambda in [-40,40]. Preserve positive support. Require resulting expected
wOBA within 1e-9 of the desired value and report clipping counts. This preserves
ratios among equal-weight outcomes; it is not an independent contact-quality model.

## Fixed development decision

Primary: active-year pooled PA-weighted wOBA RMSE for prior-minor players must
improve >=5% relative to the unchanged MLB transport component, with no active
year worsening >2%. All-MLB pooled RMSE must not worsen >1%. For both the minor
cohort and all MLB, pooled log loss may not worsen >0.25%.

Calibration assessment: report mean bias and slope for each year, both weighting
views, and both populations. Flag |bias|>.010 or slope outside [.85,1.15]. Passing
the primary rule alone does not establish calibrated talent or release readiness.
Retain a candidate for further development only if it passes the primary rule;
independent confirmation and unresolved calibration remain explicit requirements.
Equal-player and supported origin-level subgroup RMSE (50 players AND 5,000 PA)
must not worsen >5% versus transport. No gate uses the identity warm-up as a win.

Report unchanged transport, G0, C0, and Marcel on identical MLB rows. Bootstrap the
primary RMSE difference with 1,000 paired player-cluster replicates, seed260906,
keeping a player's repeated years together. An interval spanning zero is uncertain.
Disclose that participation/playing-time selection remains unresolved and no result
establishes MLB arrival, future PA, or career value. Preserve every candidate result.
