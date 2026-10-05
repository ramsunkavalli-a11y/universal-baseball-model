# NPB 2025 table layout correction

2026-10-05. The first NPB 2025 capture stopped before normalized data were
written. Its archived Orix page has a `tablefix2` table with 23 columns and no
`ststats` row classes. Handedness is a superscript inside the player-name cell.
The sealed 2005–24 parser expects a separate handedness cell and 24 columns.
That is a source-layout change, not absent 2025 player data.

Preserve the interrupted captures and old parser. A separate 2025-only parser
checks the exact year/title, first-team table, all 23 headers, recognized
handedness superscripts, nineteen integer count fields, rate arithmetic and
source row uniqueness. Strip only the structured handedness superscript from
the name; do not fuzzy-match identities. An independently written raw-row review
must check all nineteen fields from the new layout. The collector records the
new parser/runner hashes alongside all original helpers. No forecast or fit
changes, and the completed KBO source receipt remains intact.
