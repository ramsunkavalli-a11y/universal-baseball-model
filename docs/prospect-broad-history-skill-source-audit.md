# Prospect broad-history skill source audit

**Status:** verified 2026-09-10

Official StatsAPI affiliated season component totals were collected for 2008–2017.
The independent component pull matches the previously stored basic opportunity source
exactly after aggregation by season and player:

| Type | Player-seasons | Exact workload matches | Absolute PA/BF difference |
|---|---:|---:|---:|
| Hitter | 52,841 | 52,841 | 0 |
| Pitcher | 46,195 | 46,195 | 0 |

There are zero hitter rows violating hits/at-bats, extra-base-hit/hit, or intentional-
walk/walk accounting. There are zero pitcher rows violating starts/games, intentional-
walk/walk, or component/batters-faced accounting. Reported StatsAPI `totalSplits` was
not trusted; pagination continued until a short page. Raw responses and hashes are
stored under `reports/generated/affiliated-skill-source-2008-2017/` and remain source
data, not versioned model output.

This audit establishes source consistency only. It does not show that any rate is
predictive.
