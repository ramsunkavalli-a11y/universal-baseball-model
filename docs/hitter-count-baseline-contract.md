# Count based batting baseline comparison

2026-10-05. Fit one coherent historical design that predicts the arithmetic
distribution of next-year MLB events, then converts its mean to batting value.
This repairs specific temporal-meaning and endpoint issues; it is not a rerun
of the closed direct-conversion test or an algorithm tournament.

## Sources and meaning

Use the completed shared-production experiment's exact 35 chronological cells,
five player folds, original 30,506 forecasts and thirteen separate additions.
Reuse its origin-local domestic graphs excluding both outer and source-player
folds, raw counts through 2024 and archived foreign source identities. The
[horizon qualification](hitter-shared-production-horizon-qualification.md)
explains why its future foreign probability cannot be used as past production.

Domestic past probabilities retain same-season level translation. For foreign
sources reconstruct three-year observed event probabilities and their league
reference, using normalized recency 1, 0.8 and 0.6. Express the raw foreign
league-relative log fingerprint on the domestic MLB reference. This is a
provisional within-league relative skill coordinate, not an established MLB
equivalency. Separate NPB/KBO mass shares let the future-count learner estimate
the remaining league shift; never label this as a precise adjustment where
actual mover or learner support is sparse. No old future-persistence coefficient
or forecast probability is applied to the new past inputs.

Pool supported past evidence by normalized observed PA with the explicit fixed
1200 reference-PA prior. The prior is inherited for this one comparison, not
claimed as calibrated source precision. Graph context still pools parks and
selected movers. Older park/opponent reports establish useful context but only
mixed forced player-correction results in two years, with game-weighted opponents.
They do not supply a chronology/player-matched neutral correction to this entire
history; none is silently imported. Keep that limitation rather than declare
parks irrelevant or repeat the same correction.

## Joint future count learner

Use eight mutually exclusive MLB target counts: other, K, UBB, HBP, 1B, 2B,
3B and HR. Model a softmax distribution with the past relative profile as its
offset. During training the environmental offset is the completed target year's
MLB reference; at prediction use only the held origin's MLB reference. Convert
predicted probabilities relative to that origin reference with the existing
compatible event values. Future target environment is used only in labels and
historically mature training, never as a test predictor.

Fit normalized count log likelihood with the original equal-origin row weights.
Actual PA enter once through the counts, not a second time as a sample weight.
Use symmetric eight-coordinate coefficients, unpenalized intercept, fixed
L2 penalty 0.001 on non-intercept coefficients (the existing count-model default),
L-BFGS up to 1000 iterations, ftol 1e-10 and gtol 1e-6. No hyperparameter search
or post-result setting change. Convergence failure blocks that cell; do not
quietly deploy unfinished optimization.

Retain the three incumbent origin-known talent routes and train each head on
all eligible active training rows, as before. Replace raw pooled event-rate
columns with eight common past relative log coordinates and exposure controls.
Remove the four MLB batting-quality summaries (three yearly and one pooled),
so shared production is not merely a residual beside a stronger MLB-only
production channel. Retain demographics, exposure, role, draft information,
prospect scouting for its branch and MLB tracking for its branch. Scale raw
yearly workload by 600 and otherwise retain fixed physical units. Do not learn
a global StandardScaler or use incumbent forecasts as fitted inputs.

This changes likelihood, production representation and quality-channel geometry
together. It tests a coherent replacement, not a causal effect of one feature.
The [multinomial log-loss definition](https://scikit-learn.org/1.4/modules/generated/sklearn.metrics.log_loss.html)
supports the count likelihood; it does not guarantee batting-value improvement.
This design does not claim to recreate Steamer or ZiPS.

## Gates and matched scoring

No 2026 access, playing-time refit or new source collection. Hold incumbent PA
exactly fixed for originals and the existing research opportunity reference for
additions. Preserve non-arrivals in delivered batting-plus-replacement value;
their hitting rate is unobserved, not zero. This is next calendar year hitting,
not full WAR, lifetime upside, control years or trade value.

Before fits, seal source matrices, reconstructed mature counts, actual target
pairing, every 105 active-head preflight, full/active profile support, source
exclusions, finite inputs and feature ranges. Walk the previous ten fixed cases
through the actual past baseline. Verify foreign raw histories reconstruct
independently, no old persistence probability enters, tiny-sample influence is
bounded and later MLB PA dilute earlier production. Check analytic gradients,
eight-coordinate symmetry and probability mass with focused tests.

Primary: equal-origin actual-PA-weighted future MLB hitting RMSE. Require a
delivered-value RMSE improvement too, with no unexplained systematic subgroup
or totals failure. Report MAE, bias, origins, upper/lower never-debut, no-arrivals,
foreign groups, additions and qualified historical public rate comparisons.
Also report proper event log loss/Brier and predicted versus actual HR, K and
UBB frequencies. A probability win alone does not establish a player-value win.
Retain original and failed/shared/direct anchors. Nominal player-cluster paired
intervals use 2000 draws, seed 84; these years are exposed development evidence.

After fitting, replay all heads and probabilities, independently reconstruct
labels and scores, and walk fixed ten plus largest gain/harm, false high/low
and an ordinary case. Show source counts, adjustments, baseline, fitted event
correction, output probabilities, PA/value, actual events and origin-selected
peers, including failures. Source removal uses unchanged fitted models and
recomputed past profiles, not a causal claim. No next experiment or disposition
before that walkthrough. A >5% origin/stage rate deterioration, unsupported
foreign profiles or power calibration failure requires explicit review and
blocks an unqualified win. No favorable-subgroup hybrid after viewing results.
