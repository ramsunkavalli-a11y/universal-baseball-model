# Historical contract source audit: 2025

**Status:** parsed private retrospective bridge; annual valuation interpretation next
**Audited:** 2026-09-09

A public GitHub gist described as “Cots 2025 Player Contract Data” contains exactly
30 team CSV files at revision `e06fef21f5b9df5bb5bf72a4ed456ce23382a508`.
Rows include player name, 2025 service, options, contract description, 2025–2029
labor-payroll amounts and future `A1`–`A4`, option and free-agent states.

The extract was created 2026-01-31, after the season. It can support only
`retrospective_event_cutoff`, not a vintage-information claim. It has no declared
redistribution license and no MLBAM IDs, so raw/bulk data must remain private and
it cannot become the primary contract authority.

The Phase 1 identity gate will require a unique same-team normalized-name match to
the MLBAM-keyed FanGraphs Opening Day table plus agreement on service time when both
sources report it. Ambiguous names, team disagreements and service disagreements
remain review. Accepted rows can fill the 2025 historical replay contract path;
FanGraphs remains the primary current contract source.

## Materialized result

The fixed 30-file revision produces 1,289 player rows and 6,445 annual cells.
Exact team/name/service agreement attaches 1,192 rows (92.5%) to MLBAM. Thirty-seven
service disagreements and 60 unmatched team/name rows remain review. The parser
recognizes 1,482 numeric cells and 1,750 arbitration, option or free-agent states;
no nonblank annual cell is unparsed.

Cot's service cells were exported as spreadsheet numbers, so trailing zeroes were
lost: for example, `8.16` means `8.160`, not `8.016`. The source-specific parser
restores the three-place remainder before comparison. This correction raised exact
identity coverage without relaxing the matching gate.

Numeric cells are retained as source evidence, not automatically accepted salary
obligations. In an option year a displayed amount may be a buyout or payroll
allocation rather than the exercise salary. Contract text and state must agree before
the economics layer can use it.
