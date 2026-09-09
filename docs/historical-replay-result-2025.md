# Historical 2025 replay result

Status: first scored Phase 1 historical checkpoint; not a publishable ranking.

## Forecast score

The frozen March 27, 2025 model was scored without refitting or changing thresholds.
Missing MLB outcomes remain observed zeroes.

- Hitter workload totaled 183,343 projected PA versus 182,919 observed, a 0.2%
  overage. The model expected 651.5 active hitters versus 667 observed. PA RMSE was
  75.74, better than 78.95 from carrying 2024 PA forward; MAE was 29.56, worse than
  the carry-forward 25.59.
- Pitcher workload totaled 180,383 projected BF versus 182,108 observed, a 0.9%
  shortfall. The model expected 784.5 active pitchers versus 801 observed. BF RMSE
  was 76.01, better than the carry-forward 84.50; MAE was 28.76, worse than 26.48.
- On the players FanGraphs explicitly projected, its depth-chart allocation was
  materially better: hitter PA MAE was 92.81 versus 139.89 and pitcher implied-BF
  MAE was 103.67 versus 138.97. FanGraphs remains an external, team-context
  comparator and was not inserted into the universal model.

The interpretation is mixed but clear: the universal model closes league workload
and reduces large errors, while simple recent workload and FanGraphs assign individual
playing time better on average. This result is frozen evidence, not an invitation to
retune against 2025.

## Neutral WAR score

The like-for-like outcome uses the same neutral event weights, 2024 run environment,
projected position, and average-zero running/defense boundary as the forecast. It is
not a comparison to a published WAR system.

- Hitter component log loss improved by 0.00553 versus the 2024 population prior.
- Pitcher component log loss improved by 0.00348 versus the population prior.
- Whole-player expected WAR was 1,061.71 versus 995.75 observed neutral WAR, 6.6%
  high. Hitter WAR was 5.1% high and pitcher WAR was 9.1% high.
- Whole-player WAR MAE was 0.132 across the full 8,946-player zero-inclusive universe.

The skill components add real signal. The aggregate result says the Phase 1 point
forecast is modestly optimistic; it does not support a post-result correction.

## Replay checkpoint

The historical value build now passes the sequential replay contract as a complete
March 27 checkpoint:

- 8,946 frozen universe players;
- 7,803 available value records;
- 1,143 reviews, including 948 unknown-rights players and 195 players with a blocked
  control or contract year;
- no future outcome evidence and no vintage-information claim; and
- point-only historical bounds, clearly labeled as uncalibrated.

The historical checkpoint and the September 8, 2026 current checkpoint also pass as
a two-checkpoint mechanical sequence. All 3,850 material value deltas have a declared
reason. Because the model version, evidence and player universe all changed, this
sequence does not establish value stability under one fixed model.

That projection gap is now closed. The exact March opportunity fits are committed
as a durable package, and an October 15 checkpoint reuses their verified hashes while
updating only available 2025 evidence. Shared-player expected-WAR correlations are
0.689 for hitters and 0.670 for pitchers across 2026–2029. See
[the same-model update](same-model-projection-update-2025.md). Contract-value
stability still requires a cutoff-safe October owner/control/economics join.

Reproduce with:

```text
python scripts/score_historical_projection_paths_2025.py
python scripts/score_historical_war_paths_2025.py
python scripts/materialize_historical_replay_checkpoint_2025.py
python scripts/materialize_phase1_replay_sequence.py
python scripts/materialize_same_model_projection_paths_2026.py
python scripts/compare_same_model_projection_checkpoints_2025.py
```
