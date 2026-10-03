# Correct ranking capacity units before the first completed reliability fit

2026-10-03. The first fixed-reliability optimizer reached its 700-iteration limit.
No completed fit, predictions or scores were saved. The source preparation and
initial contract/preflight are preserved. Inspection of the inherited scaling
shows historical list capacity is entered as 50/99/100 while the other rank
fields use roughly unit-scale values. With a penalized odds prior this is an
inappropriate feature scale, not evidence that predictive reliability failed.

Scale the three capacity fields by 100 for both arms, a deterministic units
conversion specified before any completed real fit or outcome-score inspection.
Keep all other inputs, membership, targets, penalty, optimizer budget and
comparisons unchanged. Preserve the original preflight as
`preflight-before-capacity-scaling.json`, then prepare all folds and source cases
again with amended hashes. Do not accept silent nonconvergence or tune parameters
against exposed evaluation results.
