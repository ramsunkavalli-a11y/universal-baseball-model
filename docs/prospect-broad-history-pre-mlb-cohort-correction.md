# Prospect broad-history pre-MLB cohort correction

**Status:** frozen before corrected re-scoring

The source-window audit found that using only in-window MLB stats to identify prior
major leaguers is insufficient at the start of a historical panel. In the 2008
training snapshot, 30 hitter and 26 pitcher rows that later returned to MLB had an
official debut before the snapshot but no earlier MLB row inside the limited stats
window. They are not prospects.

Every broad-history cohort must therefore exclude a player when the official StatsAPI
MLB debut date is in or before the snapshot year, in addition to the existing stats-
history exclusion. The debut field is a stable player fact, not a future performance
outcome. It may define eligibility but cannot be a predictor.

All prior scores affected by the incomplete eligibility rule are superseded. Re-run
the frozen basic and skill models without changing origins, outcomes, features,
regression, penalties, score rules, uncertainty or pass bars.
