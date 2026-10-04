# Include the year heading in English KBO career rows

2026-10-04. The independent English check stopped on Lee's 2023 line: it found
no matching year. The archived page does contain it, but uses a row-heading
`th` for YEAR followed by statistical `td` cells. The reviewer had read only
`td` cells. The failed reviewer SHA256 is
`7068041d31af375174eb7bb1d1ecff365528c7621333e329296bd456f0fe3301`.
This is a review-parser defect, not absent 2023 performance. The source counts
and completed five-season collection are unchanged; no completed review was
overwritten.

Read the direct row's `th` and `td` cells in document order, require exact header
length and the selected origin year, and compare all thirteen shared count
fields. Add a synthetic regression using a YEAR row heading and an unrelated
future-season line. Missing or duplicate origin lines still fail; do not relax
numeric or identity checks to manufacture a match.
