# Current 2026 rest-of-season baseline

**Status:** retained Phase 1 baseline
**As of:** 2026-09-08

The first live current-season path is connected. The official MLB schedule contained
2,180 completed and 2,430 scheduled regular-season games, leaving 250 games, or
10.29% of the league schedule.

The model projects 21,596.6 remaining hitter PA and 20,597.7 pitcher BF. Applying the
existing conditional WAR rates gives 68.78 hitter WAR and 43.45 pitcher WAR, or
112.23 whole-player WAR. Hitter and pitcher value is added for two-way players.

Current usage is paced to a full season, shrunk with 200 PA/BF toward the existing
2027 team-neutral opportunity forecast, and multiplied by the remaining schedule
share. The 2027 conditional WAR rate, including supported general defense, is used as
a short-horizon proxy. This keeps the
first version consistent with the existing player paths; it does not yet use active
roster, injured-list or team-depth judgments.

## Salary and rights

The payroll source contains 914 accepted 2026 base-salary rows totaling $535.96
million after day proration. The calculation follows the championship-season-day
method in Article V and the Uniform Player Contract of the
[2022–2026 Basic Agreement](https://www.mlbplayers.com/_files/ugd/4d23dc_d6dfc2344d2042de973e37de62484da5.pdf).

Exact current-team matches connect 833 rows and $500.19 million to remaining rights.
The 81 rejected joins remain visible: 48 unresolved current organizations, 30 payroll
and current-organization mismatches, and 3 players without a projection. They are not
forced into trade value because payroll liability alone does not prove current player
rights.

The combined annual input now contains 833 current-season rows plus 50,100 future
control rows. Realized 2026 WAR is unavailable and explicitly null; only projected
remaining WAR and unpaid base salary enter the rights calculation.

## Phase 1 boundary

This is a coherent baseline, not a final in-season projection. The main remaining
pieces are current availability/role, WAR uncertainty, retained salary and special
contract terms, option buyouts, and fitted free-agent and arbitration prices. Phase 2
can refine daily playing time and injuries after the complete value path exists.
