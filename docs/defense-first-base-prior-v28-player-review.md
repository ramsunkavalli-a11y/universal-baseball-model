# First base player histories and forecast tradeoffs

These walks distinguish later MLB first-base range ability from next-year
defensive contribution. Eleven fixed/diagnostic groups contain 44 records and
38 unique player origins. All sources and calculations are preserved in
[the machine walks](../reports/model-evidence/defense-first-base-prior-v28/player-walks.json.gz).
This review covers the gains, harms, extreme misses, ordinary case, exits,
non-arrivals and unknown minor skill before disposition.

## How each calculation works

Annual 2022-origin history weights are 0.25 for 2020, 0.5 for 2021, and 1 for
2022. Actual short-season outs are used. Denote weighted runs by R and outs by N.
Original rate is 1500R/(N+3000). New rate is (1500R+3000μ)/(N+3000), where μ
is the cutoff-known held-fold mean. Quality is future measured range runs
divided by future outs, multiplied by 1500, with the locked measurement gate.
Future zeros in the source-sum table below do not imply measured zero ability.

| Excluded player ID modulo five | 2022 reference people | 2022 prior runs per 500 innings |
| --- | ---: | ---: |
| 0 | 222 | −0.02754 |
| 1 | 206 | −0.32106 |
| 2 | 215 | −0.12468 |
| 3 | 209 | −0.12246 |
| 4 | 212 | −0.05338 |

These means exclude the focal player's entire fold, not just his own record.
Their variation illustrates reference uncertainty not included in the reported
conditional bootstrap. No mean was selected by later results. Individual
history is allowed to enter that player's prediction, but not his fold's prior.

Delivered first-base runs multiply each rate by the **same saved predicted
first-base outs** and divide by 1500. Other defense, batting and position are
unchanged. Custom total-value delta is the resulting run change divided by ten;
it is not a new full-WAR model. Actual-opportunity versions are explanations,
not forecasts. Saved age-calibration support flags stay unchanged; examples
with few mature profile peers are not suddenly supported by the empirical prior.

## Fixed players and diagnostic contrasts

Freeman has +0.477/+2.126/+2.336 native range runs in 1432/4074/4133 outs.
Weighted R=3.5184, N=6528, μ=−0.12468: +0.554 falls to +0.515 versus later
+0.338. Annual future observations are +2.510/+1.095/−0.978 in
4135/3811/3717 outs. His 3595 projected next-year outs yield +1.328→+1.233
versus +2.510 actual: pooled quality improves while annual contribution worsens.
His current custom value is 4.196→4.186 versus 7.015 actual. Rizzo's later
positive quality is underestimated more; Cron/Hosmer lack the required two
substantial future measurement seasons and are not zero-skill controls.

Olson's weighted 6705.5 outs and +2.4049 runs yield +0.372→+0.272 against
later +0.699. Future annual range is −3.707/+2.934/+6.785 in
4278/4330/4287 outs. With 3743 predicted next-year outs, +0.928→+0.680
is closer to that first negative year but worse for pooled skill. Receiving
throws remains a separate unchanged channel. Walsh's limited later sample and
Castro/Jones' no future first-base exposure remain unknown pooled quality.

Goldschmidt's −3.859 latest year overcomes earlier positive runs: weighted
R=−0.7064, N=5589. Rate −0.123→−0.236 is farther from later +0.032.
Future +2.354/+0.160/−2.287 illustrates real fluctuation. Next-year range
−0.228→−0.435 also worsens against +2.354; custom value 2.996→2.975
versus 3.072. Belt's limited first-base time and Gonzalez's exit are not
evidence of average ability. Abreu's negative later range is a genuine opposite
trajectory and benefits slightly from less optimistic history.

Guerrero already has negative range in every history year. R=−4.2941 and
N=5296.75 produce −0.776→−0.796 against later −2.874. Future annual runs
are −10.197/−6.962/−1.340 in 3195/3079/3380 outs. Forecast next-year range
−1.550→−1.589 versus −10.197 barely changes the major miss. Saved age-model
profile support is only one person; a supported reference pool does not fix
that learner's extrapolation. Custom value remains 4.037→4.033 versus 0.650.
Pratto's one measured future season is unknown quality; Torkelson's later
negative quality is understated too. Toglia is not a uniformly positive peer.

Santana's fixed 2023-origin history contains +0.606/+2.630/+2.252 runs.
R=3.7186, N=5316.25 and μ=−0.62810 lower +0.671→+0.444. Projected
1863 outs versus 3750 actual already understate opportunity; forecast range
+0.833→+0.552 worsens against +10.963. Custom value 0.232→0.204 versus
2.416 also worsens. Future 2024–2025 observations total 6295 outs/+17.267,
but the three-year window is incomplete and never becomes a quality label.
Abreu/Gurriel are negative contrasts; Goldschmidt's rebound then decline shows
why a universal age narrative would be unjustified.

Wilson and Hollis/Delgado/Alvarez have no measured origin MLB first-base range.
Wilson's prior −0.02754 is explicitly unknown quality. Only 0.823 outs are
projected, so its run change is approximately −0.000015; that is not a material
player-value improvement. His later 18/12/99 first-base outs are too little
for quality. Hollis and Delgado never supply first-base measurement; Alvarez
has only 87 outs. No unknown ability is treated as an observed average grade.

Toglia is the largest main quality gain: a +1.039-run 352-out rookie sample
gives +0.465 with a zero prior. μ=−0.32106 gives +0.178. Later
+1.714/−2.767/−7.654 over 596/2672/2169 outs pools to −2.402, still a major
miss. Only 585 next-year outs are forecast, close to 596 actual: lower quality
worsens that initially positive season even while helping the pooled target.
His whole-value outcome is incomplete, not imputed. Garcia's positive small
sample followed by no future measurement stays unknown; it is not a failed
defender labeled zero. Repeated Pratto/Guerrero comparisons retain their walks.

O'Hearn is the largest main deterioration. Weighted R=0.6985 and N=526 give
+0.297; μ=−0.32106 pulls it to +0.024 versus later +2.226. Future annual
+2.775/−1.183/+4.907 over 1557/1199/1624 outs is a real favorable trajectory
not identified by the prior. Projected 140 outs also badly miss 1557 actual:
+0.028→+0.002 range versus +2.775. Custom value 0.0416→0.0390 against
1.112. Stewart/Haggerty/Dean are primary-role peers without MLB first-base
history; they help explain opportunity context, not O'Hearn's talent.

Kirilloff is the biggest false high, meaning most optimistic relative to
observed quality, not the highest numerical grade. R=−0.1158 and N=715.5
give −0.047→−0.069 versus later −5.001. Future −4.931/−1.010 over
1530/252 outs qualifies but is a noisy small measurement. Predicted 567 outs
miss 1530 actual, and −0.018→−0.026 runs barely repairs the skill error.
Thompson/Carpenter/Kwan's absent first-base measurement is not poor defense.

Santana at origin 2022 is the biggest false low. Weighted R=3.2300, N=4114.5
produce +0.681→+0.629 versus later +3.002. Annual future +2.252/+10.963/
+6.303 over 3458/3750/2545 outs shows the miss persists, not just one year.
First-year forecast +0.659→+0.609 versus +2.252 and custom value
0.199→0.194 versus 1.178 both worsen. Carpenter/Ruf have insufficient later
measurement; Abreu is a genuinely measured negative contrast.

Pasquantino is the ordinary median absolute-error case, not an accurate
success selected to flatter the model. His +0.504 over 920 outs gives
+0.193→+0.152 versus later −1.285. Future −2.449/+1.500/−5.070 over
1091/2679/3253 outs pools negative. His 1803 projected first-year outs exceed
1091 actual, and +0.232→+0.183 is only a small improvement versus −2.449.
Custom value 1.544→1.539 versus 0.209 remains badly high for other reasons.
Miranda has incomplete annual channel coverage; neither his whole-value nor
pooled quality is fabricated from the partial positive observations.

## Every unique focal and peer history

Annual history below is season:outs/runs. Weighted and future columns are
outs/runs. Rates are native range runs per 500 innings. Future totals use only
qualified measured source rows, not missing official exposure. “Unknown” means
the gate failed, not an average grade. Origin 2023 follow-up deliberately stops
in 2025 and remains incomplete. Duplicate selections retain identical records.

| Player and origin | Annual origin history | Weighted history | Old to new rate | Future measured sum | Pooled quality |
| --- | --- | ---: | ---: | ---: | ---: |
| Freeman 2022 | 2020:1432/+0.48; 2021:4074/+2.13; 2022:4133/+2.34 | 6528/+3.518 | +0.554→+0.515 | 11663/+2.626 | +0.338 |
| Rizzo 2022 | 2020:1423/+2.01; 2021:3570/+4.79; 2022:3102/−1.64 | 5242.8/+1.254 | +0.228→+0.184 | 4834/+5.834 | +1.810 |
| Cron 2022 | 2020:324/−0.01; 2021:3285/−0.02; 2022:3084/+0.90 | 4807.5/+0.883 | +0.170→+0.123 | 1506/+1.248 | Unknown |
| Hosmer 2022 | 2020:772/−1.72; 2021:3340/+0.91; 2022:2569/−0.69 | 4432/−0.668 | −0.135→−0.184 | 369/+0.278 | Unknown |
| Olson 2022 | 2020:1498/−0.26; 2021:4016/+0.44; 2022:4323/+2.25 | 6705.5/+2.405 | +0.372→+0.272 | 12895/+6.011 | +0.699 |
| Walsh 2022 | 2020:609/−0.90; 2021:3195/−3.41; 2022:2877/−0.92 | 4626.8/−2.850 | −0.560→−0.571 | 930/−1.862 | Unknown |
| Harold Castro 2022 | 2020:21/−0.18; 2021:233/−1.50; 2022:1235/−1.21 | 1356.8/−2.005 | −0.690→−0.776 | 0/0 | Unknown |
| Taylor Jones 2022 | 2020:54/−1.19; 2021:261/+0.57 | 144/−0.015 | −0.007→−0.034 | 0/0 | Unknown |
| Goldschmidt 2022 | 2020:1234/+2.50; 2021:3939/+5.06; 2022:3311/−3.86 | 5589/−0.706 | −0.123→−0.236 | 10486/+0.227 | +0.032 |
| Belt 2022 | 2020:1054/+0.31; 2021:2294/+1.61; 2022:1519/−2.60 | 2929.5/−1.718 | −0.435→−0.498 | 728/+0.819 | Unknown |
| Abreu 2022 | 2020:1410/+2.68; 2021:3459/−0.13; 2022:3409/+0.91 | 5491/+1.515 | +0.268→+0.249 | 4378/−5.661 | −1.940 |
| Gonzalez 2022 | 2020:180/+1.14; 2021:339/+1.45; 2022:294/+0.95 | 508.5/+1.958 | +0.837→+0.563 | 0/0 | Unknown |
| Guerrero 2022 | 2020:897/−1.71; 2021:3431/−2.63; 2022:3357/−2.55 | 5296.8/−4.294 | −0.776→−0.796 | 9654/−18.499 | −2.874 |
| Pratto 2022 | 2022:1021/−0.46 | 1021/−0.462 | −0.172→−0.265 | 1697/−3.041 | Unknown |
| Toglia 2022 | 2022:352/+1.04 | 352/+1.039 | +0.465→+0.178 | 5437/−8.707 | −2.402 |
| Torkelson 2022 | 2022:2775/−0.56 | 2775/−0.557 | −0.145→−0.172 | 10314/−7.263 | −1.056 |
| Santana 2023 | 2021:3501/+0.61; 2022:1966/+2.63; 2023:3458/+2.25 | 5316.2/+3.719 | +0.671→+0.444 | 6295/+17.267 | Incomplete window |
| Abreu 2023 | 2021:3459/−0.13; 2022:3409/+0.91; 2023:3552/−3.67 | 6121.2/−3.249 | −0.534→−0.620 | 826/−1.990 | Incomplete window |
| Gurriel 2023 | 2021:3666/−0.11; 2022:3679/−6.60; 2023:2014/−1.80 | 4770/−5.124 | −0.989→−1.090 | 408/−0.068 | Incomplete window |
| Goldschmidt 2023 | 2021:3939/+5.06; 2022:3311/−3.86; 2023:3460/+2.35 | 6100.2/+1.689 | +0.278→+0.081 | 7026/−2.128 | Incomplete window |
| Wilson 2022 | None measured | 0/0 | 0→−0.028 | 129/−1.042 | Unknown origin skill |
| Hollis 2022 | None measured | 0/0 | 0→−0.125 | 0/0 | Unknown origin skill |
| Delgado 2022 | None measured | 0/0 | 0→−0.053 | 0/0 | Unknown origin skill |
| Alvarez 2022 | None measured | 0/0 | 0→−0.125 | 87/−1.134 | Unknown origin skill |
| Dérmis Garcia 2022 | 2022:747/+2.78 | 747/+2.777 | +1.112→+1.090 | 0/0 | Unknown |
| O'Hearn 2022 | 2020:610/−0.40; 2021:351/−0.32; 2022:198/+0.96 | 526/+0.698 | +0.297→+0.024 | 4380/+6.499 | +2.226 |
| DJ Stewart 2022 | None measured | 0/0 | 0→−0.321 | 15/−0.440 | Unknown origin skill |
| Haggerty 2022 | None measured | 0/0 | 0→−0.053 | 81/−0.126 | Unknown origin skill |
| Dean 2022 | None measured | 0/0 | 0→−0.122 | 0/0 | Unknown origin skill |
| Kirilloff 2022 | 2021:641/+1.82; 2022:395/−1.03 | 715.5/−0.116 | −0.047→−0.069 | 1782/−5.941 | −5.001 |
| Thompson 2022 | None measured | 0/0 | 0→−0.125 | 0/0 | Unknown origin skill |
| Kerry Carpenter 2022 | None measured | 0/0 | 0→−0.321 | 0/0 | Unknown origin skill |
| Kwan 2022 | None measured | 0/0 | 0→−0.125 | 0/0 | Unknown origin skill |
| Santana 2022 | 2020:1592/+1.19; 2021:3501/+0.61; 2022:1966/+2.63 | 4114.5/+3.230 | +0.681→+0.629 | 9753/+19.519 | +3.002 |
| Matt Carpenter 2022 | 2020:93/+0.06; 2021:270/−0.59; 2022:75/+0.39 | 233.2/+0.114 | +0.053→−0.245 | 273/−0.590 | Unknown |
| Ruf 2022 | 2020:55/+0.38; 2021:902/+4.04; 2022:918/+0.04 | 1382.8/+2.151 | +0.736→+0.517 | 27/+0.152 | Unknown |
| Pasquantino 2022 | 2022:920/+0.50 | 920/+0.504 | +0.193→+0.152 | 7023/−6.018 | −1.285 |
| Miranda 2022 | 2022:1786/−2.97 | 1786/−2.966 | −0.930→−0.963 | 301/+0.108 | Unknown |

## Review conclusion

All 44 group records have been checked, including the repeated Guerrero/Toglia/
Santana peers. The historical mean is a reasonable sparse baseline in these
native units, but cannot predict who improves or declines. The observed main
gain is small, and opportunity errors often dominate annual contribution.
Unknown/minor talent and selected future MLB survivors remain distinct. The
candidate is research-only; no second prior search or blanket penalty follows.
