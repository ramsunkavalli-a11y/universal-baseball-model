# Current availability status boundary

**Status:** Phase 1 official-status sensitivity connected
**As of:** 2026-09-08

The rest-of-season model now reads the official StatsAPI status attached to every
team's full-roster response. The status is used only after an exact match to the
separately resolved current organization; full-roster presence does not prove rights.

The rules are intentionally narrow:

- `ILF`, retired, military leave and ineligible status prove no remaining 2026
  availability, so the point estimate and bounds become zero.
- 7-, 10-, 15- and 60-day injured-list status and rehab assignment do not prove a
  return date. The point estimate stays unchanged and the availability-only range runs
  between zero and the baseline.
- Active, reassigned, development, restricted and other statuses do not change the
  projection. In particular, a minor-league assignment is not treated as a loss of
  intrinsic trade value caused by depth-chart blocking.
- Conflicting or missing status remains unchanged and explicitly labeled.

Across 9,194 whole-player rows, 247 official season-out statuses remove 0.16 WAR from
the point estimate. The league point moves from 112.23 to 112.07 WAR. Another 1,052
injury/rehab statuses create an availability-only range of 97.71 to 112.29 WAR.
This is not a full forecast interval; it isolates only the unresolved return-date
question.

Among the 833 current salary/rights matches, 188 rows receive non-point availability
sensitivity. Their combined remaining WAR is 84.97, with an availability-only range
of 73.88 to 85.07. These bounds now flow into the contract-economics input table.

The next improvement is a historically calibrated return/role model using dated
transactions, workload and later appearances. Until that validates, the repo does not
invent a recovery date or suppress value based on current-team depth.
