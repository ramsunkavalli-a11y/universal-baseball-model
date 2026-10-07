# Explicit league scope for historical fielding logs

2026-10-07. The initial `sportIds` request did not include minor-league records:
Eldridge 2024 returned no splits, while Buxton 2024 returned only MLB records
despite known AAA use. Preserve both responses and the original capture runner.
They are failed scope probes, not absence of minor-league assignments.

Before expansion, make three bounded Eldridge 2024 probes: direct player stats
with singular `sportId=11`, and player hydration with `sportId=11` and
`sportIds=1,11,12,13,14,16`. Compare returned position-game totals with the
already saved annual usage for the declared sports. A correct MLB request does
not certify a minor request. A successful single-sport route may be expanded
only to sports present in the fixed cases' annual source, with all unknown and
missing scopes retained. Do not infer complete innings from PBP snapshots.

This is a source-scope amendment, not a model change or a new accuracy test.
The empty date-range response and ignored plural sport filter remain visible.
The original cutoff, fixed case membership, no-fit rule and forecast protections
are unchanged.
