# Three-year hitter follow-up: better MLB chances, ranges still withheld

Completed 2026-09-22 under the [frozen plan](multiyear-hitter-followup-v2-plan.md).
Versioned package: `model_artifacts/multiyear-hitter-followup-v2-2026-09-22/`.
This is exposed historical development, not a new independent confirmation.
No 2026 outcome was used, and all 3,907 players' v1 batting-value means are
byte-identical. The original frozen forecast and v1 package remain untouched.

## What actually changed

386 established hitters now have MLB participation probabilities based on age,
the last three calendar years of MLB PA, and batting quality regressed with a
1,200-PA league prior. Eligibility requires current MLB PA, known age, and at
least 200 MLB PA in either preceding year. These probabilities do not use the
historical roster-presence flag. Everyone else's probabilities are unchanged.

Conditional PA (PA if the player appears) remains the prior model's estimate.
Expected PA changes only because MLB participation probabilities changed.
Batting-value means are still separately estimated; this is not a coherent joint
simulation, full WAR model, or correction to hitting talent. In particular,
Judge's expected Year-1 PA remains only 393, even after his MLB chance increases.

| Example | Previous 2028 MLB chance | Updated chance | Updated 2028 expected PA |
|---|---:|---:|---:|
| Aaron Judge | 55% | 96% | 293 |
| Pete Alonso | 28% | 94% | 295 |
| Juan Soto | 82% | 99% | 487 |

These are chances of at least one MLB PA that year, not healthy/full-season chances.
Examples explain the model change; they were not used to tune or hand-adjust it.

## Historical opportunity evidence

Six origins (2016–19, 2021–22), three horizons, 6,252 established-player/horizon
rows and 703 distinct players. Every fit requires origin + horizon <= cutoff and
excludes pandemic-crossing training windows. Equal-origin scoring; 1,000 paired
player-history bootstrap draws. The intervals condition on these historical years
and do not resolve common season shocks or turn exposed evidence into confirmation.

| Probability score, lower is better | Existing | New | Paired 95% interval for change |
|---|---:|---:|---:|
| Brier | 0.13675 | 0.12875 | -0.01206 to -0.00364 |
| Log loss | 0.43159 | 0.39923 | -0.04389 to -0.02002 |

Both scores improve in all six origins and in the nonpandemic sensitivity. All
predeclared promotion gates pass. Year-1 Brier alone worsens 3.1% (0.09185 to
0.09474), within the frozen 5% guard; benefits are strongest in Years 2–3. Do not
claim that every metric at every horizon improves.

The Poisson conditional-PA challenger lowers absolute PA error by about 4 PA,
but its squared-error improvement is uncertain (paired MSE interval -1,424 to
+192), and it improves only three of six origins. It fails the gate and is not used.
No retuning was performed after failure.

## Uncertainty: a substantial improvement, but not ready for the player report

Fixed LightGBM 10th/90th quantiles plus rolling prior-origin corrections improve
interval score (width plus penalty for misses) in all four targets. Overall
coverage is 92–95%, largely because many minor leaguers have zero MLB production.
That overall number hides the group that matters most to prospect evaluation.

| Target | Old interval score | New score | New coverage: higher-value upper minors* |
|---|---:|---:|---:|
| Year 1 | 0.864 | 0.626 | 66.5% |
| Year 2 | 1.071 | 0.742 | 73.4% |
| Year 3 | 1.213 | 0.837 | 72.2% |
| Three-year total | 2.487 | 1.762 | 73.4% |

*High value means above the earlier calibration pool's stage-specific 80th
percentile of fixed mean forecasts. Current-cohort top-20% checks also fail.
Each cell has over 1,000 observations across six origins; coverage is equal-origin.
All targets fail the predeclared minimum 75% supported-group coverage. Published
ranges remain null; neither raw quantiles nor selectively widened ranges are
substituted. Full audit predictions remain in the versioned package.

This rolling method is motivated by quantile regression and conformal calibration,
not guaranteed conditional coverage: repeated players, season shifts and fitted
quantiles violate simple exchangeability assumptions. It is not a complete
probability distribution, and annual quantiles are never added.

## Source and implementation corrections

- Reprojected all 30 saved 2025 team rosters: 1,343 memberships, zero discrepancies
  with the derived source table. Alonso is the only current >=500-PA hitter absent.
- Fresh historical Mets requests for September 30 and October 15 also omit Alonso,
  while the transaction response records free agency on November 4. These are
  reconstructed endpoint responses, not trustworthy historical reserve-rights
  certificates. The exact upstream omission mechanism remains unresolved. No
  manual addition, replacement input, or claim of certified historical rosters.
- The old established-hitter audit used immature multi-year labels in rolling
  training. Its historical validation claim is withdrawn. Fixed maturity and
  missing-future-zero handling; preserved the original artifact. This v2 test
  replaces evidence for Years 1–3 only, not Years 4–6 or the live 2026 preview.
- A new-code row-order mismatch affected the first current-candidate assembly,
  not its historical scores. Caught before delivery; predictions are now attached
  to player IDs before joining. Replayed saved coefficients and shuffled delivery
  inputs to verify alignment. No model/feature/parameter change was made.
- Refitting the current Year-3 P0 opportunity benchmark reproduces saved
  probabilities and PA exactly by player ID.

## Next bounded direction

Close this batch; do not optimize repeatedly against these same coverage failures.
The next hitter experiment should model no-play probability and the conditional
value distribution together, with separate diagnostics for promotion candidates
and conditional workload. First determine whether bad ranges come from missed
arrival probabilities, conditional value spread, or calendar shifts. Freeze a
small comparison only after that error decomposition; preserve these forecasts
as its benchmarks. A new distribution model must not be judged only by accuracy
on the large never-arriving population.

In parallel roadmap order, the source-certified annual/cumulative target approach
is ready to extend to pitchers; do not claim hitter validation transfers to them.
Years 4–6 and the control/cost layer remain later milestones under the main plan.

## Reproduction

Run `scripts/evaluate_multiyear_hitter_followup_v2.py`, then
`scripts/audit_multiyear_hitter_rosters_v2.py`, then
`scripts/report_multiyear_hitter_followup_v2.py` from the repository environment.
The recovered <=2025 inputs are located through recorded absolute paths/hashes;
large source inventories remain local. Committed prediction/fit/score artifacts
permit delivery and score inspection without querying any protected-season data.
Tests are in `tests/test_multiyear_hitter_followup.py`.

Verification: 38 focused multi-year, opportunity, roster and legacy-bridge tests
pass. All 13 delivered package-file hashes verify. The original frozen hitter
package passes its 31-file verifier with the same forecast SHA-256. Browser checks
confirmed the 3,907-player count, search, player details, previous/current chances,
and withheld ranges. The updated local explorer is served on port 8774; the v1
artifact and its original HTML remain intact.
