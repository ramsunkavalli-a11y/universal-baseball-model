# Prospect primary-level exposure result

Status: promoted to the private playable build on 2026-09-10.

## What changed

The prior arrival model treated the highest level touched during a season as the
player's level. A brief promotion, rehab assignment, or temporary roster fill could
therefore look like a full season at AAA.

The model now carries three separate facts from official affiliated statistics:

- highest level reached;
- the level with the most PA or batters faced in that season;
- the share of current-season workload at that primary level.

Highest level remains useful evidence. The primary level and workload share tell the
model how much weight that evidence deserves. No player exception, outside FV, team
depth, or subjective prospect grade is used.

## Time-ordered result

The candidate was trained only on earlier snapshots and required lower pooled Brier
score and log loss without losing either score in any evaluation fold.

| Outcome | Player type | Core Brier | New Brier | Core log loss | New log loss | Decision |
|---|---|---:|---:|---:|---:|---|
| Arrival | Hitter | 0.04917 | 0.04845 | 0.17635 | 0.17378 | Promote |
| Meaningful role | Hitter | 0.02004 | 0.01954 | 0.08583 | 0.08290 | Promote |
| Established role | Hitter | 0.01060 | 0.01027 | 0.05054 | 0.04850 | Keep core; one fold missed the strict gate |
| Arrival | Pitcher | 0.05202 | 0.05095 | 0.18469 | 0.18016 | Promote |
| Meaningful role | Pitcher | 0.01902 | 0.01882 | 0.07697 | 0.07570 | Promote |
| Established role | Pitcher | 0.00899 | 0.00889 | 0.03900 | 0.03816 | Promote development-path extension |

Among current pre-MLB players, highest and primary level disagree for 336 of 2,871
hitters and 357 of 4,117 pitchers. More than half of those disagreements have at
least 75% of workload at the lower primary level, so this is not a rare edge case.

## Named arithmetic check

Fernando Gonzalez had 205 affiliated PA in 2026: 168 at Single-A, 16 in complex ball,
and 21 at AAA. His primary broad level is therefore A-or-below with 89.8% of workload,
while AAA remains present as highest-level evidence.

The new six-year probabilities are 39.5% arrival, 14.7% meaningful role, and 10.3%
established role. His nested expected WAR is 1.40 and displayed Model FV remains 45.
This is lower than treating AAA as his full-season level, but not as extreme as
discarding the AAA evidence entirely.

## Boundary

This repairs level evidence only. Constant-hazard six-year extrapolation and future
position retention remain separate research questions. The existing position-
transition sensitivity is not promoted because it failed its downstream positional-
runs test.

The pitcher established-role model also retains advancement and inactivity history;
see `prospect-development-path-result.md`.
