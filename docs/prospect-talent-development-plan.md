# Prospect talent development plan

Status: frozen before fitting the next model.

## Product question

Given what is known at the cutoff, how good can the player's baseball skill become?
Do not answer how soon he arrives, how much he plays, or what his contract is worth.

## P0 foundation

1. Reproduce the confirmed results-only Current Talent Baseline 2 for hitters at each
   historical cutoff and the current snapshot. Do not substitute the older Phase 1
   conditional WAR rate.
2. Build a pitcher present-skill profile on the same contract: translated K, BB, HBP,
   HR and contact results, recency weighting, regression, evidence strength and an
   MLB reporting scale.
3. Keep batting/pitching skill separate from running, defense and position until each
   component has its own support and uncertainty.
4. Label insufficient evidence as unresolved. Never use rank order among near-identical
   priors as information.

## Development target

For players with later observed opportunities, predict their translated skill profile
at fixed future horizons. Start with one and two years; add longer horizons only after
the short horizons work. Zero future opportunities are censored for talent and belong
to the separate opportunity model.

Inputs may include only cutoff-safe information available across the relevant level:

- present translated component profile;
- age and age relative to competition;
- current and highest level;
- evidence amount, recency and history span;
- batting/throwing hand, height, weight and birthplace when historically timed;
- PBP-derived components that have actual coverage.

No public FV, public rank, organization reputation, signing bonus or future roster
decision enters the model.

## Baselines and tests

Compare on identical player rows:

- no-change present skill;
- a transparent Tango/Marcel-style aging baseline;
- a simple regularized age/level/component model;
- richer interactions only when they win later chronological tests.

Primary scores are future component likelihood and calibration. Secondary scores are
future run-rate error and top-tail identification. Report by hitter/pitcher, level,
age, evidence strength and handedness. A candidate must improve more than one season,
avoid major subgroup reversals and retain the universal fallback.

## Ranking output

Publish three fields, not one unexplained number:

- present skill estimate and evidence tier;
- future talent median plus a wide plausible range;
- basic reasons for the estimate: strongest components, level translation, age effect
  learned from history, and missing evidence.

Position, opportunity, workload, control and contract value are attached only after
the talent layer passes.

