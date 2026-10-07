# Test repaired minor counts without changing the range baseline

2026-10-07. This test asks whether the reviewed count-reliability recipe adds
information about later MLB range quality. It follows the completed source-count
gate, not a fresh algorithm search. Preserve the earlier baseline exactly and
keep unsupported prospects on that fallback. No frozen forecast, explorer or
2026 result is changed or used.

## Target and population

Use the sealed three-year, same-position native-range labels and all eligible
2021/2022 origin positions from the reviewed minor-range comparison: no prior
or current MLB fielding, positions 1B through RF, at least 25 current minor
outs at the position. Current principal level, age and exposure remain dated.
Pool future measured native range runs over the next three calendar years and
divide by native outs, expressing quality as runs per 500 innings. Keep the
sealed requirement of 1,500 future outs and two measured seasons. Do not change
measurement or participation criteria, choose best seasons or replace missing
quality with zero. The primary origin is 2022; 2021 is separate stress evidence.
These exposed historical cohorts are development evidence, not fresh holdouts.

All eligible identities remain in forecasts and coverage. Non-arrivals, short
MLB appearances, missing native measurements and position changes stay unknown
quality. Their other-position outcomes cannot validate the origin-position grade.
This test is conditional future quality, not playing time, delivered runs, full
WAR, service years or trade value. Later measured performance is noisy evidence
of developed ability, not an exact observation of original-cutoff latent talent.

## Three matched arms

Retain the reviewed old selected count recipe as an explanatory anchor. The
benchmark is the exact saved, selected age/position/level baseline for each
outer origin and held-player fold. Reuse its parameters and prediction without
retuning or changing its penalty. Confirm exact replay before accepting the
comparison.

The new arm adds a separately fitted four-input correction: favorable
nonthrowing-error deviation, favorable throwing-error deviation, infield
assist deviation and outfield putout deviation. Use the locked count-likelihood
source recipe, current season's counts and denominator-weighted pooling across
all current levels at the position. Plays unavailable at that position are zero
correction inputs, not evidence of poor ability. First-base putouts are not
receiving talent. No park, pitcher-traffic or play-difficulty adjustment is added
in this test; those remain measurement limits.

Source priors use the current source origin plus two preceding calendar years,
the locked scope broadening and numerical rules. Exclude every held test person
at all source origins and positions. For each quality-training row additionally
exclude its own ID-modulo-five fold from reference estimation. Reuse saved source
priors only when the complete membership, cutoff, exclusions and scope match;
otherwise estimate using the unchanged source-only likelihood. Persist complete
reference membership before estimating new priors. Source parameters never use
future MLB labels. The source gate was historically exposed, so it does not
make this comparison independently protected.

## Held-player residuals and fixed regularization

Quality training requires the whole three-year label window to end by the outer
cutoff. Hold each outer ID-modulo-five fold out at all origins and positions.
Generate a baseline prediction for each training person by excluding that
person's entire fold as well as the outer fold from a nuisance baseline fit.
Reuse the incumbent outer baseline's selected penalty; calculate the nuisance
age median and scaling from its own remaining training rows. Each nuisance fit
needs at least 30 people and two mature source origins. Missing nuisance support
leaves that training residual unavailable, not zero. This is cross-fitting inside
an outer training cutoff, not pretending its model existed at the historical
row's original source year. All its labels nevertheless precede the actual
outer forecast.

Fit the correction to measured quality minus that held-person nuisance prediction.
Each person receives equal total weight across remaining training records. Scale
the four deviations by their weighted root mean square around zero, without
centering; zero-scale inputs receive a zero coefficient. Use Ridge penalty 100,
no intercept and no count-penalty tuning. A zero signal therefore adds zero,
rather than recalibrating the baseline's intercept or age/position coefficients.
Require at least 50 people and two mature origins for this four-coefficient
pooled learner. The fixed penalty avoids selecting another winner from the
already small, exposed inner validation sample. Coefficients are associations,
not causal effects of fielding skill; inspect signs and opportunity context.

## Actual fallback and support audit

Before every nuisance or correction fit persist exact training/evaluation keys,
label cutoffs, held-person exclusions and distinct-player profile counts. Do
not count repeated years as independent support. The pooled correction borrows
across positions with source-relative inputs, but does not fit four parameters
separately in every small profile.

Apply a correction only if the pooled learner is supported, its training contains
at least ten distinct people at the forecast position/principal level and five
in its position/level/age-band/current-out-band profile, and the four inputs are
inside that position/level training rectangle. Missing source inputs, absent
profiles, age/sample gaps or out-of-range count deviations use exactly the
unchanged baseline. The counts are conservative transport guards, not a proof
that ten or five examples suffice to validate an entire profile. Report all
detailed support and fallback rates, among measured and unknown prospects.
Do not relax these guards after observing their scores or delete fallback cases.

## Scores and player review

Score identical measured labels with distinct-person-balanced RMSE, MAE and
bias, retaining every forecast in the coverage ledger. Bootstrap people 2,000
times, seed 21021. Report all origins separately, position/level/age/sample
groups, applied-versus-fallback coverage and annual native measurement paths.
The primary comparative screen requires lower 2022 RMSE with upper paired
95 percent change bound below zero, no greater than one percent primary MAE
harm, no greater than five percent 2021 pooled RMSE harm and no greater than
five percent RMSE harm in a primary position or level group with at least
twenty measured people. This is not deployment approval or certification of
unmeasured lower-minor talent.

Fixed walks are Canzone 2022 RF, Frick 2022 3B, Young 2022 CF, Volpe 2022 SS,
Rafaela 2022 CF, Witt 2021 SS and Peña 2021 SS. Retain other current positions
and source levels. Add largest primary paired gain/harm, largest false high/low,
median absolute error and an unknown thin lower-level case if not represented.
Use three origin-known peers by principal level, position, age distance, log
outs distance and ID; do not select by their future success. Trace source counts
through reference parameters, weights and deviations, nuisance residuals,
correction contributions, support fallback, final quality and actual annual
native range. No new MLB-quality label is invented for Frick or non-arrivals.

Independently replay memberships, source distributions, nuisance and correction
fits, unchanged baseline arithmetic, predictions, group scores and person
bootstrap intervals. Verify that changing evaluation future labels cannot
change source priors, support, eligibility or fallback decisions. Complete the
player walkthrough before disposition or starting another component experiment.

If corrected counts remain unhelpful or uncertain, retain the useful baseline,
state the precise support/measurement limit and move to the next defense gap.
Do not retune this same recipe indefinitely or reject all minor defensive
evidence on the strength of a weakly supported comparison. Throwing, receiving,
double plays, catcher quality, position movement, longer-path lower-minor talent
and delivered-value integration remain required by the active defense goal.
