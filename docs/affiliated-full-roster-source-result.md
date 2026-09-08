# Official full-roster affiliation source audit

Completed 2026-09-07. **Decision: reject as direct dated organization-rights
evidence.** Protected 2026 data was not accessed.

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
that can retain players associated with multiple organizations. Therefore presence in
this response cannot by itself assert one current controlling organization. Do not
resolve these conflicts by row order, status text or arbitrary team priority.

## Consequence

Keep certified 40-man membership as direct evidence. `fullRoster` may later serve as
a candidate-name/coverage source if every player is reconciled through dated
transactions or another ownership authority; until then it cannot define the required
denominator or organization-rights state.

Reproduction: `python scripts/audit_affiliated_full_roster_source.py`. The generated
report includes conflict IDs and date-control details and remains ignored.
