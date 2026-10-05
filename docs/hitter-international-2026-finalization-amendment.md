# Separate preservation checks for the two forecast packages

2026-10-05. The source review preparation is sealed and its six source cases
are retained. Before executing its finalization function, inspection showed
that the legacy forecast manifest uses `artifacts` and `input_files`, not the
selected package's `files` layout. Applying one layout to both would fail or
misstate preservation. No final receipt was written by that function.

Use a separate finalizer that calls each existing package verifier, retains
both verifier receipts, and verifies the already completed final evaluation's
receipt hash against the candidate readiness record. Preserve the original
review script and preparation bytes. No collection, fit, score, case selection
or player forecast is repeated. Historical verifier fields saying results were
unopened or not evaluated describe the freeze record, not present evaluation
status. The final receipt labels that distinction explicitly.

Inspection also found the readiness record names its hash map `evidence_hashes`,
not `source_hashes`. The peer-repair preparation had already sealed its first
finalizer. Preserve that executable and use the versioned finalizer for the
actual completion, reading the existing hash-map name without modifying the
readiness receipt. Neither superseded finalization function produced a public
receipt. The equal-window peer correction remains unchanged.
