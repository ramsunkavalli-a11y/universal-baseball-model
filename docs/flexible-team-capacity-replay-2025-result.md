# Flexible team-capacity replay — 2025

Status: flexible position/role constraints rejected; broad team cap retained.

The rigid position and pitcher-role caps failed because unused workload could not move
between buckets. This challenger fixes that structural problem before considering any
cuts.

- Hitter movement is allowed only for position-group combinations supported by at
  least 30 MLB player-seasons in 2021–2024. DH is available as the universal flexible
  batting slot.
- Pitcher movement uses adjacent-season role transitions supported by at least 30
  players in 2021–2024.
- A constrained allocation moves workload into open eligible buckets and minimizes
  proportional cuts by source group.
- No player's workload can increase, and organization-neutral talent and value never
  enter the calculation.

The unchanged March 27, 2025 forecasts were scored against 2025 results:

| Component | Version | RMSE | MAE | Forecast / actual workload |
| --- | --- | ---: | ---: | ---: |
| Hitters | Broad team cap | 80.031 | 32.276 | 95.42% |
| Hitters | Flexible groups | 80.075 | 32.271 | 94.55% |
| Pitchers | Broad team cap | 79.481 | 30.804 | 94.20% |
| Pitchers | Flexible roles | 79.607 | 30.745 | 92.93% |

The flexible hitter layer is effectively neutral but does not beat team-only: RMSE is
0.043 PA worse and MAE only 0.005 PA better. The flexible pitcher layer improves MAE
by 0.059 BF but worsens RMSE by 0.126 BF versus team-only. That mixed tradeoff does not
pass the gate. Against the original pitcher forecast, its MAE gain is clear but its
RMSE interval crosses zero; the simpler broad cap already improves both with a clear
team-clustered RMSE result.

Decision: retain only the broad team-cap context. Do not reduce portable value because
a current roster is crowded, and do not keep searching aggregate position-share
variants on the disclosed 2025 season. A future depth challenger must use dated roster
slots, option/IL status and genuine player-level competition at the forecast cutoff.

Machine-readable results remain in
`docs/historical-team-capacity-replay-2025-result.json`.
