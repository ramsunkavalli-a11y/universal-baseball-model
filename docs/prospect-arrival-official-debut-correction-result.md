# Prospect official-debut eligibility correction

Status: complete and active in the private preview.

The arrival model now requires the official StatsAPI debut date when it builds every
historical prospect cohort. A player whose debut was on or before the snapshot year is
excluded even when the local season-stat window does not contain that earlier MLB
season. A labeled future arrival without an official debut date fails the build.

This removed 104 hitter cohort records and 154 pitcher cohort records across the four
training snapshots. In the oldest 2018 snapshot, 91 hitter records and 137 pitcher
records were affected; 12 and 28 of those records, respectively, had previously been
mislabelled as future arrivals.

No feature, coefficient choice, threshold, FV mapping, or outside grade was changed to
offset the correction. The fixed core model still beats its time-ordered baseline on
Brier score and log loss for arrival, meaningful-role, and established-role outcomes.
All 46 private-preview model-law checks pass.

The corrected 176-combination feature search, recalibration check, conditional-hurdle
test, and four-year horizon audit were rerun. They did not support promoting a richer
feature family or a calibration layer. The longer horizon remains diagnostic because
it is not a fresh untouched confirmation period. Production therefore stays on the
simpler core specification.

Current average six-year arrival probability changed from 15.73% to 15.41% for hitters
and from 12.62% to 12.56% for pitchers. Josuar Gonzalez's direct model FV moved from 50
to 45; his more conservative nested FV remained 45. The correction therefore has a
real but limited effect rather than remaking the full ranking.

Downstream model-FV builds now record the exact arrival model ID and both input-file
hashes. The local explorer refuses to open if those probabilities are stale or changed.

Verification: 1,464 tests pass. The same four old hash-contract tests remain blocked by
generated research files absent from this checkout; there is no new test failure.

Frozen protocol: `docs/prospect-arrival-official-debut-correction-plan.md`.
