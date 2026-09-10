# Pitcher workload environment result

Status: source diagnosis complete; no candidate or value change.

Official MLB season totals show a clear change between the workload-prior era and the
modern environment. The 2015-2019 and 2021-2024 era means are:

| Measure | 2015-2019 | 2021-2024 | Modern / prior |
|---|---:|---:|---:|
| Active pitchers | 772.4 | 874.5 | 113.2% |
| Mean BF per pitcher | 240.0 | 208.9 | 87.0% |
| Median BF per pitcher | 177.8 | 154.8 | 87.0% |
| 75th percentile BF | 303.8 | 278.3 | 91.6% |
| 90th percentile BF | 652.8 | 546.5 | 83.7% |
| Pitchers with a start | 329.8 | 379.0 | 114.9% |

League BF is broadly stable while more pitchers share the work. The expanding count
of pitchers with a start does not mean there are more traditional starters. Increased
use of openers and bullpen games gives some relievers a start with very few BF. A
binary starter label therefore no longer implies the same workload concentration.

This directly supports the prior descriptive cohort result: later established pitchers
fell below old workload ranges too often. That comparison is not chronology-safe
validation, but the environment shift still rules out raising pitcher workload merely
to make prospect values look more familiar.

The next candidate should represent each pitcher's workload relative to his season's
league distribution, forecast the league-wide usage environment separately, and then
map relative role/rank back to BF. Role evidence should distinguish rotation starters,
openers, bulk/swing pitchers, and relievers using start share and BF per start; a start
count alone is insufficient. Times through the order may be added only where source
coverage is certified. The shortened 2020 season is excluded from both era means. No
parameter is selected here.

Machine-readable evidence: `docs/pitcher-workload-environment-result.json`.
