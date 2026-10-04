# Accept historical KBO identity links without using current retirement status

2026-10-04. The first official-form probe returned the correct 2005 regular
season, but identity parsing stopped: historical players link to
`/Record/Retire/Hitter.aspx?playerId=...` rather than the current-player detail
path. The initial parser accepted only the latter. Its failed SHA256 is
`8a990c7cbfdfc800d2d09e9586cb4f24fe0c86a4d765ed49a1062edf93804b20`.
The original HTML and request receipts remain unchanged; no completed probe or
projection result was overwritten.

Accept the two actually observed official link shapes, extracting only the
numeric KBO player ID. Do not exclude retired-link rows or use that retrospective
URL category as a historical retirement/availability predictor. It is current
presentation of an identity, not the player's status in the requested season.
Continue the same source test; broad collection is still not authorized by this
partial page success.
