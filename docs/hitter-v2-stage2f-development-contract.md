# Hitter v2 Stage 2f development contract

## Decision

The next distinct candidate is `H0_NEUTRAL_HIERARCHICAL_OUTCOMES`. It is not a
J0/J0R rescue. It removes opponent-context adjustment from player talent and
builds from the useful part of C0: component-specific terminal-outcome recency
and shrinkage.

H0 must translate every historical component to a neutral MLB reference level
using player-movement evidence available strictly before the forecast. It then
models forward component change using age relative to level and a fixed
piecewise age basis. Target-year level and outcomes are available only to the
scorer, where target outcomes may be translated with parameters already frozen
from predictor history.

## Why the target changes

Raw future affiliated wOBA is partly a measurement of where a player was
assigned. A promotion can lower raw outcomes even if talent improves, while a
repeat-level season can do the reverse. Neutral batting talent therefore needs
a common reference-level target. The permanent B0, Marcel, and C0 families are
retained, but each receives the same chronology-safe reference-level wrapper so
the comparison is fair.

## Model and search

H0 retains the nested K, walk/HBP, HR, reach, hit-composition, and multi-out
structure. Component half-lives, prior PA, translation pooling, development
shrinkage, and calibration shrinkage use only the small grid frozen in the JSON
contract. A fold may select parameters only on origins earlier than that fold.
If an effect cannot be learned—especially in V2022—it is neutral with wider
uncertainty, never estimated from the target and never filled with zero skill.

The disclosed V2022–V2024 folds are development evidence, not confirmation.
H0 must beat the strongest wrapped outcome baseline on all four primary metrics
in every fold and weighting view, clear pooled, calibration, correlation, and
subgroup guardrails, and still pass a future protected confirmation before it
can be promoted.

## Contact shape

`H1_CONTACT_SHAPE_INCREMENT` remains closed until H0 passes. If opened, it uses
only five predeclared, baseball-interpretable contrasts: pulled air, opposite-
field air, pulled ground, opposite-field ground, and line-drive share. It may
adjust future HR/contact, extra-base-hit/contact, and reference-level wOBA only
as a regularized residual on top of H0. Missing or vanishing evidence returns H0
exactly. An unrestricted ten-percentage adjustment is prohibited.

Estimated distance, tracking, lineup position, physical/demographic fields,
durability, opponent context, Stage 3, and WAR are deferred. Protected 2026
remains unopened.
