# Official affiliated home/away component source

Status: source ready; no production value changed.

StatsAPI `statSplits` supplies exact home and away regular-season lines for every
listed player at Triple-A, Double-A, High-A, Single-A and rookie-complex levels from
2021 through 2025.

- 50 bounded requests: hitting and pitching are fetched separately because combined
  older-season requests can fail server-side
- 50,678 hitter split rows
- 60,069 pitcher split rows
- every response is rejected if its declared split count is not complete
- raw captures and hashes are retained outside git; canonical tables are reproducible

This source makes a 50/50 home/road assumption unnecessary. It contains the model's
core hitter and pitcher component counts but does not provide opponent quality,
weather, park renovations, or batted-ball direction.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\materialize_affiliated_home_away_components.py
```
