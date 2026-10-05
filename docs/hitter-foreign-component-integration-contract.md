# Foreign professional components for the hitter model

2026-10-04. Continue the practical hitter plan by connecting the reviewed Japan
and Korea histories to future MLB hitting evidence and workload. This contract
locks the component construction before fitting. It does not authorize forecast
deployment or claim that foreign history solves the larger public PA gap.

## What the adjustment estimates

Predict a coherent eight-event MLB batting distribution from overseas batting
history: other PA, strikeout, unintentional walk, hit by pitch, single, double,
triple and home run. These events sum to PA. The fitted adjustment estimates
next-season production among historically observed MLB movers, not an unbiased
intrinsic difference in league strength, arrival probability or full WAR.

Use only qualified consecutive NPB or KBO to MLB hitter pairs, with at least
30 PA on both sides, both seasons completed by the feature origin, and no
domestic 2020 side. An overseas 2020 to normal MLB 2021 pair remains valid.
Preserve all raw pairs and unresolved identities. Reverse moves and AAA bridge
pairs are reported as distinct support, not pooled into the fit: they select
different players, and a domestic same-season adjustment is not automatically
a next-year foreign translation. Selection, aging and first-year adaptation
remain entangled in this conditional predictive target.

## Complete league references

Calculate each league-season reference from every reviewed count row, including
unmapped and low-PA players. An MLBAM crosswalk selects a nonrepresentative part
of NPB and KBO production and must not define the league average. Remove known
people in excluded player folds from the reference. Unmapped people remain;
their unknown crosswalk limits verification of fold separation and is reported.
MLB references use all dated MLB stints in the completed season. Never construct
predictor references from 2025 or protected 2026. Future environments may be
used only to define diagnostic outcome labels, never forecast inputs.

## One fixed small model

For each event, model the target season's centered log-ratio deviation from its
MLB reference using a separate NPB intercept, KBO intercept and a shared slope
on the source player's deviation from his foreign league-season reference.
Use a half-event smoothing count per event to make log ratios finite. Penalize
all three coefficients toward zero with ridge penalty 2. The shared slope is
bounded from zero to two; this is a declared monotonicity and extrapolation
assumption, not a discovered optimum. Report bound hits. No hyperparameter search.

Each mover contributes weight equal to the harmonic mean of source and target
PA divided by 300, capped at one; divide repeated-person weights by that person's
pair count. This prevents repeated seasons or exceptional workloads from
masquerading as many independent people. This is a pragmatic precision weight,
not a correct full multinomial likelihood. Report distinct people and all pair
weights. Fit eight small constrained ridge regressions; re-center their outputs
and use a softmax with the origin MLB reference so probabilities are positive
and sum to one. Do not add a second arbitrary regression-to-mean blend.

Pool the last three observed overseas seasons with fixed recency weights 5, 4,
3 in event-probability space, using each season's complete league reference.
Feed the pool through the origin-local fitted adjustment and use the origin MLB
reference. Keep actual foreign exposure, recency and missing history separately.
Do not fabricate AAA PA or claim that overseas work implies an MLB job.

Every generated input is chronological and cross-fitted. Exclude the outer
evaluation player fold and, for a training row outside that fold, its own fold
as well. References and coefficients respect the same exclusions. With no
qualifying mover in a player's league, return an explicitly unsupported missing
translation, not a certified league-average MLB hitter. Keep the raw history.
Sparse support is a warning, not a reason to delete the forecast or silently
approve a new foreign-specific tree model.

## Required component checkpoint

Before any end-to-end comparison, reconstruct events and references independently,
verify source hashes, future-row and held-player mutation invariants, all fitted
normal equations or constrained optima, exact support and each translated
profile. Save profiles for all 641 reviewed source origins and all five outer
folds, retaining the original population and additions separately.

Walk fixed Ohtani, Suzuki, Yoshida, both Lees/Kims where present, Park and Thames
through raw seasons, complete versus mapped-only references, training people,
coefficients and translated probabilities. Retain the preselected ordinary and
unresolved cases. This input checkpoint does not invent PA predictions or
declare a model win. If scoring a component-only diagnostic, include gains,
harms, non-arrivals and current model rates on identical eligibility; zero PA
does not identify hitting ability. Unsupported cases remain in coverage counts.

## End to end comparison remains required

First reconcile dated event order, finite absence and listing versus contract
evidence under a separate source amendment, with Voit and Tatis as controls and
ordinary exits retained. Reuse prior medical/status evidence without repeating
the failed generic feature sweeps. Do not OR cumulative acquisitions into a
current employment flag or use a named exception.

Then keep the existing 30,506 forecasts and the saved original and context-only
anchors. Compare the same reconciled context without foreign production against
that context with these translated components and real professional exposure
in talent and workload. Newly qualified hitter additions require real prior
domestic histories and dated roles; score them separately. Never fill all
their domestic inputs with zero simply because the old forecast is absent.

The next head contract must seal exact features, settings, nested generated
inputs, training support and additions before fitting. Use the corrected
season-relative labels and unchanged matched Steamer/ZiPS comparisons, with
origin, stage, active and non-arrival totals and player walkthroughs. A small
foreign component sample cannot certify the full cohort, full WAR, long-term
control value or acceptable public workload error. Keep protected 2026 outcomes,
frozen forecasts and deployed explorers unchanged.

## Research informing the construction

[League equivalencies](https://library.fangraphs.com/principles/league-equivalencies/)
distinguish component translation from forecasting and describe environmental
adjustments. [Rosenblum's NPB projection discussion](https://blogs.fangraphs.com/creating-a-projection-for-munetaka-murakami/)
explains why forward and reverse movers imply different adjustments through
selection. The model and penalty above are our bounded development choices,
not coefficients established by those articles. Missing qualified park exposure
means this is not a park-neutral MLE.
