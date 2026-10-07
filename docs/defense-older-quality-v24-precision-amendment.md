# Preserve older source precision without rejecting correct defensive outs

2026-10-07. The first source runner stopped after retaining the complete 2009
response, before a ledger, labels or model. Its decimal-innings check allowed
0.001 outs and component accounting 0.00001 runs. Some source `TInn` values use
approximately two-decimal innings rather than exact thirds: 1,353.1 baseball
innings appears as 1,353.329956 decimal innings, a difference of 0.01013 outs.
Component credits also contain tiny legacy rounding differences around
0.00005 runs. These are precision differences, not a one-out or one-run mismatch.

Keep the original source, reader, preflight and retained response unchanged.
The sibling precision wrapper keeps exact outs from baseball innings and permits
at most **0.02 outs** in the auxiliary TInn check and **0.001 runs** in component
accounting. Neither allowance can hide a whole defensive out or meaningful run.
Save both raw discrepancies and original checks; use independent official outs
for actual exposure certification. A larger discrepancy still fails collection.
No forecast, target qualification, model weight or outcome-dependent tolerance
changes. Reuse the exact 2009 response/receipt, do not refetch it. Freeze this
amendment and its wrapper before processing the remaining years.
