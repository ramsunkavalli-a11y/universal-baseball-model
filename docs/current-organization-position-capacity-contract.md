# Current-organization hitter position-capacity contract

Status: **FROZEN BEFORE CAPACITY ESTIMATION OR CURRENT ALLOCATION**  
Frozen: 2026-09-09

## Question

Can broad, historically observed hitter-position capacity prevent a current
organization from assigning implausible opportunity to too many similar players while
leaving portable talent and organization-neutral opportunity unchanged?

## Source and time split

- Official StatsAPI player/team/position fielding usage and team batting PA.
- Estimate capacity shares from completed 2021–2024 MLB team-seasons only.
- Use completed 2025 only as a descriptive stability check. The 2025 position result
  has already been inspected elsewhere, so this is not fresh confirmation.
- Apply the frozen shares to the 2027–2032 current-organization view only.

## Position groups

Use five broad groups to avoid false precision from multi-position players:

1. `CATCHER`: C.
2. `MIDDLE_INFIELD`: 2B and SS.
3. `CORNER_INFIELD`: 1B and 3B.
4. `OUTFIELD`: LF, CF, RF and generic OF.
5. `DH_FLEX`: DH, missing/unresolved and other hitter positions.

For each historical player-team-season, primary position is the position with the most
games started; if no starts exist, use games played. Deterministic ties use fielding
outs, games played and normal position order. A batting row without usable fielding
evidence remains in `DH_FLEX`; it is never dropped or guessed into a premium position.

## Capacity estimation

Assign each player's team PA to his observed primary group, calculate group PA share
within each MLB team-season, take the median share across 2021–2024 team-seasons and
renormalize the five medians to sum exactly to one. Report dispersion and 2025 absolute
errors; do not tune a group or percentile using 2025.

## Current allocation

Start from the already capped current-organization hitter allocation. For each
team-season/group:

- capacity is `team_capacity * frozen_group_share`;
- if known controlled allocated PA exceeds group capacity, scale that group's players
  down proportionally;
- otherwise leave players unchanged;
- never scale a player upward;
- preserve unused group and team capacity as explicit external/replacement/flexible
  share.

Group allocation may reduce only the current-team opportunity view. It cannot change
skill, conditional WAR rate, arrival probability, control, Model FV or portable trade
value. Catcher is a workload constraint, never a talent bonus.

## Acceptance boundary

The layer is research-ready only if source coverage is explicit, all historical and
current denominators reconcile, frozen shares sum to one, no player is increased, and
every current team-season remains at or below the prior team-capacity result. Report
2025 stability and current effects even if poor. Poor stability blocks use; it does not
authorize retuning on 2025.
