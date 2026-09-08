# Official full-roster affiliation source audit

Completed 2026-09-07. **Decision: accept as the primary player-discovery source;
do not use alone as final organization-rights evidence.** Protected 2026 data was
not accessed.

The official roster-type catalog describes `fullRoster` as active and inactive
players. That makes it a promising coverage source, but its behavior must satisfy the
rights-universe grain before use.

## 2024-10-15 audit

- 30 MLB organization endpoints succeeded.
- 7,907 organization/player membership rows collapsed to 7,891 distinct players.
- Team counts ranged from 213 to 314 players.
- Five within-team duplicate source rows were present.
- Sixteen players appeared for two different MLB organizations at the same requested
  snapshot.
- A Yankees 2024-04-01 versus 2024-10-15 control differed by 93 player IDs, so the
  endpoint is date-sensitive, but date sensitivity alone does not establish clean
  as-of ownership.

The cross-organization conflicts are consistent with a season-wide roster history
that can retain players associated with multiple organizations. They affect 0.20% of
distinct players; 99.80% have one candidate organization. Therefore this is useful as
the broad denominator, while presence alone is not final proof of current control. Do
not resolve conflicts by row order, status text or arbitrary team priority.

## Consequence

Use `fullRoster` as the main candidate-name and coverage source. Treat its unique team
assignment as provisional. Certified 40-man membership remains direct evidence, and
dated transactions or another ownership authority finalizes outliers. Unresolved
players remain in the denominator with unknown rights rather than being dropped.

The materializer writes both the organization/player source table and a consolidated
one-row-per-player candidate inventory. Organization conflicts remain visible in the
report and do not block candidate coverage.

Frozen output hashes:

- organization/player candidates: `b2cd9c861bdf74ad671d2621d11cd9f91792f3e9cab083bb3f582d960ad44fc5`
- player candidate inventory: `00f57fb65349580c15c5b16fac7cab737a22c736715205f02788ccb35e496538`

Reproduction: `python scripts/audit_affiliated_full_roster_source.py`. The generated
report includes conflict IDs and date-control details and remains ignored.
