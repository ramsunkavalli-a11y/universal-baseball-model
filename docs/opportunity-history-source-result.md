# Opportunity historical source result

**Completed:** 2026-09-08
**Decision:** accept for the Phase 1 broad cohort baseline, with 2020 excluded

Official MLB StatsAPI supplies both necessary pieces at league scale:

- dated `fullRoster` responses provide a broad active/inactive player denominator and
  position identity; and
- paged season-stat responses provide actual MLB-through-rookie level, age, PA, BF,
  games and starts.

The stat endpoint's `totalSplits` field is not reliable. For example, 2023 hitting
reported 1,700 but returned 6,118 splits, while pitching reported 2,105 but returned
7,456. The collector therefore pages until a response is shorter than the requested
5,000 rows and rejects repeated pages or duplicate split keys.

`fullRoster` is not a complete denominator by itself. Across normal 2018–2024 seasons,
440–738 hitters and 433–829 pitchers with positive official affiliated statistics were
absent from that season's roster union. Historical opportunity snapshots therefore use
the union of roster identity and official stat identity. `fullRoster` is not treated as
final rights ownership, and status text is not used as playing level.

## Materialized evidence

Seven league seasons (2018–2024), all 30 organizations, were captured. The raw source
responses and generated tables remain outside git; the reusable collector is versioned.

- combined source snapshots: 25,811 hitter rows and 33,879 pitcher rows before the
  stat-identity union correction;
- corrected zero-inclusive fitted history: 74,743 hitter cohort rows and 90,727 pitcher
  cohort rows across horizons 1–6;
- distinct historical players: 8,513 hitters and 11,565 pitchers;
- missing age: 7.2% of hitter rows and 11.2% of pitcher rows, retained through explicit
  level/role or population fallback;
- hitter history SHA-256: `45509422e39d0829aa0a56cd3bcdb1dea1ad41119b8ea140cec2f44224e25ea5`;
- pitcher history SHA-256: `49e59475c33bb70f8a2256b583c6bbf166f827482426e666ac6f53d8cbb1bd95`.

Pitcher identity uses official position evidence. Position players' incidental pitching
does not create a pitcher career path; true two-way position evidence remains eligible
for both components.

The 2020 snapshot is excluded from fitting because affiliated minor-league play was
cancelled. Including it would mislabel thousands of players as normally inactive. The
source remains captured and the exclusion is named in the result rather than silently
discarded.

Population MLB participation declines from 14.8% to 11.3% across hitter horizons 1–6
and from 14.0% to 11.0% for pitchers. These are broad-denominator references, not an
individual player's path and not promoted performance claims.

## Remaining boundary

The cohort source and fallback fits are now real. The 2026-09-08 current snapshot and
2027–2032 fallback paths are also materialized. The frozen selected one-year hitter
forecast should be attached if its artifacts are recovered. Conditional WAR rates,
aging and rest-of-season 2026 production remain separate.
