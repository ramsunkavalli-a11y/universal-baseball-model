# Correct the shared hitter value baseline before scoring

2026-10-04. Independent replay stopped before any score or player result was
saved. The seventy hitter heads are valid, but the final value product used the
source frame's older `origin_replacement_rate` instead of the comparison table's
compatible origin baseline. They differ slightly because of their environment
definitions. This is an execution defect, not evidence about the model design.

Preserve the original runner, all seventy fits, per-cell forecasts, combined
forecast and hashes. Append `compatible-predictions.parquet`, replacing only
the two shared value columns with each unchanged expected PA times unchanged
batting rate/600 plus the already fixed comparison-table baseline. No head,
feature, population, target, learning strength, probability or PA changes.
Save a separate receipt showing the exact maximum change and unchanged columns.

The original reviewer remains sealed. The correction runner evaluates that
same reviewer in memory with only three path substitutions: compatible prediction
file, compatible fit receipt, and compatible prediction hash in the output receipt.
Every fitted-head, membership, label and player-review check stays in force.
This is not a rerun or changed experimental target. Protected 2026 is untouched.
