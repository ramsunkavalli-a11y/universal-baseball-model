# Dependent career-path value plan

**Status:** authoritative Phase 2 P0 implementation contract

## Product question

What is the distribution of transferable team-control value for a player when MLB
arrival, role, workload, performance, attrition, cost and club decisions are allowed
to vary together?

The output must describe paths, not create a familiar-looking ranking. Outside player
FV grades, ranks and lists are never predictors or player-level floors.

## Path state

Every simulated pre-MLB path contains a six-year arrival window followed by the full
six-year post-debut career shape, requiring up to 11 calendar years, and records:

- no arrival or first MLB season;
- limited, meaningful-only or established outcome tier;
- annual hitter PA or pitcher BF and annual pitcher role;
- active/inactive state, return, attrition and role transition;
- persistent performance-rate shock plus season event noise;
- annual WAR, service/control state, market value, salary/cost, club decision and
  discounted surplus value.

The first implementation may use the current documented constant-hazard conversion
to distribute the validated two-year arrival probability across six years, but must
label it provisional. It may not pretend independent annual active probabilities are
a career path.

## Historical path library

Build six consecutive post-debut annual paths from the official 2009–2025 StatsAPI
career source. Only debut cohorts whose full six-year window is observable are
eligible. Retain zero-workload years inside a path, including later return. Scale 2020
workload by the already declared 162/60 factor. Assign outcome tier and career role
using the frozen definitions, but preserve each player's actual annual vector and
pitcher role sequence when sampling.

At a historical forecast origin, a sampled path is eligible only when its entire
outcome window ended before that origin. Role-specific cells require at least 30
players; otherwise fall back to the player-type/tier pool. Never sample individual
seasons independently.

## Performance

Reuse the current coherent hitter/pitcher event probabilities and conditional WAR
rate. Posterior rate uncertainty is a persistent path-level shock. Finite-event noise
is season-specific and scales with that season's workload. No clipping of player WAR
is allowed; only free-agent-equivalent market value may floor negative WAR at zero
under the declared economic scenario.

## Rights and economics

Use the player's actual starting rights and guaranteed terms when present. For
pre-MLB players without a guarantee, accrue control from simulated MLB service rather
than assuming service in every forecast year or truncating late arrivals at an
arbitrary six-calendar-year display boundary. Use versioned CBA rules, projected
minimum salary, arbitration logic, explicit Super Two handling, options/buyouts,
sequential non-tender decisions and present-value discounting.

A club decision may use only information available before that decision. Same-season
realized WAR can never determine whether the club tendered that season. Until a
forecast-time non-tender policy is validated, the research engine carries all modeled
controlled seasons and allows negative annual surplus; it does not grant the club
perfect hindsight.

Apply the tested market curve path by path. A high-WAR season may receive the declared
2+ WAR market rate; dispersed low-WAR seasons do not inherit a star rate from an
average forecast. This is the intended nonlinear concentration effect.

## Required output

For each player report:

- mean, median, P10 and P90 discounted surplus value;
- mean controlled WAR and expected cost;
- no-arrival, bust/limited, meaningful, established/regular and star probabilities;
- mean arrival year when applicable;
- source/model IDs and all provisional assumptions.

## Validation and promotion

Treat 2025 as development evidence because it has already been inspected. Use rolling
calendar origins with complete outcome embargoes, selecting only on earlier origins.
Reserve a later untouched origin for confirmation. Score arrival with log loss/Brier
and calibration; workload and WAR with proper distribution scores and coverage;
value against transaction/contract decisions only where a defensible market target
exists. External systems are reasonableness checks, never training labels.

The first engine remains research-only until it passes chronology, probability,
mean-reconciliation, path-dependence, CBA/control, cost/value and deterministic-rerun
tests. Known provisional assumptions must stay visible in the explorer.
