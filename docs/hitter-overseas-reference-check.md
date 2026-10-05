# Overseas comparison replacement reference check

2026-10-04. Preparation failed its saved-label reconstruction before any model
fit or output was saved. The source feature frame retained the legacy reference
570 divided by origin MLB PA. The current compatible-value benchmark applies
the completed origin schedule fraction exactly once. The largest evaluation
discrepancy was approximately 0.00184 batting wins for Charlie Blackmon's 725 PA
in 2017, forecast from 2016.

The initial diagnosis incorrectly attributed this to different league PA totals.
An explicit per-origin comparison showed that the MLB count totals match exactly.
The actual cause is the schedule fraction: 2016's fraction is 0.999177, 2021 and
2024 are 0.999588, and 2018 is 1.000412. A second totals-only reconstruction also
failed before outputs or fitting. Neither failure changes the experiment arms.

The comparison therefore reconstructs the existing benchmark reference as
570 times completed origin schedule fraction divided by complete origin MLB PA.
Original source labels and legacy reference are preserved. A separate integration
reference supplies both candidates and their shared evaluation labels, and must
match the saved benchmark to numerical tolerance. This is an accounting check,
not a predictive gain or a new schedule adjustment. It illustrates why passing
source joins alone cannot establish consistent value units.
