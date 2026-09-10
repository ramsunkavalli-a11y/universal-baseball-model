# Prospect ranking sanity audit plan

**Status:** active P0 product gate  
**Started:** 2026-09-10

## Goal

Compare the frozen model prospect top 50 with a current FanGraphs or MLB Pipeline
top 50 and explain every important agreement and disagreement with basic, auditable
baseball logic. Outside ranks, names and FV grades are diagnostics only. They never
enter a player projection, coefficient, bonus, floor or quota.

## Required explanation chain

Every reviewed player must expose this chain:

`age and level -> observed workload and performance -> conditional skill -> MLB and
role probabilities -> expected career workload -> WAR -> cost/control -> value`

An unconventional rank is allowed. An unexplained rank, missing input, duplicated
value, excessive position/role effect, or result driven by a weak fallback is not.

## Work sequence

1. Freeze the current model output and outside comparison snapshot.
2. Build separate source-top-50 and model-top-50 tables using stable MLBAM IDs.
3. Separate identity/eligibility mismatches from actual model disagreements.
4. Show age, level, workload, arrival, meaningful-role, skill-rate, WAR and value for
   every player; show hitter run components or pitcher run prevention.
5. Flag missing evidence, fallback evidence, thin samples and extreme skill rates.
6. Review both tails: public top-50 players rated low and model top-50 players absent
   from the outside top 50.
7. Trace large differences upstream and fix only general data or model rules.
8. Re-run historical/time-ordered model tests for any rule that changes.
9. Rebuild the private explorer only after a structural correction passes.
10. Publish the comparison, explanations, unresolved limitations and before/after
    changes as the ranking-sanity gate result.

## First comparison source

Use the captured 2026 FanGraphs Top 100 because it already has a saved source page,
source hash and 91 MLBAM matches. The audit uses its top 50. MLB Pipeline can be added
as a second diagnostic later without changing model inputs.

## Promotion rule

There is no required overlap percentage and no requirement to reproduce public
rankings. The gate passes when extreme results are traceable to complete inputs and
consistent baseball rules, and all material structural defects found by the audit are
fixed or clearly quarantined. Named-player tuning is prohibited.
