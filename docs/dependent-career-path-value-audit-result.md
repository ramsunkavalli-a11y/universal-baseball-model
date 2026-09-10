# Dependent career-path value audit

**As of:** 2026-09-08  
**Status:** sensitivity audit only; no model selected or promoted

## Numerical stability

A second simulation used 8,192 draws, a different seed, and 300 players: the top
100 research values plus a broad player-ID spread. Compared with the 2,048-draw run:

- value rank correlation was 0.9924;
- mean absolute value movement was $0.35M and the 90th percentile was $1.05M;
- mean absolute controlled-WAR movement was 0.056 and the 90th percentile was 0.163.

That is adequate for a research view but not perfectly stable at fine ranking
differences. A promoted build should use more draws or a lower-variance integration
method.

## Catcher and pitcher diagnosis

The career simulator did not create a new catcher preference. Catchers are 23 of the
top 100 hitters under both the old value benchmark and the dependent simulation.
Shortstops are 43 under the old benchmark and 44 under the simulation. The earlier
position audit remains the relevant warning: position value is real, but future
position retention and player-level defense are still weak.

Pitcher compression clearly predates this simulator. The old pre-MLB top 100 had 99
hitters and one pitcher; the dependent result has 100 hitters. The simulation therefore
does not explain the imbalance. It modestly increases an already-known upstream issue:
pitcher expected workload and conditional WAR are too compressed to produce top-end
controlled WAR. The next challenger belongs in pitcher environment/workload modeling,
not in FV cutoffs or a manual pitcher bonus.

## Boundaries

No later outcome, publication FV, rank list, target position share or target number of
pitchers was used. Segment results are diagnostics, not causal demographic effects and
not parameter-selection evidence.

Machine-readable details are in `dependent-career-path-value-audit-result.json`.
