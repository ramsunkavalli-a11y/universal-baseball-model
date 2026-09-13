# Peak pitcher structure result

Last updated: 2026-09-12  
Status: **REJECTED; KEEP THE EXISTING PEAK COMPONENT MODEL**

## Question

Do two simple ideas found in public minor-league pitcher systems improve our
age-24-to-26 talent forecast?

1. origin-season starter share;
2. different component relationships by minor-league level, including the published
   KATOH-style diminishing return for very high Triple-A strikeout rates.

The test keeps translated K/BB/HBP/HR/other outcomes as the foundation. Public rank,
FV, future workload and arrival are not inputs.

## Result

The development period selected the combined version with strong ridge shrinkage.
Against the frozen component-development baseline, it subsequently improved:

- equal-player log loss in 1 of 5 later groups;
- equal-player Brier score in 1 of 5;
- exposure-weighted event log loss and Brier score in 3 of 5;
- paired equal-player uncertainty in 0 of 5.

The direction was inconsistent: it worsened both player scores in 2018, 2019, 2024
and 2025. The isolated 2023 gain is not enough to promote it.

## Decision

Do not add a starter bonus or level-specific component interactions to peak pitcher
talent. Starter history remains useful for role and arrival, but it is not demonstrated
additional evidence about pitching quality once age, level and translated component
performance are known.

This narrows the remaining gap. A richer results-only rearrangement is unlikely to fix
low-minors pitcher ordering. The next useful challenger must add genuinely new evidence:
pitch-call process measures where official sequences are physical, or velocity/movement
where tracking exists. Missing lower-minors tracking must remain explicit.

Machine-readable detail: `reports/generated/peak-pitcher-structure/report.json`.
