# Hitter affiliated component regression audit result

Status: 400-PA challenger improves point scores but fails the frozen uncertainty gate;
retain 1,200 PA.

The 2024 development fold selected the lightest tested regression prior, 400 PA. Its
component log loss was 0.986884 versus 0.988074 for the current 1,200-PA prior, and
its Brier score was 0.465624 versus 0.465840. Every heavier prior was worse than
1,200 PA on both development scores.

The frozen 400-PA challenger also improved the 2025 point scores: log loss by
0.001242 and Brier by 0.000254. However, the player-bootstrap 95% upper bounds were
slightly positive (`0.000084` log loss and `0.000025` Brier). It therefore fails the
predeclared promotion rule.

## Decision

Keep the current 1,200-PA prior. The evidence does not support adding more shrinkage
to push down high-end prospect hitters; directionally it favors trusting translated
performance more, but the gain is not yet reliable enough to alter current values.

No demographic, physical, position, organization, contract, player-name, outside-FV,
or current-2026 input entered selection.

Machine-readable evidence: `docs/hitter-affiliated-regression-audit-result.json`.
Frozen protocol: `docs/hitter-affiliated-regression-audit-plan.md`.
