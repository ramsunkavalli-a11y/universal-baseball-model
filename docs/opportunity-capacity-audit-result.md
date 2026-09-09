# Opportunity capacity audit

**Run date:** 2026-09-09  
**Status:** league-capacity pass; closed-system identity fail; correction is research-only

In every completed source season, total MLB hitter PA exactly equals total pitcher BF.
The median full-season pool from 2018–2025, excluding 2020, is 182,926.

The current six-year paths do not exceed that historical league capacity. They also
do not close: hitters and pitchers independently allocate different totals for the
same future plate appearances in all six seasons. The gap ranges from 0.4% to 5.4% of
the league pool and is largest in 2030 (9,848 PA/BF).

| Season | Hitter PA | Pitcher BF | Gap | External/replacement share after symmetric reconciliation |
|---|---:|---:|---:|---:|
| 2027 | 177,894 | 175,556 | 2,338 | 3.4% |
| 2028 | 179,556 | 178,823 | 733 | 2.0% |
| 2029 | 180,304 | 174,169 | 6,135 | 3.1% |
| 2030 | 176,406 | 166,558 | 9,848 | 6.3% |
| 2031 | 160,455 | 152,568 | 7,887 | 14.4% |
| 2032 | 142,430 | 143,418 | -988 | 21.9% |

The first research correction projects both sides onto one shared pool using their
capacity-capped arithmetic mean. This is the symmetric least-squares solution to the
identity PA = BF. It changes opportunity, not skill, and preserves the unassigned
share for replacement players, trades, and future acquisitions.

This league-level correction must be validated before integration. Organization,
position, catcher, starter, and relief constraints are the next layer; they must not
be simulated by talent bonuses or quotas. Machine-readable details are in
[`opportunity-capacity-audit-result.json`](opportunity-capacity-audit-result.json).
