# How this project will decide what an experiment means

Adopted 2026-09-25 for future development. Does not retroactively rewrite old
contracts or change the locked 2026 evaluation. Current entry point:
[model audit](model-decision-audit-2026-09-25.md).

## Before computing a new score

Write a short experiment contract containing:

1. **Decision:** what would change if this works, and what remains outside scope?
2. **Quantity:** mean production, participation probability, conditional rate,
   distribution or rights value; units and the exact label formula.
3. **Population/time:** cutoff-known denominator, non-arrivals, horizon,
   censored/missing labels, COVID handling and available source vintages.
4. **Mechanism and alternatives:** why it might help; other explanations for
   the observed problem; one contrast that separates them.
5. **Controls:** strongest same-target existing reference plus an interpretable
   simpler control. Same rows, labels, cutoffs and metric. A product forecast
   can be a benchmark without being a complete production model.
6. **Scoring and decisions:** one primary contrast; secondary diagnostics;
   uncertainty assumptions; justified harm margins if deployment is in scope;
   explicit stop conditions. No undeclared "best of many" rescue.

If these are missing, do not run another model. A diagnostic may legitimately
end with "not identified". That is more useful than a confident wrong mechanism.

## Match the score to the job

- Expected PA/production/value is a **mean**. Squared error and its square root
  are appropriate point scores. MAE favors the median: with 90 zero outcomes
  and ten 10-win outcomes, the correct mean is 1 and median 0. The mean improves
  MSE while worsening MAE. MAE is informative, not an automatic veto on a mean.
- Participation needs probability scores and calibration, not just classification
  accuracy. A correct average arrival count can still allocate chances badly.
- Future rate error among actual participants is useful but conditions on a
  future outcome. It does not replace zero-inclusive delivered-value testing.
- Distribution forecasts need proper distribution scores, interval coverage,
  tail/event calibration and mean checks. Good interval coverage alone can be
  obtained with unhelpfully broad ranges.
- Rights value needs calibrated joint production/service/cost paths. An accurate
  calendar mean cannot validate nonlinear option or retention choices.

This follows the distinction between target quantities and consistent scoring
rules in [Gneiting, Making and Evaluating Point Forecasts](https://arxiv.org/abs/0912.0902).
Weights also change the quantity a fitted regression targets; specify why PA,
square-root PA, equal-player or equal-origin weights match the intended use.

## Hard invalidity checks versus practical tradeoffs

Hard stops include future-label access, duplicate people counted as independent
players, changed denominators across arms, wrong units/signs, missing observations
converted to measured zeros, broken accounting identities, and a claim of a
single joint distribution whose outputs violate its own bounds. Fail loudly.

A reproducible program can still have a bad statistical design. Unit tests and
hashes do not validate the choice of target, comparator or weighting. Conversely,
a probability/PA pair that is not a coherent distribution can still have a
useful PA point forecast; retain that evidence without simulating from the pair.

Small secondary score reversals are not automatically invalidity. Do not use
"every metric must improve," a universal percentage subgroup threshold, or any
increase in aggregate absolute error as interchangeable deployment gates.
For a deployment experiment, state tolerable loss in PA/wins/probability terms
before scoring and explain its decision cost. Report a sensitivity range if the
cost is uncertain. A margin chosen after results cannot justify promotion.
The next accounting diagnostic has no deployment gate, so it needs no invented
acceptable-harm number.

## Always inspect these views

- Individual errors, signed biases and predicted/actual totals, by origin.
- Prospect, prior-MLB and remaining populations separately, then cutoff-known
  level, age, prior-workload and debut/returner groups.
- Annual Years 1–3 and cumulative production: getting the right player a year
  too early is different from betting on a player who never arrives.
- Zero outcomes and positive outcomes as diagnostic decompositions; never use
  future participation to choose the forecast route.
- Number of unique players, positive events and distinct origins, not just rows.
  Sparse groups get uncertain conclusions, not fabricated precision.
- A few named-player examples chosen by a declared error-ranking rule, with
  actual histories and numerical contributions. Examples illustrate a mechanism;
  they neither certify it nor create player-specific exceptions.

League totals and cohort totals answer different questions. Show who is in the
denominator, future-entrant reserves, organization overlap and component budget.
Report opposite-signed subgroup errors even when the grand total looks good.
Keep 2021 and pandemic-crossing paths visible as stress tests; sensitivity
excluding them must never silently become the headline selection population.

## Uncertainty and repeated research

Use paired errors on identical rows. Cluster repeated records by player; report
equal-origin effects and each origin separately. Player resampling conditions
on the observed seasons and does not capture shared league shocks. Two or three
overlapping origins cannot sustain precise claims of cross-era robustness.
Do not bootstrap thousands of player rows and describe that as thousands of
independent tests of a league-wide change.

Nested chronological fitting protects against future labels only if feature
preparation, tuning and selection use genuinely earlier information. Old
recipes' out-of-time predictions are not interchangeable with a new recipe's
out-of-time predictions for calibration. Repeated inspection and model selection
on the same historical folds still create selection bias; see
[Cawley and Talbot (2010)](https://www.jmlr.org/papers/v11/cawley10a.html).

Label all exposed historical comparisons development evidence. A contract
written after inspecting those data improves discipline, not their independence.
Preserve the original 2026 freeze. Evaluating its next-year forecast later will
not validate a newly chosen Years 2–6 model or a post-freeze assembly.

## Decision vocabulary and required result summary

Distinguish **invalid test**, **useful component evidence**, **useful diagnostic
contrast**, **candidate worth further testing**, **provisional delivery**, and
**independently confirmed**. Never use "passed/failed" without naming the gate
and what it establishes. Preserve historical failed decisions; changing future
standards does not retroactively select the failed model.

Every result summary must state, in plain language:

1. What changed, what was held fixed, and what decision was tested.
2. Predicted quantity, players, years, sample/event counts and comparator.
3. Baseline and candidate scores, uncertainty and per-origin consistency.
4. Where it helped/hurt, with magnitude and a baseball interpretation.
5. Which explanation is supported and which cannot be distinguished.
6. Exactly what is now used in the explorer/forecast, what is research-only,
   and one next action (or why no further test is justified).
