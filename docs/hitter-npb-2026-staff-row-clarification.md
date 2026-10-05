# Exclude roster staff from static player identity parsing

2026-10-05. The current-listing recovery stopped before writing any normalized
NPB collection. `rosterPlayer` is also the class of the manager row, whose name
has no player-ID link. It is not a missing batting identity or a count failure.

A versioned wrapper removes only explicitly labeled manager/coach sections
before the unchanged strict identity reader. It requires recognized playing
sections for all retained rows and still rejects malformed player keys or birth
dates. The section is used only to avoid joining staff as player identities;
no position or current role enters a projection. Both stopped capture scripts
and their parsers remain intact. Existing archived raw pages are reused by hash,
not recollected or overwritten. KBO collection is not repeated. Six-control
selection, source scope, missing-key retention and forecast preservation stay
unchanged.
