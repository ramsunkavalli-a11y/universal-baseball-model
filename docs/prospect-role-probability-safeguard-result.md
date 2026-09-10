# Prospect role-probability safeguard result

Status: active private-preview safeguard; year-by-year state model remains P0.

The six-year nested hurdle repeated separate two-year conditional hazards three times.
For many players this made the probability of a meaningful or established career much
higher than the model's direct unconditional estimate. That is internally
indefensible: conditioning and horizon conversion were compounding favorable states.

The private preview now caps nested meaningful and established masses at the matching
direct six-year unconditional estimates while preserving
`established <= meaningful <= arrival`. No outside FV, rank, position quota or manual
player floor is used. The safeguard affected 5,528 meaningful and 5,366 established
probabilities across hitters and pitchers.

For pre-MLB hitters, expected six-year WAR fell from 1,671.7 to 711.1; FV 50+ counts
fell from 82 to 9. Among 658 catcher prospects, expected WAR fell from 420.3 to 161.3
and FV 50+ counts from 19 to 2. This shows that the catcher-heavy top end was mainly a
probability-compounding problem, with catcher workload assumptions amplifying it.

Fernando Gonzalez (MLBAM 692232) moved from 4.09 WAR, $24.7M and FV 50 to 1.63 WAR,
$10.1M and FV 45. His six-year role masses are now the direct 19.3% meaningful and
10.3% established estimates instead of 39.2% and 33.8%.

This is a conservative guardrail, not the final solution. The next P0 design must fit
one year-by-year career-state process in which arrival, role progression, workload,
attrition and return are mutually exclusive transitions. It must replace both the
repeated-hazard shortcut and this cap only after rolling-origin validation.

An existing cutoff-safe four-year pitcher diagnostic was extended without changing
its cohort. On 3,642 players, the cap improves meaningful-career Brier from 0.04579 to
0.04234 and log loss from 0.17022 to 0.16087 versus the compounded conditional form.
For established careers, Brier improves slightly from 0.02740 to 0.02701 but log loss
worsens from 0.10860 to 0.11663 because the direct estimate is conservative. This
supports the safeguard against the large compounding error, but not treating it as a
calibrated final transition model.

Machine-readable impact: `docs/prospect-role-probability-cap-impact.json`.
