# Prospect pitcher conditional-quality audit

**Status:** development outer test; no current values changed

This test asks a narrower question than arrival: among pitchers who later earn at
least 200 MLB BF, can cutoff-safe minor-league performance predict their MLB component
quality? Lower values of the target are better pitching. Model form and shrinkage are
chosen only inside the 135-pitcher 2018 development cohort, then scored on
225 pitchers from the 2021 snapshot using 2022-2025 outcomes.

The selected `baseball_interactions` ridge model fails the outer point score. Population-mean RMSE
is 0.20004; candidate RMSE is 0.20116.
The paired candidate-minus-baseline MSE difference is
0.000450, with a 95% player-bootstrap interval
of -0.004236 to 0.004925.

The historical established tier is also checked as a linked outcome rather than an
input feature. Its mean component-rate difference from other meaningful pitchers is
-0.0473, with a 95% interval of
-0.0960 to -0.0009. A negative difference
means the established group pitched better. This descriptive relationship can support
a future joint tier-and-quality path only if it repeats in a later cohort.

Using the earlier cohort's tier relationship to predict the later cohort's quality
fails: it produces RMSE 0.20098 versus 0.20004 for the population mean. Its
paired MSE difference is
0.000376, with a 95% interval of
0.000211 to 0.000548. Realized
future tier is used here only to test dependence inside a latent joint path; it is not
treated as information known on the forecast date. The relationship changed direction
between periods, so the attractive later-cohort tier difference is not promoted.

This conditional test excludes non-arrivals by definition; the separate hurdle audit
retains all failures and zeroes. Hand, origin, age/level, role, workload and performance
families were eligible, while current physical measurements and outside FV were not.
No candidate is promoted if the outer gain is absent, uncertain, or reverses in a
material supported subgroup.
