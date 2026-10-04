# Missing ages in older hitter snapshots

2026-10-04. The population audit found 237 origin rows with missing reported age,
including roster-only Bryce Harper in 2010. Before any model fit, recover birth
dates where available rather than repeating the previous default age of 27.

First use the hash-verified cached official demographic table. For remaining
missing-age identities, request only ID, name and birth date from the official
people endpoint. Do not request current height, weight, position, activity,
transactions, MLB debut dates or performance. Save raw captures and parameters.
The request set is all remaining missing-age identities, not eventual successes.

Preserve the original reported age. Use June 30 of the origin season to calculate
age only where the reported age is absent, and save its birth-date provenance.
If birth date is still unavailable, keep age unknown. This is a current-corrected
stable demographic fact, not a claim of historical retrieval vintage. It does
not repair missing batting history or prove that a roster-only hitter was ready
for MLB. Original source audit files remain unchanged; the completed review
contains the supplemented population and separately records the correction.
