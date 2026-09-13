# Peak pitcher pitch-process result

Last updated: 2026-09-12  
Status: **PROMOTED AS AN OPTIONAL HIGH-MINORS PEAK INPUT**

## Test

The already selected full pitch-call profile was added to the frozen peak component
model with the same ridge strength. It was fitted only on certified 2018–19 and
2021–22 full-season high-minors data. Every scored player was excluded from that fold's
training players, so an earlier observation of the same pitcher could not leak across
the boundary.

The 2019 development origin improved all four scores. Both untouched later origins did
the same:

| Origin | Players | Player log-loss change | Player Brier change |
|---|---:|---:|---:|
| 2021 | 170 | -0.000780 | -0.000418 |
| 2022 | 178 | -0.000120 | -0.000123 |

The 2021 paired uncertainty intervals were entirely below zero. The smaller 2022 gain
had intervals crossing zero. Combined with the stronger three-fold next-year result,
this passes as a selective process layer, not as a new universal baseline.

## Current integration

The production peak model remains the anchor. For a covered current pitcher, only the
ILR component difference between the process model and its results-only model fitted on
the exact same historical cohort is added. This prevents the selected historical
cohort's overall intercept from entering current rankings.

Among 1,083 current supported-age pitchers with certified process evidence, the median
change is +0.06 runs per 800 BF and the mean is +0.14. The 10th/90th percentiles are
-3.35/+3.97 runs. Missing or uncertified evidence produces exactly the prior forecast.

Current outputs also expose `pitch_process_runs_change` plus the four shrunken,
level-season-relative process inputs. This makes a player's movement auditable in the
results explorer without treating raw small-sample rates as true talent.

This materially separates pitchers with similar K/BB/HR results using basic process
logic while staying centered on the established model. It still cannot recover
velocity, movement or arsenal information for lower-minors pitchers.

Model artifact: `model_artifacts/peak-pitcher-process-v1.json`.  
Machine-readable audit: `reports/generated/peak-pitcher-process/report.json`.
