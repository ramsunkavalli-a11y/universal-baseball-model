# Count based expected playing time comparison

2026-10-03. One objective/link contrast after the seventeen retirement-policy
reviews. No feature expansion, parameter sweep, probability claims or new source
collection. Keep working V33b, source-repaired V34 and reviewed games V38 visible.

## Question and fixed comparison

Does a Poisson-deviance log-link boosted mean improve following-calendar-year
MLB expected PA and delivered batting-plus-replacement contribution over the
games model's squared-error identity-link mean? Use the exact V38 239 inputs,
35 training/test cells, equal-origin training weights and 30,506 forecast rows.
Same 250 iterations, depth 3, leaf minimum 30, rate .05, L2 10, seed 31, no early
stopping, two threads. Change only loss/link. Effective regularization and split
behavior can differ by loss; the result is this fixed objective implementation,
not a universal theorem about losses. Output is bounded [0,800] identically;
record clipping. Apply V44 reported-retirement and old permanent-status policies
to both comparison arms, not just the candidate. Keep rate predictions exact.

The [official learner documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
describes nonnegative targets and the Poisson log link. Locally installed
scikit-learn is 1.7.2. We use the loss for conditional-mean estimation: expected
deviance is minimized at the conditional mean, even when PA variance is not
Poisson. Actual baseball PA is bounded, overdispersed and has excessive zeros;
do not use a fitted Poisson variance or event probability as calibrated risk.
No arrival/risk head or quantile forecast is created in this test.

## Source and leakage gates

Reuse the completed V38 official games/count reconstruction, V34 complete 2020
source extension and V43/V44 source qualifications. Exact actual held-player
membership and mature targets are preserved; target 2020 excluded. No training
outcome, later medical event, new player label or public forecast becomes an
input. No 2026 outcomes. Re-run equivalent chronology/identity checks on actual
cells, carry existing support counts and persist missing/sparse profiles.
All 218 unverified roster-only rows remain in headline scoring, with a supported
diagnostic alongside. The foreign universe and present-day prospect talent
target are not certified. No silent deletion improves this experiment.

## Scoring and required review

Primary: expected-PA RMSE/MAE, delivered-contribution RMSE, origin/stage PA and
contribution totals, brief debuts/never-debut upper minors/absent prior debuts,
and the unchanged 1,789 public matches. Hold batting rate fixed; value changes
are a mechanical workload comparison, not a new talent or dependence model.
Score against retirement-qualified V38 first; retain retirement-qualified
working V33b/V34 and Steamer. Player-clustered nominal paired intervals are
development evidence. Require no harmful cohort reallocation masquerading as
a pooled win. Declared practical public tolerances are not changed after results.

Replay every saved head and exact log-link tree accounting for cases. Fixed
Kurtz/Volpe/Judge-debut/Judge-established/Rooker/Pujols-before-retirement plus
largest gains, losses, false highs/lows and ordinary cases. Show dated own counts,
actual game/usage inputs, control versus candidate raw and bounded means, fixed
rate and contribution arithmetic, actual outcomes, actual profile support and
origin-only selected peers. Include unsuccessful peers. Log-path accounting is
descriptive, not causal; exponentiating individual terms does not make additive
PA effects. No disposition or next model experiment before manual review.

If the candidate loses, close this objective contrast rather than tuning to
names or declaring all count models useless. If it helps, finish a clearly
labeled coherent research assembly without inventing calibrated prospect grades,
defense or six-year market value. Frozen/deployed 2026 remains unchanged.
