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
season cannot be valued without an explicit remaining salary obligation; the code does
not guess it from calendar days because salary timing, bonuses and retained money can
differ.

A current controlled season is passed to Contract Economics as
`current_season_committed`. This prevents the annual tender logic from pretending a
club has an offseason non-tender choice during the active season. Future tender and
option decisions retain their normal control states.

This fixes the accounting boundary, but it does not create a rest-of-season WAR model
or calculate unpaid salary. Those two dated inputs are required before a live 2026
surplus value is available.
