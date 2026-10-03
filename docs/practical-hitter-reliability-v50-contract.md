# Learn how much actual MLB batting evidence should count

2026-10-03, before fitting. The 31 readiness reviews are complete. This returns
to the talent milestone, not another workload gate or library tournament.

## Question and target

Can an explicitly anchored component forecast improve future MLB hitting rate
and delivered offense? Predict eight mutually exclusive next-calendar-year MLB
PA outcomes, then convert their probabilities to the same neutral-weight batting
rate as the working model. Keep the reviewed binary-scouting expected PA fixed
for all new talent arms; also report a working-PA reconnection. Retain all 30,506
evaluation identities, including exits and non-arrivals. Zero MLB PA means zero
delivered contribution and unobserved conditional hitting, not zero talent.
This is not present-day equivalency for every DSL prospect or six-year value.

## Structural comparison

Learn a conditional MLB event prior from age, draft, listed position, observed
career context, separate minor-level count/rate evidence and historical rank
features. Exclude all own-MLB event/value/quality/workload features from that
prior: actual MLB outcome history enters the explicit anchor instead. Minor
counts retain old fixed 100-opportunity stabilization and 1/.8/.6 recency;
this test does not certify those adjustments, park neutrality or all translations.

Transport each historical MLB year's event proportions from its own completed
league environment to the forecast environment, renormalize to that year's actual
PA, then pool with the same 1/.8/.6 weights. The actual source count and empirical
environment are saved separately. Training uses the already completed target
environment as a likelihood offset; test predictions use only origin environment.
No observed future test environment enters predictors or forecast conversion.

For each event j, blend explicit own counts C_j with prior probability q_j as
(C_j + alpha_j q_j)/(N + alpha_j), then normalize eight nonnegative results to
sum to one. Compare (a) all alpha_j fixed at 100, (b) eight alpha_j learned jointly
with the prior on that actual earlier training cell. At N=0 both reduce to the
prior. This is a predictive empirical shrinkage model, not an exact conjugate
posterior or measured latent true talent. Normalization means displayed N/(N+
alpha_j) is pre-normalization influence, not final causal allocation.

This differs substantively from the failed fixed-prior anchored logit: reliability
can differ by skill, and minor/age/pedigree information supplies the prior rather
than giving a tiny MLB debut an inflexible 100-opportunity league anchor. Retain
that failed test as an older reference; do not claim it rejected all shrinkage.
The fixed-100 counterpart isolates the new adaptive reliability, while contrasts
with working Ridge also change prior specification and likelihood.

## Fixed fitting and support

Use the existing 35 chronological whole-player cells and source identities.
Reconstruct old eight-event labels and old batting rates exactly before fitting;
every full/active subset and coarse actual exposure/rank profile is saved before
any fit. Future-active training labels must be mature at cutoff. Preserve sparse
evaluation rows and 218 qualified roster-only rows. No source joins after 2024,
new college data, current scouting biographies or protected 2026 outcomes.

Both arms use the same log-count likelihood, equal-origin weights on active
training rows, slope L2 penalty .001, no penalty on intercepts, L-BFGS-B up to
700 iterations and gradient/finite-difference checks on synthetic data before
real fits. Adaptive log alpha bounds are log(20) to log(5000), initialized at
log(100); report boundary contacts rather than retuning them after results.
Fitted slopes start at zero. Do not restart live jobs or accept silent nonconvergence.
No random validation, tuning sweep or public forecasts in training. Public
environment/date qualifications carry forward.

## Scoring and required review

Primary conditional batting-rate MSE, weighted by actual future PA within equal
origins, plus delivered contribution MSE on every person using unchanged workload.
Report event count log loss, rate bias, matched public scores, each origin/stage,
brief debut, current/prior MLB exposure, listed/top20 prospects and all cohort
totals. Report per-event learned strengths and whether changes retain established
power while de-emphasizing poor tiny debuts. No PA improvement can be claimed.

Fixed cases: Judge debut/established, Winn, Steer, Votto, Bellinger debut,
Alonso pre-debut, Volpe, Kurtz, Salas and Concepcion. Add each arm's largest
rate/value gain, harm, false high/low and an ordinary case; persist source counts,
prior, transported anchor counts, each alpha, pre-normalization blend and final
probabilities/rate/value, actual results, support and origin-selected peers.
An improved event likelihood alone is insufficient. Complete actual player
walkthroughs before disposition or any next experiment. A negative result closes
this specification, not all predictive reliability, minor information or anchoring.

The practical goal remains active; no automatic working/deployed/frozen forecast
change. References motivating the structure, not proving this implementation:
[Tango's Marcel description](https://www.tangotiger.net/marcel/) and
[Jared Cross's projection/testing lesson](https://blogs.fangraphs.com/fangraphs-prep-build-and-test-your-own-projection-system/).
