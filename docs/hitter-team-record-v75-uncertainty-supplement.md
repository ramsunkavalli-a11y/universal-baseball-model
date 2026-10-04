# Checking shared team context in the record comparison

2026-10-03, while the fixed fits are running and before scoring. Keep the
original player-clustered intervals and all original comparisons. No training,
features, targets, membership, clipping, model settings or forecasts change.

Team record is shared by many prospects within an organization and season.
A player-only resample does not represent shared organization-year errors.
As a supplementary descriptive check, use 1,000 crossed resamples of player
identities and organization-year identities, independently drawing each
cluster set with replacement and multiplying their row weights. Average loss
within each target year, then equally across years, just as in the primary
score. Unknown affiliation forms an explicit unknown group for that year.
Use seed 75 and retain the original nominal player interval separately.

Report paired PA and delivered-value MSE differences for record versus coverage
control and record versus current, on all never-debut forecasts and known-record
never-debut forecasts. Show every origin and organization-year contribution,
including positive and negative changes. These are development sensitivity
intervals, not a calibrated causal test, fresh holdout or cure for having only
seven evaluation years. Use concentration and player evidence to interpret
the result, not to find a subgroup to promote after seeing the scores.
