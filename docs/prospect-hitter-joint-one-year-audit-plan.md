# Prospect hitter joint one-year audit plan

Status: preregistered before scoring.

## Question

Using only evidence available through 2024, how well does the deployed prospect
framework predict 2025 MLB batting-plus-replacement WAR for the full pre-MLB hitter
pool?

This is a diagnostic of the joint result. It does not retune arrival, workload, skill,
or position separately.

## Fixed construction

- Fit the already-selected two-year arrival and ordered role models on the production
  training origins: 2018, 2021, 2022, and 2023.
- Convert each two-year probability to its implied first-year constant hazard.
- Use historical first-MLB-season workload means for the existing fringe,
  meaningful-only, and established tiers, restricted to paths observable by the 2024
  cutoff.
- Rebuild translated hitter batting-plus-replacement WAR rates using only affiliated
  and MLB evidence through 2024.
- Score every eligible 2024 pre-MLB hitter against 2025 MLB output; retain zeros for
  every non-arrival.

## Required reporting

Report mean prediction, observed mean, bias, MAE, and RMSE for:

1. all eligible hitters;
2. hitters with at least 80% implied two-year arrival probability and below-average
   translated batting runs; and
3. all hitters who actually reached MLB, to expose a zero-leaning model that improves
   averages by missing the positive tail.

No public rank, FV, organization, or current 2026 result may enter the calculation.
This audit can identify the next candidate but cannot promote one.

