# Smaller official matchup captures

2026-10-04. While the official capture was running, compare three already
captured games with the same endpoint restricted to `allPlays`, `about`,
`atBatIndex`, `matchup`, `batter` and `id`. All three sequence projections are
identical to their full captures. Preserve the probe captures and hashes.
This is an implementation check, not independent certification of the source
screening or an estimate of the frequency of identity errors.

Resume the same locked game list with this smaller official projection, using
six workers and persistent connections. Deliberately stop the current capture
process before resuming; do not run two writers on the same cache. Keep all
completed full captures and their receipts. A capture without a receipt must be
parsed and projected again before reuse. Partial compressed files are never
accepted as completed evidence. Record the actual URL, capture hash and sequence
hash for both full and narrow captures. No sampling, identity, league or model
decision changes, and the original contract remains intact.
