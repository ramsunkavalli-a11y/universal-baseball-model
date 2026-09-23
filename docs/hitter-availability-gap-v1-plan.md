# Position-adjusted regular-player PA shortfall

Pre-fit addendum, 2026-09-22, responding to the user's simpler proxy proposal.
This supersedes the health-feature fitting arm in `hitter-health-budget-v1-plan.md`
before any fits/scores. Preserve its transaction-source audit and league-budget
ledger; do not proceed with a broader injury-feature sweep.

## Meaning and support

Call this **availability/workload shortfall**, not diagnosed health. It can reflect
injury, platooning, demotion, suspension, role loss or a lower lineup slot. Never
condition cohort inclusion on subsequently reaching MLB.

The recovered MLB fielding-position history covers 2004–2025. Recovered all-level
position history covers 2021–2024 only; it does not support the same multi-origin
two-year test. First test established MLB regulars' contextual features, keeping
all other panel players in scoring with explicit unsupported indicators. Do not
present this as validation of the minor-league version or all-level health coverage.

## Fixed proxy, created at each historical cutoff

Use the prior season's dominant MLB position by games played (ties by fielding
outs, then position abbreviation), not a mutable present-day primary position.
Include C, 1B, 2B, 3B, SS, LF, CF, RF, DH. Unknown position stays unknown.
For season t, define an established regular **before t** using t-1 MLB PA divided
by its certified schedule fraction: >=400, or >=300 for catchers. These are fixed
practical thresholds, not medical classifications. Require known prior position.

Estimate a typical high-workload regular's full-season PA as the 75th percentile
of observed schedule-normalized PA among such predesignated regulars in the last
three completed seasons strictly before t, excluding 2020 from the reference pool.
Players who lost their job or never appeared in those seasons stay in that pool
with zero PA. Use a position cell with >=30 rows, otherwise the pooled regular
reference with >=30 rows; record support/fallbacks. No manual PA target per position.

For known regulars, expected opportunity = reference PA x season t exposure.
Shortfall = max(0, expected minus observed MLB PA) / expected. Use the last two
observed seasons' shortfalls and their difference when both exist. Missing regular
status/reference stays flagged unknown, not healthy. The reference for every t
is constructed only from seasons before t, even when fitting much later.

## Fixed ablation

Use the four origin folds and training maturity from the prior plan (2019, 2021,
2022, 2023; training origins >=2016; Year-2 target). Hold saved participation and
carry-forward performance fixed. Standardized/imputed Poisson alpha=1/max_iter=2000,
conditional PA bounds 1–750. Fit three forms, no tuning:

- E: existing 81 features, exposure-aware training as previously declared;
- T: E plus prior-position dummies, regular/measurement flags and the two workload
  references (controls for adding position/context rather than the shortfall);
- P: T plus the two shortfalls and their change.

P versus T is the primary comparison. P versus E and T versus E are diagnostics.
The gap is a contextual/nonlinear transformation of existing PA, not magically new
injury information. A gain here need not transfer to flexible tree models.

Primary gates: ordinary-window paired player-cluster 95% PA-MSE improvement,
MAE not worse, majority of three origins improve; same MSE/MAE requirements in
supported measured-regular players (>=100 rows, >=2 origins). Fixed-rate value MSE
not >1% worse overall or >5% in supported stage/age/top-50 groups. All-four-origin
PA and fixed-rate value MSE not >5% worse. All declared cohorts remain visible.
Bootstrap 1,000 player clusters, seed 417. Small young-star groups descriptive.
No current forecast delivery even on a pass: require a separate coherent-value
validation and current-source coverage. The old direct-value benchmark is reported,
not silently replaced by a head product.

## Accounting and verification

Complete the prior plan's PA/partial-value budget ledger without rescaling named
players. Include historical outsiders and an explicit unallocated/excess bucket.
Full WAR remains outside this partial batting-plus-replacement model.
Test prior-only peer references, prior-season regular classification, no future
MLB-survivor filtering, position joins, unknown versus zero gap, exposure maturity,
unchanged probability/rate, budget identities and original forecast hashes.
