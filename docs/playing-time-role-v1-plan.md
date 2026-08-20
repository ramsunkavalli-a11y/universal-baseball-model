# Playing time / role v1 plan

Last updated: 2026-08-17

Status: **PRE-DEVELOPMENT / SOURCE-FEASIBILITY — NO MODEL FIT OR 2025 ACCESS**

Governing methodology review:

`docs/playing-time-role-methodology-review.md`

## Purpose

Model **opportunity separately from batting-rate skill**.

Frozen batting-rate input remains:

`frozen_current_talent_carry_forward_v1`

Playing time / role v1 will answer:

> Given only information available at an October 15 snapshot, what is the player's probability distribution over MLB batting opportunity in the following regular season?

## Initial estimand

For every eligible snapshot player, define next-calendar-year regular-season MLB PA:

`Y = next-season MLB plate appearances`

including `Y = 0`.

Primary distributional outputs should support:

- `P(Y > 0)`;
- `E[Y | Y > 0]`;
- unconditional `E[Y]`;
- probability mass across later frozen PA/role bands.

Zero MLB PA is an opportunity outcome, not a batting-rate outcome.

## Population

Start from the universal affiliated-player snapshot population supported by frozen Current Talent evidence, not only players already in MLB.

This permits the model to represent:

- incumbent MLB players losing opportunity;
- minor leaguers reaching MLB;
- players receiving part-time versus regular MLB opportunity.

Exact eligibility/identity rules will reuse the existing universal snapshot contract and must be frozen before scoring.

## Chronology

Provisional development chronology mirrors settled Projection chronology:

1. `2021-10-15 -> 2022` next-season MLB PA;
2. `2022-10-15 -> 2023` next-season MLB PA;
3. `2023-10-15 -> 2024` next-season MLB PA.

Untouched confirmation candidate:

4. `2024-10-15 -> 2025` next-season MLB PA.

**Do not access 2025 opportunity targets before the final playing-time development/confirmation contract is frozen.**

## Model architecture under consideration

### Required Baseline 0

A deliberately simple transparent comparator, using only universally available snapshot context. Exact form is not yet frozen.

Likely ingredients:

- as-of level;
- recent observed MLB PA / affiliated PA;
- prior MLB evidence;
- age;
- frozen Current Talent strength/profile summarized without future information.

Do not add historical roster status to Baseline 0 unless the source audit proves exact chronology-safe availability.

### Candidate family

Preferred first family is a **two-part model**:

1. binary participation: `P(next-season MLB PA > 0)`;
2. positive-count model: `MLB PA | MLB PA > 0`.

Leading mature implementation:

- statsmodels Logit for participation;
- statsmodels zero-truncated Negative Binomial for positive PA.

Packaged statsmodels `HurdleCountModel` is an implementation comparator to inspect before freezing the exact family.

No custom maximum-likelihood optimizer should be written if mature package behavior satisfies the contract.

## Feature families to audit before freezing

### Universally available from existing certified evidence

- exact age at snapshot;
- as-of level;
- recent MLB PA;
- recent total affiliated PA;
- recency/evidence-volume measures;
- prior MLB evidence;
- frozen Current Talent B2 state or low-dimensional scalar/profile summaries derived only from that state.

### Roster-context candidates — SOURCE AUDIT REQUIRED

- active roster;
- 40-man roster;
- injured/other list status where source semantics are exact;
- organization/team;
- recent transaction/option context if reconstructable without hindsight.

These are **not authorized model features yet**.

### Explicitly deferred from individual v1 baseline

- future team;
- future depth chart;
- future roster role;
- human/manual playing-time forecasts;
- a full team positional allocation optimizer;
- defense/position value not already required solely to describe opportunity;
- injuries learned after the snapshot;
- prospect rankings/scouting grades unless separately sourced and validated later.

## Team-coherence boundary

Individual expected PA forecasts need not initially sum exactly to 30 team-season totals because player movement and uncertain roster membership make a portable player model distinct from a team allocator.

Later architecture may add a team/organization allocation layer that constrains finite roster/position opportunity.

Do not use team-coherence constraints to contaminate the first test of individual opportunity signal.

## Evaluation framework — TO FREEZE AFTER SOURCE AUDIT

The final contract should include separate proper/decision metrics for both pieces rather than selecting solely on PA RMSE.

Expected candidates:

### Participation

- log loss;
- Brier score;
- calibration intercept/slope and reliability;
- discrimination as secondary diagnostic.

### Positive PA amount / full distribution

- held-out count log likelihood or proper predictive score;
- MAE/RMSE as secondary diagnostics;
- calibration of predicted mean and quantiles;
- calibration of derived `P(PA >= threshold)` once thresholds are frozen.

### Required strata

At minimum:

- as-of level;
- age band;
- prior MLB evidence;
- recent MLB-PA band;
- frozen Current Talent/evidence-strength band;
- 40-man/active status if those features pass source certification;
- prospect-to-MLB versus incumbent-MLB pathways.

## Immediate source/data gate

Before fitting or selecting any model:

1. **historical roster POC** — prove exact date-specific active/40-man roster retrieval at selected Oct. 15 development snapshots and compare with transaction/known roster controls where possible;
2. **target-surface POC** — use existing certified 2021–2024 player-game evidence to materialize next-season MLB PA including zeros for the universal snapshot population;
3. report zero share, positive-PA distribution/overdispersion, snapshot-level coverage, and target-only/predictor-only populations;
4. decide which roster-context fields are trustworthy enough to enter the frozen feature contract;
5. only then persist the exact Baseline 0, candidate forms/search space, metrics, promotion rules, and 2025 confirmation rule.

## Hard boundaries

- Do not reopen Current Talent.
- Do not reopen/tune the rejected explicit age Projection challenger.
- Do not let zero future MLB PA alter batting-rate skill.
- Do not infer historical roster status from future transactions.
- Do not open 2025 targets before the playing-time confirmation contract is frozen.
- Prefer mature count-model packages to custom likelihood code.
