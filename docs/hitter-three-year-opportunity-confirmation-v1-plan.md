# Three-year playing time, prospects and delivered value

Predeclared 2026-09-22, before this experiment's scores. Follow-up to the
[role/workload screen](hitter-role-workload-v1-result.md). This is a development
confirmation on exposed historical seasons, not an independent holdout. Preserve
every original 2026 forecast and the delivered v2 report; never read 2026 outcomes.

## Questions and scope

1. Does the fixed base LightGBM hurdle work for each of Years 1–3, not just Year 1?
2. Does it assign increasing future opportunity to minor leaguers appropriately,
   including those who never arrive, and distinguish newcomers from MLB returners?
3. Does improved PA transfer to the value means the current report actually delivers?

Current delivered multi-year means are batting plus replacement, not full WAR.
They are independently modeled (rich Year 1, selected Ridge later years), not the
product of the separately displayed PA and a hitting rate. Test that real reference;
do not manufacture a talent rate by dividing value by PA. Position, running and
defense are outside this multi-year target and must not be claimed improved.

## Fixed population, timing and benchmarks

Use the identical official-snapshot panel for origins 2016–19, 2021–22, all three
horizons, including every zero-outcome player. Latest target is 2025. Use the same
77 predictors and identical training rows for candidate and harmonized ensemble.
Each fit requires origin+horizon <= forecast cutoff and excludes training windows
crossing 2020. Cutoff is reconstructed year-end; roster facts are the existing
certified within-origin snapshots. Never substitute future teams or later rosters.

Candidate: unchanged balanced LightGBM participation plus positive-PA regression,
seed 417, conditional PA clipped 1–750, as in the preceding screen. No role additions,
workload bins, tuning or new blend weights.

Mandatory comparators:

- Exact accepted multi-year universal PA plus established-player probability update.
- Harmonized old ensemble recipe: direct LightGBM plus LightGBM/XGBoost/EBM/Ridge
  hurdle forecasts, equal fifths as previously selected; probability is the mean
  of the four classifiers. Refit on the SAME 77-feature rows and mature targets.
  Retain its historical conditional clipping 0–750 and direct seed 427. This is an
  architecture comparison, not a claim to reproduce the old high-dimensional panel.
- Saved old high-dimensional roster ensemble, Year 1 only on the exact overlap,
  labeled non-harmonized context. Do not compare pooled errors across populations.

Cache fitted outputs by source/code/plan fingerprint. Verify candidate Years 1–2
reproduce the earlier screen on matched keys. Models never receive player IDs.
Cold-start diagnostic: origin 2022, all three horizons, exclude every evaluation
player ID from both models' training history. Score PA/probability only; do not
pretend the separately fitted value anchor is player-disjoint.

## Prospect checks, declared before results

Use cutoff-known stage, age and official debut dates <= origin to define:
upper minors, lower minors, current MLB, MLB age 30+, top-50 forecast stars,
young stars, no-prior-MLB minor leaguers, minor-league MLB returners, and players
whose MLB debut occurred in the origin or previous year. Debut table through 2025
is used only to identify already-occurred debuts; later dates or missing rows are
not predictors. Verify consistency with observed historical MLB PA; explicitly
describe any coverage limits instead of silently declaring missing evidence a debut.

Report annual PA, annual MLB probability, actual/proposed three-year PA totals and
growth from Year 1 to Years 2 and 3 for the entire starting prospect cohort.
Zeroes and non-arrivals stay in all primary scoring. Report calibration separately
by level and age (<23, 23+) and for each origin, not just pooled all-player RMSE.

Auxiliary arrival-by-horizon model: fixed LightGBM classifier with the same features
and mature training rows, target ANY MLB PA in the next h seasons. For h=1 reuse
candidate annual activity. Project its three probabilities with cumulative maximum
to enforce nondecreasing arrival-by-deadline probabilities; save raw values too.
This does not change annual activity or workload predictions. Score Brier/log loss
on no-prior-MLB minor leaguers. Annual activity is NOT cumulative arrival probability.
Do not sum annual probabilities or claim independent annual events.

Actual first-arrival timing and subsequent workload can also be summarized to
explain misses, but groups selected by future arrival are descriptive only and
cannot pass an adoption gate. The prospect-growth test is on the full cutoff cohort.

## Transfer to delivered value

Keep the previously independently fitted, origin-safe performance anchor fixed.
For every horizon compare:

- V0: the exact delivered historical direct-value recipe.
- V1: candidate expected PA * performance anchor / 600 (full replacement).
- Vcontrol: accepted expected PA * the same anchor / 600, to isolate PA's contribution.
- V2: V0 + beta * (candidate PA - accepted PA) * anchor / 600.

V2 is a small empirical reconciliation, not a joint career simulation. For each
horizon/cutoff, estimate beta from prior out-of-time rows whose horizon targets have
matured, excluding pandemic-crossing calibration rows; weight each origin equally.
Use a zero-intercept squared-error slope, shrink by n/(n+100), clip to [0,1].
Require >=2 earlier origins and >=300 rows, otherwise beta=0. No target-year
calibration, no choosing weights from the final scored sample, no manual uplift.
Generate chronological OOS calibration starting with the six declared origins;
early unsupported beta=0 is a declared fallback, not an exclusion from scoring.

Test each annual value and the sum of three predictions against observed annual
and cumulative batting/replacement value. Never add annual uncertainty bounds.
Report V2's calibration support and fallback count; it must add value beyond V0,
not only beat a poor product model.

## Scoring, guards and decision

Equal-origin MSE/RMSE, MAE, bias, probability Brier/log loss; 1,000 paired whole-player
bootstrap draws (conditional on seasons and fits). Normal windows primary; retain
all pandemic-crossing results separately. Year-3 normal support is only origins
2016, 2021, 2022; disclose dependence and limited era coverage. No multiplicity-
adjusted certainty is claimed. Existing data/model selection is exposed development.

PA confirmation requires favorable paired PA-MSE interval versus accepted PA in
each normal horizon, majority improving origins, no worse MAE, no point reversal
against the harmonized ensemble, and <=5% MSE worsening for supported predeclared
groups (>=100 rows and >=3 origins). Probability scores and calibration are reported
separately and must not worsen by >5% for supported prospect cohorts. Young-star
smaller cells remain visible but cannot establish confirmation. Cold-start and
non-harmonized comparisons are separate stress/context evidence.

Value recommendation requires a favorable cumulative value-MSE interval versus V0,
majority improving normal origins, non-worse cumulative MAE, <=5% annual/subgroup
MSE worsening, and no prospect cumulative-value reversal. Evaluate V1 and V2 as
predeclared alternatives, with V0 retained if neither qualifies. Passing this
screen authorizes a recommendation, not silent rewriting of frozen forecasts.

Deliver auditable code/tests, keyed historical predictions, cohort/growth/arrival
tables, source hashes, plain-language result, updated direction, and milestone
commit/push. No unsafe historical FanGraphs workload fields or contract proxies.
