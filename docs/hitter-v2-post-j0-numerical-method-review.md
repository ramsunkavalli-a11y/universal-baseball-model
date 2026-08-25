# Hitter v2 post-J0 numerical-method review

Date: 2026-08-24

## Decision

`J0_JOINT_CONTEXTUAL_NESTED` remains a final documented failure. It must not be
rerun with a larger iteration limit, looser tolerance, selected intermediate
variance, or different initialization. It was never scored, so the failure says
nothing about predictive value; it says the frozen estimator was not capable of
completing the declared full-data fit.

The scientifically sensible next experiment is a distinct candidate with a
predeclared, non-iterative shrinkage scale. It should retain J0's matched-cohort
context contrast but remove the unstable empirical variance fixed-point loop.
This review does not authorize that candidate's implementation, fit, or score.

## What failed

For every binary component, J0 repeatedly:

1. fit the uncontextual event model at a current batter-effect standard deviation;
2. computed posterior second moments from the fitted player effects and diagonal
   information;
3. formed a new standard deviation from their mean;
4. damped the update 50/50; and
5. required relative change at or below 1% within 20 iterations.

At least one binary component did not meet step 5. The inner MAP optimizer did
not report a failure; the outer variance iteration did. Because the runner did
not emit the active node or iteration trace, no narrower attribution is supported.

## Method gaps exposed by the run

### The convergence rule measured update speed, not likelihood optimality

The outer loop stopped on the relative change of a damped fixed-point update.
Slow contraction can fail the 20-iteration ceiling even when the sequence is
stable and approaching a sensible value. Conversely, a small update does not by
itself establish that a marginal-likelihood objective is optimized.

### The claimed marginal-likelihood evidence was incomplete

The update used MAP effects plus diagonal posterior variances. It did not persist
an evaluated marginal objective, a score, a bracket, or curvature for the
variance parameter. The label "marginal maximum likelihood" was therefore
stronger than the observable evidence produced by the implementation.

### Failure observability was inadequate

The execution contract required node convergence diagnostics, but diagnostics
were only assembled after a node returned successfully. The runner did not emit
node start/completion markers or a durable per-iteration trace. The all-or-
nothing publication policy correctly prevented a partial result, but it also
made root-cause attribution unnecessarily weak.

### Event-level refitting was expensive without changing the variance question

The uncontextual variance loop repeatedly traversed millions of events. The
uncontextual likelihood can be represented by grouped success/trial sufficient
statistics at player and league-season-level cells. A future implementation
should prove grouped and event-level objectives/effects agree on synthetic data
before full-data execution.

## Recommended distinct candidate

The next contract should define a new identifier such as
`J0R_FIXED_INFORMATION_SHRINKAGE`; it must not relabel J0. Its batter-effect
scale should be derived once per component and training origin from the already
frozen component prior strength and the predictor-history pooled event rate:

`sigma_logit = clip(sqrt(1 / (prior_PA * p * (1 - p))), 0.05, 1.25)`

For the 1B-reference hit-composition contrasts, use the corresponding diagonal
multinomial information approximation predeclared in the new contract. The same
derived scale must be used in the contextual and uncontextual fits. No validation
metric may choose or modify it.

This is preferable to simply raising J0's iteration count because it is:

- directly linked to the already frozen empirical-Bayes prior strength;
- deterministic and component-specific;
- computable from predictor history only;
- stable at full-data scale; and
- interpretable as prior information rather than a hidden optimizer outcome.

A fixed-scale sensitivity at half and twice the frozen prior PA may be reported
as a non-decisional robustness diagnostic, but neither alternative may be chosen
from future outcomes.

## Required observability before another real fit

A new execution package must durably record, before any target score:

- active node and phase;
- input row, player, and league-season-level counts;
- derived pooled rate, prior PA, and batter-effect scale;
- every optimizer iteration's objective, maximum parameter change, and accepted
  step size;
- final objective improvement and convergence reason;
- contextual and uncontextual row/key hashes;
- nonfinite and boundary-hit audits; and
- exact B1 fallback checks.

Failure information must be written atomically to a separate incident artifact,
even when no model artifact is accepted.

## Pre-fit gates for the next candidate

Before a new full-data fit can be authorized, a new hashed contract and distinct
namespace must pass all of these target-free checks:

1. grouped-versus-event likelihood and effect equivalence on synthetic data;
2. exact deterministic rerun equality;
3. recovery across simulated low/high event-rate and evidence regimes;
4. all four platoon cells and zero-evidence fallback tests;
5. runtime and memory certification on a non-decisional synthetic surface with
   the real source's row/group counts;
6. an intentional nonconvergence test proving the incident artifact names the
   node and retains no partial candidate; and
7. a full repository test/lint pass.

Only after those checks and explicit fit authorization may the same certified
2021–2024 input be opened by the new fitter. Candidate scoring, J1, tracking,
protected 2026, Stage 3, and WAR remain closed.
