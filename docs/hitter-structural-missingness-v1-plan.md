# Distinguish a source outage from a player's absence

2026-09-23. Sequential development follow-up, specified after the canceled-block
experiment and before these fits. The first experiment improves 2021 arrival
scores by 13–15% and recovers counts 58→93 versus 157, but harms 2022. Historical
outage stress favors omitting unavailable blocks in 4/4 cases. This motivates a
single different mechanism, not selecting the successful 2021 routing post hoc.

## Fixed source-outage augmentation

Keep the original rich feature set and append two source-outage flags. At real
cutoffs these are one only for never-debuted minor leaguers with an absent annual
record in the canceled 2020 slot (lag1 at 2021, lag2 at 2022). No stat is invented;
current evidence, dates and age are unchanged. Actual individual absence remains
distinct from an unavailable source. Flags are fixed by known cancellation, not
observed success.

For each eligible never-debuted training snapshot, retain one original copy and
create two additional copies: one with its lag1 annual stat/PBP inputs hidden,
one with lag2 hidden. Set the corresponding source-outage flag and clear dependent
rate changes when lag1 is hidden. Keep cumulative career evidence in all copies.
Assign 0.50 of the snapshot's original identity weight to the original and 0.25
to each hidden copy. Other players get one original row at full weight. Total
weight per snapshot, identity and class is unchanged. Normalize weights using
the original training-row count, never the augmented count. Targets are repeated,
not changed. This trains robustness to source loss, not a simulated missed season
of physical development. Artificial outages are never added to test players.

A is the primary augmented candidate. T is a duplicate-only control: identical
rows, weights, flags and model settings, but the two extra copies retain their
original inputs and flags. This controls for duplication's possible interaction
with tree fitting. R, the original model, is the mandatory practical control.
No hyperparameter, augmentation-fraction, seed or calibration search. LightGBM
uses the same seed417/settings. Real queries use their real inputs and dated flags.

## Cutoffs, scoring and acceptance

Fit A/T at the six ordinary annual origins 2017,2018,2021–2024 and two ordinary
three-year origins 2021/2022 for arrival and regular workload. All original label
maturity rules, excluded pandemic-crossing training windows, targets and source
panels remain unchanged. Full populations retained. No 2026 outcomes or live edits.

Report equal-origin Brier/log loss, observed/expected counts, each year, upper/
lower and young-advancing slices, and stronger matched references. Paired 2,000
player-cluster intervals are development uncertainty, not season-shock certainty.
For an annual development candidate require: 2021 both score intervals favorable
against R and >=25% absolute count-error reduction; all-six pooled proper scores
favorable with interval upper bounds<0 against both R and T; no >10% harm at any
other annual origin or supported upper/lower group (>=200 rows,30 positives);
and lower pooled proper scores than the earlier probability ensemble on shared
rows. Three-year outcomes remain exploratory because only two overlapping origins
exist. A winner still requires delivered-value testing; do not call it a full WAR
upgrade. If it fails, record the failure without a third tuning round in this task.

Freeze plan/code/input hashes. Test per-snapshot/identity/class weight conservation,
unchanged outcomes, copying only prior inputs, dated source flags, missing vs zero
values, and outcome/identity exclusion from features. Mutate unavailable future
labels/predictors and refit 2021 A regular; require identical probabilities. Verify
the original 2026 seal. Preserve the first experiment and report both, including
the 2022 harm, rather than replacing it with a more favorable story.
