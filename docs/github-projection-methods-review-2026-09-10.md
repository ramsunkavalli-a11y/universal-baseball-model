# GitHub projection-method review and execution decision

**Status:** Active methodology input  
**Reviewed:** 2026-09-10  
**Production changes from this review:** None yet

## Decision

The next model work will strengthen the simple universal foundation before adding
more feature families. The immediate order is:

1. score aging together with the separate probability of returning and receiving
   workload, while retaining zero-follow-up players;
2. tune shrinkage separately for each hitter and pitcher component with walk-forward
   splits and a frozen later check;
3. test age/level translations only after the first two pieces are stable;
4. keep demographics as incremental challengers to the baseball-only baseline; and
5. reserve pitch tracking, batted-ball quality and platoon models for coverage-limited
   Phase 2 layers with the universal fallback unchanged.

This sharpens rather than replaces the existing architecture. Skill conditional on
participation remains separate from participation, role and workload. A player who
does not return contributes an observed zero to the joint production score, but does
not receive a fabricated zero component-rate target.

## Useful outside implementations

- [Baseball Hydra](https://github.com/lambertchu/baseball-hydra) found that simple
  Beta-Binomial shrinkage could beat its neural challengers for rest-of-season rates.
  It supports component-specific prior strength, separately projected opportunity,
  and calibrated probability intervals.
- [Baseball Projections](https://github.com/jackseeburger/baseball-projections) uses
  walk-forward testing, frozen selection periods, explicit baselines, separate pitcher
  workload, and additive pitch-quality challengers. Several plausible additions are
  withheld when they do not clear the declared gate.
- [LongBall Analytics](https://github.com/nielsjsc/LSTMLB) provides a useful example of
  level/age MiLB translation, MLB/MiLB evidence blending and pitcher-component
  reconstruction. Its published-FV prospect floors and rank blending are prohibited
  here and will not be copied.
- [NPB Stan Research](https://github.com/yasumorishima/npb-stan-research) shows why a
  small player-component gain must also be checked at the downstream team or value
  target: the aggregate result can worsen.
- [Court Vision](https://github.com/neeljshah/court-vision) illustrates a useful
  sparse-data backoff ladder for pitch and plate-appearance models. That pattern is a
  later MLB/process layer, not a universal minor-league foundation.
- [Aging](https://github.com/qntkhvn/aging) and
  [Extreme-value baseball](https://github.com/teddygroves/baseball) demonstrate the
  selection problem created when low-opportunity or disappearing players are omitted.
  Aging and workload must therefore be judged jointly even when their models remain
  separate.

## Binding validation rules

- Every challenger sees only evidence available at its forecast cutoff.
- Selection and scoring use identical player rows, including non-returners.
- Component skill is scored conditionally; total production is scored unconditionally.
- Shrinkage strength is learned separately by component and population. A pooled
  constant must win rather than be assumed.
- Hyperparameters are selected inside the development window and frozen before the
  later check. Disclosed validation years are not reused for rescue tuning.
- Simple carry-forward, population-prior and current production baselines remain on
  every scoreboard.
- Promotion requires improvement in the integrated WAR/value target without material
  damage to calibration, coverage or supported groups.
- Published FV, rankings and scouting grades remain evaluation-only inputs.

## First deliverable

Build a reusable next-season transition table from the retained MLB history. Each
source player-season must receive exactly one next-season state: active hitter,
active pitcher, active two-way, observed inactive, or right-censored. Join the
conditional component prediction only for active follow-up, and score the product of
return probability, workload and conditional performance against actual production.
This directly measures whether an aging change improves what the valuation consumes.

In parallel, inventory the incumbent regression constants and run a component-by-
component walk-forward sweep. Prefer stronger shrinkage on ties and reject constants
whose apparent gain does not persist in the frozen later seasons.
