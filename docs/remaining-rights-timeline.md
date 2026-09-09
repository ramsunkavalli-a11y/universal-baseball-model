# Remaining-rights timeline

**Status:** implemented
**Date:** 2026-09-08

The trade-value input is what an acquiring club can still receive or owe. For a live
in-season snapshot:

- WAR already produced is reported but excluded from rights value;
- only projected WAR after the as-of date enters value;
- only unpaid/transferred current-season salary enters cost; and
- future seasons use full-season WAR and full future obligations.

The adapter requires each row to declare `remaining_current_season` or
`full_future_season`. Future rows cannot contain realized WAR. A controlled current
season cannot be valued without an explicit remaining salary obligation. The dated
2026 build now calculates a base-salary remainder from each club's official
championship-season calendar, while keeping bonuses, retained money, deferred pay and
special payment covenants outside the result.

A current controlled season is passed to Contract Economics as
`current_season_committed`. This prevents the annual tender logic from pretending a
club has an offseason non-tender choice during the active season. Future tender and
option decisions retain their normal control states.

Realized WAR can be null in a current-season row when that reporting input is not
available. It remains excluded from value and receives the explicit status
`remaining_only_realized_war_unavailable`. Future seasons still require realized WAR
to be exactly zero.

The current [rest-of-season baseline](current-rest-of-season-2026-09-08.md) now feeds
projected remaining WAR and prorated base salary into this interface. It is an
economics input, not yet a published dollar ranking.
