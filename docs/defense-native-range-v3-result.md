# MLB defensive history identifies useful range talent

2026-10-06. We now have a tested MLB range baseline instead of treating everyone
as an average defender. It is a useful research building block, not a completed
defense/WAR forecast or a change to explorer 8810.

## What improved

For forecasts made after 2022, measured against pooled 2023–2025 same-position
MLB range, 261 players supplied 317 qualifying position observations:

| Estimate | Typical prediction error, runs/500 defensive innings |
| --- | ---: |
| Assign everyone average range | 2.707 |
| Recent defensive record, shrunk for sample size | 2.393 |
| That record calibrated for age, position and reliability | 2.291 |

History cuts error about 12% versus neutral; calibration cuts it about 15%, or
another 4% versus simple history. The paired person-resampling interval for
calibration minus history is −0.185 to −0.015 runs/500 innings. The improvement
is credible within this development cohort, not independent final confirmation.
These percentages are **range-quality error**, not total-WAR improvement.

The 2021 stress origin also improves, from 2.378 to 2.316 versus history, but its
incremental interval includes no improvement. It is reported separately and
not used to change the recipe. In 2022 calibration improves six of seven position
groups; 3B worsens from 2.289 to 2.350. The age-30+ group also worsens slightly
(2.408 to 2.422), while younger groups improve. We have not tuned those groups.

## Why this is a different, useful question

The previous adjusted minor-league ground-ball experiment was an 89-player
ordinary-year comparison with a team-ground-ball denominator. This comparison
uses actual MLB range history for a much broader established-MLB population.
It does not overturn that feature's negative result. It demonstrates that
defensive information itself is useful and supplies a transparent baseline for
the missing defensive layer.

The source ledger retains range, arms, double plays, first-base receiving and
catcher components separately in native runs. Histories here use defensive outs,
not batting PA, and quality is distinct from arrival or playing time. Source
extraction and the fixed player checks are documented in
[the source review](defense-native-range-v3-source-review.md).

## What the model does with actual players

All numbers below use the same 2022 cutoff and later three-year quality window.
The full machine walkthrough preserves annual source rows, recency/shrinkage,
every actual input, fitted contributions, fixed-fit explanation probes, future
paths and three origin-only peers for each case. It covers 12 focal players,
including unknown-quality exits, not just successful examples.

- **Arenado, 3B:** history +2.72 → calibrated +1.99; observed +2.12. Positive
  2020–2022 history is retained, with the older-player adjustment moderating it.
  His three future seasons stay positive. This is a sensible improvement.
- **Castellanos, RF:** −2.40 → −3.34; observed −2.94. His dated RF history is
  negative in all three years; calibration makes it more negative. Both models
  identify a poor defender, with the calibrated estimate somewhat too low.
- **Witt, SS:** −1.89 → −0.70; observed +4.89. The actual rookie SS record is
  −6.88 runs/2,477 outs, not an invented bad-defense label. Youth and position
  soften it, but the model still misses his large improvement. Its fixed-fit
  no-history probe is +1.18, showing that his negative rookie record pulls him
  down substantially. That probe explains the fit; it is not a replacement grade.
- **Ezequiel Tovar, SS:** −0.45 → +0.43; observed +3.53. Only 234 prior SS outs
  limit the record's influence. Age/position help, but do not identify the full
  talent. His peers Henderson, Grissom and Peguero are chosen by cutoff age and
  exposure, not by later success; two lack qualifying same-position quality.
- **Kiermaier, CF:** +1.67 → +1.81; observed +5.80. Both estimates identify
  positive range but underrate him. His large later improvement is not supplied
  to the model. Same-age peers Springer, Hicks and Bradley lack sufficient
  future CF measurements; they are not labeled average defenders.
- **Semien, 2B:** +1.36 → +0.98; observed +3.76. Calibration makes this miss
  worse. Earlier negative SS range is separate from 2B history; an age-based
  decline assumption cannot fully describe his position development.
- **Refsnyder, LF, largest gain:** −0.02 → −1.80; observed −3.69. His same-LF
  history is tiny (232 weighted outs). Most of the downward change comes from
  learned age/position expectations rather than strong personal LF evidence.
  The gain is statistically useful, but not proof of rich individual scouting.
- **Jankowski, LF, largest deterioration:** +0.07 → −1.71; observed +2.36.
  The same age/position expectation hurts him. Known positive CF range in 2020,
  2021 and 2022 is retained in the audit but **not used in this fit**. Leaving
  other-position ability out is a representation gap. His origin-selected
  comparators include Refsnyder, illustrating why the generic prior cannot
  distinguish them well. A position-transfer model needs a proper matched test;
  do not patch one player or assume CF-to-LF rates transfer unchanged.
- **Enrique Hernández, SS, false high:** +0.20 → +0.24; observed −7.97.
  Just 201 weighted prior SS outs are overwhelmed by a generic position prior.
  Future SS range is −9.31/1,653 outs in 2023 and −0.42/179 in 2024. His other
  defensive roles are not evidence of equivalent SS ability. This is another
  sparse-position gap, not a reason to award every versatile player SS quality.
- **Michael Siani, CF, false low:** +0.03 → +1.29; observed +7.27. The 190-out
  origin sample cannot establish elite range. His future label is about 92%
  2024 exposure, despite three measured calendar years. The player looks strong
  in that year, but this is noisier evidence of lasting talent than three full
  seasons. Keep that uncertainty visible.
- **Mateo, 2B, ordinary median-error case:** +0.05 → +0.03; observed −1.44.
  His positive 2022 SS record is not used as 2B quality. The comparison does
  not silently validate his whole defensive profile from one position.
- **Wilfredo Tovar, 2B:** +0.09 → −0.32, with no future quality. The fixed
  surname case rule retains him alongside Ezequiel. No MLB participation is
  not a measured poor-defense outcome and is excluded from quality scoring only,
  not the prediction/coverage ledger.

## Limits and totals that still matter

Every one of the 13,402 eligible origin-position rows receives a prediction.
In 2022, 746 people/1,777 positions are eligible, but only 261/317 qualify for
future same-position quality. Position converts and exits are therefore a major
boundary, not discarded evidence that everyone else is a bad defender. No
lower-minors or debut talent claim follows from this test.

Each actual 2022 held-player fit has 309–332 training people across four mature
origins, 2016–2019. Genuine 2020 MLB exposure appears in some pooled historical
windows, weighted by actual outs; no nonexistent 2020 minor season is created.
Even so, 221 of the 317 evaluated positions have fewer than 20 training people
in their detailed position × age × exposure profile. This limits broad claims
from age/position priors. Thirty-seven labels have over 80% of exposure in one
season; a three-year window alone does not guarantee a precise talent measure.

Using **actual future exposure only as a diagnostic**, measured range sums to
180.81 runs. History predicts 265.50 and calibration 104.65. Those are not
forecast delivered runs: future innings are supplied by reality, and the sample
excludes many players/positions. Calibration still underestimates this exposure-
weighted total, despite improving person-balanced errors. In 2021 this issue is
larger: actual 302.20, history 278.63, calibration 93.16. Do not claim improved
league totals, or choose a scale to force these selected totals to match. The
quality-opportunity association must be handled in the integration layer.

## Disposition and what comes next

Retain both transparent history and calibrated MLB range as research baselines.
The quality result is positive; profile support and baseball reasonability are
qualified; deployment is not approved. Position-transfer representation, catcher
opportunity denominators, other defensive skills and actual opportunity/value
integration remain unfinished under the active
[defense-layer goal](defense-layer-v3-plan.md).

The next range improvement is coherent use of cutoff-known fielding at other
positions, not another weight search or retry of adjusted minor ground balls.
The next catcher checkpoint is native pitch/steal-opportunity coverage, not a
framing score divided by batting PA. Neither step may use 2026 outcomes to tune.

Integrity checks independently replay 13,304 source rows, 13,402 histories and
predictions, all 20 learned fits using a second linear-system formulation, and
paired person-bootstrap intervals. Thirteen focused regression tests pass.
These certify execution, not the unsupported scientific claims above.
An initial output-schema error was repaired without changing the locked model;
the original runner, preflight and repair record are retained.

Evidence: [final review](../reports/model-evidence/defense-native-range-v3/final-review.json),
[scores](../reports/model-evidence/defense-native-range-v3/report.json),
[full player calculations](../reports/model-evidence/defense-native-range-v3/player-walkthrough.json),
[chronological support](../reports/model-evidence/defense-native-range-v3/fit-preflight.json).
