# Pitcher team-capacity v2 result

Date: 2026-09-22

## Decision

Keep the team-capacity result as an organization-context view only. Do not scale the
portable pitcher-value forecast.

For each 2021-2024 forecast origin, the test maps the pitcher's affiliated teams to
their same-season parent MLB organization. A player is eligible only when every team
maps to one parent organization. Multi-organization rows are left unchanged. When one
organization's summed expected BF exceeds the same-season league-average MLB team BF,
all eligible pitchers in that organization are scaled down uniformly; nobody is ever
scaled up.

The data cover 19,696 player-season rows. A single stable organization is available
for 19,307 (98.0%); 389 multi-organization rows are deliberately not guessed. Fifty-five
of 120 organization-seasons exceed the cutoff-safe capacity before scaling.

## Results

The capacity view improves workload RMSE from **70.019 to 69.816 BF** and improves bias
from **+1.221 to +0.123 BF**. The RMSE change is **-0.203 BF**, but its player-clustered
95% interval runs from **-0.459 to +0.044**. It helps in three of four seasons and
slightly hurts 2022 outcomes from the 2021 origin.

Scaling pitcher component WAR by the same factor changes RMSE from **0.307446 to
0.307204**. The **-0.000241 WAR** change has a 95% interval from **-0.001122 to
+0.000619** and improves only two of four seasons. That is not adequate evidence to
change portable player value.

## Why it remains separate

Forecast-time playing organization is not verified offseason ownership and is not the
player's known next-season destination. Trades and free agency can make the old club's
depth irrelevant. Uniform scaling also says that an overfull organization must lose
innings but does not identify which pitcher loses them.

The result is still useful for a roster viewer: it can show an organization-constrained
opportunity scenario alongside the organization-neutral forecast. It cannot replace the
neutral forecast or silently reduce talent/value.

The next version needs dated rights/roster evidence at each historical cutoff and a
player-specific depth allocator. Until then, team capacity is descriptive context.
The protected 2026 outcome remains sealed.

