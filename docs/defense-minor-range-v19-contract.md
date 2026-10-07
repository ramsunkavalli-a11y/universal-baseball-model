# Test minor fielding counts against later MLB range

2026-10-07. This is one development comparison after the reviewed minor-count
audit, not an algorithm tournament or a forecast promotion.

## Question and fixed population

Do traditional minor counts improve identification of later same-position MLB
range beyond age, position, principal level and current defensive exposure?
Use the sealed count audit's range rows, without prior/current MLB fielding,
window three years, origins 2021 and 2022. Keep every eligible origin-position
identity, including non-arrivals and unknown future quality. The 2022 origin is
primary and 2021 is a separate COVID/reorganization stress cohort. All outcome
windows end by 2025. Quality is native range runs per 500 defensive innings,
with the audit's unchanged two-season, 1,500-out and completeness requirements.

Unknown quality is not a zero label. Scores can identify quality among measured
arrivals, not prove accuracy for the entire DSL population or certify arrivals,
position retention, full defense, WAR or trade value. No additional 2026 outcomes
or changes to frozen forecasts/explorer are permitted.

## Fixed comparison

Retain a neutral zero-run conditional-quality reference, and fit a transparent
ridge baseline with age, unknown-age indicator, log current minor outs, position
and principal level. Age is centered at 23 and scaled by five; log outs is
centered at log(1501). Position and level are categorical. Fit an intercept and
standardize continuous inputs using training rows only. Unknown age uses the
training median plus its indicator. Do not pretend the neutral reference is a
measured grade for a player with unknown quality.

The challenger adds four count signals, with the same training and evaluation
identities and otherwise the same baseline. No double-play rescue, adjustment
ground-ball-share retry, handedness/pedigree addition or player-specific override:

- Nonthrowing error avoidance: errors minus throwing errors, per recorded chance.
- Throwing error avoidance: throwing errors per recorded chance.
- Infield plays: assists per defensive out for 2B, 3B and SS only.
- Outfield plays: putouts per defensive out for LF, CF and RF only.

First-base receiving and catcher quality are not inferred from putouts. The
play-volume signals are unadjusted opportunity proxies, not context-neutral
range grades. Pitcher ground-ball/fly-ball mix, parks, scorer conventions and
positioning can confound them. A negative result does not reject the possibility
that properly adjusted opportunity data contain defensive information.

## Small samples and level mixtures

Build per-player, per-origin, per-position, per-level count aggregates from the
sealed raw counts. Retain all current levels. Reference expectations use only
the same calendar origin and its two preceding years, never a future source
season. Missing 2020 minor baseball remains missing. Exclude all held-fold
people and the focal player's own records from the reference expectation.

Reference groups first use position, source level and existing age band. With
fewer than 30 distinct other people, broaden to position/level, then position/
age band, then position. Thirty is a declared pooling stability rule, not
predictive validation. Every chosen reference scope and person count is saved.

Within a reference group, give each person's available records equal total
weight. Estimate between-record variation after subtracting binomial count
noise for errors and Poisson noise for plays; this variation also includes
short-term development/context, not pure latent talent. Use corrected moments
to obtain beta/binomial or gamma/Poisson prior strength. Nonpositive estimated
between-record variation produces zero reliability, not infinite confidence.
For an individual level, reliability is n/(n+strength), in that signal's actual
denominator; posterior deviation is reliability times raw-minus-reference rate.
Error signals have the favorable sign reversed. Combine level deviations by
actual chances for errors and outs for play volume. Preserve missing rates.

This estimates reliability from source variation rather than inserting a 50/50
blend. The exact moment equations, fallback and source ranges require unit and
independent numerical checks before interpreting a fit.

## Chronology and limited tuning

Five held-player folds use ID modulo five. Training quality windows must end by
the relevant forecast origin. Exclude outer held people at every prior origin
and position. Give each training person's repeated origin-position rows equal
total weight; they do not become extra independent people.

Tune only ridge penalties 10 and 100, separately for each arm, using the latest
two available earlier origin cohorts whose complete quality windows end by the
outer cutoff. For each internal origin, exclude one additional ID fold as well
as the outer held fold; training labels must be complete by that internal
origin. Internal source references exclude both held folds. If there are fewer
than 30 distinct training people or two training origins, retain that validation
cohort with a neutral fallback but do not use it to choose a penalty. If no
internal comparison is supported, use the more conservative penalty 100 and
record the absence of tuning support. Equal scores choose 100.

Persist an equivalent preflight before every fit: exact train/test identities,
window cutoffs, distinct people, source completeness, joint and level-position
support, missing metadata, numerical feature ranges and unknown-level effects.
Stop on player overlap, label chronology violations or missing required counts.
Sparse groups stay in scoring with explicit warnings. For a test level-position
absent from supervised training, use the baseline forecast in both candidate
and baseline; do not invent a count-driven transfer effect. Other extrapolation
is flagged for the player review, not silently deleted or called validated.

## Scores and reasonability

Primary loss is 2022 quality RMSE with equal total weight per measured player,
split across his scored positions. Also report MAE and bias, 2021 separately,
neutral-reference scores, position/level/age/sample errors, measured/unmeasured
membership and forecast distributions. Bootstrap distinct players, not repeated
positions, 2,000 times with fixed seed 19019 for paired RMSE/MAE differences.
Keep native units; do not multiply a conditional quality score by guessed PA.

Positive research evidence requires improved primary RMSE and MAE, an RMSE
paired interval below zero, and no greater than 5% RMSE deterioration in a
2022 position/level/age group with at least ten distinct measured people.
This screen is not automatic deployment approval. Review unsupported profiles,
extreme rates, target selection, coefficient directions and sample response.
Report serious individual harms even if the pooled score improves. The target
does not cover throwing, DP turning, first-base receiving or full outfield arms.

## Mandatory player review and next decision

Fixed cases use the available 2021/2022 origins for Witt, Peña, Volpe, Abrams,
Rafaela, Edwards and Eldridge. Resolve names to source IDs; do not copy the unused
incorrect fixed-ID tuple in the preceding runner. A missing eligible case is
reported, not forced into the population. Select largest origin position, prefer
2022 when eligible, and retain all of the player's modeled positions in detail.
Add the largest gain, deterioration, false high, false low and median absolute-
error case among measured 2022 rows, then deduplicate. Add one unmeasured,
unsupported-level and thin-sample case selected by origin IDs/exposure if those
contrasts are not represented. Each focal case receives three same-origin,
level/position peers by nearest age/log exposure, selected without future success.

Show actual source counts by level, reference expectations, estimated reliability,
model terms and fitted coefficients, support/fallback, forecast, fixed annual
native paths and realized pooled quality. Independently replay the inputs, selected
fits, matched scores and intervals. A data/design defect leaves the disposition
provisional; no next modeling experiment before this review.

If a credible quality signal survives, separately test its contribution to
delivered value with arrival and position exposure fixed under a new integration
contract. Otherwise retain the transparent practical fallback and document
whether the result concerns count quality, target selection or missing context.
Longer-path lower-minor talent, catcher history, position transfers and full
player-value integration remain part of the active goal, not waived by this test.
