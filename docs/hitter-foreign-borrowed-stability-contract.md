# Borrow domestic skill stability for overseas hitting inputs

2026-10-04. The completed affine and matched-history reviews found excessive
compression of contact and power. Test one substantive alternative: estimate
component persistence from the larger domestic history, then estimate an
overseas adjustment with that persistence fixed. Preserve both prior versions.
No algorithm or penalty sweep, named correction or forecast deployment.

## Target and population

The target remains a next-season eight-event MLB distribution conditional on
observed MLB batting, not arrivals, playing time, true league strength, full
WAR or trade value. Use the same complete references, coherent centered
log-ratio coordinates, smoothing, three-year 5/4/3 recency pool and 641 overseas
source origins across five outer folds. Keep all 3,205 profiles and sparse or
missing cases. No protected 2026 data or current explorer changes.

Domestic calibration uses completed consecutive MLB seasons from the reconciled
2008–2024 stints, at least 30 PA in the source and target season, and a recorded
hitter or mixed hitter/pitcher role in the source season. Unknown and recorded
pitcher-only sources do not become certified hitter calibration observations.
Report that coverage limit. Exclude a pair whose source or target year is 2020
from primary domestic calibration; actual 2020 batting may remain in an older
history lag. This is production per PA, not an invented full-season workload.
Use a three-year source history exactly as in the repaired overseas mapping.

The foreign adjustment uses the same qualified 27 forward-mover people,
chronology, source histories, target counts, weights and role evidence as the
matched-history experiment. Preserve the valid overseas 2020 to MLB 2021 pairs.
Reverse moves and AAA bridges remain separate, not automatic extra support.

## Locked estimation

For each event, fit target CLR deviation from the target MLB reference on an
intercept and source CLR deviation from a matched domestic source reference.
Use ridge penalty 2 on both coefficients and bound the slope between zero and
two, as before. Each pair weight is harmonic source/target PA divided by 300,
capped at one, divided by that person's eligible pair count in the actual cell.
No held person's observations enter calibration or identified references.

Call the fitted intercept a and slope b. For each overseas league estimate
the regularized adjustment d = sum(w * (target - a - b * source)) /
(sum(w) + 2). The prediction is a + d + b * source, re-centered and combined
with the origin MLB reference through the same softmax. Do not estimate b from
the tiny overseas sample again, add a second shrinkage blend, fabricate AAA PA,
or change penalty after looking at the player results.

This is a transfer assumption, not a established fact: stability of the
normalized skill in MLB might not transport overseas. Different competition,
selection, age and adaptation can invalidate it. Record actual domestic support
by source age, workload, K and HR profiles and its ranges, separately from the
foreign mover people. Thousands of domestic players cannot certify the foreign
offset or eliminate missing qualified park exposure. Retain all warnings.

Every input row uses its own origin. Exclude the outer evaluation player fold
and the row's own fold for training rows, as in the preceding component cache.
Preflight every actual cell before fitting. Source histories cannot use a year
after the source origin; target seasons must be completed by the fitting cutoff.
No qualifying league mover means an unsupported translation, not average talent.

## Comparison and player checks

Before any whole-model fits, compare against the repaired affine mapping on
identical profiles. Score the original saved forecasts with foreign histories
as a fixed source cohort: future MLB appearances stay in coverage/arrival totals,
but their conditional hitting rate is unobserved when future PA is zero. Do not
invent a hitting outcome for those zeros or remove them from the cohort ledger.
Report source-role hints and unresolved/pitcher cases separately rather than
quietly changing eligibility after a win.

For rows with observed future MLB PA and both supported component profiles,
primary component score is per-PA multinomial log loss, averaged equally across
players within origin and then equally across origins. Report proper multiclass
Brier and K/HR rate RMSE, and PA-weighted sensitivity. These are conditional
component diagnostics, not full model or Steamer benchmark wins. Pair player
bootstrap differences with 2,000 resamples, seed 84; development exposure and
shared-season uncertainty remain qualifications. Report every origin and totals.

Keep the same fourteen source/context player cases, including absent forecasts,
Thames's non-arrival and shortened 2020 control. Add the largest improvement,
largest deterioration, false highs/lows and an ordinary case from the fixed
component scoring cohort. Retain actual counts, reference, coefficients,
adjustment, support, output probabilities and source-only peers. Review before
disposition. A luckier aggregate loss cannot justify erasing a baseball failure.

## Relation to the full hitter goal

If useful, carry this component and the uncompressed raw production/exposure
into the existing foreign/status integration. Still qualify ordered employment
and finite absence, preserve original rows, supply real domestic histories for
additions, fit a fixed end-to-end contrast, and compare playing time, hitting
and season-relative delivered value with existing anchors and public systems.
This checkpoint does not approve a full hitter candidate or waive the benchmark.
