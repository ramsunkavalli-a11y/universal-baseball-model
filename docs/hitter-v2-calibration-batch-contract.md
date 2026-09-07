# C2026A: chronological outcome calibration

Declared 2026-09-06 after the transport diagnosis and before fitting either new
candidate. This is a new disclosed-development experiment; failed C0/G0/H0/S0
results and contracts are preserved. User instruction: prioritize the model and
continue work, with interface development paused.

## Question and exact candidates

Can earlier out-of-time forecast errors teach a stable correction without the
compounding nested transformations that destabilized H0?

- **CAL_GLOBAL:** q = softmax(t * log(p_G0) + a).
- **CAL_ORIGIN:** q = softmax(t * log(p_G0) + a + b_origin).

Both preserve a positive exhaustive twelve-outcome distribution. The shared
temperature t is bounded [0.5, 1.5]. Intercepts a and b are bounded [-1, 1]. All
parameters initialize at identity. Fit multinomial count log loss, divided by
total training PA, plus 0.0005 * sum(a²) + 0.001 * sum(b²) + 0.01*(t-1)².
These constants are fixed; no search, post-result retuning, or extra candidate.
Use L-BFGS-B with analytic gradients, maxiter=1000, ftol=1e-12, gtol=1e-8.
Fail closed on nonconvergence. Centering of intercepts is implicit in the ridge.

Origin is the largest-PA level in the latest predictor season, aggregated across
leagues, with alphabetical tie break. Missing origin uses a separate unknown
category. No observed future level, player name, target PA, or target outcome is
used at prediction time. CAL_ORIGIN learns the average next-year change associated
with known origin, including the historical mixture of moves. It is NOT an explicit
MLB-equivalent translation model or a correction conditional on a known destination.

## Chronology and population

V2022 has no earlier G0 scored forecast and is an explicit identity warm-up, not a
required improvement test. Fit V2023 only on paired V2022 forecasts/outcomes. Fit
V2024 on paired V2022+V2023 forecasts/outcomes. Earlier G0 forecasts must retain
their own original cutoffs. Predictions for every G0 forecast player are written
before that fold's candidate evaluation. Use the exact G0 overlap population for
paired comparisons; report target players lacking a G0 forecast separately.

Verify all original G0 contract inputs. Use only 2022–2024 disclosed outcomes;
protected 2026 is closed. Do not call these years untouched confirmation evidence.

## Decision rule fixed before results

Primary: pooled PA-weighted wOBA RMSE across active V2023+V2024 must improve >=1%
over G0. No active-year RMSE may worsen >2%. Pooled terminal log loss may not worsen
>0.25%. Report Marcel and C0 on exactly the same rows, both weighting views, every
year, and every movement/source-level group. These are development comparisons.

Calibration readiness additionally requires absolute mean wOBA bias <=0.010 and
slope in [0.85,1.15] in both weighting views of every active year. On supported
origin and movement groups (>=50 players AND >=5,000 PA), RMSE must not worsen
>5% against G0. Rare terminal categories must retain nonzero probability and their
component mean errors must be reported. Failing readiness cannot be waived by a
better primary metric. If both qualify, choose lower primary RMSE; no ensemble.

Uncertainty: 1,000 paired player-cluster bootstrap replicates, seed 260906,
resampling unique players once across both active years. Report a 95% interval
for candidate-minus-G0 pooled RMSE. Do not resample player-year rows independently.
An interval spanning zero means improvement remains uncertain.

Deliver coefficients, all forecast probabilities, paired scores, subgroup results,
the decision, tests for gradients/chronology/probability validity, and the next
modeling implication. Do not update the website or ship a model from this batch.
