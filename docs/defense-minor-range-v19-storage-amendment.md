# Resume the unchanged range test with compressed evidence

2026-10-07. The first run stopped with a verified disk-full error while saving
`inner-2018-3-4-fit.json`. Thirty-four completed cells and the incomplete cell's
preflight/features remain. No headline comparison or disposition was produced.

Seventy byte-identical public mirrors were removed only after SHA256 comparison
with preserved local originals, recovering 88,102,863 bytes. The completed JSON
records are then losslessly compressed, decompressed and checked against their
original byte hashes, mirrored in compressed form and recorded in an archive
index. The zero-byte incomplete save stays present as failure evidence. Every
removed copy can be recovered from an original or byte-identical decompression.
No older project data, source captures, forecast packages or results are removed.

The sibling resume runner keeps the original sealed runner, model module, test
rules, population, target, feature definitions, penalties and seeds unchanged.
It validates the original preflight hashes, returns saved results for completed
cells, verifies the incomplete cell's preflight/features before finishing it,
and compresses new JSON output. It records an additive resume preflight before
any remaining fit. This is a storage/execution repair, not another experiment,
changed statistical comparison or rerun of completed fits.

The partial results remain provisional. Independent verification and player
walkthrough are still required before the disposition or another model test.
