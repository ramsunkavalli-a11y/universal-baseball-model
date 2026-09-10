# Prospect StatsAPI position-code correction result

Status: correction accepted; private prospect results rebuilt.

## What was wrong

The StatsAPI season-stat feed supplied numeric hitter position codes while the model
expected abbreviations. Almost every historical and current hitter therefore entered
the probability models as `OTHER`. The correction translates the official numeric
codes before assigning the existing catcher, middle-infield, outfield, corner, and
other role groups. It adds no new positional or catcher bonus.

The corrected current arrival population contains 484 catchers, 634 middle infielders,
865 outfielders, 590 corner players, and 298 other hitters.

## Checks

- All nine supported hitter codes have direct unit tests.
- Multi-position rows now use summed games with a fixed official-code tie-break.
  Two full robustness reruns and two conditional-hurdle reruns produced identical
  hashes; the prior unordered tie behavior is removed.
- The original candidate grids and time splits were rerun without post-result tuning.
- The corrected nested probabilities have zero `arrival < meaningful` or
  `meaningful < established` violations.
- Catchers are 19.5% of current hitter forecasts, 26.0% of 45+ forecasts, 25.6% of
  50+ forecasts, and 24% of the top 100 by modeled value. This is elevated but does
  not explain most of the top list; shortstops are the largest group at 43% of the
  top 100.
- Among historical minor-league catchers that arrived within two years, 88% to 92%
  remained catchers at MLB arrival across the tested snapshots. Among those reaching
  meaningful workload, the range was 88% to 97%. This supports retaining position as
  evidence, while a later model should allow position-change probabilities.
- The highest current hitter conditional rate is 3.73 WAR per 600 PA. The top-list
  issue is therefore driven more by career probabilities and workload than by an
  impossible per-PA rate.

## Result and limit

The corrected nested hitter model has 404 players at 45+ FV and 86 at 50+ FV, versus
378 and 81 before the correction. Josuar Gonzalez moves from 17.34% to 19.98% arrival,
from 12.50% to 14.95% established, and from 1.55 to 1.83 expected six-year WAR; he
remains 45 FV.

No outside FV opinion was used. The present role is treated as predictive evidence,
not destiny. The next positional improvement should estimate transitions from minor-
league position to MLB position chronologically instead of imposing a catcher quota
or a subjective position preference.
