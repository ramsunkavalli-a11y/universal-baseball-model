# Hitter v2 Stage 2d joint contextual development contract

Status: **PRE-REGISTERED BEFORE EVENT-LABEL IMPLEMENTATION, CANDIDATE FIT, OR SCORE**  
Date: 2026-08-24  
Machine contract: `docs/hitter-v2-stage2d-development-contract.json`

## Scientific question

Can chronology-safe pitcher quality and observed batter/pitcher handedness improve a
strong outcome-only hitter forecast? This is a neutralization test, not a claim that
matchup difficulty is intrinsic hitter talent. The model must return the frozen
three-year Marcel outcome forecast exactly whenever certified context is unavailable.

The earlier C0/C1, D0-D2, and E1 candidates remain documented failures. This gate
does not repair, rescore, or relabel them. Contact direction, trajectory, estimated
distance, tracking, park, physical, demographic, and lineup inputs are excluded so
they cannot rescue the contextual hypothesis.

## Required source gate first

The certified matchup sidecar identifies batter, pitcher, hands, date, and prior
pitcher exposure, but it does not yet carry an individual terminal outcome label.
Before any model is implemented, one exhaustive label must be attached to each
eligible PA using the 14-category Hitter v2 taxonomy:

`UBB, IBB, HBP, K, HR, 3B, 2B, 1B, ROE, FC_REACH, SF, MULTI_OUT,
OTHER_OUT, SH_OR_SPECIAL`.

MLB labels reuse the structured Savant true-PA mapping. MiLB labels use only a
deterministic structured-event or narrative mapping and must reconcile exactly at
player-game grain. Labels may not be invented to force official totals, duplicate
rows may not be selected by file order, and player names and model predictions are
unavailable to the process. An unresolved player-game fails closed to the exact
outcome-only forecast.

No fit may be authorized unless certified labels cover at least 90% of all eligible
PAs and at least 90% of every supported MLB through Single-A season-level cell; the
floor is 85% for rookie/complex cells. Any target-free semantic correction requires
a new contract version and hash before fitting. No such correction is allowed after
a candidate score.

## Frozen base and component structure

`B1_MARCEL_345_K1200` is both the strong universal base and exact fallback. It uses
three seasons with 3/4/5 recency weights and 1,200 PA of regression. Missing context
never drops a player.

`J0_JOINT_CONTEXTUAL_NESTED` models these nested nodes separately:

- `P(K)`;
- `P(UBB | eligible non-K, non-IBB PA)`;
- `P(HBP | eligible non-K, non-BB PA)`;
- `P(HR | contact)`;
- `P(non-HR reach | non-HR ball in play)`; and
- `P(1B, 2B, 3B | non-HR hit in play)`.

IBB, ROE-versus-FC composition, out composition, and sacrifice/special policy remain
unchanged from B1. GIDP remains a distinct opportunity model.

For each modeled node, pitcher quality is a chronology-safe posterior log-odds
residual for the same outcome. It uses only certified outcomes dated strictly before
the current game date, with a two-season half-life and fixed node-specific prior
strength. Same-day, current-PA, and future information are forbidden. Zero pitcher
evidence produces a residual of exactly zero; posterior reliability is not multiplied
a second time.

The contextual event model contains a league-season-level intercept, a batter random
effect, the prior-only pitcher residual, and an observed batter-side/pitcher-hand
effect. A matched model fits the identical events and penalties without pitcher or
platoon terms. The player context increment is the contextual batter effect minus
the matched uncontextual batter effect, then applied to the corresponding B1 logit.
This subtraction is intended to remove schedule and platoon composition without
replacing the robust outcome baseline.

## Candidate ladder

J0 tests only pitcher and platoon neutralization. It must pass independently.

`J1_CONTEXTUAL_COMPONENT_DEVELOPMENT` may be implemented only after a passing J0.
It adds component-specific age-relative-to-level and level-transition projections.
All continuous inputs are standardized inside each training origin and must pass a
strict scale-invariance test. J1 equals J0 for D2022 and cannot rescue a failed J0.

There is no hyperparameter search. Variance components are estimated only from
predictor-history likelihood, never evaluation metrics. Optimizer failure or absent
context yields a zero increment and exact B1 fallback.

## Evaluation and advancement

Development folds are D2022, D2023, and D2024 in both PA- and player-weighted views.
The metric-wise comparator is the best loss among one-year empirical Bayes, B1
Marcel, and frozen C0 on identical forecast-target rows. Context likelihood is also
compared with the matched uncontextual model on identical labeled PAs.

J0 must, in every fold and weighting view:

- strictly improve terminal log loss and Brier score;
- strictly improve future wOBA and runs/600 RMSE;
- meet pooled relative gains of 0.25% for both proper scores and 1.0% for both rate
  RMSEs;
- improve node log loss over the matched context ablation in every supported
  node-fold; and
- satisfy the frozen calibration, correlation, coverage, and supported-subgroup
  guardrails in the machine contract.

Bootstrap uncertainty uses 10,000 resamples and seed 20260824. The least complex
candidate clearing every rule is selected. Failure is documented and stops the
ladder; validation results cannot trigger tuning.

## Information boundary and present authorization

D2022-D2024 are disclosed development folds. Previously accessed 2025 is diagnostic
only and may not select, reject, promote, or reweight a candidate. Completed 2026
offense remains an unopened one-shot confirmation season.

This contract authorizes only source-side terminal-outcome label materialization and
reconciliation. It does **not** authorize candidate implementation, fitting, scoring,
tracking work, Stage 3, full WAR, or protected-season access. A successful development
result could authorize freezing a separate confirmation package; it cannot itself
promote a production model.
