# V43: joint annual opportunity/contribution distribution

2026-10-03. Contract before fitting; V42's 15 player reviews are complete.
One structural test, not an algorithm or parameter tournament.

## Why this is a different question

Current annual expected PA × separately fitted batting rate gives a useful point
forecast, but does not describe non-arrival, retention, collapse or breakout risk.
The distribution of outcomes, and their dependence, matters to player value.
Quantile forests retain weighted training outcomes in leaves rather than only
their averages ([Meinshausen 2006](https://jmlr.org/papers/v7/meinshausen06a.html)).
Distributional forests extend the idea to multivariate responses, with specialized
distribution-sensitive splits ([Ćevid et al. 2022](https://jmlr.org/papers/v23/21-0585.html)).
This experiment uses ordinary squared-error Extra Trees and paired weighted leaf
outcomes. It is an adaptive empirical neighborhood baseline, **not** that paper's
MMD splitting implementation, an honest causal forest or a calibrated distribution
by assumption. Its probabilities and ranges require actual held-out checking.

## Locked population, inputs and model

Same V34 30,506 forecasts, 35 chronological whole-player-held-out folds, exact
training rows and original 199 count/context/draft inputs. No V42 age substitution,
V38 game inputs, post-result winner mixing, external forecast feature or new
college information. Source class/roster/history limits remain visible. Training
targets are mature by cutoff; target 2020 excluded; canceled minor features and
complete 2020 source cohort unchanged. Preserve all non-arrivals and exits.

Fit one ExtraTreesRegressor per fold, 200 trees, min leaf 20, max features .7,
no bootstrap, unlimited depth, squared-error multioutput criterion, seed 43,
two threads. Training outputs are [next MLB PA / 600, next batting-plus-replacement
contribution / 2], equal-origin sample weights. This explicit physical output
scale gives 600 PA and 2 contribution wins comparable splitting emphasis; it is
not an optimized economic preference. No tuning or loss-weight sweep. Source
target wins already reflect each observed year's environment. Never call them
full WAR or six years of control.

For each forecast, use the same equal-tree, within-leaf normalized training weights
for the paired actual PA/contribution observations. No bootstrap multiplicities
are needed because bootstrap is false. Marginal means must reproduce the saved
forest predictions. Preserve joint pairings rather than randomly combining PA
with another player's value or multiplying independent means. Duplicate seasons
from one player are not independent calibration confirmations; score intervals
cluster on player. Tree split/leaf estimation shares training outcomes, so narrow
leaf uncertainty is not presumed honest. Hard permanent unavailability overrides
the entire pair distribution to PA/value zero, as in the control.

Output expected PA and expected contribution; PA 10th/50th/90th percentiles;
probability of MLB participation, at least 400 PA, negative contribution and at
least 2 contribution wins. The 400-PA threshold is a workload event, not an
assertion catchers must have 400 PA to be regulars. An implied wins/600 from the
mean pair and origin replacement rate may be displayed for arithmetic only; it
is NOT a separately estimated current talent grade or the same estimand as the
control's future-active conditional rate. Do not score it as a pure talent model.
Zero-PA future batting is unobserved, not a bad batting rate.

## Verification, scoring and decision

Reuse V34 preflight plus actual stage/debut/current-workload profile counts for
all fits; V42 draft-source limitations remain documented, not assumed repaired.
Check zero PA implies zero target contribution, count ranges, exact memberships,
held-player disjointness, feature finiteness, and conditional support before fit.
Pin source/code/settings. Replay all 35 mean and distribution artifacts; exact
leaf probability normalization and mean reconstruction are required.

Primary point comparison: mean PA RMSE/MAE and delivered contribution RMSE against
V34/V33b and the same 1,789 public matches; totals by origin/stage and brief-debut,
limited-draft and missed-year groups. Do not use the median to masquerade as
expected PA to win a MAE benchmark. Report its MAE/RMSE separately to clarify the
mean-versus-typical-outcome distinction.

Probability/range comparison: equal-year participation/400-PA/negative/2-win
Brier, clipped log loss, fixed probability reliability bands; 80% PA interval
coverage and mean width, pinball loss at .1/.5/.9. Discrete PA and its zero mass
make exact 80% coverage impossible for many non-arrivals, so report current-MLB,
upper/lower-minor and all-cohort results, not a misleading population total only.
A training stage/debut empirical distribution, smoothed toward the overall
training distribution with weight 20, is a simple probability reference. This is
not a claim of public-system uncertainty equivalence. Public snapshot and value-
conversion limits stay. Nominal paired player intervals are development evidence.

Review fixed Kurtz/Volpe/Judge-debut/Judge-established/Kjerstad/Burger plus largest
PA/value gains, harms, false highs/lows and ordinary outcomes. Walk through dated
stats, real inputs, exact weighted future-outcome neighbors and means/ranges,
observations and support. List high-weight zero outcomes too; do not cherry-pick
successful comparables. Every listed neighbor must have target available by
cutoff and a different whole-player group. Save full weights for cases, not just
rounded top names. No disposition/next experiment before manual review.

Promote neither means nor risk simply because the algebra replays. Evaluate
practical mean error, conditional calibration and baseball failures separately.
This is an annual offense/risk experiment, not a certified career or market-value
system. If the means lose, risk may remain a separate research component only
with its limitations shown. Frozen 2026 and deployed explorer stay unchanged.
