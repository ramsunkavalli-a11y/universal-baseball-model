# Joint hitter aging and opportunity replay — 2025

**Status:** Current Marcel aging fails this diagnostic; no production change  
**Population:** All 3,891 hitter rows in the frozen March 27, 2025 forecast

## Test

The frozen opportunity, workload, position, replacement and run environment were held
constant. The only counterfactual removed the standard Marcel age multiplier from the
predicted hitter event profile. Both versions retained every projected player,
including the 3,224 players with zero observed 2025 MLB PA.

| Result | Marcel aging | No aging |
|---|---:|---:|
| Component log loss | 1.041506 | 1.041477 |
| Predicted hitter WAR | 643.7 | 608.5 |
| Observed neutral hitter WAR | 612.6 | 612.6 |
| Zero-inclusive WAR MAE | 0.16515 | 0.16193 |
| Zero-inclusive WAR RMSE | 0.50041 | 0.49817 |

No aging improved every point metric and removed 35.1 WAR of aggregate optimism. The
paired player bootstrap places the no-aging minus Marcel MAE difference between
-0.00457 and -0.00194 WAR, entirely below zero. The MSE interval crosses zero, so the
RMSE improvement is directionally positive but uncertain.

## Decision

The current generic Marcel hitter age multiplier is not supported by this joint 2025
replay. Do not replace it from this comparison alone: 2025 was already disclosed and
the counterfactual was constructed afterward. Freeze no aging as the leading simple
hitter challenger for the next valid confirmation. Any richer replacement must first
address survivor bias and then beat both no aging and Marcel on conditional component
accuracy and zero-inclusive production.

This result does not reject age as useful information. It rejects this particular
uniform adjustment, which moves all positive offensive events together based only on
age. Outside FV and 2026 outcomes were not used.

Machine-readable detail: `docs/joint-hitter-aging-2025-result.json`.
