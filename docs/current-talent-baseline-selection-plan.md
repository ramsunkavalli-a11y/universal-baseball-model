# Current Talent simple-baseline selection plan

Last updated: 2026-08-16  
Status: **predeclared before grid execution**.

This document freezes the first hyperparameter/model-selection search for the simple results-only Current Talent baseline. It exists specifically to prevent retrospective goalpost changes after grid results are visible.

## Scope

Search only the highest-value unresolved simple-baseline choices:

1. predictor recency half-life;
2. Baseline 1 empirical-Bayes prior strength;
3. environment-translation variant.

Keep all other currently implemented rules fixed for this first search.

No Baseline 2, process/tracking/scouting inputs, component-specific shrinkage, post-hoc recalibration, actual-league residuals, projection aging, playing time, WAR, or ranking enters this gate.

## Candidate grid

### Recency half-life

- **45 days**
- **90 days**
- **180 days**

Rationale: compact multiplicative spread around the current 90-day candidate. It tests meaningfully more reactive and more persistent evidence without a fine-grained search that would overfit six development folds.

### Baseline 1 prior strength

- **50 effective core events**
- **100 effective core events**
- **200 effective core events**

Rationale: compact multiplicative spread around the current 100-event candidate. It tests substantially less and substantially more shrinkage without searching a dense continuous range.

### Translation variant

- **fitted translation** — training-only `matched_adjacent_stint_clr_wls_v1` level effects;
- **zero offsets** — controlled ablation with all learned level CLR effects set to zero.

The zero-offset variant still uses current level in Baseline 0's age+level peer prior. This choice therefore isolates the learned observation-layer translation rather than removing all competitive-level information.

### Total candidates

`3 half-lives × 3 prior strengths × 2 translation variants = 18 candidates`.

## Fixed settings during this grid

Do not change these while the grid is running:

- Baseline 0 method: `loo_age_level_population_prior_v1`;
- Baseline 1 method: `translated_recency_empirical_bayes_v1`;
- Baseline 0 age-band width: **2.0 years**;
- Baseline 0 minimum preferred age+level peers: **12**;
- translation minimum core events per stint: **20**;
- translation max gap: **365 days**;
- translation CLR pseudocount: **0.5**;
- 12-component core profile definition;
- exact Chadwick age-as-of policy;
- fail-closed ambiguous current environment policy;
- 90-calendar-day future target;
- all eligible future core events for proper scoring;
- retrospective event-cutoff temporal semantics;
- certified source/evidence artifacts and authority rules.

If a fixed rule fails structurally, stop and document the failure rather than silently changing it inside the search.

## Development/selection folds

Use **only 2021 and 2022** for the grid:

- 2021-07-15
- 2021-08-01
- 2021-09-01
- 2022-07-15
- 2022-08-01
- 2022-09-01

All six folds already satisfy the universal six-level support contract.

## 2023 role

The three 2023 folds are **held out from this hyperparameter grid search**:

- 2023-07-15
- 2023-08-01
- 2023-09-01

Important wording: 2023 is **not untouched project-wide**. The current 90-day / 100-event candidate has already been inspected there during baseline stability work. The valid claim is only that **alternative grid configurations will not be evaluated on 2023 until one candidate has been selected from 2021–2022**.

Do not inspect 2023 grid results during selection.

## Primary selection objective

For each candidate and each of the six development folds:

1. calculate event-weighted multinomial log loss inside the fold;
2. calculate event-weighted multinomial Brier inside the fold;
3. retain component, stratum, and calibration diagnostics.

### Across-fold aggregation

**Equal-weight the six fold-level scores.**

Primary score:

`mean(fold event-weighted log loss)`

Secondary proper score:

`mean(fold event-weighted multinomial Brier)`

Do **not** pool all future events across folds as if they were independent. July/August/September target windows overlap within a season, and future-opportunity volume differs materially by cutoff. Event weighting is correct *within* a fold; equal fold weighting is the more defensible model-selection aggregation across these overlapping chronological snapshots.

## Selection rule

1. Rank all 18 candidates by **equal-fold mean log loss**; lowest wins the primary ranking.
2. Report equal-fold mean Brier and identify the log-loss/Brier Pareto frontier.
3. Report per-fold log loss and Brier so a mean win cannot hide a large chronological regression.
4. Report calibration intercept/slope/ECE and component/stratum results as guardrails, not as a post-hoc weighted composite invented after seeing the grid.
5. Preselect **one primary candidate from 2021–2022 before running alternative grid candidates on 2023**.

If the primary log-loss winner has a clear conflict with the other proper score or severe calibration instability, **do not improvise a new composite objective**. Mark selection unresolved, document the conflict, and carry a small explicitly named challenger set forward. The grid must not be expanded merely because the preferred current candidate loses.

## Simplicity / tie handling

Do not define an arbitrary tiny score tolerance after seeing results.

If candidates are numerically indistinguishable at displayed precision, prefer the simpler configuration in this order:

1. zero-offset translation over fitted translation;
2. stronger shrinkage only if proper scores are effectively identical at machine/display precision;
3. longer half-life only if proper scores are effectively identical at machine/display precision.

Otherwise let the predeclared primary log-loss objective decide.

## Coverage guardrail

For a given fold, all 18 candidates must score the same eligible player / target-environment population. Hyperparameters change probabilities, not who is considered scoreable.

Fail the grid if candidate coverage differs unexpectedly.

## Calibration guardrails

For each candidate report:

- equal-fold mean absolute calibration-intercept error;
- equal-fold mean absolute calibration-slope error;
- equal-fold mean fixed-bin ECE;
- component calibration summaries, especially K, BB/HBP, and LD/OFFB directional bins.

Ideal intercept = 0, slope = 1.

Calibration is a guardrail/tie-breaker, not permission to discard a proper-score winner based on whichever calibration statistic is most favorable after the fact.

## Confirmation rule

After one primary candidate is selected from 2021–2022:

1. run that candidate on the three selection-held-out 2023 folds;
2. compare it with Baseline 0 and the existing 90-day / 100-event reference configuration;
3. require the candidate to retain a clear B1-vs-B0 proper-score advantage;
4. if the selected candidate differs from the current reference, require its 2023 mean log loss to confirm rather than reverse the 2021–2022 selection advantage, with Brier/calibration reported alongside it;
5. if confirmation fails, **do not select a new candidate using 2023**. Record hyperparameter instability and keep the simple baseline unfrozen.

## Freeze rule after confirmation

A simple Current Talent baseline may be frozen only if:

- B1 continues to beat B0 out of time;
- the selected parameterization confirms on 2023 rather than materially reversing;
- no major level/transition/evidence stratum is catastrophically harmed;
- calibration remains interpretable and no new structural coverage failure appears.

Only after that freeze should Baseline 2 or richer process/tracking/scouting inputs be tested.
