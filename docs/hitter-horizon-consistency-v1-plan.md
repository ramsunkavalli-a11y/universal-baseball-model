# Hitter Year-1 / Year-2 consistency test

Frozen before new fits, 2026-09-22. Trigger: only 2 of the current top 50 Year-1
hitters improve in Year 2. This is a diagnostic trigger, not a requirement to
make more players improve. Historical results have already been exposed.

## Questions and fixed comparisons

1. Does the displayed drop remain when both years use the same 77-feature Ridge
   family (alpha 20, existing imputation/scaling), each with its mature labels?
2. Does it remain if both Ridge horizons use exactly the same training rows,
   requiring both labels known at the cutoff? This separates model-family and
   training-vintage differences from learned horizon effects.
3. Does extending the fixed existing five-member rich Year-1 recipe to Year 2
   improve actual Year-2 production and high-value/young-player calibration?

Ridge comparisons are diagnostic only: making Year 1 weaker is not an improvement.
The only promotion candidate is the unchanged five-member recipe refit to Year-2
targets: direct LightGBM, LightGBM activity x PA x conditional rate, XGBoost
activity x conditional total value, EBM activity x conditional total value, and
Ridge activity x conditional total value. Equal weights, existing balanced settings,
seeds 417 and existing member offsets, four threads. No new tuning, blends, floors,
monotonic age constraints, or forced rise from Year 1 to Year 2.

Reference: delivered Year 1 + D1 Year 2, with v2 opportunity held fixed. Candidate
replaces Year 2 only; Year 3, Year 1, probabilities, PA and unavailable ranges remain
unchanged. Target is the same MLB batting-plus-replacement calendar value, not WAR
per PA, conditional talent, or full WAR. Train from the same cutoff snapshot, not
next year's features. Replace ALL outcome fields when adapting the rich recipe.

## Timing, support and evaluation

Use the fixed aggregate panel cohorts at origins 2016, 2017, 2018, 2019, 2021,
2022, plus 2023 (Year-2 outcomes through 2025). The 2023 fold extends evaluation;
it is development evidence, not a designated untouched holdout. At least two rich
training origins with origin+2<=cutoff are required. Missing rich scoring rows or
insufficient training origins retain D1. Record support, rather than pretending
fallback rows tested the rich model. Current scoring uses 2025 inputs only.

Ridge diagnostics use all mature aggregate rows. The rich recipe uses all mature
rich-panel rows with matched certified targets. Preserve original target conventions,
including actual shortened 2020 production. Report nonpandemic sensitivity excluding
forecast windows crossing 2020. No 2026 outcomes, current injuries or transactions.

Evaluate annual MSE/RMSE, MAE, signed bias and change from Year 1 to Year 2, with
equal origin weights. Fixed groups: stage; current MLB age <26, 26-29 and >=30;
top 50 by REFERENCE Year-1 prediction within each origin; young (<26) players in
that top 50. Keep those memberships identical across candidates, never use future
performance to define a high-value group. Report actual value changes separately
from prediction changes. A selected high Year-1 forecast is not an unbiased sample
for interpreting regression toward the mean.

## Promotion gate (all required)

- At least three eligible rich outer origins and 100 changed rows per such origin.
- Favorable paired player-cluster 95% interval for equal-origin Year-2 MSE versus
  delivered D1 across the full fixed cohorts (1,000 draws, seed 417).
- Year-2 MSE improves in a majority of eligible origins, and in the pooled
  equal-origin nonpandemic sensitivity. MAE must not worsen overall.
- In each supported fixed group (>=100 rows over >=3 origins), Year-2 MSE cannot
  worsen >5% and absolute bias cannot worsen >0.10 value units.
- On the six original fully mature three-year cohorts, cumulative MSE cannot worsen
  >5%, overall or in those supported groups. Year 1 and Year 3 must remain exact.

No choosing a best-looking ensemble member after scoring. If the candidate fails,
leave the explorer unchanged, commit diagnostic findings and identify the next
specific issue. Even a passing result is provisional development evidence.

## Audit and delivery

Save source/code hashes, all per-player predictions, support and subgroup/fold
scores. Tests must prove outcome maturity, complete target replacement, stable ID
alignment, and zero changes to protected forecasts. Preserve v1/v2 packages.
Record whether any evidence actually supports systematic young-star decline;
do not equate lower Year-2 projections with proven aging or talent loss.
