# Pitcher age-relative-to-level and handedness result

Status: passes the frozen point-score gate; promote cautiously to the private build.

The 2024 development fold selected the small age-relative-to-level, throwing-hand,
and interaction family. It started from the incumbent translated component profile,
used a fixed player-scale penalty, and changed all five probabilities coherently.

On the untouched 2025 confirmation population of 146 pitchers and 17,852 MLB BF,
component log loss improved by 0.000171 and Brier improved by 0.000052. Both
player-bootstrap intervals cross zero, so this is a small, uncertain improvement—not
a general demographic law.

The direction is useful. The candidate improved both scores among 58 younger-for-level
pitchers and among 110 right-handed/other pitchers. It worsened both among the 36
left-handed pitchers. The overall neutral run estimate moved from 10.3 runs below
average per 800 BF to 8.5 below, closer to the observed 6.4 below. The top quintile
improved from 2.4 below predicted versus 1.8 below observed to 0.9 below predicted
versus 1.0 above observed.

## Decision

Apply the frozen adjustment only to affiliated-translated pitcher profiles in the
private build. Keep its provenance and subgroup warning visible. Do not add height,
weight, birth country, grade targets, or a manual value boost. Rebuild current paths
and measure the player-value impact before making any broader claim.

Machine-readable detail: `docs/pitcher-age-level-handedness-result.json`.
