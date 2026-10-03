# Smooth expected playing time comparison

2026-10-03. Test one substantive alternative to the tree and peak-reference
models: a regularized smooth mean of next-calendar-year MLB plate appearances.
This is an opportunity experiment, not a complete hitter model. Keep corrected
V53 hitting and all frozen forecasts unchanged.

## Target and fair comparison

Keep the 63,282 source identities, 30,506 scored identities and 35 chronological,
whole-player separated cells from V61. Keep non-arrivals and known exits.
Exclude target 2020; use the reconstructed origin 2020 when its later target is
observable. All labels are next-year MLB PA, including certified zeros, divided
by 800. The physical engineering bound is 800, not a promised full-season job.
All observed labels must lie within it. Public comparisons retain the identical
2,627 current-MLB Steamer and ZiPS matches. Snapshot vintages remain unknown.

Use identical V61 inputs in both arms, including coverage-qualified observation
state. No source collection, public projection as a predictor, clinical recovery
inference or new injury cap. Every fit uses equal-origin weights. Reuse V61's
actual per-cell rare-status eligibility and retain sparse forecasts in scoring.

Two locked arms use the same basis:

- Smooth squared error predicts PA/800 with an identity link, then bounds the
  output to [0,800].
- Smooth fractional logit predicts the conditional mean of PA/800 directly;
  multiply its sigmoid output by 800. Zero outcomes enter the objective unchanged.

Fractional logit follows the conditional-mean approach of
[Papke and Wooldridge](https://academicweb.nd.edu/~rwilliam/ndonly/readings/CDA/Fractional/Fractional_Response_Models_1996.pdf).
This application is our modeling hypothesis. A fraction of 800 is NOT the chance
of appearing in MLB, and 800 PA are NOT assumed independent Bernoulli trials.
The method supplies neither calibrated career uncertainty nor a binomial variance.

Both minimize weighted mean loss plus 0.0001/2 times squared coefficient norm;
the intercept is unpenalized. Squared loss is half squared fraction error and
fractional loss is log(1+exp(eta)) minus y*eta. The different losses have different
curvature: the shared penalty does not imply identical effective shrinkage or
isolate the link alone. No hyperparameter search or favorable-profile routing.
Use deterministic L-BFGS with 2,000-iteration limit, ftol 1e-12 and gtol 1e-7;
require success and maximum gradient below 1e-5. Failure stops that cell.

## Representation and source limits

All enabled inputs get a linear term after deterministic physical-unit scaling
and saturation to [-1,1]. PA history uses 800, pooled PA 2,000, career PA 10,000;
annual and pooled games use 170 and 400; PA per game uses 5. Rates use K .5,
BB .3, HBP .1, HR .1, BABIP .5, doubles .12 and triples .06. Centered age uses 4,
age squared 16, elapsed 3, draft elapsed 2, quality 3, gap 5, scouting capacity
100, log possible absence days 7, observed/roster return counts 5. Other bounded
scores and indicators use 1. Record saturations rather than silently treating
an extreme as missing. Historical unavailable values remain qualified by the
existing coverage/presence fields; this does not recertify publication vintages.

Add quadratic B-splines with fixed knots -1,0,1 and constant extrapolation on:
centered age, elapsed, career PA, last-stat gap, demonstrated workload,
MLB/AAA/AA annual PA at each of three lags, pooled MLB quality and draft rank.
Subtract each basis function's value at zero. No empirical quantile knots or
rare-feature standard deviations. Drop columns constant in actual training only.
Add prior-debut interactions with centered age, elapsed, draft rank, current
scouting rank, and pooled AAA/AA exposure and K/HR/BABIP. This permits broad
prospect versus previously arrived differences without fitting selected subgroup
winners. It is not a comprehensive interaction model.

Persist per-cell source preflight, actual distinct-player profile counts,
training-range warnings and basis dimensions before any fit. Verify all inputs
finite, unchanged identities/labels and no held-player leakage. Save every fit,
replay predictions and trace each reviewed player's complete additive predictor.
Known hard-unavailable and reported-retired rules still force PA to zero.

## Scoring and baseball review

Primary practical checks remain the V30 public PA goals, meaningful improvement
over V53, and sensible full-population/stage/origin totals. Report RMSE, MAE,
bias, clipping, and fixed-hitting delivered offense in common-origin units.
This mechanical product is batting plus replacement, not full WAR, a joint
talent/workload distribution, trade value or six years of club control.
Use player-cluster paired development intervals; exposed historical tests do not
become independent confirmation. Inspect current/absent/brief/large MLB use,
never-debut, lower/upper minors, exits and 2021/2023 opposite cohort errors.

Fixed cases are Judge at 2016 and 2022 origins, Tatis 2022, McLain 2024, Lux 2023,
Franco 2023, Langford 2023 and Yordan 2022. Add each arm's largest value gain,
harm, false high, false low and ordinary error. Origin-only nearest peers use
stage, prior debut, age, recent workload, demonstrated capacity and minor PA,
not future outcomes. Review actual dated counts, scaled inputs, additive terms,
saved-fit replay, support, intermediate PA/rate/value and reality before
disposition. Bounds alone are not a win. Do not tune to reviewed names or build
a post-result comeback blend. Retain V53 if coherent improvement is absent.

After this bounded architecture comparison and player review, close the current
workload architecture batch. Move to the plan's compatible talent and delivered
value milestone rather than another penalty/link/library sweep. Protected 2026
outcomes, frozen forecast and deployed explorer remain unchanged.
