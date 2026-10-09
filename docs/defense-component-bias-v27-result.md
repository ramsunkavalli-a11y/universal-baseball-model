# Why first base and catcher value are overestimated

The saved forecasts overestimate these components mainly because their skill
estimates are wrong, not because they assign too much playing time. Giving each
player his actual defensive opportunities does not remove the bias. There is
also no single penalty that fixes the individual mistakes: the same framing
recipe overrates Realmuto and underrates Hedges and Bailey.

This is a diagnosis of unchanged 2023–2025 forecasts, not an accuracy improvement
or a new defense model. The full defense goal remains unfinished.

## Actual playing time does not fix the totals

The following are native component runs on the unchanged complete twelve-channel
subset. The middle column uses the saved historical rate with actual future
opportunities. It is an explanatory calculation, not a deployable forecast.

| Season and component | Forecast | With actual opportunities | Observed |
| --- | ---: | ---: | ---: |
| 2023 first-base range | −5.01 | +1.60 | −64.60 |
| 2024 first-base range | −13.68 | −10.21 | −29.99 |
| 2025 first-base range | −11.55 | −6.66 | −60.95 |
| 2023 framing | +27.41 | +24.91 | +8.45 |
| 2024 framing | +13.06 | +19.23 | +7.17 |
| 2025 framing | +19.17 | +37.81 | +3.19 |

For example, the 2025 first-base error is +49.41 runs. Opportunity differences
contribute −4.89 runs and rate errors contribute +54.29. The 2025 framing error
is +15.98: opportunity differences contribute −18.65 and rate errors +34.62.
Opportunity errors partly conceal, rather than cause, the optimistic skill totals.

The complete subset has 4139, 4083 and 3892 players by origin. These are not full
league totals; missing measurements in another channel can remove a valid
catcher or first baseman from the complete comparison. All forecasts remain in
the audit, including 318 players with an incomplete combined outcome.

Using each channel's own measured actual defenders gives the same broad finding.
For first-base range, forecast / actual-opportunity prediction / observed totals
are −2.04 / +3.88 / −59.82 in 2023, −12.52 / −11.13 / −31.76 in 2024, and
−7.47 / −5.95 / −43.47 in 2025. First-base positive-exposure results remain unknown
for 17, 18 and 23 players respectively; they are not assigned zero skill.

For framing, the corresponding totals are +22.94 / +23.23 / +0.08, +17.09 /
+19.60 / +2.26, and +18.86 / +28.60 / +1.33. There are 102, 100 and 110 measured
actual catchers. The difference from full qualified framing totals in 2025 is
one catcher outside this forecast cohort, not a changed target.

Do not judge quality using the thousands of people with no future exposure.
Among measured actual defenders, first-base range error with actual opportunities
is 1.830, 1.933 and 1.914 runs; framing error is 4.944, 4.002 and 3.519. Near-zero
errors among non-catchers or non-first-basemen do not establish defensive talent.

## References and shrinkage need different treatment

First-base range is not reliably centered on zero in this native source. Full
qualified totals are +17.02, −10.64, −60.96, −46.90, −11.58, +10.49, −20.35,
−62.63, −32.56 and −43.47 runs from 2016 through 2025. The short 2020 season uses
its actual 46215 outs, not a fabricated full season. A zero shrinkage prior is
therefore not automatically an average first baseman in the source's units.
But this fluctuating history also rules out treating the exposed 2023 or 2025
deficit as a fixed universal penalty.

The source distinguishes range from receiving throws. Freeman and Olson can have
good receiving value without equally good range. Statcast describes receiving
as a separate difficulty-adjusted skill, not the same statistic as range.
[MLB receiving definition](https://www.mlb.com/glossary/statcast/first-base-receiving-scoops).
Infield range itself accounts for play difficulty and runner context; dividing
its runs by innings still does not make every player's opportunities identical.
[MLB range definition](https://www.mlb.com/glossary/statcast/outs-above-average).

Framing differs: full qualified annual totals are already near zero, ranging
from −8.08 to +4.73 runs in 2018–2025. Its rate uses received non-swing pitches,
not all pitches thrown or only shadow-zone pitches. Raw pitch counts, shadow
counts and run values were checked against the saved source. A first-base-style
reference correction or a blanket subtraction is not justified for framing.

In 2025, catchers with measured origin framing history deliver +15.21 runs while
those with no eligible MLB history deliver −13.87. The latter all receive a
zero quality prior. That is an information gap, not measured average ability.
It contributes to optimistic totals that year, but the same group delivers
+6.24 in 2023. Do not infer a universal bad-rookie-framer rule from one year.

The existing age calibration is not an untested remedy. With actual first-base
opportunities it improves totals but worsens individual error relative to history
in each of these years: 1.830 to 1.904, 1.933 to 2.081, and 1.914 to 1.917 runs.
This is existing exposed evidence, not a fresh comparison. Better league totals
are insufficient to adopt it. The earlier framing age learner also failed its
young-player/source checks; this audit does not reopen that same recipe.

## Player calculations

All fixed cases below use the 2022 cutoff and 2023 outcome. Rates are range runs
per 1500 outs or framing runs per 1000 received pitches. First-base history is
1500 × weighted runs / (weighted outs + 3000); framing is 1000 × weighted runs /
(weighted pitches + 6000). Recent-year weights are 1, 0.5 and 0.25. No new
candidate is present; the actual-opportunity column changes only the denominator.

| Player and component | Weighted runs / exposure | Shrunk rate | Forecast runs | Actual-opportunity runs | Observed runs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Freeman range | 3.518 / 6528 | +0.554 | +1.328 | +1.527 | +2.510 |
| Olson range | 2.405 / 6705.5 | +0.372 | +0.928 | +1.060 | −3.707 |
| Goldschmidt range | −0.706 / 5589 | −0.123 | −0.228 | −0.285 | +2.354 |
| Guerrero range | −4.294 / 5296.75 | −0.776 | −1.550 | −1.654 | −10.197 |
| Realmuto framing | 5.133 / 14436 | +0.251 | +1.965 | +2.460 | −14.428 |
| Willson Contreras framing | −1.668 / 10501.25 | −0.101 | −0.610 | −0.711 | −6.604 |
| Murphy framing | 11.447 / 13125.25 | +0.599 | +4.241 | +4.469 | +3.978 |
| Hedges framing | 4.133 / 10085.25 | +0.257 | +1.166 | +1.319 | +14.485 |

### Freeman and his comparisons

His 2020/2021/2022 range records are 1432/4074/4133 outs and +0.477/+2.126/+2.336
runs. The weighted record gives 68.5% reliability. Forecast exposure is 3595
outs versus 4135 observed. The prediction is sensible but low, not an example
where an across-the-board first-base penalty helps.

Origin-selected Rizzo, Cron and Hosmer have forecast/observed range of +0.385/
+4.975, +0.276/+1.248 and −0.161/+0.278. Rizzo's +4.785 in 2021 and −1.641 in
2022 illustrate annual movement; the shrinkage rule misses his 2023 rebound.
Freeman's receiving forecast is +1.932 versus +3.608 observed. His combined
defined-defense forecast is +3.259 versus +6.117, so range is not all his value.

### Olson and his comparisons

His annual range is −0.265/+0.440/+2.251 across 1498/4016/4323 outs. Forecast
3743 outs versus 4278 observed barely explains the miss: even actual opportunities
leave a +4.767-run rate error. His receiving forecast +2.942 versus +4.187 goes
in the opposite direction. Total defined-defense +3.870 versus +0.480 conceals
that component contrast.

Peers Walsh, Harold Castro and Taylor Jones have forecast/observed range −0.856/
−1.285, −0.269/0 and −0.001/0. Walsh's three negative annual records correctly
identify a negative direction, but the actual 552 outs are far below the 2291
forecast. Castro and Jones have no future first-base exposure, not confirmed
average talent or evidence that their historical estimates were correct.

### Goldschmidt and his comparisons

Range moves +2.497/+5.057/−3.859 in 2020–2022. The negative latest season makes
the weighted rate slightly negative; 2771 forecast outs versus 3460 actual
cannot explain the subsequent +2.354. Peer Belt also rebounds from a negative
latest season: −0.168 forecast versus +0.819 observed. Abreu reverses the other
way, +0.459 versus −3.672; Marwin Gonzalez has no future first-base exposure.
These are not uniformly predictable declines of older first basemen.

Goldschmidt's near-matched expanded value, 2.996 versus 3.072 custom wins, is not
proof that defense is right: defined-defense is −1.107 versus +4.218 and forecast
PA is 542 versus 687. Offsetting mistakes can make final value look accurate.

### Guerrero and his comparisons

His range is negative in all three known years, −1.709/−2.634/−2.550 runs.
The shrunk forecast correctly identifies direction but misses magnitude. Actual
3195 outs versus 2995 forecast change expected range by just −0.103 runs; the
remaining +8.543 error is in the rate. This is the largest positive range error
in the diagnostic, not proof that a new penalty fitted to Guerrero will work.

Peers Pratto and Torkelson are likewise pulled toward zero: −0.139 versus −3.041
and −0.247 versus −5.256. Toglia, with only 352 origin MLB first-base outs, goes
the other way: +0.181 versus +1.714. Guerrero's receiving also misses negatively,
−0.873 versus −3.558. Combined defined-defense is −2.423 versus −13.755.

### Realmuto and his comparisons

His 2020–2022 framing record is +0.311/+5.265/+2.423 runs over 2642/8385/9583
received pitches. Nothing in that fixed input directly reveals the size of the
2023 −14.428 result. Actual pitches raise, rather than lower, expected framing
from +1.965 to +2.460. This is the largest optimistic framing miss.

Peers Vázquez, Barnhart and Díaz finish +4.862/+5.521/−12.766 versus forecasts
+2.729/+0.167/−3.411. Díaz's dated negative 2021–2022 history supplies the right
direction but understates the loss. Barnhart's latest negative season does not
justify a generic decline: he rebounds. Realmuto's blocking is understated
(+1.887 versus +3.015) while throwing is overstated (+3.017 versus +1.162).
Framing dominates his total defense miss, +6.854 versus −10.250.

### Willson Contreras and his comparisons

His known framing progresses +3.397/−0.437/−2.299. The pooled estimate captures
the direction but shrinks it almost to zero. Forecast 6039 versus actual 7037
pitches explains only +0.101 of the total optimistic error; the rate contributes
+5.893. Nearly exact PA, 494 versus 495, does not rescue defense.

Narváez has positive annual framing history and declines from +3.070 forecast
to +0.932 observed. Bethancourt's single measured origin season yields +0.347
versus −2.951. Knapp has no future catching exposure. Contreras's throwing is
underestimated, +0.753 versus +2.690, while blocking +0.211 versus −0.199 is
overestimated. Expanded value nevertheless goes 2.359 versus 3.144, showing why
the direction of a component miss cannot stand in for a total-value diagnosis.

### Murphy and his comparisons

His annual framing rises −0.139/+4.933/+9.015 over 2949/7590/8593 pitches.
The +4.241 forecast is close to +3.978 actual; actual-opportunity prediction
+4.469 remains close. This is a reasonable individual forecast, not a failure
just because the cohort total is high.

Peers Smith, Heim and Kelly show forecast/observed +0.364/+3.776, +7.671/+11.911
and +0.452/−2.619. Heim's strong positive 2021–2022 history carries useful signal
but both workload and rate understate his contribution. Murphy's throwing and
blocking are also understated, +0.631/+1.618 versus +2.208/+4.082. His total
defined-defense forecast +6.490 versus +10.268 needs more value, not less.

### Hedges and his comparisons

His known framing is only +1.334/+2.528/+2.536 across 1907/6387/6415 pitches.
The shrunk rate +0.257 is far below his later performance. The earlier talent
review already found strong 2019 framing outside this fixed three-year window;
this audit does not rerun or tune recency to bring it back. Forecast 4538 pitches
versus 5134 actual explains only −0.153 runs, while rate error is −13.166.

Sánchez reverses from negative older framing to +2.708 observed versus −0.696
forecast. Trevino's very strong 2021–2022 history yields +8.179 versus +6.945,
partly because forecast opportunities exceed actual. Haase stays negative but
improves, −3.072 forecast versus −1.769 actual. Hedges's total defined-defense
+1.937 versus +16.385 is a serious talent miss despite PA being close, 220/212.

### Additional miss and ordinary cases

Carlos Santana at the 2023 cutoff is the largest pessimistic range miss. His
known 2021/2022/2023 range is +0.606/+2.630/+2.252. Weighted +3.719 runs over
5316.25 outs yields +0.671 per 1500 outs. The 2024 prediction +0.833 becomes
+1.677 with actual opportunities, still far below +10.963 observed. Peers
Abreu, Gurriel and Goldschmidt have forecast/observed −0.869/−1.990,
−0.252/−0.168 and +0.475/+0.160. Santana is a breakout miss, not evidence that
every older first baseman deserves an optimistic adjustment.

Weston Wilson is the median absolute-error first-base defender: no eligible MLB
range history gives zero predicted runs; his 2023 −0.598 is modest. Origin-only
peers Hollis, Delgado and Alvarez have no future first-base exposure. Their
zeros are contribution outcomes with unknown talent, not measurements of skill.

Patrick Bailey is the largest pessimistic framing miss: no eligible 2022 MLB
history gives zero quality and zero predicted framing, versus +16.963 in 2023.
Peers Fulford, Carlos Narváez and Micael Ramirez also have no origin MLB framing
history and no 2023 catching exposure. This comparison exposes an all-minors
information gap; it does not validate the average prior or explain Bailey away.

Rutschman is the median absolute-error framing defender. One measured year,
+8.630 over 6223 pitches, gives +0.706 after shrinkage; +6.029 forecast versus
+4.265 observed is reasonably close. His peer William Contreras instead improves
from negative known 2021–2022 history to +9.345, versus −3.061 forecast. Huff has
limited future exposure and −1.110 versus +0.586. Langeliers has sharply more
catching opportunities than forecast and −11.096 versus −0.246. Sparse history
can miss either development or persistent weakness; it is not all one problem.

The duplicate outcome-selected Guerrero and Realmuto groups retain their fixed
case calculations and peers. Fourteen groups and all 56 player records are
reviewed, including comparison exits, limited exposure and major reversals.

## Decision and next work

Retain the history baselines as qualified fallbacks; do not certify their totals,
minor transport or all-player talent. Test one past-only first-base position prior
in the native source units, instead of shrinking every record to raw zero.
Compare it against zero, unchanged history and the existing age calibration on
the same mature three-year MLB quality labels before checking annual value.
Keep observed quality and unknown minor estimates distinct. A historical prior
may improve a weak baseline; it cannot by itself identify Bailey or Guerrero.

Do not add a catcher penalty, force cohort totals to zero or repeat the failed
age polynomial. The framing fallback remains qualified, while earlier-compatible
quality and minor talent evidence are still needed for development and transport.
Return to that supported evidence after the bounded prior comparison, rather
than another opportunity-weight tournament.

## Evidence and verification

[The locked diagnostic](defense-component-bias-v27-contract.md),
[all cohorts and totals](../reports/model-evidence/defense-component-bias-v27/report.json.gz),
[player calculations](../reports/model-evidence/defense-component-bias-v27/player-walks.json.gz),
[unchanged value context](../reports/model-evidence/defense-component-bias-v27/player-value-context.json.gz)
and [independent source replay](../reports/model-evidence/defense-component-bias-v27/independent-review.json.gz)
preserve the audit. All 24864 focal histories, 120 cohort summaries, 2541 raw
native records and 56 player records replay. The original descriptive reference
entries omitted their channel label; the additive independent receipt identifies
each uniquely from native counts and runs without replacing the old output.

Integrity and player review pass. This is not a statistical improvement, source
repair, deployment approval or completed defense model. No forecast, explorer
or 2026 selection changed. The documentation skill kept component evidence,
opportunity diagnosis and final-value claims separate.
