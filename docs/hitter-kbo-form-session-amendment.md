# Check a fresh KBO form session before declaring extraction unavailable

2026-10-04. After the retired-link correction, the probe accepted the historical
2005 average page. Its published PA sort action returned HTTP 200 but redirected
to `/Error/Error.html?aspxerrorpath=...`, with no record form. The parser failed
rather than accepting it as statistics. The code SHA256 at that failure is
`a73a9dc059136985cb94e6b8c2d85eba2200257f4d6a180ea14675182b4b568c`.
The response and request bytes remain in the original cache.

The retry had replayed a cached form in a new requests session. Session dependence
is an unproven explanation, not the established cause of the server error.
Make one separately named fresh-session attempt, fetching and posting live form
state sequentially. Require the returned URL to stay on the requested record
page, in addition to HTTP success, before parsing counts. Never overwrite the
prior failure or treat an HTML error page as a certified empty season. If the
same public action fails with fresh state, stop this form route and document the
source limitation rather than silently widening or bypassing access.
