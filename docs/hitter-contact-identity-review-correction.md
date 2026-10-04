# Signed count differences in the player review

2026-10-04. The first season walkthrough exposed a reporting defect before its
case selections were accepted. Subtracting unsigned Polars counts made a loss
of one contact appear as 4,294,967,295. That reversed the largest gain and loss
selections. The official sequence overlay, 1,920 identity corrections and
physical contact ledger were unaffected; no new model had been fitted.

Keep the original `season-review-2016.json` and its artifacts as superseded
case-selection evidence. Convert both count columns to signed integers before
subtraction, add a regression test reproducing the one-contact loss, and save
a separate signed review and artifacts. Do not overwrite the original receipt
or use its selected cases as evidence of an actual gain. The full eight-season
source gate remains pending, including the fixed 2018 and 2024 player checks.
