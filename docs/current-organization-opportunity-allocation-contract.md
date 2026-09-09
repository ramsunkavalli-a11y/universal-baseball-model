# Current-organization opportunity allocation contract

Status: **FROZEN BEFORE CURRENT RESULTS**  
Frozen: 2026-09-09

## Purpose

Create a separate current-organization view of future opportunity without changing
organization-neutral talent or trade value. This first layer closes team workload
capacity; position and pitching-role allocation remain later layers.

## Inputs

- organization-neutral hitter expected PA and pitcher expected BF by player-season;
- dated incumbent organization and future control state;
- one fixed full-season team capacity equal to the accepted historical MLB median
  league PA/BF pool divided by 30 teams.

Only player-seasons explicitly marked controlled and attached to one organization are
eligible for known current-team allocation. Free agents, future acquisitions,
replacement players and unresolved ownership remain in an explicit unassigned share.

## Allocation

For each organization, season and player type separately:

1. Sum organization-neutral expected workload for known controlled players.
2. If the sum is at or below team capacity, leave every player unchanged.
3. If the sum exceeds capacity, multiply every known controlled player by the same
   factor `capacity / raw_total`.
4. Define external/replacement share as `capacity - allocated_known_total`.

The method never scales a player's opportunity upward. It cannot change conditional
skill, WAR rate, arrival probability or contract/control state. Hitter PA and pitcher
BF each close exactly to capacity after their own explicit unassigned share is added.

## Required checks

- one row per player-season in each opportunity input;
- one organization per player-season in the ownership input;
- exactly 30 organizations represented in each projected season;
- no negative or nonfinite workload;
- allocated workload never exceeds organization-neutral workload;
- player sums plus unassigned share equal team capacity within numerical tolerance;
- league sums equal 30 times team capacity;
- two-way players may retain separate hitter and pitcher rows;
- organization-neutral paths remain byte-for-byte untouched.

## Boundary

This is a conservative capacity layer, not a depth-chart model. It does not decide
which catcher, shortstop, starter or reliever receives a specific slot. A later
chronological validation must establish position/role constraints before those can
redistribute workload. This research output cannot replace organization-neutral trade
value.
