# Testing hitting uncertainty in next year delivered offense

2026-10-04. This contract is saved before new fits. The practical hitter plan
calls for useful uncertainty as well as point forecasts. The completed workload
risk test varied playing time but held hitting ability fixed. This comparison
adds uncertainty in realized MLB hitting, without changing any current mean.

## Target and comparison

Keep all 30,506 historical forecasts, all non-arrivals, seven origins and 35
whole-player cells. Targets end in 2025. Predict next-calendar-year delivered
batting plus replacement in the existing fixed-event, common-origin win units.
This is not full WAR, latent talent, service-control value or trade value.
An inactive player has zero delivered offense but no observed hitting rate.

All arms reuse the current appearance probability, conditional PA mean and
completed beta-binomial workload distribution. Conditional on positive PA n,
the center of the realized batting rate is the current Ridge hitting forecast.
Compare three distributions without tuning:

- Workload only holds that batting rate fixed, preserving the preceding test.
- Constant hitting spread adds a centered Normal rate error with one variance
  estimated from earlier nested held-player residuals.
- Sample dependent hitting spread adds a centered Normal rate error with
  variance a + b times 600/n, with nonnegative a and b estimated from the same
  residuals. A small MLB sample can therefore be much noisier than a full season.

For every positive n, delivered offense has mean
n times (predicted rate/600 + origin replacement rate). Its conditional variance
is (n/600) squared times the rate-error variance. Zero PA contributes an exact
atom at zero. Thus every arm has exactly the current expected delivered offense.
The construction assumes the PA-weighted batting center does not vary further
with realized PA. It does not prove workload and performance are independent;
selection and their remaining dependence are explicit model limitations.

The fitted a is persistent forecast error, not uniquely identifiable talent
uncertainty; b also absorbs finite-sample noise and other errors related to
workload. Normal errors are an approximation, not a coherent event-count model.
Report probability outside the event-value envelope at every positive PA.
More than one percent impossible mass in a major population, or consequential
player ranges relying on impossible outcomes, blocks an unqualified physical
distribution claim even if proper scores improve. Do not clip draws afterward:
that would change means and conceal a design limit.

## Nested calibration and source checks

Reuse the workload test's exact 95 inner contexts and selected inner group
(outer fold plus one modulo five). The outer players are excluded from all
inner training and calibration; each inner player's whole group is also
excluded from its own fit. Each inner training target is mature at that inner
cutoff and target 2020 is excluded. No outer test residual or fitted training
residual enters dispersion estimation.

Fit the same 199-feature Ridge, alpha 100, deterministic existing safe scaling,
equal-origin weights multiplied by next MLB PA and normalized to mean one.
Its target remains the original target-season-relative batting rate. It is the
current hitting recipe, not the translated-contact alternative. For dispersion,
independently reconstruct common-origin observed rates and offense from eight
actual event counts, the paired environments and corrected replacement rate.
Subtract the nested rate prediction from the common-origin observed rate.
This includes unpredictable future environment changes in forecast errors;
future environments remain labels only, never inputs.

Before any new fit, validate all actual inner and outer active subsets with
the required chronology/player/source preflight. Check matching rate-feature
values against the saved current source. Count distinct calibration people by
stage, prior debut, age, prospect rank, exposure and origin-known position;
keep sparse and absent profiles in scoring. Verify the saved workload receipts
and fixed forecasts. Reuse a nested head across cells only after exact training
and validation membership checks. Save all checks before fitting.

Fit dispersion using equal represented calibration-year weights, not PA
weights: each active player-season is a rate observation. Constant variance is
the weighted squared error. Fit nonnegative a and b by Gaussian negative log
likelihood, with variance floor 1e-8 and bounds [0,10000] on each parameter.
Use three deterministic optimizer starts (constant, equal split and noise only)
as optimization checks, not held-out tuning. Report boundaries, objective,
calibration residual bias, observed PA range and distinct people. No stage
parameters, recentering or post-result width multiplier. No missing-calibration
fallback is allowed without a new prefit amendment.

## Scoring and player review

Primary comparison is equal-target-year mean pinball loss at delivered-offense
P10, P50 and P90. Compare sample dependent spread with both constant spread and
workload only. Also report the proper 80 percent interval score, width, coverage,
negative-offense probability and probability of at least two custom wins.
Zero/non-arrival mass makes inclusive coverage alone misleading. Current means,
PA scores, appearance probabilities and public point comparisons stay exact.
Public systems supply point forecasts, not comparable uncertainty ranges.

Show all players, public matches, current MLB, never-debut upper/lower minors,
previously debuted but absent, thin new draftees, every origin and active-outcome
diagnostics. Report nominal player-clustered paired intervals, not a new holdout
or an adjustment for the many historical experiments. Independently replay every
nested head and variance fit. Check numerical inverse CDFs against a separate
scalar implementation on selected players, including the zero atom and negative
batting yields. No protected 2026 outcomes or frozen/deployed changes.

Fixed player walks are Judge 2024, Soto 2023, Kurtz 2024, Langford 2023,
Alonso 2018, Reynolds 2018, Holliday 2023, Belt 2023 and Franco 2023 when eligible.
Add the largest gain and harm against each reference, a false high/low and an
ordinary active case. Trace dated stats, actual model inputs, saved Ridge
contributions, opportunity means, calibration membership/parameters, distribution
calculations, observed MLB outcomes, physical limits and four origin-selected
peers. Do not turn a wide range containing Kurtz into a repair of his low arrival
probability. Follow the required review before disposition or another experiment.

Only retain qualified research ranges when proper scores, physical limits,
major cohorts and player walks support them. A failed Normal approximation does
not reject hitting uncertainty. Public playing-time and readiness gaps remain
regardless of this result. No automatic deployment or goal-completion claim.

The evaluation follows
[Gneiting and Raftery on proper probability and interval scores](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).
The sample-dependent variance is a declared working model, not a finding from
that paper. Earlier workload-only and old event-profile uncertainty artifacts
remain preserved; their numeric parameters are not imported into this fit.
