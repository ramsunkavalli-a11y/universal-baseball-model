# Overseas hitting translation improves but remains a component candidate

2026-10-04. Borrowing how strongly skills carry forward from a much larger MLB
sample preserves overseas contact and power differences better than the earlier
small-sample affine adjustment. The fixed comparison improves, including when
small MLB samples receive less influence. It still makes consequential mistakes.
Retain this as an input for the planned complete hitter comparison, not an
approved replacement for the current hitting forecast.

## What changed

The [sealed contract](hitter-foreign-borrowed-stability-contract.md) separates two
questions. Domestic MLB history estimates component persistence; the same
twenty-seven qualified overseas movers estimate the additional Japan/Korea
adjustments. All histories, targets, references, role qualifications, penalties,
fold exclusions and source profiles remain matched to the
[repaired affine comparison](hitter-foreign-component-history-repair-result.md).
No tuning followed these player results.

Domestic calibration contains 5,802 consecutive season pairs from 1,480 people
through 2024. Every historical fit uses only completed targets available at its
cutoff and excludes the evaluation player folds. The domestic sample cannot
certify transportability to overseas professionals. The foreign adjustments
still rely on very few movers, and neither arm has qualified park exposure.

Independent reconstruction checks all 1,680 domestic component optima, 3,360
foreign offsets and 3,205 profiles. The combined model/scoring suite passes
18 focused tests; the original arithmetic review passed 15 before the three
uncertainty regressions were added. All 31 protected files remain verified.
Execution checks do not establish full model quality.

## Exact comparison and uncertainty

The source cohort retains 253 original forecasts, including 225 with no next-year
MLB batting. Those 225 have unobserved MLB hitting rates, not zero hitting talent.
The ledger has 251 dated hitter hints and two mixed/conflicting role hints;
these are not new eligibility approvals. Conditional scores cover the same
28 active seasons, 20 people and 7,776 MLB PA in both arms. All active profiles
are supported by at least one league mover. Across the entire profile cache,
67 unsupported profiles remain explicitly missing.

The primary score averages per-PA eight-outcome log loss equally within each
origin and then equally across the seven origins. Lower is better. This tests
the foreign-only component against the repaired affine component, NOT against
the current complete UBM forecast, Steamer or ZiPS.

| Metric | Repaired affine | Borrowed stability |
| --- | ---: | ---: |
| Primary log loss | 1.475512 | 1.465249 |
| Multiclass Brier | 0.707206 | 0.703270 |
| K rate RMSE in percentage points | 10.47 | 9.33 |
| HR rate RMSE in percentage points | 2.10 | 1.78 |
| PA weighted log loss within origins | 1.515912 | 1.507046 |

Each origin's primary loss improves; the effect is largest in 2018 and smallest
in 2021. Brier slightly worsens in 2021 and HR RMSE worsens in 2022, so it is
not a win in every metric/group. The primary log-loss difference is -0.010263,
with corrected nominal player-cluster 95% interval [-0.016200, -0.003401].
Brier difference is -0.003936, interval [-0.006332, -0.000959]. These intervals
do not cover shared season shocks, overseas selection or repeated development.

An uncertainty-reporting defect was corrected under the
[scoring amendment](hitter-foreign-borrowed-stability-scoring-amendment.md).
The original bootstrap rebuilt origin weights from the sampled people. The
corrected procedure retains original observation weights and checks all 2,000
draws independently through both row-level and player-aggregate calculations.
Original intervals are preserved; no fit or point score changed.

The declared future-100-PA diagnostic retains 19 seasons, 14 people and 7,387 PA.
Log loss improves 1.506775 to 1.500027; K RMSE improves 6.16 to 5.63 percentage
points and HR RMSE 1.66 to 1.34. This outcome-conditioned diagnostic cannot
replace the primary cohort, but shows the gain is not solely Adduci's five PA.

## What the player review found

The [complete player review](hitter-foreign-borrowed-stability-player-review.md)
keeps all fourteen fixed cases, the rule-selected ordinary/unresolved controls
and five score-selected categories covering four further player-origins.
It traces dated counts, actual inputs, coefficients, translated probabilities,
MLB observations, existing forecasts and outcome-blind comparisons.

Lee's debut K estimate moves from 21.28% to 12.95% against 8.23% observed.
Ohtani's moves from 21.84% to 26.62% against 27.79%; his power estimate improves
but remains much too low. These are less compressed fingerprints, not proof
that superstar value was identified.

Suzuki's debut K moves in the wrong direction, from 21.62% to 18.32% against
24.66% observed. Hyeseong's moves from 20.82% to 18.70% against 30.59%.
Ha-Seong's debut contact also worsens. One universal Korean or Japanese contact
correction would not solve these opposing errors. Sparse selected movers and
MLB adaptation are limitations, not established explanations for each miss.

Adduci's largest score improvement comes against three strikeouts in just five
PA. His more recent 278 MLB PA were intentionally outside this foreign-only
component. Yoshida's ordinary 2025 case improves K, but worsens BB and HR and
barely changes overall loss. His 1,001 intervening MLB PA must not be displaced
by older Japanese production. Henry Ramos is the largest harm; Gurriel remains
too high in K despite improvement and an already available low-K MLB debut.

## Disposition and remaining full model work

Execution and arithmetic review are complete. Predictive evidence favors this
component over the failed affine construction within the small observed cohort.
Baseball review is mixed, and population/foreign-park/transport limitations
remain. Retain the estimate alongside raw league-relative counts and exposure
for one coherent complete hitter comparison. Do not approve it as a standalone
replacement or tune another translation to these names.

The next work is the already specified integration: reconcile ordered employment
evidence and known finite absence, qualify additional hitters with their actual
domestic histories, then contrast fixed original and separately reported added
cohorts. Actual MLB evidence must increasingly dominate older overseas evidence.
Compare PA, conditional hitting and season-relative delivered value with the
existing anchor and matched public systems; inspect totals and consequential
player paths. The unresolved public workload gap is not excused by this score.

No new full hitter forecasts, playing-time estimates, eligibility or explorer
were created. Protected 2026 outcomes and frozen forecasts remain unchanged.
The broad practical hitter goal is not achieved.

Public bounded receipts are in `reports/model-evidence/foreign-borrowed-stability`.
Complete count/fit/profile traces remain in the private generated evidence,
including `review-supplement.json` and the corrected interval artifact. Bulk
provider tables are not published.
