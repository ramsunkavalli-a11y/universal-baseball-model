# Separate role evidence from unreliable medical increments

2026-10-05. Written before fitting. This repairs the failed finite-return
reference; it is not another suspension flag or parameter search.

## Confirmed defect and one change

The saved 2016/held-player-fold-3 conditional model gives Devon Travis 851 raw
PA, clipped to 800. Scope interruption, days, spells and surgery contribute
434 PA. Only one training person has scope interruption, three have surgery,
and his three spells exceed the training maximum of two. These inputs are
standardized: a rare flag can create a large extrapolation. This is demonstrably
unsafe, not evidence that surgery improves durability.

The source also has a March-to-September 2016 spell despite positive MLB use
that year. The May roster-status change does not explicitly say IL activation;
its revised effective date is September. Neither that text nor annual PA gives
an exact medical return date. A missing activation must not certify continuous
absence, and an observation-scope exit is not recovery.

Remove all six clinical/capture variables from BOTH established-role heads:
annual coverage, open medical evidence, scope interruption, days, spells and
surgery. Keep the preceding twenty inputs, training people, weights, folds and
fixed settings unchanged. Do not replace the six variables with zeros and claim
the player healthy. Their source evidence remains in the walkthrough, with
unknown or contradictory spans explicitly flagged. No clinical risk model is
fitted with these defective inputs.

## Target, eligibility and chronology

Predict next-calendar-year MLB participation and PA conditional on participation
for previously established hitters (last observed MLB season within the existing
three-year window and at least 300 normalized PA). Include future exits. Use the
same unrestricted training subset as the preceding reference: remove only
cutoff-known hard exclusions, retirement and pending nonmedical restrictions.
No future-return filtering. PA is ordinary delivered workload, including routine
health risk implicit in historical workload/outcomes, NOT a healthy maximum.

Keep all 30,519 evaluation identities, 35 original chronological player-held-out
cells and their actual fold-specific translated features. Score the same 1,988
original unrestricted established forecasts for the broad reference contrast.
Target years end at 2025. Exclude target 2020; retain normalized shortened MLB
history and unknown cancelled minor-league history. This is not a new independent
test: these development outcomes and named cases have already been examined.

Before any fit, run forecast_validation.preflight on all 70 full/active subsets.
Count distinct people by age band, prior regular workload, actual gap and MLB
link; separately retain clinical/capture support and input-range warnings from
the failed reference. Removing medical inputs does not validate medical transport.

## Fixed comparison and limited Tatis construction

StandardScaler + LogisticRegression(C=1, max_iter=2000), and StandardScaler +
Ridge(alpha=100), existing equal-origin training weights; conditional PA clipped
to 1–800, exactly as the failed reference. No tuning or extra fit arms.

Compare medical reference, separated role reference and stronger observation
benchmark on identical players. Also evaluate batting-plus-replacement
contribution with the observation hitting rate unchanged. This is NOT full WAR.

For the already sealed finite-return gate only, show the reported-ready
construction with explained gap removed and the actual-gap sensitivity.
Apply the known 20-game budget once (142/162) to conditional PA. Neither
construction is a confidence bound; participation is not probability of full
medical recovery. No additional injury deduction can be multiplied into this
calendar factor without reconciling overlap. No other forecast is replaced.

## Checks and disposition

Primary broad loss: equal-origin PA RMSE; also MAE, Brier, log loss, unchanged-rate
contribution error, per-origin errors and totals, and exits. Obtain paired player
cluster-bootstrap 95% intervals (500 draws, seed 314), retaining equal-origin
loss weighting in each draw. For a general replacement require no worse primary
loss or participation losses, total PA within 5% of actual, and no origin MSE
deterioration over 2%. These are predeclared screening guards, not proof of
deployment readiness. A failure does not establish that medical information is
useless; this contrast tests removal of an unsafe encoding.

Revisit all fifteen retained cases. Add largest gain/harm, false high/low and
ordinary cases under the new reference, selected mechanically with row-ID tie
breaks. For each show actual dated stats, used/omitted inputs, two heads, support,
same-origin outcome-blind peers and actual results. Recompute all saved heads
and score equations independently before disposition. Preserve original artifacts.

Stop after this repair and its player review. Do not tune unsigned-player
probabilities or saturation to these outcomes. Keep clinical availability and
unsigned-player handling open if unsupported. Both frozen packages, the final
2026 evaluation and explorer remain unchanged. No deployment is authorized.
