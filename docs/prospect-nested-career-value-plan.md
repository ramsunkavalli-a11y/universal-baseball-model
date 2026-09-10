# Prospect nested career-value sensitivity plan

Status: frozen before current probabilities or values are inspected.

## Model

Fit the accepted core two-year models on the existing 2018, 2021, 2022, and 2023 historical snapshots:

- arrival on every eligible pre-MLB player;
- meaningful role conditional on observed arrival;
- established role conditional on observed meaningful opportunity.

Convert each two-year probability to the existing three-window six-year approximation. Then form ordered unconditional probabilities only by multiplication:

- six-year meaningful = six-year arrival × six-year meaningful-given-arrival;
- six-year established = six-year meaningful × six-year established-given-meaningful.

The repeated-window approximation is a Phase 2 sensitivity, not a claim that hazards are literally constant or independent.

## Value conversion

Use the already frozen mature workload priors:

- fringe arrival;
- meaningful but not established;
- established.

Multiply disjoint tier probabilities by their historical six-calendar-year workload means, then apply the player's existing conditional WAR rate. Do not change skill, role, defense, running, contract, cost, or uncertainty inputs.

## Review

Report probability distributions, threshold counts, total expected WAR, supported workload-prior cells, and named examples. Check that probability order holds exactly without clipping.

FanGraphs Top-100 FV is diagnostic only. It cannot fit, select, calibrate, floor, or rescue the model. There is no target count of 45, 50, or 55 FV players.

Promote only to the private playable preview if it fixes the independent-probability contradiction, avoids the original full-season-on-any-arrival inflation, and does not recreate the binary model's near-total collapse. A later forecast period is still required before public use.

