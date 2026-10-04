# Precision aware minor tracking adjustments to MLB hitting

2026-10-04. Repair the identified integration defect before trying another
algorithm. Preserve the combined prospect/MLB forecast and current expected PA.
Learn a small additive adjustment from minor tracking, rather than refitting
production, pedigree and MLB tracking coefficients in order to add those inputs.
This is a new exposed-development experiment, not a prospective confirmation.

## Fixed question and comparison

Use the same 30,506 forecasts, seven origins, five whole-player groups and
future MLB targets as the reviewed minor comparison. Keep all non-arrivals in
delivered-contribution scoring and their rate observations missing. Preserve
2020's short MLB history and absent minor season. No protected 2026 data,
forecast changes, team-record tests, college collection or algorithm tournament.

Two fixed Ridge adjustment heads, alpha 10, no intercept or feature rescaling:
one uses nine precision-weighted source exposure features; the other adds
36 precision-weighted measurement deviations. Alpha is a declared modeling
choice for this low-dimensional adjustment, not an optimized constant or a
claim that the old joint head's alpha is directly comparable. No tuning follows
the result. Both use equal-origin times actual-PA training weights, normalized
to mean one, and exactly the same training identities and labels.

The base forecast is the existing translated Ridge for never-debuted players,
otherwise the reviewed MLB tracking Ridge with current exact untracked fallback.
Replay the saved outer-cutoff heads on training and test rows. Training residuals
are outcomes minus those fitted training predictions. This is classical
stagewise fitting, not an independently cross-fitted training residual: all
labels used are mature at the cutoff and exclude the whole held-player group,
but in-sample residual shrinkage is a limitation. Verify every test base forecast
against the existing stored combined benchmark before learning adjustments.

Keep the old joint head as a named historical contrast, not a newly fitted arm.
The paired new arms isolate adding measurement values to the exposure adjustment.
Comparison with the old joint approach changes anchoring, dimension, scaling,
precision and regularization together; do not attribute its entire effect to
one of those changes.

## Estimate contact noise from source data

For each same-season league and whole-held-player exclusion, use the reviewed
contact ledger and existing annual summaries. Measures are mean EV, best-half EV,
mean launch angle and hard-air fraction. Omit raw angle SD and EV95 in this
bounded repair; it does not settle the usefulness of those other measures.

For ordinary means and binary hard air, compute within-player contact sums of
squares and the unequal-sample random-intercept ANOVA moment estimates:
within variance is within SS divided by N minus J; between MS is weighted
between SS divided by J minus one; effective group size is
(N minus sum(n squared)/N)/(J minus one). Estimated between-player variance is
max((between MS minus within variance)/effective group size, 0).
Prior-equivalent contacts k equal within variance divided by that between-player
variance. If either variance component cannot be estimated, or between-player
variance is zero, mark the precision relationship unavailable and its adjustment
feature zero. Do not fabricate a convenient finite k or optimize it on forecasts.

For best-half EV, bootstrap each player's actual EV distribution 128 times,
with deterministic player/season/league seed and ceil(n/2) upper-half definition.
For reference estimation only, require at least twenty EVs so tiny samples do
not define a noise prior. Pool n times bootstrap variance weighted by n as
an approximation to within-contact variance; feed that pooled value into the
same unequal-sample between-player moment calculation. The reference includes
no held players or later seasons and no future MLB results. All players with
known own measurements can receive an adjustment; twenty is a reference-quality
boundary, not a new outcome-based eligibility filter. This normal approximation
for an order statistic is qualified, not an exact likelihood or uncertainty band.

Save reference IDs, counts, means, components, k, bootstrap denominators and
own sample moments. Park, opponent, aging and intragame contact dependence are
not removed by this source-distribution model. Same-season centering is not
minor-to-MLB translation; separate league/lag coefficients learn that association
against future MLB hitting.

## Prevent small samples from dominating strong histories

For each league and annual lag, the measurement feature is its deviation from
the reference mean divided by a fixed unit scale (10 mph, 20 degrees or one
fraction), multiplied by n/(all recent measured minor contacts of that kind
plus recent measured MLB contacts of that kind plus k). EV measures use EV
counts, angle uses angle counts and hard air uses complete-pair counts, all over
the same three history years. MLB angle counts are decoded from the already
reviewed log-count predictor. Distinct contact samples are counted once.

With no MLB history this is reliability shrinkage with an information budget
shared across minor leagues/lags. With MLB history it additionally limits
minor evidence relative to stronger existing history. That information-share
guard is a regularization design, not an exact posterior for batting talent:
MLB and minor contacts are not interchangeable observations of one hitting
parameter. No fixed age/role label or chosen 10% veteran discount is imposed.
Extensive recent MLB history therefore attenuates small minor appearances
continuously; substantial minor evidence can still change the baseline.

Exposure-control features use the mean-EV information share for each league/lag.
There are no unshrunk measurement or known-flag bypasses, free intercepts or
unconditional power bonuses. If a measurement/reference is unknown, its feature
is zero and missingness remains recorded in the source receipt. No measurements
means exact unchanged baseline, not inferred average or weak talent. Keep the
previous league support routing and disabled blocks identical in both arms.

## Checks before fitting and after testing

Seal source/benchmark receipts, code, prior estimates, feature frames, all
35 rate preflights, source/profile support and ranges before fitting. Unit tests
must check the moment calculation, increasing sample influence, attenuation
by MLB history, unknown reference behavior and held/later-source mutations.
Independently verify annual counts and moments from the contact ledger.

Primary score is equal-origin actual-PA-weighted next-year MLB rate RMSE among
the same minor-eligible participants. Show MAE, equal-row errors, origins,
prior debut, sample bands and public matches. Separately score unchanged-PA
delivered batting plus replacement contribution for everyone, with totals and
bias. Preserve earlier-model and combined benchmarks. Use nominal paired
player-cluster intervals with the prior fixed seed and 2,000 resamples; results
are not independent confirmation or multiplicity corrected.

Retain a research candidate only if measurements add to exposure control and
the combined benchmark, with sensible player behavior and no meaningful
systematic contribution harm. A small uncertain gain is not a solved model.
Do not promote a post-result subgroup. Verify saved heads, exact fallback,
response units, cohort totals and protected hashes before disposition.

Keep all sixteen reviewed player origins and their corrected origin-only peers.
Append the largest contribution gain/harm, false high/low and ordinary active
case if different. Walk actual dated stats through noise estimates, information
shares, actual fitted terms, fixed PA, baseline/update/actual outcomes. Bichette
in both origins is a fixed diagnostic, not a tuning target. Retain Caminero,
Elly, sparse prospects and non-arrivals. No next experiment until the readable
player review and separate integrity/support/accuracy/reasonability decision.

## Research rationale

[Measurement-error models](https://mc-stan.org/docs/stan-users-guide/measurement-error.html)
distinguish noisy observations from underlying quantities rather than treating
all sample summaries as equally precise. This implementation uses moment-based
shrinkage and a separate information-share guard, not a full Stan latent model.
[Sapolsky and Cross](https://tht.fangraphs.com/improving-projections-with-exit-velocity/)
also distinguish new contact information from power already reflected in a
veteran's production. These sources motivate the repair; they do not establish
our chosen count guard, minor translation or next-year accuracy in advance.
