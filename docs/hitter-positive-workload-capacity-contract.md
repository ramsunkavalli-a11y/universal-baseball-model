# Testing more flexible forecasts of workload when active

2026-10-04. Saved after the completed error-budget player review and before
new fits. Compare conditional MLB PA models on the current source and inputs,
keeping appearance probability, hitting and all evaluation identities fixed.
Public active-workload error motivates this comparison; it is not an assertion
that all injury or job variation can be predicted.

## Fixed targets and membership

Keep the 63,282 current input rows and all 30,506 whole-player chronological
forecasts, including prospects, exits and non-arrivals. The target is next-year
MLB PA conditional on positive PA, not median PA, eventual arrival or full WAR.
Train only the original active rows in each saved current training set: target
year no later than origin, no target 2020, and the entire tested player group
excluded. Preserve the current 251 encoded opportunity features, coming-preseason
ranking dates, origin weights and source qualifications. Do not import corrected
medical, employment, roster, park, opponent or contact branches into only one arm.
No new collection, public forecast predictors or protected 2026 access.

Replay the saved current conditional head on every test cell before fitting.
Verify hashes, exact labels, input definitions and active training identities.
Save all actual training/profile checks before any new fit, including distinct
people by current stage, age, prior PA, rank and thin/new-entry intersections.
Retain sparse/absent forecasts in overall scoring with qualifications. A large
pooled training count is not evidence of elite-entry support.

## Three fixed constructions

The anchor is the saved current histogram head: squared-error loss, 250 trees,
depth three, minimum leaf thirty, learning rate .05, L2 ten, no early stopping,
seed 31. Current appearance and hitting estimates remain bit-identical.

One challenger is histogram boosting with the same settings except maximum
depth six and maximum thirty-one leaves. The other is LightGBM squared-error
regression with 250 trees, depth six, thirty-one leaves, minimum leaf thirty,
minimum child weight .001, learning rate .05, L2 ten, L1 zero, full feature/row
sampling, no early stopping, seed 31, deterministic column-wise execution and
two threads. Record installed versions. No categorical auto-conversion, training
parameter search, held-test selection or feature additions. Different splitting
and binning remain part of the comparison; it does not isolate capacity perfectly.

Use the same equal-origin weights recomputed on each active subset. Bound each
conditional prediction to [1,800], multiply by unchanged appearance probability
for expected PA, then by unchanged custom batting-plus-replacement yield for
delivered contribution. Report raw negative/high predictions and clipping; the
bound is an engineering support, not a declaration that 801 PA are impossible.
No learned mixture bins, participant-only evaluation, median routing, universal
upward factor, post-result subgroup hybrid or tuned availability rule.

## Scores and actual player checks

Primary comparisons are each challenger versus current on public PA MSE and
whole-population delivered-contribution MSE, with equal target-year weight.
Also compare LightGBM versus the deeper histogram head. Show RMSE, MAE, bias,
raw totals, nominal player-cluster paired intervals, every origin and current
MLB PA band, absent prior debutants, upper/lower never-debut and thin new entrants.
Keep the same 2,627 public matches and original Steamer PA/value benchmark.
The practical 10% RMSE, 15% MAE and 10% contribution allowances stay unchanged;
merely crossing a threshold by a negligible change is not meaningful improvement.
Hitting accuracy and arrival scores must be exactly unchanged by construction.

Fixed walks are Judge 2024, Solano 2022, Votto 2023, Belt 2023, Tatis 2022,
Langford 2023, Kurtz 2024, Reynolds 2018 and Rortvedt 2023. Add the largest
PA/contribution gain and harm for each challenger, false high/low and an ordinary
active case. Follow raw stats through all actual inputs, saved fits, raw/bounded
conditional PA, fixed probability/rate, expected PA/value and MLB reality.
Preserve at least four origin-selected peers and both workload and hitting
errors. Value gains caused by cancelling errors are not reasonability passes.

All saved heads must replay and player review must be completed before
disposition or another fit. A useful candidate needs coherent matched gains,
cohort/origin totals and baseball behavior, not a single improved pooled loss.
Current missing employment/availability information and thin-profile support
limits are not fixed by deeper trees. Exposed years remain development evidence;
no automatic forecast/explorer promotion, full goal completion or new tuning if
this comparison is uncertain or harmful.
