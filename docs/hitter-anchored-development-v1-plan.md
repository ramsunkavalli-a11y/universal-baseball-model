# Anchored hitter performance, development and opportunity

Frozen before new fits, 2026-09-22. A bounded Year-2 experiment, not a new sweep.
Earlier [rate-only development](two-year-talent-development-result.md) is conditional
on later observed play; the [linked hitter replay](dependent-career-linked-hitter-replay-result.md)
underpredicted MLB arrivals. Neither establishes unconditional player value.

## Fixed design

Use the same certified 77-feature aggregate panel and current 3,907-player cohort,
batting-plus-replacement calendar targets, and origins 2016–19, 2021–23 from the
horizon consistency test. No 2026 outcomes or current-season evidence. No floor,
manual youth bonus, player names/IDs as predictors, or requirement to improve.

1. **Performance anchor:** at every historical origin from 2012 onward (excluding
   2020), fit the existing fixed LightGBM regression settings (350 trees, .025 rate,
   15 leaves, depth 5, leaf minimum 60, alpha .25, lambda 4, subsample .85,
   colsample .70, seed 417, four threads) to next-year value per 600 MLB PA among
   active players, using only origin+1<=cutoff labels. Weight by PA / mean PA.
   Clip predictions to the existing practical rate bound [-5,10], record clipping.
   These are forecasts conditional on MLB play, not identified pure/counterfactual
   talent for all minor leaguers. Never obtain an anchor by dividing the displayed
   unconditional mean by a separately estimated opportunity forecast.
2. **Leakage-safe development rows:** each row's anchor is the forecast made at
   that row's own origin, not an in-sample fit made at the later evaluation cutoff.
   All later heads use the identical 77 features plus that anchor and exactly three
   interactions: anchor x centered age, anchor x log current MLB PA, and centered
   age x log current MLB PA. Impute and scale within each fit.
3. **Opportunity:** standardized logistic C=.1, max_iter=2000, seed 417 for any
   Year-2 MLB PA. Standardized PoissonRegressor alpha=1, max_iter=2000 for PA
   conditional on activity. Clip conditional means to [1,750], count clipping.
   These new heads are challengers, not replacements of the accepted v2 odds.
4. **Development:** Ridge alpha=20 predicts Year-2 rate minus the origin's anchor,
   among Year-2 active players, weighting by Year-2 PA / mean PA. Add this estimated
   change to the anchor, clip [-5,10], and combine with the probability and PA heads.
   No assumption that predicted change must be positive for young players.

PA-weighted rate regression targets E(PA x rate | X, active) / E(PA | X, active),
not the unweighted mean rate. Multiplying a well-estimated version by mean PA
accounts for PA/rate dependence in the conditional mean; it does not require
independent PA and performance. This identity is a motivation, not a guarantee
that finite fitted heads reproduce it or define a full joint distribution.
Zero-play rows enter probability/value tests, never receive zero skill labels.

Use only fully mature origin+2<=cutoff rows for all later heads. Training starts
with origin 2012 because earlier anchors lack the declared history. Include actual
2020 MLB outcomes consistently with existing value labels; report nonpandemic
sensitivity excluding crossing windows. The canceled MiLB year remains missing,
not a zero-performance/repeat-level observation.

## Comparisons (no model/weight selection)

- **Reference:** exact delivered D1 Year-2 value and unchanged displayed Year 1/3.
- **A, sole candidate:** anchor + learned rate change, with the two new opportunity
  heads. This is a prior centered on retaining the anchor, not an immutable anchor.
- **C diagnostic:** identical probability/PA, unchanged anchor, no development.
- **D diagnostic:** identical probability/PA/features/weights, Ridge predicts the
  future rate directly. Including anchor as a predictor means A and D have the
  same linear function class but different shrinkage centers. Do not misrepresent
  A as new information or add an extra tuned degree of freedom after scoring.

## Acceptance, before scoring

Year-2 value: favorable paired player-cluster 95% MSE interval versus reference
(1,000 draws, seed 417); majority of seven origins improve; overall MAE not worse;
nonpandemic MSE improves. Same fixed groups as previous test (stage, MLB ages <26,
26–29, >=30, reference Year-1 top 50, young members of those top 50): supported
means >=100 rows across >=3 origins. No >5% group-MSE worsening and no >.10 extra
absolute bias. Three-year MSE must not worsen >5% overall or in supported groups
on the six complete original cohorts, with Year 1 and Year 3 untouched.

To establish the claimed mechanism, A must also beat carry-forward C in paired
unconditional value MSE and improve PA-weighted active-player rate MSE; direct-rate
D is reported but cannot be substituted if A fails. Report probability proper
scores, conditional/unconditional PA errors and rate errors alongside total value.
Do not promote on MAE or a handful of pleasing current examples alone. If any gate
fails, keep the explorer unchanged and close this batch without retuning.

Even if value gates pass, do not publish the new probability/PA heads without
separate comparison to accepted v2 opportunity. Save source hashes, anchor vintages,
per-player decompositions, support, clips and scores in a distinct package. Check
future-label mutation, shuffled ID alignment, original package hashes, no zero-skill
labels for no-play rows, and no hidden transfer of protected outcomes.
