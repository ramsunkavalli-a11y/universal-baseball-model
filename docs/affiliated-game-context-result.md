# Official affiliated game context

Status: promoted as the park-factor source.

The source materializes final official StatsAPI schedules for the 2021-2025
affiliated minor-league levels: Triple-A, Double-A, High-A, Single-A and the
rookie complex leagues. It records the home club, away club, venue, scheduled
innings and final score at one row per game.

- 25 bounded schedule requests
- 51,301 scored games
- 208 venues and 213 teams in the raw source
- exact duplicate listings removed
- conflicting suspended/resumed listings excluded when one final score could not
  be assigned honestly across two venues

This is enough to estimate a repeatable home/road run environment. It is not a
player projection by itself and does not silently treat a team or league label as a
park effect.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\materialize_affiliated_game_context.py
```
