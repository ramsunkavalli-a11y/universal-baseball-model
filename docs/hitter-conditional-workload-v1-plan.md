# Conditional workload v1: corrected history, direct mean versus role mixture

2026-09-23. Fixed before fitting/scoring. This is a workload-only experiment;
no batting, defense, position, running, catcher-value or live forecast update.

## Question

With the corrected F annual participation probabilities held fixed, can a
better estimate of PA **conditional on playing in that particular MLB season**
beat both the inherited workload head and the stronger harmonized ensemble?
Fit Years 1–3 separately; do not substitute cumulative arrival probabilities.

## Data and folds

Use the repaired historical panel and frozen probability/value-transfer archive.
Year 1 origins 2016/2017/2018/2021/2022; Year 2 origins 2016/2017/2021/2022;
Year 3 origins 2016/2021/2022. Three-year totals use 2016/2021/2022. Do not
change populations, earlier forecasts or historical source semantics. Labels
must mature by each forecast cutoff; exclude windows spanning the canceled
2020 season. Never zero-fill an unobserved outcome or open 2026 outcomes.

Only positive-PA training outcomes train a conditional head. Weight each player
equally across that player's eligible **active** training snapshots. All starting
players, including non-arrivers, remain in unconditional evaluation. This is
not a forecast-time selection of future survivors. A basic and detailed head
use identical training rows/weights so feature comparisons are meaningful.

## Three fixed heads, no tuning

- A, basic control: corrected existing 77 aggregate features, prior-debut flag
  and six dated league-context fields. LightGBM conditional PA mean.
- D, detailed direct mean: same conditional target and learner, all corrected
  F features (892 columns before training-support drops). Primary direct model.
- M, detailed role mixture: same detailed features, a three-class LightGBM
  classifier among active players: brief (1–99 PA), part-time (100–449), regular
  (450+). These are workload bins, not certified job titles or injury diagnoses.
  Conditional mean PA is the probability-weighted sum of **past-training-only,
  identity-weighted observed mean PA in each bin**. No hand-chosen PA values,
  manual weights, class balancing or future calibration. This adds a role
  distribution but does not identify a full career-path distribution.

Use existing balanced LightGBM settings and seed 417, four threads; drop only
constant/unobserved training features. No parameter search, feature selection,
blending or ratio caps. Predicted conditional PA uses the existing 1–750 bound.
Require all three role classes in training; fail rather than invent missing
class evidence. Save role probabilities, bin means and clipping counts.

36 fitted heads across 12 folds; two future-mutation checks for both D and M
(four extra fits). Keep F participation fixed. For prospects, expected PA is
F probability times the new conditional mean. All other players are unchanged
in the primary scope. Save a separately labeled universal-head diagnostic;
it cannot be selected to rescue the prospect result.

Controls: B accepted C2 PA; I corrected-arrival + inherited conditional PA from
the prior transfer; E the existing harmonized ensemble. Never recover an
ensemble conditional workload by dividing its output by an average probability:
it contains a direct-total member and is not one documented hurdle product.

## Decisions fixed before results

Score conditional PA among actual participants (legitimate conditional-target
evaluation), and unconditional PA over every starting prospect. Use equal-origin
RMSE, MAE, bias, annual totals; separate horizons and three-year totals. Inspect
upper/lower minors, under-23 upper minors, returners and established current MLB
(>=200 current PA). Actual future regulars are diagnostic, not selection rules.

D and M are the two declared candidate hypotheses; A is a feature-depth control.
For each candidate require:

1. Three-year prospect PA MSE beats I and E with paired whole-player **97.5%**
   intervals entirely below zero (2,000 draws, seed 417), and improves in at
   least two of three origins against each. The wider interval accounts
   conservatively for considering two candidate heads; shared season shocks
   and historical development exposure are still not fully accounted for.
2. Prospect PA MSE beats E in each horizon. Three-year MAE and mean annual
   absolute total-PA error do not worsen versus I.
3. No >5% MSE harm versus I in any annual prospect/upper/lower/young-upper cell
   with >=200 rows and >=10 active outcomes; no >5% harm in each annual-origin
   prospect cohort. Non-prospects must remain exactly unchanged in primary PA.

If both pass, prefer simpler D; if only M passes, retain M. A cannot be selected
post hoc. Passing supports a workload research candidate, not deployment or a
claim of improved WAR. If neither passes, retain the prior sources/probabilities
and report the failure without another tuning round. Do not fit value integration
or change the explorer inside this experiment. Freeze all inputs/code before fits,
verify unchanged prior archives and 2026 seal, and commit the evidence milestone.
