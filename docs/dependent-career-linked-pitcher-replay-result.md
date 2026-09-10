# Linked pitcher path replay

Status: **development replay complete; not promoted**.

The replay fits the hurdle on the 2018 snapshot, forecasts every eligible 2021
pre-MLB pitcher, uses only six-year career paths complete by the 2021 cutoff, and
scores actual 2022-2025 MLB component WAR. Non-arrivals remain zero.

| Players | Observed mean WAR | Incumbent predicted | Linked predicted | Incumbent RMSE | Linked RMSE | Arrival-only RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3,642 | 0.090 | 0.042 | 0.095 | 0.560 | 0.552 | 0.552 | 0.577 |

Applying the direct-evidence cap to the same linked path predicts
0.051 mean WAR with
0.554 RMSE and 0.143 MAE.

The linked construction is directionally coherent and its broad scale is plausible in
this replay: predicted mean WAR is close to observed and it beats predicting zero.
The tiered path changes MSE versus an arrival-only pooled path by
+0.000054, with a 95% interval of
[-0.006657, +0.006122]. This cohort and hurdle have already
been used in development, so this is not fresh confirmation. No current player value
or rank changes.

The simpler arrival-only path changes MSE versus zero by
-0.028084, with a 95% interval of
[-0.047617, -0.009532].

Against the cutoff-reconstructed incumbent, the arrival-only path changes MSE by
-0.008490, with a 95% interval of
[-0.021237, +0.002733]. The incumbent
uses only information available through 2021, including level translations fit on
2018 and 2021, the deployed 800-BF regression, and Tango component aging.

The common-cohort guardrail also shows that the small RMSE gain is not a broad error
gain under absolute error: MAE worsens from 0.150 to
0.197. MAE targets the cohort median, which is zero here, so
it is descriptive and no longer a promotion veto for expected WAR.

The complete zero-plus-positive-path distribution scores
0.103 CRPS versus
0.150 for the incumbent
point mass. Candidate-minus-incumbent is
-0.046155 with a 95%
interval of [-0.049678,
-0.042368]. This is the
right zero-inclusive distribution diagnostic, but the cohort is not fresh and the
incumbent does not yet have its own uncertainty distribution.

This tradeoff persists at every tested prefix from one through four years: candidate
MAE is worse at all four horizons, and no horizon has a reliably favorable paired MSE
interval. The failure is not caused only by extending two-year odds to four years.

Fixed 25%, 50%, and 75% linked blends remain exposed-cohort sensitivities, not promotion
candidates. The linked path remains unpromoted pending a proper common-distribution
comparison and fresh confirmation.
