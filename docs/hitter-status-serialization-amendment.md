# Resume status materialization after a serialization failure

2026-10-04. The first source-only process reached all 83,300 rows, then exited
with TypeError while serializing date-valued clinical spells. No status ledger,
summary, case receipt or model fit was written. Its source seal is preserved.

The successor script verifies that seal and all unchanged sources, rebuilds the
same population and rules, and serializes date objects explicitly as ISO dates.
No employment/availability decision, evidence cutoff, model input definition or
membership changes to repair this execution failure. A separate recovery seal
records the successor code and amendment. Existing artifacts cannot be replaced.
The original failed preparation script remains intact and reproducible.
