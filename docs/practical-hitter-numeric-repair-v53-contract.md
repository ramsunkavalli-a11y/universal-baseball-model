# Repairing numeric prospect history inputs

2026-10-03. Before adding a prospect specialist, direct source inspection found
that the existing pooled-history materialization inferred integer columns from
its initial rows. The intended fractional time since draft was truncated in
23,401 of 28,813 drafted source rows. Several weighted rookie and DSL PA columns
also have integer storage. This is a representation defect, not evidence that
draft age or lower-level history is unimportant. Old artifacts remain unchanged.

Pre-fit reconstruction additionally finds 229 RK128 pooled-PA differences: its
current float column preserves previously truncated older rows after a later
source concatenation widened the dtype. All reconstructed component rates are
unchanged. The full allowed correction is draft elapsed time and pooled PA for
DSL, RK120, RK128 and RK134. This source finding predates any new fit or score.

## The fixed comparison

Reconstruct all fourteen leagues' three-year pooled counts and component rates
from the existing season-level count file, with explicit floating-point storage.
Reconstruct time since draft as (origin year minus dated draft year)/10, zero
only when draft history is unknown. Compare every reconstructed numeric input
against the old input; record all differences before any fit. Other features,
population, historical ranking information and outcomes remain unchanged.

Use all 30,506 historical evaluation rows and the same 35 chronological,
whole-player-separated training/test cells. Origins are 2016–18 and 2021–24;
outcomes are the following calendar year's MLB PA and batting counts through
2025. Preserve non-arrivals, exits and roster-only source qualifications. Target
2020 is excluded; the repaired origin-2020 source remains in eligible training.
Missing canceled MiLB exposure is not invented production. No protected 2026
outcomes, additional college collection or future public forecast inputs.

Refit exactly the selected construction: V34 regularized batting-rate Ridge
(alpha 100, existing safe scaling, conditional future participants, actual-PA
and equal-origin weights) and V49 scouting binary participation and conditional
PA heads (250 iterations, depth 3, leaf minimum 30, learning rate .05, L2 10,
no early stopping). Save 105 heads and replay every prediction. Known hard
unavailability and reversible reported retirement still zero opportunity only.
The old candidate remains the benchmark; no settings or source eligibility
change in response to results.

Also report PA-only and rate-only product changes as fixed mechanical diagnostic
contrasts, not new fitted models. Expected offense is expected PA times batting
wins/600 plus origin replacement; it is not full WAR, trade value or a career
talent distribution. The product still approximates dependence between talent
and opportunity.

## Checks and interpretation

Save source reconciliation and preflight for every actual all/active training
subset before fitting. Count distinct people by origin-known stage, age, draft
history and thin professional exposure. Unsupported rows stay in scores and
are marked. Persist original and repaired inputs and source hashes.

Primary comparison is equal-target-year delivered offense MSE on the unchanged
population, with paired player-cluster nominal development intervals. Report PA
RMSE/MAE, participation Brier/log loss, participant-only PA-weighted hitting-rate
error, upper/lower never-debut cohorts, origin totals and the same broad/legacy
public samples. Actual and predicted public event rates use the same origin
environment as the prior unit audit. Exact public archive dates and park
neutralization remain unresolved; no superiority claim from this rerun.

Before disposition review actual stats, source joins, old versus repaired inputs,
saved fitted calculations and outcomes. Fixed diagnostics are Kurtz 2024,
Langford 2023, Bellinger 2016, Alonso 2018 and Salas 2024. Add the largest
delivered-value gain/harm, false high/low and ordinary case; select four peers
from origin-known stage, age, professional exposure and draft rank without
looking at their outcomes. Review both successes and failures.

The numeric correction is valid even if scores worsen; deployment is a separate
question. Keep the corrected source for subsequent research, retain the old
candidate for transparent comparison, and do not claim the fast-entry problem
solved merely because a data bug was fixed. Finish the player review before
choosing another modeling experiment. This contract is written before new fits.
