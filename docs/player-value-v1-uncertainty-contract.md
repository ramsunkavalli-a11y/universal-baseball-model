# Player Value v1 forecast-uncertainty contract

Last updated: 2026-08-20

## Status

**PRE-OUTPUT METHOD FROZEN.** This contract was committed before materializing
the first Player Value v1 interval table. It adds a diagnostic forecast
distribution around the already-frozen 2024 point estimates. It does not alter
any component, ranking, population, upstream model, or selection decision.

## Target and interpretation

For each of the 3,051 rows in the final Player Value v1 population, estimate
equal-tail 80% and 95% intervals for next-season realized WAR under the frozen
v1 model and the uncertainty sources listed below.

These are model-based forecast intervals, not confidence intervals for a
player's immutable true talent and not guarantees that every omitted model
assumption is correct. The frozen `war` field remains the ranking statistic.
Interval endpoints must never reorder the published ranking.

## Frozen inputs

Consume without refitting:

1. the verified 3,051-player final table from Actions run `32385002209`,
   artifact `9412571491`;
2. the frozen 2023-to-2024 B2 batting profile from run `32099733186`, artifact
   `9311172007`;
3. the selected 2024 Playing Time scored surface and coefficients from run
   `32142089669`, artifact `9326300207`;
4. the certified 2024 MLB batting Performance environment from run
   `31955392482`, artifact `9265954750`;
5. the frozen 2024 catcher-opportunity surface from run `32269076231`, artifact
   `9371426672`;
6. the frozen Defense native run-conversion parameters and the already-recorded
   out-of-time development residual MSEs.

The materializer must fail closed if player coverage, projected PA, point WAR,
the B2 simplex, Playing Time alpha, component families, or source hashes differ
from the frozen records.

## Deterministic simulation

Use exactly 20,000 Monte Carlo draws per player. Use NumPy `PCG64` with master
seed `20240820`; create each player stream from `SeedSequence([20240820,
player_id])` so results are independent of table order and parallel execution.

### Playing Time

Use the selected frozen hurdle distribution directly:

- participation is Bernoulli with
  `predicted_any_mlb_pa_probability`;
- positive PA follows the fitted zero-truncated NB2 distribution;
- the common frozen NB2 dispersion is `alpha = 0.7461189032566083`;
- recover the underlying untruncated NB2 mean as the unique positive solution
  whose zero-truncated mean equals `predicted_positive_mlb_pa_mean`;
- do not cap, floor, winsorize, or otherwise repair positive draws.

The artifact identity
`predicted_expected_mlb_pa = participation_probability * positive_mean` must
reconcile exactly with final projected PA within `1e-10`.

### Batting

Treat the frozen B2 empirical-Bayes profile as a Dirichlet posterior mean with
total concentration

`baseline2_effective_core_events + prior_strength_core_events`.

For the certified pooled MLB run-value vector, compute the exact first two
moments of core-event run value. In each draw, batting runs are normal with:

- mean equal to sampled PA times the frozen player batting runs per PA;
- variance equal to the sum of (a) finite-season core-event outcome variance
  under the common MLB core-event coverage and (b) posterior profile-mean
  variance implied by the Dirichlet concentration.

This is a moment-matched normal approximation to the Dirichlet-multinomial
batting forecast. Zero sampled PA produces zero batting runs.

### Defense

Scale each frozen defensive opportunity by sampled PA divided by frozen
expected PA. Add independent zero-mean normal skill residuals on the native
z-score scale, converted with the frozen opportunity-specific run rate.

Use the already-recorded pooled out-of-time MSE for the actual selected/fallback
family:

| component family | MSE |
| --- | ---: |
| general range T1 | 0.878640460280284 |
| general range U1 | 0.8900360540992999 |
| general range B0 | 0.9304792055721907 |
| catcher throwing C2 | 0.9385276019479529 |
| catcher throwing B0 | 1.0063647479219435 |
| catcher blocking C2 | 0.8506475669670914 |
| catcher blocking B0 | 0.9532962787607702 |
| catcher framing F1 | 0.6478744253399015 |
| catcher framing F0 | 0.9846201792216872 |

General-position residuals and the three catcher residuals are independent in
v1 because no frozen cross-component covariance surface exists.

### Remaining terms

For sampled PA `PA*` and frozen expected PA `E[PA] > 0`, scale these point
components by `PA* / E[PA]`:

- baserunning;
- positional adjustment, including DH;
- MLB centering;
- replacement runs.

`Rpark` remains zero. RPW remains `9.682629939156854`. No independent variance
is added for baserunning skill, future position/DH mix, park, centering,
replacement level, RPW, source revisions, or cross-component dependence because
the frozen v1 pipeline contains no authorized covariance or probabilistic
surface for them. These omissions must be reported in the result and table.

The six outside-snapshot zero-exposure rows remain structural all-zero point and
interval rows. Do not infer Playing Time or component variance for them.

## Output

Freeze:

- `docs/player-value-v1-uncertainty-2024.json`;
- `reports/generated/player-value-v1-uncertainty-2024.parquet`.

The table must preserve `player_id`, frozen rank, point WAR, evidence/fallback
fields, interval endpoints, widths, simulated mean/median, and component
variance shares. At minimum persist Playing Time, batting, Defense, and
deterministic-scaled variance shares, with shares summing to one when total
variance is positive.

## Mechanical QA

Fail closed unless:

1. all 3,051 unique final players appear once and point WAR/rank are unchanged;
2. the six structural zero rows have zero-width intervals;
3. all non-structural endpoints are finite and satisfy
   `p025 <= p10 <= median <= p90 <= p975`;
4. all widths are nonnegative;
5. each positive total-variance row has component variance shares summing to
   one within `1e-10`;
6. rerunning with the same inputs is byte-deterministic;
7. no 2025 outcome, upstream refit/reselection, interval-driven cap/floor, or
   ranking-driven parameter is used.

## Boundary

This layer quantifies meaningful uncertainty that the frozen artifacts can
support. It deliberately does not fabricate uncertainty for unresolved sources.
A later v2 may add out-of-time calibration of full WAR residuals, correlated
role/position paths, and baserunning posteriors only through a new predeclared
development gate.
