# Preserve missing incumbent comparisons during fit recovery

2026-10-04. The fixed runner completed two cells and fitted four heads for
2016 fold 2, then stopped before saving that cell's forecasts. Its all-repaired-
column finite assertion included mechanical comparisons that require a current
incumbent forecast. Hwang is an admitted addition with no incumbent forecast;
those comparison fields must be null, as the contract requires. The new model
outputs themselves are not the source of the failure.

Preserve the original runner, its seal, all saved models and completed cell
receipts. A narrowly defined recovery runner changes only the finite-check scope
and loading of the already saved four unfinished-cell models. Require every new
forecast output to be finite; require mechanical comparison nullness to match
missing incumbent inputs exactly and finite values on original rows. Resume the
unchanged fits for remaining cells. Hash the four recovered files before loading
and preserve their bytes. Their first hashes were captured after the interruption,
unlike completed cells whose models already had recorded creation hashes.

No model setting, training row, feature, label, membership or outcome selection
changes. No new result-based branch, blend or second experiment is authorized.
The interrupted runner's pending receipts stay intact; the completed review must
record this execution qualification and independently replay all 140 heads.
