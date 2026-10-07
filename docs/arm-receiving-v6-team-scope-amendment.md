# Check whole season scope for traded players

2026-10-06, before any arm or receiving model fit. The original pilot requested
`with_team_only=1`. Its arm value differs from the all-team native ledger for
Matt Reynolds in 2022 and Ryan Vilade in 2025. The captured values are +0.391086
versus +0.219921 runs for Reynolds and +0.014713 versus +0.105421 for Vilade.
These discrepancies cannot be removed by tolerance or assigned to a position.

Capture the same two completed seasons with `with_team_only=0`, preserving the
original responses. Inspect returned metadata, team scope, opportunities and
identities; compare every row to the native all-team component. Inspect both
players explicitly alongside the fixed cases and small samples. Do not extend
history or fit a model until the discrepancy is explained or quarantined.

The first-base source already matches all 350 pilot player-season receiving
numerators. Its six throw-type counts and expected-out identities still require
a full check and player walkthrough. Receiving and range remain separate.

Whole-season arm opportunities aggregate a player's observed position mix. A
non-outfield run numerator cannot be silently assigned to an outfield denominator.
Where actual opportunity counts cannot be separated by position, retain that
scope limit rather than fabricate an isolated outfield rate. No frozen forecast,
explorer or 2026 outcome changes are authorized by this source correction.
