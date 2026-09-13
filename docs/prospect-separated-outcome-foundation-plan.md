# Prospect separated-outcome foundation

Status: active P0 contract, frozen before FV calibration.

## Purpose

Rebuild prospect evaluation without allowing workload, level, uncertainty, arrival,
conditional MLB quality, or value to impersonate one another. Named players are
diagnostics only. Public rankings and FV are never predictors, floors, fit targets,
or calibration targets.

## Model law

1. Official PA and BF remain raw counts. They are never relabeled as "effective PA"
   or used as a hard ranking-eligibility threshold.
2. The primary developmental level is the exact level supplying the most current-
   season workload. Highest level reached remains evidence but cannot replace the
   primary level after a brief promotion.
3. Level translation and regression determine an estimate and its uncertainty. They
   do not decide whether a player receives an estimate.
4. Every historical origin player remains in outcome scoring. No MLB arrival is a
   zero all-player outcome, not a missing observation.
5. Report separately:
   - probability of reaching MLB;
   - MLB component quality conditional on arrival;
   - cumulative batting/pitching-plus-replacement production conditional on arrival;
   - all-player expected batting/pitching-plus-replacement production.
6. Enforce the identity `expected outcome = arrival probability × conditional
   cumulative outcome` within numerical tolerance.
7. Conditional MLB rate outcomes are regressed by 200 MLB PA/BF toward the historical
   arrival-population rate before equal-player comparable averaging. This prevents a
   tiny MLB sample from defining conditional talent.
8. A current hitter's conditional-rate estimate is displayable only when at least ten
   of his historical neighbors reached MLB. This is an outcome-support gate, not a PA
   eligibility gate. It passes strict nonoverlapping 2008, 2013, 2018 and 2021 folds;
   unsupported raw estimates remain diagnostic only.
9. No FV mapping is authorized until full historical distributions support stable
   thresholds across time, player type, age and exact level.

## Current implementation

The universal 150-neighbor comparison uses exact primary level, age, current raw
workload and regressed production components. It now runs for every current hitter
and pitcher. Pitcher conditional rate is withheld because it failed its held-out
baseline, while pitcher arrival and all-player expected outcome passed. A strict
chronology audit uses only references whose full four-year outcomes end before each
2008, 2013, 2018 or 2021 target snapshot. Hitter conditional quality passes every
fold; pitcher conditional quality fails two of four. The current reference uses 2018,
2019 and 2021 origins but keeps only the latest snapshot per player, so
long-lived minor leaguers do not receive duplicate weight;
players appearing in both cohorts are removed from the reference.

The explorer shows raw current and three-year workload. Its former effective-evidence
number is retained only as a plainly labeled translation-confidence diagnostic. It
cannot suppress a player or erase historical outcomes.

Conditional talent is now shown directly from the separately validated age-24-to-26
peak component model: mean runs above average plus above-average and impact
probabilities. This is distinct from arrival and career value. The historical
comparable WAR rate remains an additional validated hitter diagnostic and stays
withheld for pitchers.

The all-player outcome is now a distribution rather than only a mean: P10, median,
P90 and the historical probabilities of reaching 1, 3 and 6 partial WAR are retained
from the same neighbor set, with non-arrivals still zero. These are four-calendar-year
batting/pitching-plus-replacement outcomes, not whole-player or controlled WAR. They
are foundation inputs for later calibration, not FV cutoffs.

The fixed-neighbor sensitivity has been run at 25, 50, 100, 150 and 250 neighbors.
No count dominates all held-out objectives. For hitters, smaller neighborhoods help
the all-player outcome while larger neighborhoods help conditional-rate stability;
arrival Brier and log loss also choose different widths. Pitcher all-player MAE is
best at 50, while conditional rate fails the population baseline at every tested
width. Keep 150 as the neutral foundation until a frozen adaptive or ensemble test
can improve every required output; do not tune width from current names or public
rankings.

## Remaining gates before FV

1. Replace fixed 150-neighbor breadth with a frozen distance-quality test if that
   improves held-out proper outcomes without subgroup failures.
2. Validate arrival probabilities with Brier score and calibration, not ranking
   resemblance.
3. Validate conditional rate and cumulative outcomes among arrivals, including small-
   MLB-sample sensitivity.
4. Add total-value components only after batting/pitching-plus-replacement outcomes
   are stable: defense, baserunning, position and pitcher role remain separate.
5. Run monotonic, brief-promotion, raw-workload, missing-data and leakage safeguards.
6. Audit the frozen output against public top-50 lists and explain disagreements.
7. Estimate an internal FV scale from historical outcome distributions. Do not assume
   any WAR value for a 50 FV grade.
