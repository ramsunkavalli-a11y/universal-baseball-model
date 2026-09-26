# Fixed test: one population measure for participation and conditional PA

2026-09-25. Before new fits. Implements milestone 2 of the repair program.

Use the exact repaired panel, detailed D columns, chronological folds, seeds,
LightGBM settings, active rows and [archived D reference](hitter-conditional-workload-v1-result.md).
First replay all twelve D conditional heads and require agreement with archived
conditional predictions within 1e-9 PA. Abort on mismatch before candidate fits.
No new participation fit. Query identities and labels must match the archive.

Candidate W changes only sample weights: compute inverse eligible snapshots per
player on the activity training population, then retain those weights when
filtering positive PA. Current D recalculates inverse active snapshots per player.
Normalize weights to mean one in both fits, preserving existing regularization
scale. Feature filtering, clipping [1,750], scope and source cutoffs stay fixed.
Only never-debuted prospect expected PA changes; all others remain archived D.

Primary: equal-origin mean squared error for three-year summed prospect PA,
W minus D. Keep the stronger historical E comparator, annual Years 1–3, original
non-arrivers and 2021/2022 separately. Paired player-history bootstrap 95%
interval, 4,000 draws, seed 1729, shared identities across origins. Three complete
origins are not independent validation of future regimes; report each origin.

Diagnostics: conditional PA on actual participants; lower/upper minors, age
under 23 versus older, no next-year PA, prior workload <100/100–299/300+ (source
pa_lag0); signed totals and MAE. These are not selection scopes. No bin tuning,
uniform PA bump, optional weight search or learned reconciliation. Retain the
scope of the original D experiment; its lack of incumbent intervention is not
evidence about weighting for incumbents.

Evidence of improvement requires a favorable primary interval and no conflicting
origin/horizon pattern concealed by pooling. Otherwise retain D and report why
the coherent weighting change did not yield an established predictive gain.
There is no automatic production deployment, even for a favorable comparison.
Inspect exact worst/best ten player-error changes per cumulative origin without
manual adjustments. Run at least one future-outcome/input mutation replay for W.

Hash this contract, code, input panel and archived inputs in a prefit manifest.
Write replay certificate BEFORE any W fit. Candidate outputs are separate;
do not overwrite any archived D, E, H or frozen forecasts. Subsequent batting
factorial retains its original archived inputs regardless of this result.
