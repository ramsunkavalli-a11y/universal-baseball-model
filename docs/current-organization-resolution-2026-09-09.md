# Current organization resolution — 2026-09-09

**Status:** Phase 1 current rights states resolved with one review

The 2026-09-08 league snapshot previously left 21 players unresolved because the
season-wide `fullRoster` endpoint listed each under more than one organization. The
source remains the broad player denominator, but it is not final ownership proof.

The league build now applies a fail-closed evidence order:

1. unique membership on one organization's dated official 40-man endpoint;
2. the latest conclusive official acquisition, MLB-rights transaction or release; and
3. a unique `fullRoster` organization only as a labeled provisional fallback.

The original 21 multi-organization cases were resolved: 15 from unique 40-man
membership and six from exact transactions. The broader pass also found that the season
`fullRoster` source can retain released players. The current snapshot now contains
8,355 players with an organization, 37 talent-only players with an exact no-rights
release state, and one same-day transaction conflict in review. The six-year controlled
future path contains 50,058 player-years for 8,343 players; 12 otherwise owned players
still lack a verified opening service balance.

The resolver does not use player-name matching or transaction-description guesses.
Internal assignments do not change ownership. A release by an affiliate is accepted
only in the current season and only when StatsAPI supplies one stable current-team
parent MLB organization. Of 208 affiliate IDs, 205 have one parent and three conflicts
are ignored. Current parent mappings are never projected backward to older releases.

Exact transactions now support 6,923 players, dated 40-man membership supports 1,368,
and only 64 unique `fullRoster` assignments remain provisional. The one unresolved
same-day conflict stays ownerless and in review rather than being guessed.
