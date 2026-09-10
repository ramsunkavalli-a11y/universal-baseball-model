# Pitcher pooled-XBH component plan

Status: frozen before score.

## Question

Does one pooled non-home-run extra-base-hit outcome add stable future MLB pitcher
information that was lost in the five-part profile, without the rare-triple noise of
the rejected eight-part profile?

## Model and source

Reproject the saved official StatsAPI season captures into seven mutually exclusive
BF outcomes: SO, UBB, HBP, 1B, non-HR XBH (`2B + 3B`), HR, and other out. Compare it
with the five-part incumbent expanded to those same outcomes using only the prior MLB
season's contact mix.

Test 800, 1,600, 2,400, and 4,000 BF regression priors. Hold the existing recency,
level discounts, population, and component translations fixed. Select the lowest
2024 component log loss only among candidates that also improve 2024 Brier.

## Later-period rule

If no candidate clears development, stop without calculating 2025. If one clears,
freeze it and score 2025 once, with paired player bootstrap intervals and run-rate
diagnostics. Because other pitcher experiments have already exposed general 2025
component outcomes, this is a retrospective outer check, not fresh confirmation.
Even a passing result remains research-only until the completed 2026 season tests the
fully stacked model.

No 2026 outcomes, pitch sequences, current height/weight, contracts, outside FV,
player names, or target grade counts may enter selection.
