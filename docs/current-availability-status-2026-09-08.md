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
  return date. Exact current-status/transaction agreement receives the historical
  activation-timing factor; unmatched cases keep the baseline point. The
  availability-only range runs between zero and the baseline in either case.
- Active, reassigned, development, restricted and other statuses do not change the
  projection. In particular, a minor-league assignment is not treated as a loss of
  intrinsic trade value caused by depth-chart blocking.
- Conflicting or missing status remains unchanged and explicitly labeled.

Across 9,194 whole-player rows, current status and transaction replay agree for 263
injured players, 261 of whom have a projection. Their 10.92 unadjusted WAR becomes
1.84 WAR. The league point moves from 114.35 to 105.13 WAR after all availability
treatment. The availability-only range is 102.07 to 114.40 WAR.
This is not a full forecast interval; it isolates only the unresolved return-date
question.

Among the 833 current salary/rights matches, the combined remaining WAR is 79.51,
with an availability-only range of 77.82 to 87.10. These bounds flow into the
contract-economics input table.

The narrow return model is now historically calibrated from 2022-2025 activation
timing. It still does not invent a recovery date or suppress value based on
current-team depth.
