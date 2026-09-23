# Disrupted-cohort diagnosis: era and schedules

Fixed development experiment, 2026-09-23, before new fits. Earlier 2021 results
are exposed development evidence, not a fresh holdout. No tuning or deployment.

## Questions and fixed arms

1. Does the explicit `reorganization_era` step transmit the unusual first modern
   cohort into the next forecast? Refit R without that one field (E), and the
   already frozen outage augmentation A without that field (AE). Compare E/R
   and AE/A on identical next-year folds 2017, 2018, 2021–2024. These are feature
   ablations, not identification of a causal era effect: other inputs can proxy
   calendar time. Do not remove those proxies after seeing results.
2. Do actual team schedules add information beyond raw PA? Reconstruct completed
   regular-season team games from already captured official schedules for
   2015–2019 and 2021–2024. Join by season, sport and team to annual batting
   stints. Retain actual PA and all original features except the explicit era
   step. Add current-year minor PA schedule coverage, PA divided by each stint's
   full-season team games (summed across stints), and the corresponding PA-weighted
   harmonic schedule length. Require complete stint coverage for the last two.
   They measure schedule-relative workload, NOT days healthy, roster tenure,
   games the player could personally attend, or a promoted player's rest rate.
   Do not multiply all levels by a common factor.

Schedule comparison S0/S1 uses identical training restricted to origin>=2015,
and annual tests 2021–2024. S0 has no schedule features; S1 adds the three.
Earlier schedule coverage is absent locally, so do not let a source-start flag
silently distinguish pre-2015 players from others in this comparison. Historical
lags still use their actual dated available records. S0/S1 use ordinary fitting,
not augmentation, to isolate the schedule addition. Compare with full-history R
as a practical reference, but do not attribute any difference vs R to schedules.

## Controls and scoring

Keep the existing LightGBM recipe, all starting players, label-maturity rules,
player weights, and missing-season exclusion. Recompute identity weights after
the schedule training restriction. No 2026 outcomes, forecast edits, or source
requests are needed. 12 era fits + 8 schedule fits + two future-mutation replays.
Freeze source/code hashes and schedule-feature inputs before fitting. Cache
fold results with hashes. Test future source isolation, duplicate game handling,
cross-sport team keys, partial coverage, and multi-team denominators.

Report prospect Brier/log loss, expected vs observed arrivals by origin,
equal-origin pooled losses, player-cluster paired intervals, upper/lower minors,
and non-prospect safety slices. Emphasize annual results: pooling can conceal
offsetting errors. The intervals do not capture all shared-year uncertainty.

Era hypothesis support requires AE to improve 2022 Brier and log loss vs A
and reduce its count error; show E/R as a separate interaction control. Schedule
predictive evidence requires both paired pooled 95% intervals below zero vs S0,
both scores improving in >=3/4 years, and no >10% score harm in a year or stage
with >=200 players and >=30 events. A broader research candidate additionally
must beat R in both pooled scores and pass its ordinary-year harm guards.
These criteria cannot authorize deployment: only next-year arrival is tested.

Stop after these specified tests. If neither mechanism resolves the failure,
retain the diagnosis and failed results; do not tune to the known arrival count.
Three-year regular status and delivered value remain separate later gates.
