# Hitter v2 batting development contract

Status: **PRE-REGISTERED / NO CANDIDATE SCORED / PROTECTED CONFIRMATION CLOSED**  
Version: `hitter_v2_batting_development_contract_v1`  
Date: 2026-08-23

## Authorization boundary

This contract freezes the Stage 2 candidate families, search, folds, metrics,
subgroups, tolerances, and promotion rule before any Hitter v2 candidate is
scored. Stage 0 authorizes none of that scoring. After Stage 0 review, the next
authorized work is Stage 1 source-only outcome materialization and invariants.

Position-player v1 is a historical comparator only. No v1 artifact, decision,
hash, or result may be rewritten. Player names may appear in diagnostic tables
but never in features, search, selection, thresholds, or acceptance criteria.

## Estimands

Primary Stage 2 estimand:

> A player's distribution of terminal outcomes, future wOBA, and batting
> runs/600 conditional on receiving a future PA in a neutral league/park
> environment.

Current Talent (as-of rate), one-year Projection, environment translation, and
opportunity remain separate. Target-season outcomes, membership, PA, parks,
run values and centering cannot enter predictors.

## Chronological folds

Required disclosed rolling-origin validation folds:

| Fold | Predictor cutoff | Target season | Role |
|---|---|---|---|
| V2022 | 2021-12-31 | 2022 | required validation |
| V2023 | 2022-12-31 | 2023 | required validation |
| V2024 | 2023-12-31 | 2024 | required validation |

2025 is diagnostic-only because repository work already accessed PA, PBP,
position, and defense outcomes. It cannot promote, rescue, retune, reweight, or
reject a candidate.

Completed 2026 offense is the protected one-shot confirmation. Before opening
it, the selected PBP-only candidate, parameters/refit protocol, source contract,
eligible population policy, run-value weights, exact scorer, and hashes must be
frozen locally and review must authorize the source boundary. No 2026 outcome
access is allowed during Stage 0, Stage 1, or development search.

Within each validation fold, hyperparameters are selected using earlier
training seasons only. A target fold is never used to select its own
hyperparameters, translations, priors, parks, age effects, or run values.

## Permanent baselines

1. `B2_CONTACT_SHAPE_V1`: existing frozen 12-bin v1 score, continuity only.
2. `B0_ONE_YEAR_EB`: prior-season terminal outcome counts, each component
   shrunk to its prior league-season-level mean.
3. `B1_MARCEL_345_K1200`: three seasons weighted 3/4/5 oldest-to-newest,
   regressed by 1,200 PA to the chronology-safe league mean, plus the fixed
   Marcel age rule.
4. `B2_PBP_COMPONENT_NO_TRACKING`: best chronology-safe PBP component candidate
   selected below; it becomes the universal comparator before tracking opens.
5. `B3_PBP_PLUS_TRACKING`: capability-aware fused challenger on the identical
   eligible overlap only, after B2 is frozen.

The strongest simple outcome baseline in a fold is the better of
`B0_ONE_YEAR_EB` and `B1_MARCEL_345_K1200` on that metric. V1 can never be used
as the sole promotion comparator.

## PBP-only candidate families

All candidates are coherent nested empirical-Bayes/hierarchical models:

1. `P(K)`;
2. `P(UBB | non-K, hitter-talent PA)` and `P(HBP | non-K, non-UBB)` so UBB and
   HBP are separately recoverable;
3. `P(HR | contact)`;
4. `P(reach/hit | non-HR ball in play)`;
5. `P(1B/2B/3B | hit in play)`;
6. `P(MULTI_OUT | observed GIDP opportunity)` as a separate opportunity model.

`ROE`, `FC_REACH`, `SF`, and `OTHER_OUT` remain explicit in the coherent
non-HR-ball-in-play allocation. An alternative Dirichlet-multinomial assembly
may be evaluated only as `C2_MULTINOMIAL`; it must use the same inputs/folds and
must beat, not replace without comparison, the nested baseline.

Candidate ladder:

- `C0_NESTED_EB`: component-specific recency and shrinkage, league-season-level
  priors, no age/translation/park covariates;
- `C1_HIERARCHICAL_PBP`: C0 plus chronology-safe player-movement translations,
  age relative to level, and separately estimated park/environment effects;
- `C2_MULTINOMIAL`: coherent Dirichlet-multinomial sensitivity using the same
  hierarchy and no additional predictors.

No player identity predictor and no broad black-box learner are permitted.

## Fixed hyperparameter search

Search is training-only and component-specific:

- recency half-life in seasons: `{1.0, 2.0, 3.0}`;
- beta/Dirichlet prior effective PA: `{50, 100, 200, 400, 800}`;
- translation partial-pooling prior mover PA: `{100, 250, 500}`;
- park partial-pooling prior PA: `{500, 1000, 2000}`;
- age-effect ridge penalty: `{1, 10, 100}`;
- age effect is piecewise linear at ages `{20, 24, 28, 32}` relative to
  level-season median age, with no player-name or cohort-membership feature.

Each component chooses the minimum event log loss on training-origin folds;
ties within `1e-8` choose, in order, larger prior, longer half-life, larger
pooling prior, and larger ridge penalty. Search results and all failed choices
are persisted. No grid expansion is permitted after V2022/V2023/V2024 or 2026
is opened; a new family requires a versioned new contract and a later protected
confirmation season.

Direction/trajectory bins may enter only `C1_HIERARCHICAL_PBP` as pre-PA PBP
auxiliary counts with their own shrinkage. The candidate must also be scored
without those auxiliaries as an ablation. They cannot replace terminal outcome
history.

## Tracking increment after PBP freeze

Tracking cannot open until one PBP-only candidate is frozen from the disclosed
folds. The initial increment family is intentionally narrow:

`fused_link = pbp_link + reliability * tracking_increment`

Inputs:

- recency-weighted mean EV;
- recency-weighted sweet-spot share (launch angle 8–32 degrees);
- evidence/source-quality terms used only for reliability, not talent.

Only source-certified hard-hit/barrel summaries may be added before scoring;
bat speed, discipline and sprint speed are deferred to a new source gate.

Fixed search:

- EV/LA recency half-life days: `{180, 365}`;
- residual ridge penalty: `{0.01, 0.1, 1.0, 10.0}`;
- reliability `n_eff / (n_eff + k)`, `k` in `{20, 50, 100}`;
- model forms: linear residual with intercept, and component-wise multinomial
  residual with intercept; no other form.

The earlier no-intercept Challenger 2 remains a documented failed baseline; it
cannot be repaired using its 2023 confirmation result. Tracking is evaluated
against the identical future terminal-outcome/wOBA target. PBP and fused rows
must contain identical player/outcome keys. If tracking is removed or evidence
is zero, the fused output must equal PBP bit-for-bit.

## Metrics and weighting

Every fold reports both:

- PA/event-weighted views; and
- player-weighted views, with each eligible player contributing equally.

Primary metrics:

- terminal-outcome multiclass log loss and multiclass Brier score;
- future player wOBA and neutral batting runs/600 MAE and RMSE;
- Pearson and Spearman with future wOBA/runs;
- calibration intercept/slope and ten fixed predicted-probability deciles;
- aggregate league/level outcome and run-rate calibration;
- coverage and fallback rates.

Run values and wOBA constants for a target season are estimated/frozen only
from predictor-season history or a declared neutral historical pool. Completed
target-year weights are diagnostic-only and cannot drive prediction or
selection.

## Required subgroups and support

Report MLB, AAA, AA, High-A, A, complex/Rookie, age bands `<20`, `20–22`,
`23–25`, `26–29`, `30+`, evidence bands `<100`, `100–249`, `250–499`,
`500–999`, `1000+` prior hitter-talent PA, promotions, demotions, other movers,
and training-defined high/low K and high/low HR power quartiles.

A level subgroup is promotion-supported at at least 100 players and 10,000
target hitter-talent PA in a fold. Other subgroups are supported at at least 50
players and 5,000 PA. Lower-support results are reported as diagnostics and
cannot be pooled away or used to claim transport.

## Frozen promotion rule

For **each** V2022, V2023, and V2024 fold, in both PA-weighted and
player-weighted views, the candidate must have strictly lower (by more than
`1e-8`) than the strongest simple outcome baseline:

- terminal log loss;
- terminal Brier score;
- future wOBA MAE and RMSE;
- future neutral batting runs/600 MAE and RMSE.

Across all three validation folds pooled, it must additionally improve:

- log loss and Brier by at least **0.25% relative**;
- wOBA RMSE by at least **1.0% relative**;
- batting runs/600 RMSE by at least **1.0% relative**;
- wOBA and runs/600 MAE by at least **0.5% relative**.

Pooled paired player bootstrap (10,000 resamples, seed `20260823`) must have a
90% confidence interval upper bound below zero for candidate-minus-baseline
player-weighted wOBA RMSE and runs/600 RMSE. Pearson or Spearman may not decline
by more than `0.02` pooled, even when primary loss gates pass.

Calibration guardrails:

- wOBA calibration intercept absolute value `<= 0.005`;
- wOBA calibration slope in `[0.90, 1.10]`;
- each terminal component calibration slope in `[0.80, 1.20]` where
  identifiable;
- no predicted decile absolute wOBA error above `0.010`;
- league/level aggregate wOBA error `<= 0.005` and outcome-rate absolute error
  `<= 0.005` for every supported level.

Supported-subgroup reversal is material if candidate-minus-baseline worsens
both wOBA RMSE by more than `0.002` and runs/600 RMSE by more than `0.5`, or
worsens both proper event scores by more than `0.0005`, in any required fold.
Any material supported-level reversal fails promotion.

After disclosed validation selection, the unchanged refit must pass the same
directional, calibration, coverage, and subgroup rules in the one-shot 2026
confirmation. Failure is final for this candidate; no rescue tuning on 2026 is
allowed. A PBP-only failure stops Hitter v2 at batting and forbids WAR work.

Tracking promotion uses the same gates on the identical eligible overlap, with
PBP-only as comparator. The universal PBP model remains production fallback
regardless of tracking result.

## Scientific invariants

Before any candidate score is accepted, tests must prove:

- probability vectors are finite, nonnegative, exhaustive, and normalized;
- moving coherent probability mass from an out to 1B/2B/3B/HR increases value
  strictly in that order;
- increasing HR probability while maintaining the simplex increases value;
- players with identical K/BB/contact-direction profiles but sufficiently
  different terminal HR/hit histories receive different contact-quality
  estimates;
- target outcomes cannot affect predictors, priors, translations, parks,
  weights, eligibility, or cohort membership;
- PBP baseline is identical before optional tracking residual application;
- missing tracking returns exact PBP, never an error or zero-filled rich row;
- reliability converges smoothly to zero with evidence;
- PBP/fused overlap keys are identical and cannot gain by cohort change;
- source outcome counts reconcile exactly under the source contract.

## Required persisted evidence

Each run records commit/contract hashes, exact command, dependency versions,
source hashes/vintage, train/target keys, parameters, metrics, subgroups,
calibration, coverage, fallback, failed candidates, and deterministic output
hashes. Full Ruff and test suites run after every material gate.

No leaderboard ordering or named-player result may alter this contract.
