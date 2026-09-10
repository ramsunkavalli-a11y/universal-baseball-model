# Historical hitter performance paths

Status: **source ready; no model promoted**.

The original hashed StatsAPI captures were re-read to retain intentional walks. The
source links annual batting-plus-replacement WAR to 2,147 complete six-year hitter
workload paths. Defense, baserunning and position are excluded because matching
historical player-season inputs are not available here.

| Career tier | Hitters | Mean six-year PA | Mean component WAR | Median component WAR |
|---|---:|---:|---:|---:|
| Established | 476 | 2,112 | 8.19 | 6.73 |
| Meaningful only | 224 | 652 | 0.56 | 0.47 |
| Fringe | 1,447 | 68 | -0.32 | -0.10 |

These are empirical career paths, not player grades. The negative fringe result is
retained rather than clipped: brief MLB hitters can perform below the batting-plus-
replacement reference during their observed playing time.
