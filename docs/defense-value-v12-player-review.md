# How defensive skill changes individual value forecasts

The fixed skill histories improve delivered defense and expanded value overall,
but an individual value gain can still come from one error cancelling another.
This review keeps those mechanisms separate. All figures are for the next MLB
season after the stated origin, not a lifetime talent grade or full WAR.

Nineteen focal cases and 57 origin-selected peers retain raw three-year native
records, eligibility, weighted runs/opportunities, fixed priors, range calibration
support, each position/channel's projected time, all nine forecasts and actuals
in the [case records](../reports/model-evidence/defense-value-v12/player-walkthrough.json).
The nine original focal cases and 27 peers are unchanged. Added cases are the
contracted extreme gains/losses, false highs/lows, calibration extremes and
ordinary participant; they are explanations, not independent validation.

## The original players show why skill and total value can disagree

The [source review](defense-value-v11-source-player-review.md) supplies the
dated statistics and exact shrinkage for these nine players and their peers.
Here the primary opportunity arm is the own-repertoire repair, not the
transition arm illustrated in that source review. Neutral and history have
identical batting, PA and positional adjustment. Their entire value difference
is history defensive runs divided by ten.

| Player and origin | History defensive runs | Actual defined runs | Neutral expanded value | History expanded value | Actual expanded value |
| --- | ---: | ---: | ---: | ---: | ---: |
| Trout 2022 | +0.622 | +3.469 | 3.420 | 3.482 | 3.058 |
| Castellanos 2022 | -5.666 | -8.196 | 1.545 | 0.979 | 1.531 |
| Kiermaier 2022 | +2.555 | +10.244 | 0.235 | 0.490 | 2.558 |
| Olson 2022 | +3.870 | +0.480 | 2.880 | 3.267 | 6.565 |
| Varsho 2022 | +3.064 | +10.999 | 2.194 | 2.501 | 1.362 |
| Witt 2022 | -3.718 | +9.756 | 3.122 | 2.750 | 5.178 |
| Álvarez 2022 | +0.178 | +11.204 | 1.904 | 1.922 | 2.913 |
| Chourio 2023 | Unknown mean 0 | +6.499 | 0.895 | 0.895 | 3.050 |
| Eldridge 2024 | Unknown mean 0 | +0.444 | 0.138 | 0.138 | -0.142 |

Castellanos is the clearest counterexample to using total value alone as the
defense verdict. Weak RF/arm history correctly moves defense toward -8.196
actual runs. But the neutral value happened to be nearly exact: understated
batting (2.138 versus 3.101) and too little negative positional value (-5.921
versus -7.512 runs) offset the missing defensive loss. Adding useful defense
breaks that cancellation. His RF history gives -4.359 projected runs and his
arm -1.306; the later measured components are -4.619/-3.577.

Olson exhibits the opposite. Receiving contributes +2.942 predicted runs,
versus +4.187 actual, but range is +0.928 predicted versus -3.707 actual. His
total defense estimate is worse than neutral, yet expanded value improves
because the unchanged batting forecast, 3.972 versus 7.739, is far too low.
Neither case justifies rejecting/accepting all defense on the value score alone.

Varsho's useful positive range history improves defense, but wrong C/RF
exposure and an optimistic batting forecast make the larger value miss worse.
The research forecast has 673 C outs despite no later catching, and gives
no LF outs despite 2,453 actual. Witt's wrong-sign young range history harms
both defense and value; age calibration partly reduces the mistake, not fixes
it. Chourio/Eldridge remain honest unknown-skill fallbacks, not demonstrated
minor-league talent identification.

The preserved peers display the same distinctions. Below, each triple is
history defensive runs / actual defined runs / history versus actual expanded
value. Partial means the applicable defensive total is unmeasured, not zero.

| Focal group | Origin selected peers and actual comparisons |
| --- | --- |
| Trout | Hernández +2.045/-13.121, 1.491/-0.933; Herrera +0.308/0, 0.216/0; Engel +0.309/partial, value outcome partial |
| Castellanos | Renfroe +1.174/-3.065, 1.609/0.396; Grichuk -0.055/-5.581, 1.040/1.008; Dozier -1.723/partial |
| Kiermaier | Springer +0.214/-1.112, 2.100/1.322; Hicks +0.229/-3.445, 0.425/0.696; Ortega +0.135/+0.879, 0.258/0.118 |
| Olson | Walsh -0.833/-3.351, 0.526/-1.091; Castro -1.207/-4.856, 0.187/-0.933; Jones +0.010/0, 0.046/0 |
| Varsho | Castro -0.044/+3.126, 0.368/1.816; Tucker +3.387/-4.460, 3.501/3.550; Eaton -0.043/partial |
| Witt | Perdomo -0.089/+1.214, 0.619/1.858; García -5.859/-3.273, 0.956/0.506; Soto -0.771/-1.200, 0.717/-0.068 |
| Álvarez | Naylor -0.677/+0.269, 1.063/1.729; Pineda -0.300/0, 0.270/0; O'Hoppe -0.722/-8.640, 0.596/0.444 |
| Chourio | Anthony 0/0, 0.327/0; Calabrese 0/0, 0.006/0; Wood 0/-4.810, 0.727/1.122 |
| Eldridge | Isaac 0/0, 0.091/0; Clifford 0/0, 0.006/0; Ariza 0/0, rounded value 0/0 |

Herrera/Pineda/Anthony and the other non-arrivals still have no observed future
quality. Tucker's expanded value looks excellent despite a wrong-sign defense
forecast: underestimated batting cancels it. Grichuk's near-exact value likewise
does not make near-zero defense a good prediction. These are real limits of
an additive model with imperfect components, not excuses to tune by player name.

## Bailey identifies persistent catcher skill but still understates it

Bailey at the 2024 origin has +16.963/+22.434 framing runs in 2023/2024.
With recency weights, +30.916 runs and 11,274.5 pitches become
1,000 × 30.916/(11,274.5+6,000) = +1.790 per 1,000. The 6,013 forecast
pitches give +10.761 runs; 8,913 actual pitches produce +25.054.
Throwing adds +2.299 predicted versus +5.205 actual; blocking -0.555 versus
+1.214. Total defense is +12.505 against +31.473, the biggest primary defense
gain versus neutral, but still a large undershoot.

His unchanged batting is 0.692 versus -0.375 and positional value +5.755
versus +8.828 runs. Expanded value improves 1.268 → 2.518 against 3.655 actual.
The playing-time forecast, 345 versus 452 PA, and conservative skill estimates
both limit the gain. Kirk's peer history similarly helps, +9.535 versus +22.175
defense and 2.875 versus 5.492 expanded value. Diaz has -0.813 versus -3.233
defense, but value 2.500 versus 1.454 because batting is too optimistic. Amaya
plays less than forecast (103 versus 258 PA); his -0.345 defense versus +0.622
and 1.040 versus 0.842 value are not a persistent talent win.

## Realmuto reverses despite positive historical catcher components

At the 2022 origin, Realmuto has +5.133 weighted framing runs in 14,436
pitches, +9.820 throwing runs in 67 weighted attempts and +4.934 blocking
runs in 7,630.25 opportunities. Their shrunk rates are +0.251 per 1,000,
+5.880 per 100 and +0.464 per 1,000. Fixed opportunities give
+1.965/+3.017/+1.887 runs, plus a small negative 1B range contribution:
total +6.854 versus -10.250 actual. Framing flips to -14.428; throwing and
blocking remain positive at +1.162/+3.015. This is the largest defense harm.

Neutral/history expanded values are 2.527/3.212 against 1.837. His 455
expected PA versus 540 actual and 1.779 versus 1.883 batting do not explain
away the catcher-quality reversal. Vázquez's total remains partial. Barnhart's
positive estimate +1.147 undershoots +4.956 actual and his 0.495 value is
near 0.463 partly through other errors. Díaz has -2.661 versus -9.022 defense,
but understated batting/workload (278 versus 526 PA) leave value 0.675 versus
1.423. The same recipe has both persistent successes and real reversals.

## Raleigh gains value from a sensible defense estimate while batting misses

At 2024, Raleigh's framing history is +10.225/+6.348/+12.694 runs in
2022–2024. Weighted +18.425 runs and 14,691.75 pitches give +0.890 per 1,000;
7,612 predicted pitches yield +6.778 versus +6.955 actual. Throwing is
+1.077 versus +1.004; blocking -0.434 versus -1.051. Total +7.421 is close
to +6.907 actual. Expanded value improves 2.687 → 3.429 versus 7.506 actual,
the largest primary value gain; it does not repair 486 versus 705 PA or
2.066 versus 6.306 batting value.

Stephenson's -4.494 defense versus -5.828 helps value move 1.667 → 1.218
toward 1.009. Fortes's +2.454 versus +1.726 also helps, 0.468 → 0.714
against 0.888. Jeffers has reasonably negative defense (-4.304/-5.016), but
its addition moves value 1.674 → 1.243 away from 2.114 because batting/time
are understated. This peer repeats the Castellanos error-cancellation problem.

## Murphy combines positive past skill with too much future time and hitting

Murphy at 2023 has +9.719 weighted framing runs over 13,660 pitches,
+3.215 throwing over 105.25 attempts and +6.171 blocking over 7,246
opportunities. Shrunk rates are +0.494/+1.566/+0.602 in their channel units.
Forecast contributions are +4.138/+1.035/+2.646, totaling +7.819. Actual
framing/throwing/blocking are -1.048/-1.006/+2.651, only +0.598 combined.
Blocking persists; the other two reverse. Forecast workload is 485 versus
264 PA, and batting 2.118 versus 0.200. Adding the excessive positive defense
moves value 2.894 → 3.676 against 0.769, the largest primary value deterioration.
Future low workload is an observation, not an origin-known override.

Heim also reverses (+8.122/-1.138 defense, 2.170/0.368 value); Smith has
+2.390/-3.609 defense and 3.459/2.804 value. Knizner's negative history helps
directionally (-1.936/-1.176 defense), but 0.106 versus -0.671 value still
misses poor batting. No negative result is deleted from the catcher comparison.

## The largest false high is Ruiz and the largest false low is Rafaela

Ruiz at 2022 has -5.217 weighted framing runs over 8,981.5 pitches,
+0.500 throwing over 61 attempts and +1.291 blocking over 4,688 opportunities.
Rates are -0.348/+0.310/+0.168. The forecast -2.733/+0.156/+0.683 totals
-1.893, while actual channels are -11.886/-8.029/-2.408, totaling -22.323.
History is directionally better than neutral, but still 20.430 runs too high.
Expanded value is 1.756 versus -0.096, not validation of the positive positional
credit attached to real catching time. Kirk's peer positive skill persists;
Rivero does not arrive. Melendez remains partially measured and later moves
mostly to the outfield, so his total outcome is not manufactured.

Rafaela at 2024 has CF +5.383 weighted range runs over 2,069 outs, but SS
-5.699 over 2,008.5. Shrunk rates are +1.593/-1.707. The forecast assigns
1,764 CF and 1,456 SS outs, giving +1.873/-1.656 runs plus tiny other channels:
only +0.229 total versus +21.665 actual. He fields 3,502 CF outs and no SS;
actual CF range is +19.404. Age calibration raises total defense to +2.249
and helps, but remains far short. The miss is both quality and placement,
not evidence that his observed CF history should be discarded.

Rojas's +4.541/+6.278 defense persists, but value is too high (0.866/0.348)
because batting/time are optimistic. Harris's +4.971/+6.542 defense likewise
helps the skill estimate while harming a batting-overoptimistic value forecast
(3.190/1.559). Pages has weak short MLB history (+0.074 forecast defense) and
later +12.037; his 1.167/4.173 value remains low. Those peers keep the young
development/position gap distinct from a generic neutral-defense verdict.

## Calibration improves in aggregate but Kwan shows why it is not universal

Kwan at 2024 has LF range +8.670/+6.476/+2.926 runs in 2022–2024.
Weighted +8.331 over 5,762.75 outs shrinks to +1.426 per 500 innings; the
saved calibration lowers it to +0.118. At 3,182.5 projected LF outs this
reduces range from +3.026 to +0.250. The unchanged arm forecast is +1.018.
Total defense falls +4.044 → +1.267, while actual is +11.486: the largest
calibration harm. Expanded value also worsens, 2.485 → 2.207 against 2.405:
the smaller defense estimate overcorrects the optimistic batting forecast,
2.726 versus 1.982. The lower defense estimate is not a talent success.

Marsh's history is nearly exact at +1.158/+1.133 defense, while the calibration
lowers it to +0.685. Benson's negative estimate (-0.633/-1.375) and calibrated
-1.131 help direction. Steer's total remains partial. These are saved historical
model outputs, not another fitted age or position weighting exercise.

## Ordinary value misses still require component checks

Smith at 2022 is the participant nearest the median absolute primary value
error among players with at least 100 actual PA and 300 fielding outs. His 1B
history is +1.351 weighted runs over 805.75 outs, but RF -1.959 over 1,514.5.
Rates +0.532/-0.651 give +0.156/-0.351 predicted runs; receiving adds -0.060.
Total -0.255 versus -3.746 is weakly directionally helpful. Expanded value
0.291 → 0.266 versus -0.537 remains an ordinary roughly 0.8-win miss.
His 268/228 PA and 0.710/0.242 batting explain additional error. Sheets's
negative defense history helps but batting still fails; González never plays;
Olivares has a partial total and must not be treated as a measured success.

Judge at the 2023 origin is the largest expanded-value false low. Forecast
536/704 PA and batting 5.142/11.047 dwarf the defense issue: forecast +0.595
versus -2.910 native runs. Positive arm history contributes +0.887, but range
and the CF/RF move are missed. Value 4.558 versus 10.413 is chiefly a hitter/
playing-time miss, not a reason to tune defense to Judge. Renfroe is partial,
Bryant plays much less than forecast and Castellanos remains negatively skilled.

Acuña is the largest expanded-value false high: 588/222 PA and batting
5.573/0.955 yield value 4.891 versus 0.650. Defense -0.911 versus -0.852
is unusually close, but that cannot rescue the workload/batting miss. Sánchez
and McCarthy exceed forecast participation; Lowe's hitting is overforecast.
None of these later outcomes supplies a permissible preseason player override.

## What survives the walkthrough

All twelve channel point errors improve versus neutral among actual measured
participants. The combined improvement is real development evidence for using
qualified MLB defense histories, not a blanket proof of every component or
full WAR. Extra range calibration has a smaller uncertain whole-value effect.
Unknown-all-channel players receive identical neutral/history/calibrated runs;
the 323 actual defenders in that origin-unknown group demonstrate the remaining
talent-identification gap. No lower-minors improvement is claimed.

The aggregate positional ledger remains too generous: it underprojects 1B/DH
use and overprojects SS, while the modeled skill histories overpredict net
defensive runs. The small value improvement must not conceal these cohort
problems or the clear individual reversals. Retain the matched, modular research
layer; resolve opportunity/position-budget consistency and practical sparse
talent evidence next, without another indiscriminate learner or prior sweep.
Frozen forecasts/explorer and 2026 selection are unchanged.
