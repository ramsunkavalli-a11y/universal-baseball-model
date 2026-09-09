# Current organization resolution — 2026-09-09

**Status:** Phase 1 ownership conflicts resolved from official evidence

The 2026-09-08 league snapshot previously left 21 players unresolved because the
season-wide `fullRoster` endpoint listed each under more than one organization. The
source remains the broad player denominator, but it is not final ownership proof.

The league build now applies a fail-closed evidence order:

1. unique membership on one organization's dated official 40-man endpoint;
2. for a remaining multi-organization player, the latest conclusive official
   acquisition or MLB-rights transaction; and
3. a unique `fullRoster` organization only as a labeled provisional fallback.

This resolved 15 cases from unique 40-man membership and six from exact transactions.
All 8,393 players now have an organization in the current snapshot. The six-year
future path increased from 50,100 to 50,226 player-years because all 21 players also
have resolved service balances. Same-day conflicting ownership transactions and
multiple 40-man organizations still fail closed in code and tests.

The resolver does not use player-name matching, minor-league affiliate `currentTeam`,
or transaction-description guesses. Internal assignments do not change ownership.
Only explicit acquisitions and MLB roster moves whose structured `fromTeam` or
`toTeam` identifies the MLB organization can settle a conflict.

This closes the known multi-organization queue. It does not make all 7,019 unique
`fullRoster` assignments direct evidence; those rows remain visibly provisional until
a stronger source is present.
