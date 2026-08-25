# Hitter v2 Stage 2e development contract

Date frozen: 2026-08-24

## Scope

This contract defines `J0R_FIXED_INFORMATION_SHRINKAGE`, a distinct successor to
the failed `J0_JOINT_CONTEXTUAL_NESTED`. J0 remains a final numerical failure and
is not amended, rerun, or silently relabelled. No J0 parameter or partial fit is
reused.

J0R asks the same narrow baseball question: does strictly prior pitcher quality
and observed batter/pitcher handedness improve the strong B1 terminal-outcome
forecast? It changes only the method used to set batter-effect shrinkage and the
minimum observability required before a full-data run.

This gate freezes design only. It does not authorize implementation, numerical
certification, real-data fitting, candidate scoring, J1, tracking, 2026 access,
Stage 3, or WAR.

## Fixed information shrinkage

J0R removes J0's iterative variance estimator. For each binary node and
development origin, let `p` be the eligible predictor-history event rate and
`n0` the already frozen component prior PA. The batter-effect standard deviation
is fixed before either matched model is fit:

`sigma = clip(sqrt(1 / (n0 * p * (1 - p))), 0.05, 1.25)`

Rates are clipped to `[1e-6, 1 - 1e-6]` only for numerical definition. For 2B
and 3B versus the 1B reference, the scale uses the corresponding diagonal
multinomial information:

`sigma_j = clip(sqrt(1 / (n0*p_j) + 1 / (n0*p_1B)), 0.05, 1.25)`

The contextual and uncontextual fit for a component must use identical event
rows and the identical derived batter penalty. No future metric can select the
scale. Half/double-prior-PA variants are non-decisional sensitivity diagnostics
and cannot replace or rescue the primary candidate.

## Model and chronology

The frozen binary nodes are K, UBB, HBP, HR, and non-HR reach. Hit composition
uses 1B as reference with separate 2B and 3B contrasts. Denominators, responses,
pitcher priors, platoon cells, and nested probability application are unchanged
from Stage 2d.

The uncontextual model contains league-season-level and batter effects. The
contextual model adds the observed platoon cell and the same-node pitcher
residual built strictly before the game date. Their batter-effect difference is
the only increment applied to B1. Missing, failed, or zero context returns B1
exactly.

Development origins remain chronology-safe: D2022 uses evidence through 2021,
D2023 through 2022, and D2024 through 2023. A pooled 2021–2024 refit cannot occur
before promotion. Target-year membership, outcomes, environments, and weights
remain forbidden.

## Numerical certification gate

Before any real fit, a new Stage 2e namespace must pass target-free synthetic
certification. Required checks include grouped/event equivalence for the
uncontextual likelihood, deterministic repeat hashes, recovery at rare and
common event rates, low/high evidence, all platoon cells, chronology exclusion,
exact B1 fallback, nested-simplex isolation, and intentional failure.

The source-shape performance check may retain certified keys and group structure,
but it must drop canonical outcomes and every response column before generating
responses from frozen seeds `20260824` and `20260825`. It is numerical evidence,
not model evidence, and cannot authorize a real fit by itself.

Every run must durably identify node, origin, and phase before optimization. It
must record derived shrinkage, row/key hashes, and each iteration's objective,
parameter change, and accepted step. An intentional failure must name the node
and phase, atomically write an incident, and publish no candidate artifact.

## Evaluation and stopping

J0R inherits Stage 2d's frozen folds, comparators, metrics, subgroup guardrails,
tolerances, and promotion rule unchanged. It must eventually beat the strongest
simple outcome baseline on both future rate value and proper event scores in
every required fold and weighting view without a supported-level reversal.

None of that scoring is authorized here. The exact next gate is review of this
contract, followed—only if authorized—by target-free Stage 2e implementation and
numerical certification. Any implementation or certification failure is
documented before further work; any J0R fit failure is final for J0R.
