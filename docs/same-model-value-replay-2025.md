# Same-model 2025 value replay

Status: the first same-method Phase 1 projection, control and value update is complete.

## What changed

The March 27 and October 15 checkpoints use the same Phase 1 model version and the
same frozen opportunity coefficients. The October checkpoint adds completed 2025
performance, official roster-entry history, official transactions and the October
40-man/full-roster snapshot. It removes the completed 2025 season from remaining
value and forecasts 2026–2029.

The contract-term table is held fixed from the March replay. This isolates projection,
service and ownership movement without inventing post-cutoff contracts. Those terms
were retrieved later, so this remains an event-cutoff replay and not a true-vintage
information claim.

## Coverage

- The projection universe contains 9,086 players.
- 8,079 have a resolved owner; 1,007 remain unknown-rights players.
- Official roster-entry evidence resolves end-of-2025 service for 8,814 players.
  The 272 unresolved service records remain missing; no service is invented.
- 7,749 players have usable checkpoint values and 1,337 are in review. Of those
  reviews, 1,007 lack an owner and 330 have a control or contract exception.
- 31,552 annual rows calculate and 764 remain in review. The largest bounded issues
  are 558 missing-service rows, 103 Super Two rows and 97 option rows.
- Every calculated annual value now carries the existing Phase 1 uncertainty range.
  Median remaining-WAR width narrows from 2.76 WAR in March to 2.07 WAR in October.
  The ranges are moment-based references, not empirically calibrated guarantees.

## Value movement

The October checkpoint has $12.05 billion of transferable value versus $15.17 billion
in March. That total is not a like-for-like performance score: the 2025 season has
been consumed and the player universe changes.

Among the 5,660 players with usable values at both checkpoints:

- value correlation is 0.691;
- median absolute change is about $99,000;
- mean absolute change is $2.74 million; and
- total value rises by $383.7 million.

The gap between the median and mean is expected: a small number of breakouts and
role changes produce large moves. Nick Kurtz, Drake Baldwin, Kyle Teel and other 2025
breakouts appear among the largest increases. This is directionally sensible, but it
is not an accuracy score.

The replay ledger contains 4,049 material changes and zero unexplained material
changes. Rights changes, completed games, projection evidence and contract/control
evidence remain separately labeled.

## Data decision

No more current FanGraphs downloads are needed for this gate. A genuinely dated 2025
payroll archive would improve a future true-vintage replay, but it is not required to
finish the Phase 1 same-method test. Remaining service, Super Two and option exceptions
are bounded follow-up work rather than reasons to reopen the projection model.

Reproduce with:

```text
python scripts/materialize_historical_people_control_2025.py
python scripts/materialize_historical_war_uncertainty.py --as-of-date 2025-03-27
python scripts/materialize_historical_war_uncertainty.py --as-of-date 2025-10-15
python scripts/materialize_same_model_control_value_2025.py
python scripts/materialize_same_model_replay_checkpoint_2025.py
python scripts/materialize_same_model_value_replay_sequence_2025.py
```
