# Required player walkthrough after every model test

User instruction, 2026-09-27. This is a mandatory experiment-completion gate,
not an optional illustration after a headline score. Apply to hitter, pitcher,
playing-time, running, fielding, catcher, park/opponent, integration and value
experiments. Apply equally when a candidate wins, loses or is inconclusive.
For source/adjustment tests, trace their effect on representative player evidence
even if no end-to-end forecast is yet fitted. Ordinary unit tests do not each
require a separate baseball report; they support the experiment walkthrough.

## Required sequence

Contract and source/support checks → run the fixed test → aggregate scores →
player walkthrough → disposition and next-work decision.

Scores may be reported while the walkthrough is pending, explicitly as
provisional. Do not label an experiment complete, adopt/reject an approach, or
launch the next modeling experiment on the strength of aggregate scores alone.
Diagnostic work needed to explain a result is part of this checkpoint. Stop and
document missing evidence rather than inventing an explanation.

## Select cases without cherry-picking

Use a manageable handful, normally six to eight distinct players. Record the
selection rule, player IDs, origins, horizons, folds and benchmark/candidate.
Selection must collectively cover:

- Fixed diagnostic cases selected before fitting, including the hypothesized
  beneficiary and an opposite-risk profile, when eligible.
- A large improvement and a large deterioration relative to the benchmark.
- A major false high and a major false low after the change.
- At least one ordinary/well-predicted case, not only famous outliers.
- Relevant level, age, sample-size and role contrasts for the claimed scope;
  include minor leaguers and non-arrivals/exits when those are in the population.

Cases may cover multiple categories; add cases if needed rather than excluding
an inconvenient category. If a category is empty, report that fact. Do not change
eligibility to force a favorite player into a test. For each focal profile use
at least one comparison selected from origin-known information without looking
at its future success; three to five comparisons are preferable when support
allows. Include unsuccessful comparisons when they emerge from that rule, not
by selecting only successes to imply every promising prospect should succeed.

Outcome-selected examples are diagnostics, not independent confirmation. Show
the selection rule and full-cohort score/group totals alongside the anecdotes.
Do not silently replace deteriorating examples with flattering ones. Persist
the selected cases so later iterations cannot erase a recurring failure.

## Walk through each player, not just their final error

1. **What was known then:** actual dated statistics by season and level, exposure
   and denominators, age/role/position where available, missing history and any
   genuinely cutoff-known context. Separate later injury/trade/breakout facts
   from information the model was entitled to use.
2. **What the model actually received:** trace source joins, component rates,
   park/opponent/level adjustments, reliability, recency, shrinkage and fallback
   behavior. Show what is omitted or compressed. State which branch is being
   tested; do not imply it includes every feature developed elsewhere.
3. **How the forecast was produced:** show relevant intermediate quantities,
   such as arrival/regular probabilities, conditional workload, batting rate,
   positional/defensive contributions and final value. Give exact units and
   horizon. A component score is not automatically full WAR, and calendar years
   are not service/control years. Identify actual training/profile support.
4. **What changed and what happened:** benchmark and candidate side by side,
   followed by the observed outcome on identical eligibility and horizon. For
   multiyear claims inspect annual paths as well as cumulative value. Handle
   canceled/short seasons explicitly. Explain how the case relates to cohort
   calibration/totals, not just its absolute error.
5. **Why the change happened:** trace a calculation or replay the saved fit.
   Where needed, use narrowly labeled sensitivity/ablation probes with unchanged
   fitted parameters and consistent derived features. Record out-of-support or
   artificial combinations. Such probes explain model mechanics, not causal
   effects or validated replacement forecasts.
6. **Baseball judgment:** distinguish a data bug, lost representation, adjustment
   error, unsupported extrapolation, misleading evaluation target, plausible
   statistical tradeoff and genuinely unpredictable outcome. State evidence and
   uncertainty. A reasonable forecast may miss; a lucky forecast may be unsound.

Adapt intermediate quantities to the component: for park tests, show the same
player's exposure/raw versus adjusted outcomes and reliability; for defense,
show opportunities and position/context rather than treating errors alone as
talent; for pitching, distinguish rate, role, workload and delivered value.
Do not fabricate downstream predictions for a test that never estimated them.

## Deliverable and disposition

Save a readable walkthrough linked from the result report, plus machine-readable
case IDs, source/cutoff provenance, actual inputs, intermediate values,
benchmark/candidate forecasts, realized outcomes, comparison selection and any
diagnostic probes. The summary to the user must contain concrete player findings,
including a failure or tradeoff when present—not only an aggregate metric/link.

Record `player_walkthrough_status` as `pending`, `complete`, or `blocked`, with
the artifact path and unresolved issues. New experiment reporting code must
check completion before a final disposition; do not claim old runners already
enforce this. `complete` means the review was performed, NOT that the model passed.
Keep statistical validation, baseball reasonability and deployment separate.

If the walkthrough reveals a design/data defect, qualify the score and repair
the defect under a documented contract. If it reveals a new feature hypothesis,
put it into the controlling plan for a bounded test; do not tune to those names
or immediately switch directions. An unsuccessful test with flawed methodology
does not justify rejecting the entire baseball idea.

Older results are not retroactively certified. Before relying on an older
result to adopt/reject a component or steer new work, supply the missing
walkthrough or explicitly mark the evidence provisional. Append corrections;
do not rewrite historical contracts or conceal original outcomes.

## Compact report outline

- Test question, benchmark/candidate, population, cutoff and horizon.
- Aggregate result and uncertainty, marked provisional until review is done.
- Case selection manifest and origin-known comparison rule.
- Per-player: stats → actual inputs/adjustments → intermediate forecast →
  benchmark/candidate/outcome → explanation and support limits.
- Cross-case patterns, cohort/totals check, confirmed defects versus hypotheses.
- Walkthrough status; retain/reject/repair/uncertain disposition; one justified
  next step within the controlling plan, with no automatic deployment.
