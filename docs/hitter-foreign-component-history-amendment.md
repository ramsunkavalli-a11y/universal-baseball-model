# Match overseas calibration histories to the model inputs

2026-10-04. The first foreign component player review found a design mismatch:
calibration used one overseas season while model inputs pooled three. Applying
a slope learned from a noisier single season to a longer history can suppress
skills for reasons unrelated to league translation. The direction and size of
that effect are not assumed. Preserve the first fits, profiles and report.

Before another fit, change only the calibration source definition to the same
three-year pool used by a forecast profile: observed seasons from source year
minus two through source year, recency weights 3, 4, 5 times observed PA, with
half-event smoothing and the complete same-season league reference. Missing
older identity/stat history remains unknown, not a certified zero. For a mover
from one league, use that league's history; do not import another league into
the calibration vector. Retain its actual observed source PA and earliest/latest
source years in the receipt.

Keep all qualified 30-PA forward pairs, targets, folds, cutoffs, precision weights,
three coefficient definitions, ridge penalty 2, monotonic slope bounds, references
and forecast history construction unchanged. Do not change the penalty or tune
named misses. Assert each primary source season reconstructs the original pair.
Every prior observation precedes the mover's target and the fitting cutoff.

This is an additive methodological repair, not a new league source, a source
eligibility change or a whole-hitter victory. Repeat independent normal-equation,
reference and profile checks and the same fourteen player/control reviews.
Compare the two component profiles on identical inputs and show persistent
failures as well as changed mechanics. Keep ordinary/unmapped controls. No new
PA/value forecast, frozen 2026 change or explorer promotion follows automatically.
The original end-to-end integration requirements still apply.
