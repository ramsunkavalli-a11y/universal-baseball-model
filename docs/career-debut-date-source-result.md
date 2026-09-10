# Extended career debut-date source result

Status: source complete for the expanded official outcome universe.

The official StatsAPI people endpoint returned every requested identity from the
2009-2025 MLB outcome backbone: 5,321 of 5,321 players. Every returned player has an
exact MLB debut date. Requests were batched without roster, transaction, draft, or
contract hydration, and raw responses were retained with hashes.

Debut date is a stable current-corrected profile field, not proof of historical
retrieval vintage. That limitation does not expose future performance, but the replay
must still enforce that every training player's full outcome window ended before the
evaluation cutoff.

Machine-readable evidence: `docs/career-debut-date-source-result.json`.
