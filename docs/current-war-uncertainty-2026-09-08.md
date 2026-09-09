# Current multi-year WAR uncertainty — 2026-09-08

**Status:** Phase 1 reference ranges connected; historical coverage calibration remains Phase 2

The 2027–2032 hitter and pitcher paths now carry a consistent uncertainty calculation.
It reuses the earlier Player Value v1 separation of opportunity and performance risk,
but extends the calculation to pitchers, prospects and all six future seasons.

## Method

Opportunity uncertainty comes from the same pre-cutoff cohorts used for the point
forecast: 74,743 hitter rows and 90,727 pitcher rows. Each age/level/role cell now
retains the observed positive-workload variance and shrinks its second moment through
the same hierarchy and prior strength used for mean PA or BF. Non-arrival remains an
explicit zero outcome. No workload is capped.

Performance uncertainty uses the coherent hitter or pitcher event probabilities.
Finite-season event variation and posterior rate uncertainty are calculated from the
declared regression strength and each player's effective evidence. Opportunity and
performance variances are added. Hitter and pitcher variances are also added for the
22 valid two-way players; their means still add exactly.

The output reports a symmetric central 80% normal-moment reference range around the
unchanged point estimate. This is a useful contract-value sensitivity, not a claim of
80% out-of-time coverage and not a simulated correlated career path. Endpoints are not
clipped, so downside can be negative.

## Result

- 55,164 whole-player seasons and all 9,194 players receive a range.
- All 50,100 future control/economics rows now carry lower and upper WAR inputs.
- Whole-player projected WAR remains 4,118.80 across six seasons.
- Median annual range width is 0.51 WAR; the 90th percentile is 1.55 and the maximum
  is 7.01 WAR.
- Opportunity supplies 56.2% of aggregate modeled variance. This confirms that
  arrival and workload uncertainty is at least as important as rate precision.
- The top two-way mean is 4.11 WAR in 2027, with a 0.60 to 7.61 reference range; this
  reconciles the previously separate hitter and pitcher maxima.

## Boundary

Phase 1 does not model cross-season correlation, two-way component covariance,
independent baserunning or future-position error, detailed pitcher contact outcomes,
future injury timing beyond historical opportunity attrition, or source revision.
The economics engine continues to call these sensitivity bounds, not probabilities.
A Phase 2 replay should test empirical coverage and build correlated career paths
before probability-weighted option exercise is published.
