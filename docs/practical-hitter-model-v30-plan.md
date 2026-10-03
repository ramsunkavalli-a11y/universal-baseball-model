# Practical hitter model: finish a useful system, not another endless patch sequence

2026-10-02. New user direction: get the hitter model to a decent, useful place;
revisit important assumptions and earlier negative tests, use common sense,
and try substantively different approaches without excessive micro-testing.
This supersedes the prior *narrow next-experiment* queue, not historical results
or chronology/identity/coverage controls. Protected 2026 stays closed.

## What decent means

An intelligible hitting-rate forecast, expected MLB playing time, delivered
value, and explicit prospect/availability uncertainty. The first milestone is
next-year offense/workload, not a claim of complete defense, trade value or six
years of club control. Older established hitters and never-arrived minors must
eventually be covered; the existing post-debut elapsed-0–5 panel cannot certify
those populations. Do not rename that research slice the full hitter model.

Working next-year benchmark targets, declared before the new fits: on the
matched public sample, PA RMSE within 10% of Steamer and PA MAE within 15%;
delivered batting-value RMSE within 10%. These are practical engineering goals,
not scientific equivalence tests. Require meaningful improvement over the
existing UBM workload error, and show real false highs/lows and cohort totals.
Raw public batting-value conversion has an environment offset and cannot prove
batting-talent superiority. Snapshot-date differences remain qualified.

No automatic rejection because one tiny rare-group relative loss exceeds 2%.
For this new program assess scale, uncertainty, support and systematic harms
together. A major target/source defect or harmful baseball mechanism still
blocks adoption. Keep earlier tests' original gates/results unchanged.

## Coherent sequence

1. **Workload architecture, not another injury-feature tweak.** Existing tests
   mostly optimize participation bins then use class-conditional PA heads.
   Try predicting expected PA directly, with the same historical membership,
   versus that existing architecture. The failed V20 test changed a regular
   conditional head, not this unconditional target. Use simple regression,
   bagged trees and several gradient-tree implementations with the same actual
   origin-known count histories. No target names, repeated parameter sweeps or
   assuming older residual/contact tests settled this different question.
2. **Talent estimate and population coverage.** Carry the strongest defensible
   workload construction into a small matched batting comparison: existing
   outcome/PBP winners, learned coherent cross-level components, and a simple
   recency/shrinkage floor. First establish which prior winner artifacts have
   compatible targets and provenance. Expand established-player/pre-debut
   eligibility with certified source coverage; preserve exits and non-arrivals.
   Do not spend days polishing the same rare status source before doing this.
3. **Integration and useful uncertainty.** Validate joint delivered value,
   arrivals and workload, not only conditional rate. Recent contact/park/opponent
   inputs remain a supported extension, not a mandatory anchor for every model.
   Unknown foreign production and legal availability require flagged scenarios,
   not universal penalties or fabricated zero talent. Use known bonus/pedigree
   where supported, no new college collection. Check Years 2–3 and longer paths
   only where actual mature support exists; do not extrapolate annual wins into
   certified six-year value.
4. **Finish and expose the candidate.** Freeze the best coherent development
   candidate, plain-language model card, comparison table and selected player
   traces. Provide a local research explorer with team filter if useful; do not
   overwrite the frozen 2026 forecast or its deployed explorer. Keep unresolved
   component/valuation limits visible. Milestone updates stay brief and concrete.

## V30 first batch: locked direct-workload comparison

Population: same 4,396 historical next-calendar-year forecasts, 1,476 people,
origins 2016–18 and 2021–24. Anchor V24 and rules-only V29b. Train on complete
2011+ source windows, mature target years <= cutoff, exclude target 2020,
exclude the entire test-player group. All existing evaluation identities stay.
Source-only reconciliation and all actual preflights saved before fits.

Use raw own-player MLB/AAA/AA counts for three history years (PA, K, UBB, HBP,
HR, BABIP, doubles, triples), exposure/missingness and fixed deterministic rate
stabilization; age and observed-window MLB performance/workload. Separate levels:
AAA is not assumed equal to MLB. No learned legacy minor scalar, cross-sectional
priors or saved contact adjustment is silently inherited. Standardization fits
only training data. 2020 schedule-adjusted MLB opportunity and missing MiLB
season are separate; canceled minor samples never become poor performance.

Six predeclared models, no tuning in this batch:

- Standardized ridge, alpha 100.
- Extra Trees: 200 trees, leaf minimum 20, max features 0.7.
- Histogram gradient boosting: 250 iterations, depth 3, leaf minimum 30,
  learning rate 0.05, L2 10, no random validation/early stopping.
- XGBoost: 250 trees, depth 3, rate 0.05, minimum child weight 30, L2 10,
  deterministic full-row/full-feature sampling.
- LightGBM: 250 trees, depth 3/8 leaves, leaf minimum 30, rate 0.05, L2 10,
  deterministic full-row/full-feature sampling.
- CatBoost: 250 iterations, depth 4, rate 0.05, L2 10, no validation-based
  selection, no random bootstrap. Library behavior/version checked locally.

Each learns continuous expected next-year PA directly, equal-origin training
weights, predictions bounded [0,800]. Permanent status rules remain explicit;
unsupported indefinite availability is flagged, not declared solved. Report
how often clipping binds. Do not invent calibrated arrival/regular probabilities
from point regressions; probability/path modeling remains a later integration task.

For this workload-only test retain V24's expected batting yield (value/PA) and
multiply by new PA as a diagnostic. This is a mechanical contrast, **not** a
new joint PA/talent model or a claim that independent means give correct value.
Score next-year PA RMSE/MAE/bias/totals and that fixed-yield delivered value;
show public matched scores, each origin, current PA bands, brief debut, prior
regular/current absence and large-workload players. Keep both gains and harms.

Every arm gets player review before disposition: fixed Steer, Winn, Rooker,
Judge debut/established, Lux, McLain, Tatis, Franco, Marcano and Thames cases;
largest workload gains/losses and ordinary cases. Preserve unsuccessful peers.
Replays/essential invariants suffice; no hundreds of redundant tests or a false
requirement that every noisy group must improve. Select no deployed model from
this workload-only batch. If it exposes a material defect, repair it; if it has
useful evidence, proceed to the talent/population milestone without a new sweep.
