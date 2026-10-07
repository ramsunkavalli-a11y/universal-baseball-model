# Test the reliability of minor fielding counts before estimating talent

2026-10-07. This source-calibration gate follows the reviewed minor-range recipe.
It checks whether small samples and uncertainty are represented sensibly before
another future-MLB-quality fit. It cannot establish MLB defensive talent, a WAR
gain or the value of a minor leaguer. No frozen forecasts, explorer or 2026
outcomes are changed or used.

## Fixed population and outcome

Use the sealed minor-count sources and eligible origin positions, without prior
or current MLB fielding, positions 1B through RF. Preserve each source level at
each position, not only the principal level. Origins 2018, 2021 and 2022 predict
the following recorded minor season at the same position and source level.
2022 is primary, 2021 separate COVID/reorganization stress and 2018 a pre-COVID
check. Do not forecast 2019 into a nonexistent 2020 minor season. Keep every
origin identity with separate missing/zero-target-exposure status; promotions,
position changes, exits and unobserved counts are not zero quality.

The four channels match the prior test: nonthrowing errors per chance, throwing
errors per chance, assists per out at 2B/3B/SS and putouts per out in the outfield.
First-base putouts do not imply receiving talent. Catcher skills are not modeled
in this gate. All accepted counts must be recorded and satisfy source identities.

For probability evaluation, condition on the realized following-season trial
count, as a count distribution necessarily needs its number of trials/exposure.
That exposure is used for scoring only, never to estimate reference parameters
or choose the player's prior. No forecast of playing time, retention or promoted
performance is implied. This gate tests input count distributions, not the
ultimate target of eventual MLB performance.

## Comparison and chronology

The moment-based reference and the likelihood-based reference use identical
source group membership: current origin and its two preceding calendar years,
position/level/age band, then position/level, position/age, position, broadening
when there are fewer than 30 distinct other people. All held-player ID-modulo-five
folds are excluded at all earlier seasons and positions. Evaluation people's
own reference rows are therefore excluded. Missing 2020 remains absent. Reference
inputs may include MLB returners playing in the minors, just as in the earlier
recipe; the new gate does not certify that mixture as pure prospect talent.

The baseline repeats the sealed moment equations and its record-weighted,
person-balanced rates. A nonpositive inferred variance gives a point prior
and therefore no personal count update. Otherwise use its beta/binomial or
gamma/Poisson prior, update with the focal current count and denominator, and
score the resulting predictive distribution. Exact zero/one mean is a genuine
point prediction; record impossible future observations as infinite loss, never
silently floor their probabilities.

The challenger estimates a beta-binomial distribution for errors and a
gamma-Poisson distribution for plays from source counts. Within a selected
reference group, pool each person's counts and denominators across the available
source records; each person supplies one marginal-likelihood observation, not
independent duplicated seasons. This assumes a shared short-window rate within
that reference scope; development and context can violate it. The changed
within-person pooling is part of the candidate recipe, not an isolated optimizer
contrast. Current focal counts update the selected prior, as in the baseline.

Optimize the two reference parameters only; no future labels or model-family
tuning. Use three deterministic starting strengths 1, 100 and 10,000 with the
pooled-count rate as initial mean; bounded numerical searches use log mean
(log odds for errors) and log strength in [log(0.001), log(1,000,000)]. Record
all starts, convergence and boundary diagnostics. Compare with the exact
point-distribution likelihood; if that is best within 1e-6 per person, retain
the point prior rather than a fake finite concentration. All-zero counts retain
their zero point mean; an error group of only one-chance people cannot identify
concentration and retains the point prior with an explicit support limitation.
Before estimation, numerical mean bounds are fixed at log odds [-20, 20]
for errors and log rate [-20, 5]; exact zero/one point candidates remain
outside these interior bounds. Log-strength bounds apply only to strength.
Start means are constrained only to these numerical bounds. Each start permits
300 iterations, with objective tolerance 1e-10. These numerical choices are not
adjusted after outcomes are scored.
Optimization failures use the matched moment prior, visibly tagged, rather
than dropping forecasts. Boundaries are diagnostic limits, not proof of talent.

Persist the complete reference membership, source sums, exclusions, numerical
counts and population preflight before any estimation. Invalid chronology,
held-person overlap, duplicate identities or unrecorded required inputs stops
execution. Count-specific support includes people with at least two trials,
number of positive counts and exposure ranges. No arbitrary 50/50 weight or
post-result sample floor is added.

## Scores and statistical sense

Primary score is 2022 person-balanced average negative log predictive mass over
observed positive target exposures. Each person has equal total weight across
positions, levels and applicable channels. Retain impossible predictions and
report their count separately; an infinite headline cannot become a finite
score by deletion. Also report conditional finite-loss comparison, posterior
rate error, mean-error bias and 90% central predictive interval coverage/width.
Discrete intervals can conservatively cover more than 90%; report this rather
than manufacturing exact coverage with randomization.

Bootstrap distinct people, 2,000 replicates, seed 20020. Where either arm has
impossible observations, bootstrap the paired finite-loss subset only and label
the interval as conditional; the impossible cases remain a separate gate.
Report all origins separately and groups by channel, level, age band and current
denominator band (<20, 20–99, 100+). Data-rich source calibration is not
data-rich training for MLB skill.

The input-calibration screen requires no additional impossible observations,
improved primary finite paired loss with an upper 95% bound below zero, no >5%
finite-loss deterioration in a channel/level group of at least 100 people and
no 90% interval coverage below 85% in such a group. This is neither automated
deployment nor MLB-quality approval. Always inspect the actual small-sample
weights, broadening, boundaries and errors among non-returners.

## Required player review and next action

Replay Canzone's 2022 complex RF six-chance example, Frick's 2022 AA 3B sixteen
chances, Young's 2022 Single-A CF and Volpe's 2022 AA/AAA SS evidence. Retain all
their origin positions/levels. Add largest 2022 paired finite-loss improvement
and deterioration, largest posterior-rate over/underprediction and median-error
case; add an unmeasured and a thin lower-level example if missing. Select three
same-origin, position/level peers by age, log denominator and ID without future
success. Persist selection, raw counts, priors, posterior weights and uncertainty,
target counts, separate level/position paths and source support.

Independently replay source membership, distributions, scores and intervals
before disposition. One-chance beta-binomial data must be algebraically invariant
to concentration at a fixed mean; unit tests must reproduce this and proper mass
normalization, missing exposure, point priors and zero counts. Changing future
counts must not change eligibility or reference parameters.

If this input gate survives, freeze its source recipe and contract the planned
incremental future-MLB-quality correction with the existing baseline unchanged.
If it fails, explain whether unstable source context or count uncertainty is
responsible; do not use same-level prediction as a substitute for identifying
MLB talent. Catcher history, position transfers, lower-minor trajectories and
delivered-value integration remain required by the active defense goal.

Probability definitions follow the official
[beta-binomial documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.betabinom.html)
and [negative-binomial documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nbinom.html).
The count-likelihood choice is a statistical repair hypothesis, not a literature
claim that these aggregate counts are sufficient to grade minor-league defense.
