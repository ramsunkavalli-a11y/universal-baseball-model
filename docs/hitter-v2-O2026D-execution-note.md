# O2026D population correction

The first completed execution used the old prescore training tables. Review of
`rolling_origin_slices` then revealed those tables already filter on modeling
eligibility. That violates the frozen O2026D population specification even though
the new cohort builder itself does not filter on eligibility.

Preserve that execution in `hitter-v2-O2026D-superseded-filtered-result.json` and
the generated `hitter-v2-O2026D` directory. It is not the accepted benchmark.
The corrected execution uses the original unfiltered 2021–2023 player-season
artifact, sliced strictly before each forecast year, and writes a separate
`hitter-v2-O2026D-unfiltered` directory. Official source responses are reused
byte-for-byte. The contract, formula, smoothing, targets and evaluation remain
unchanged. Target results were already inspected before this source correction;
the rerun is disclosed development evidence, not untouched confirmation.
