# Next experiment: isolate the batting-value connection

2026-09-25. **Specified, not executed or selected.** One fixed diagnostic
experiment, not another learner tournament. Governed by the
[decision standard](model-decision-standard.md) and motivated by the
[audit](model-decision-audit-2026-09-25.md). No live update authorized by its scores.

## Question and competing explanations

Does the improved H workload help delivered batting value when connected to
the strongest archived rate reference? If not, is the old failure chiefly the
workload allocation, rate block, inherited batting residual, or their interaction?

These are different explanations. Current E versus N comparisons hold PA and
nonbatting fixed but change both batting rate and accounting. Repeating that
comparison would not answer the question.

## Fixed inputs and eight accounting cells

Use the archived matched integration rows and labels; do not refit or tune.
For each player/origin/horizon retain B batting `b`, B PA `w0`:

| Factor | Choice 1 | Choice 2 |
|---|---|---|
| Workload `w` | Existing E expected PA | Fixed H expected PA |
| Rate `r` | Independent H1 `performance_anchor`, carried across horizons | Existing horizon-specific `rate` |
| Assembly | Product `w*r/600` | Marginal `b+(w-w0)*r/600` |

The full crossing has eight cells. Existing N is E/anchor/product; existing H
is H/horizon-rate/marginal. Existing common E is E/horizon-rate/marginal.
Five other cells have not been scored in this audit. Keep all eight, not only
the best-looking ones. No clipping or zero caps beyond the already archived inputs.

At fixed rate and workload, marginal minus product equals
`b - w0*r/600`. This inherited residual is independent of the new workload.
That identity isolates an otherwise hidden source of disagreement. It can
retain a nonzero value at zero new PA; check and describe this without treating
negative expected batting outcomes as automatically invalid.

The two rates are **blocks**, not a clean aging experiment: the anchor uses an
H1 LightGBM fit carried forward, seed 417, mature active rows including available
pandemic-crossing targets; the other uses horizon-specific LightGBM fits, seed
427, and the six-year maturity mask excluding pandemic-crossing paths. Both
use PA-weighted rate targets and existing [-5,10] clipping. Do not attribute
their difference solely to forecasting horizon, aging, or one seed. That would
require a later matched refit only if this diagnostic justifies it.

## One primary contrast

**H/anchor/product minus E/anchor/product (N), on three-year cumulative
batting-plus-replacement MSE.** Equal-origin average of per-origin mean squared
errors, same starting players including zeros. Display RMSE alongside MSE
differences; favorable sign is negative. This isolates workload at the stronger
existing rate/construction and directly answers whether the PA improvement
transfers there. It does not measure full WAR or contract value.

Report paired player-history bootstrap 95% interval, 4,000 draws, fixed seed
1729, preserving the same resampled player multiplicities across both arms and
all origins/horizons. Report all three origin effects separately; do not treat
the player bootstrap as uncertainty over new league regimes.

Secondary fixed contrasts, explicitly exploratory:

- Workload contrast at each of the other three rate/assembly combinations.
- Product versus marginal at each of four workload/rate pairs.
- Anchor versus horizon-rate at each of four workload/assembly pairs.
- Difference-of-differences for interactions, with algebraic decomposition of
  squared-error change into the residual's cross term and square term.

No selection of a subgroup, formula, horizon-specific blend or threshold from
these secondary contrasts. Do not declare the minimum-RMSE cell "the winner."

## Population, support and reporting

Input: `model_artifacts/hitter-integrated-opportunity-value-v1-2026-09-25/`
`predictions.parquet`, existing cumulative table and score report;
`hitter-anchored-development-v1-2026-09-22/historical-anchors.parquet` joined
many-to-one on origin/player. Verify all archive hashes and rate cutoffs first.
Missing join keys fail; never fill with current forecasts or later outcomes.

Annual folds: H1 origins 2016/17/18/21/22; H2 2016/17/21/22;
H3 2016/21/22. 52,181 annual rows and 12,891 complete cumulative player-origin
rows. Preserve the existing exclusion policy. No 2026 outcomes. Annual forecasts
and cumulative sums must recompose; original three cells reproduce archives
within numerical tolerance before any new score is calculated.

Primary population is all matched players. Mandatory diagnostic views: prospect,
prior MLB, remaining, lower/upper minors, age and previous MLB workload bands;
all established cutoffs come from the integration/cohort-audit definitions.
Report group sizes, unique players, participants, per-origin errors, signed
bias and predicted/actual totals. Include annual Years 1–3 and cumulative;
include 2021 separately and an explicitly secondary without-2021 sensitivity.
Use a fixed top-ten absolute error-change list per origin to inspect actual
player histories; do not add manual overrides.

Also report the expanded-ledger score as secondary on its exact 8,308 complete rows
from 2021/22. Use the existing safe nonbatting recipe for each workload: rate
heads respond to PA, direct totals stay fixed, neutral stays zero. Within a
fixed workload every rate/assembly cell must have identical nonbatting totals.
Between workloads, call out the induced nonbatting rate-head change separately.
Do not substitute expanded-target RMSE for the primary batting result.

## Interpretation rules and stop conditions

- Favorable primary interval plus consistent magnitude across origins: workload
  has credible development evidence of transfer **under this rate/assembly**.
  Candidate for further integration, not permission to overwrite the display.
- Primary interval spans zero or conflicts materially by origin: transfer
  unresolved. Report effect sizes; do not rescue with a favorable secondary cell.
- Adverse primary result: PA MSE improvement did not transfer here. Inspect
  whether errors moved onto higher-value PA before concluding the workload is
  generally worse. No new rate fitting within this experiment.
- Product/marginal gap at fixed `w,r`: evidence about the inherited residual's
  usefulness. A rate-block gap at fixed `w,assembly`: evidence about those
  archived rates as fitted, not pure aging or universal independence.
- Benefits depend on the other factor: report interaction; no universal claim
  that "products win" or "the PA head failed."
- Broken replay/cutoff/accounting: stop as an invalid experiment, not a negative
  baseball result. Preserve inputs and write a concrete diagnosis.

There is no deployment gate or newly invented acceptable-harm threshold here.
This is identification on already exposed history. The output is a single
explanation-backed recommendation or a finding that the cause remains uncertain.
Any subsequent deployment contract needs justified practical loss margins,
component/exposure consistency, joint-probability limits and new validation.

No learned calibration is required for these contrasts. If a later learned
reconciler is justified, audit nested predictions again: older 2012–2015 states
do not contain the same E/F/D recipes, and the earliest 2016 common test has no
earlier same-recipe complete prediction folds. Do not fit on the evaluated
outcomes or invent earlier support. Stop after this report; do not automatically
launch a replacement learner, career simulation or engine search.
