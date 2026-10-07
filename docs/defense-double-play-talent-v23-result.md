# Keep double play forecasts neutral rather than carrying noisy history forward

2026-10-07. The fixed regressed MLB-history double-play rule worsens later
same-position quality prediction. Keep neutral DP credit in the research defense
assembly; do not add this rule to player value or retune its weights. This result
does not reject double-play ability or a genuine chance-based model.

## What was actually tested

Compare neutral credit with weighted native DP history at the same infield
position: three source years weighted 1, 0.5 and 0.25, and 3,000 zero-credit prior
outs. This prior is an inherited practical assumption, not an optimized or
validated DP-specific reliability estimate. No model was fitted or tuned.

The primary 2022 origin has 469 people/884 eligible positions; 145 people/159
positions qualify for pooled 2023–2025 DP runs per 500 innings. All other forecasts
remain saved with unknown quality. The separate 2021 stress origin measures
2022–2024. Position moves, exits and missing credit are not zero ability. This
is later adjusted run quality under observed traffic, not mechanical conversion
probability, delivered WAR or a minor-to-MLB transfer test.

| Origin | Neutral RMSE | History RMSE | Neutral MAE | History MAE | Paired RMSE change interval |
| --- | ---: | ---: | ---: | ---: | --- |
| 2022 primary | 0.51525 | 0.55856 | 0.38317 | 0.42914 | +0.01144 to +0.07903 |
| 2021 stress | 0.48783 | 0.51935 | 0.36754 | 0.37461 | −0.01195 to +0.06928 |

Errors are runs per 500 innings, with each person's multiple positions sharing
one total weight. The paired interval resamples people, not independent position
rows. Primary RMSE worsens 8.4 percent; all four infield positions worsen, with
1B/3B/SS failing the predeclared five-percent harm guard. Every primary age and
history-exposure band also worsens RMSE. The 2021 loss is uncertain but is not
used to rescue the primary rule. Signed primary bias stays small at +0.02472.

Within the measured primary cohort, multiplying by actual future exposure
produces +23.23 predicted DP runs against −7.34 observed over three years. These
are matched oracle-exposure totals, not forecasts of league opportunities or
league WAR. The same player may contribute different position rows, but each
position's runs are distinct. Neutral predicts zero; it does not claim everyone
has exactly average mechanical skill.

## Why the loss makes statistical sense

The independent squared-error identity is revealing. The candidate's weighted
mean squared magnitude is 0.06010, but twice its weighted product with later
quality is only 0.01360. Their difference, +0.04651, exactly equals the increase
in mean squared error. The history estimate introduces substantially more
variation than it successfully tracks in later quality. This is arithmetic,
not proof that teammates, traffic or aging caused the reversal.

Actual DP chances and difficulty variables are absent from the saved seasonal
response. Native adjusted credits help, but dividing by innings still mixes
skill and traffic. [The measurement definition](https://baseballsavant.mlb.com/leaderboard/fielding-run-value)
keeps DP separate from range and receiving. Small run values, noisy conversion
events, role changes and future measurement noise are plausible limits. Neither
the variance identity nor these examples identifies an ideal alternative weight.
We do not estimate one from this already-exposed cohort.

## What happens to actual players

Eleven primary focal selections and their three origin-only peers cover 43
player origins/96 positions. A supplemental stress review adds 12 player
origins/27 positions. Four minor 3B source walks are retained as unknown-quality
examples. All source rows, actual weights, reliability, missing histories,
support counts and annual same/other-position paths are saved.

| Player and position | Weighted DP runs | Weighted outs | Actual shrinkage weight | Neutral | History | Later quality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Semien 2B | −3.1874 | 5,748.5 | 0.6571 | 0 | −0.5465 | +0.3399 |
| Giménez 2B | +0.7697 | 3,562.75 | 0.5429 | 0 | +0.1759 | +0.5489 |
| Lindor SS | −0.0573 | 6,060.75 | 0.6689 | 0 | −0.0095 | +0.3553 |
| Arenado 3B | +2.0897 | 5,637 | 0.6527 | 0 | +0.3629 | +0.1994 |
| Goldschmidt 1B | −0.0887 | 5,589 | 0.6507 | 0 | −0.0155 | +0.0590 |
| Witt SS | +0.1298 | 2,477 | 0.4523 | 0 | +0.0355 | +0.1405 |
| Rivera 3B | −2.2432 | 2,438.5 | 0.4484 | 0 | −0.6187 | −0.5999 |
| Crawford SS | +4.6978 | 6,221.5 | 0.6747 | 0 | +0.7642 | −0.2691 |
| Merrifield 2B | +2.2726 | 3,855.5 | 0.5624 | 0 | +0.4972 | −0.9579 |
| Dubón 2B | +0.0657 | 367 | 0.1090 | 0 | +0.0293 | +1.8115 |
| McNeil 2B | −0.9613 | 3,492 | 0.5379 | 0 | −0.2221 | +0.1052 |

The shrinkage weight genuinely multiplies the raw rate, unlike Lovich's separate
batting defect. The candidate is 1,500 times weighted runs divided by weighted
outs plus 3,000. No other position's range grade enters this calculation.

Semien's large negative 2022 credit drives the miss; future 2023 and 2025 credit
is positive. Giménez, Arenado and Witt improve versus neutral but do not establish
full defensive development. Lindor and Goldschmidt remain approximately neutral.
Peers retain awkward outcomes: Swanson and Seager's stronger histories fade;
DeJong becomes negative; Perdomo becomes positive despite negative source credit.
Peers that leave the position or lack measured follow-up remain unknown.

Rivera is the largest absolute-error gain: negative 2021 and 2022 credit predicts
negative 2023–2025 quality well. His origin-selected peer Burger also has negative
future quality, but tiny source evidence leaves the forecast near neutral.
Crawford is the largest deterioration: all three source seasons have positive
credit, while future annual rates are −0.758, +0.165 and −0.105. His peers Correa,
Mateo and Kiner-Falefa also have negative measured later SS rates. These are
real reversals in the saved measurements, not a range/DP mix-up or an ID bug.

Merrifield is the largest false high, with positive credit in all three source
years and negative 2023/2024 rates. No 2025 2B exposure is not another negative
season. Dubón is the largest false low: only 367 weighted source outs yield
properly small influence. His measured annual future rates are +2.517, −0.565
and +1.474, so the high pooled result is not three identical elite seasons.
McNeil is an ordinary median-error example: recent negative history leads to
−0.222, but later annual rates +0.771, +0.060 and −0.780 pool slightly positive.

At the stress origin, Sosa's negative rookie SS credit forecasts −0.597 versus
later +0.468. Rojas's positive history forecasts +0.605 versus +0.034. Bruján has
only 87 MLB 2B outs with −1.027 DP runs: even the 3,000-out prior leaves −0.499,
while his modest 1,629 later outs pool +0.984. This reveals a limitation of the
inherited prior and of per-inning noisy event credit, not a reason to optimize
a new weight from these cases. His small source profile and later sample remain
explicit. Frick and his minor peers receive no learned skill grades; no MLB
quality is a missing observation, not confirmation of a neutral forecast.

## Support and decision

Fully mature earlier MLB labels supply 162–191 distinct people per held fold
for 2022, but 349/884 forecast profiles have fewer than ten earlier people in
their position/age/DP-history intersection. Semien has four and Arenado five.
There is no fitted reference model extrapolating from those profiles; still,
the result cannot certify their distinct development paths. All 1,743 forecasts,
4,776 source origins, ten support cells, scores and bootstrap draws independently
replay. Ten unit checks pass. This proves execution, not talent accuracy.

The source is a current retrospective measurement extract. Historical vendor
publication dates and internal adjustment training are not certified as vintage
forecast-time information. Own history cutoffs are enforced; that does not cure
vendor vintage uncertainty. The source-era boundary and selected measured-cohort
scope remain stated, not silently turned into a prospective validation claim.

Keep neutral DP in the research assembly and skip the delivered-value experiment
for this failed rule. No per-position cherry-picking, prior/recency sweep or
algorithm tournament. The main opportunity for improvement remains lower-level
range/development and correct assembly of reviewed components. Next inspect
older compatible quality measurements to address the explicit historical
training/follow-up gap, then pursue contextual minor evidence only with a
supported later-MLB target. Frozen forecasts, explorer, 2026 selection and the
separate Lovich repair are unchanged; the broader defense goal stays active.
