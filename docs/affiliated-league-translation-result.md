# Partially pooled affiliated league translation

Status: rejected; retain the level-only translation.

The candidate adds a league-within-level residual to the existing same-player,
same-season component translation. Every league residual is ridge-shrunk toward its
parent level; MLB league residuals are fixed at zero so the target remains pooled
MLB. The shrinkage grid was selected on 2024 outcomes and frozen before the 2025
confirmation.

Both hitters and pitchers selected the strongest tested prior, 2,500 exposure units.
That is evidence that league residuals are weak relative to the broad level effect.

| Group | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Hitters | +0.000069 | +0.000005 | -0.000180 | -0.000069 | Reject: lost selection year |
| Pitchers | +0.000024 | -0.000014 | +0.000037 | +0.000041 | Reject: failed both-year gate |

Negative is better. The 2024/2025 scored samples were 130/112 hitters and 173/146
pitchers. The underlying fits contained 1,077/2,084 hitter mover pairs and
1,429/2,886 pitcher mover pairs.

This is not evidence that parks do not matter. Venue identity is now complete, but a
park candidate must be estimated from home/away or game-context evidence rather than
from a team label.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_affiliated_league_translation.py
```
