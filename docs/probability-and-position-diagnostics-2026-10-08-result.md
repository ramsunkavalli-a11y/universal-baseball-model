# Playing time calibration and outfield positional credit

2026-10-08. Overall playing-time calibration hides meaningful differences between
player groups. Same-season outfield comparisons do not justify a large reduction
in the existing CF premium once range and position use compatible reference
points. Neither finding changes the frozen forecasts or explorer.

These are the two fixed diagnostics requested after
[Szymborski's probability example](https://x.com/DSzymborski/status/2089018876080124113)
and [Lau's positional-value discussion](https://x.com/903124S/status/2093001808780390412).
The [test contract](probability-and-position-diagnostics-2026-10-08-contract.md)
preceded scoring. The uncertainty test uses the older saved workload-risk model,
not a newly fitted distribution around the current production hitter model.
It cannot establish current hitting, full WAR or six-year value uncertainty.

## Overall calibration masks prospect readiness errors

There are 30,506 player-origins for 11,020 distinct people, predicting next-year
MLB PA in 2017–2019 and 2022–2025. Non-arrivals and exits stay in the population.
The saved distribution has a separate zero-PA probability and a beta-binomial
positive workload spread. Every appearance probability, workload mean and
batting-value mean remains unchanged. No 2026 outcomes are used.

For a continuous calibrated distribution, about 10% of outcomes should land in
each forecast percentile tenth. PA is discrete, often with a very large atom
at zero. We therefore integrate the outcome's possible randomized percentile
across its CDF interval, rather than assign all tied zeros to one percentile.
This removes an arithmetic artifact; it does not make a poorly allocated
arrival forecast good. Results below weight represented target years equally.

| Population | Forecasts | Outcomes in top percentile tenth | Player-cluster interval | Interpretation |
| --- | ---: | ---: | ---: | --- |
| All | 30,506 | 9.97% | 9.80–10.14% | Looks close overall |
| Current MLB | 4,541 | 8.37% | 7.62–9.19% | Upper tail happens less often than forecast |
| Upper minors never debuted | 5,454 | 12.03% | 11.35–12.69% | Good outcomes happen more often than forecast |
| Lower minors never debuted | 17,852 | 9.86% | 9.80–9.94% | Many zeros overwhelm the view of rare arrivals |
| Previously debuted but absent | 1,766 | 8.90% | 7.97–9.83% | Aggregate return/risk allocation still needs care |

The intervals are nominal player-cluster development intervals, conditional on
these repeatedly exposed seasons. They do not include common season shocks or
model-selection uncertainty. All ten bins, each origin, forecast probability
bands, MLB age bands and unsupported-profile groups are saved in the evidence.

The strictly-above-P90 comparison makes the zero issue particularly clear:
current MLB has 8.32% observed exceedance versus 9.90% predicted; upper minors
has 6.92% versus 4.84%; lower minors has 0.246% versus 0.400%. The last two expected
rates are not 10% because many individual P90 values are zero. Compare observed
rates with the distribution's actual exceedance probabilities, not a continuous
rule applied mechanically to tied zero forecasts.

The count checks expose failures the overall percentile chart hides. These are
pooled counts across the fixed historical forecasts, not full-league budgets.

| Population | Expected MLB appearances | Actual appearances | Expected 400 PA seasons | Actual 400 PA seasons | Expected total PA | Actual total PA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current MLB | 3,547.9 | 3,596 | 1,278.3 | 1,403 | 1,129,697 | 1,156,856 |
| Upper minors never debuted | 589.5 | 730 | 32.5 | 59 | 74,239 | 92,891 |
| Lower minors never debuted | 82.0 | 54 | 2.1 | 2 | 7,055 | 5,194 |
| Previously debuted but absent | 167.0 | 155 | 5.6 | 9 | 17,187 | 15,309 |

Upper-minors arrivals are about 19% below reality, and their regular seasons
are about 45% below reality. Lower-minors arrival counts are about 52% above
reality, with only 54 positive outcomes supporting their conditional workload
diagnostic. A global widening rule cannot fix both groups. The conditional
positive-workload view must stay separate: among current MLB participants its
top tenth contains only about 7.9% of outcomes, while middle bins are overfilled.
This suggests the spread/shape is not simply too narrow everywhere.

The saved spread still beats its narrow mean-matched binomial control on CRPS:
13.577 versus 16.803 PA overall, 72.098 versus 91.991 in current MLB, and 12.332
versus 13.441 in upper minors. This reproduces earlier distribution-score
evidence; it is not a new improvement or a comparison with public-system ranges.
A better proper score and a nearly uniform pooled percentile chart do not
establish subgroup readiness calibration.

## Player checks distinguish probability errors from ordinary surprises

All fourteen original workload cases were retraced using their saved dated
counts, full actual inputs, fitted-head effects, nested spread fit and origin-only
peers. Their full traces are preserved in
[the case evidence](../reports/model-evidence/probability-position-2026-10-08/workload-cases.json.gz)
and the [earlier readable upstream walkthrough](hitter-workload-risk-player-walkthrough.md).
Percentile placement below means the realized PA's position within this saved
forecast, not a percentile ranking of player talent.

| Player and origin | Origin evidence | Chance of any MLB PA | Expected PA | P10 / P50 / P90 PA | Actual next-year PA | What this check shows |
| --- | --- | ---: | ---: | --- | ---: | --- |
| Nick Kurtz 2024 | 35 A PA and 15 AA PA | 6.1% | 10.2 | 0 / 0 / 0 | 489 | Outcome around the 99.9th percentile; old arrival estimate overwhelms the positive spread |
| Wyatt Langford 2023 | 200 minor PA, including 80 AA/AAA PA and 10 HR overall | 59.9% | 214.9 | 0 / 194 / 523 | 557 | About the 92.9th percentile; a plausible upside outcome but low expected opportunity |
| Pete Alonso 2018 | 574 AA/AAA PA and 36 HR | 80.4% | 215.0 | 0 / 199 / 459 | 693 | About the 99.8th percentile; strong upper-minors evidence did not translate to enough workload |
| Aaron Judge 2016 | 410 AAA PA, then 95 MLB PA with 42 K | 92.5% | 309.9 | 56 / 305 / 561 | 678 | About the 98.1st percentile; much more than a moderate upper-range season |
| Aaron Judge 2024 | 704 recent MLB PA after 458 and 696 | 99.1% | 530.8 | 315 / 552 / 720 | 679 | About the 81st percentile; strong season fits the forecast range |
| Matt McLain 2024 | 403 MLB PA in 2023, no MLB PA in 2024 | 44.7% | 131.7 | 0 / 0 / 414 | 577 | About the 98.2nd percentile; absent-season return mechanism is consequential |
| Brandon Belt 2023 | 404 MLB PA and 19 HR following 298 PA | 64.6% | 244.2 | 0 / 239 / 559 | 0 | Zero has 35.4% probability; surprising non-employment is not an impossible forecast outcome |
| Wander Franco 2023 | 491 recent MLB PA | 99.0% | 559.5 | 350 / 584 / 737 | 0 | Zero has only 1.0% probability; this old generation lacks adequate availability context |
| Jed Lowrie 2018 | 680 recent MLB PA after 645 | 90.7% | 458.7 | 111 / 498 / 703 | 8 | Around the 9.3rd percentile; downside injury season, not evidence that every healthy regular should have a tiny mean |
| Rhys Hoskins 2023 | No 2023 MLB PA after 672 in 2022 | 10.1% | 26.3 | 0 / 0 / 16 | 517 | About the 99.4th percentile; an injury absence was badly represented in this old forecast |
| David Ortiz 2016 | 626 MLB PA, plus known retirement rule | 0% | 0 | 0 / 0 / 0 | 0 | Correct degenerate zero forecast contributes evenly to randomized percentile bins; it supplies no evidence about active-player spread |
| Matt McLain 2023 | 403 MLB PA and 16 HR after AAA success | 98.5% | 599.4 | 399 / 632 / 762 | 0 | Zero has 1.5% probability; the opposite return/injury case must remain visible |
| Fernando Tatis Jr. 2022 | No 2022 MLB PA; 546 PA and 42 HR in 2021 | 13.4% | 39.7 | 0 / 0 / 174 | 635 | About the 99.7th percentile; this is the already-known old absence/suspension representation failure, not a new claim about the repaired model |
| Adam Engel 2021 | 140 MLB PA plus 60 AAA PA | 94.2% | 260.0 | 49 / 244 / 493 | 260 | About the 53.4th percentile; useful ordinary control rather than a list containing only misses |

The original origin-only peer selections also expose limits. Kurtz's nearest
available input peers include Luis Ariza and Carlos Avila, both forecast near
zero and both non-arrivals; that does not certify support for an elite recent
draftee. Langford's peers include Crews (132 actual PA) and Montgomery (zero).
Judge's 2016 peers include Renfroe (479) and Moya (zero). Belt's peers include
Martinez (495) and Blackmon (499): his non-employment cannot justify labeling
all comparable veterans finished. Engel's imperfect input peers include Trout
and Jankowski; proximity in recorded exposure is not proof of equal talent.

These cases describe the saved older workload model. They do not reopen closed
suspension/retirement tests or erase subsequent repairs. The new finding is how
their probability failures coexist with apparently good overall percentile
calibration, not that these previously reviewed misses were just discovered.

## Raw range and positional value answer different questions

The outfield comparison uses 2016–2025 certified native range and official
position innings. It includes 266 player-seasons from 165 people with at least
150 measured innings at CF and 150 at LF/RF combined in the same season.
Official records identify 274 otherwise eligible player-seasons; eight have a
missing measurement in a corner stint and are excluded from measured pairing,
not credited zero defense. Small, invalid and wholly missing stints remain in
the coverage audit. The 2020 short season remains visible with six eligible
pairs; 2021 has 39. Annual estimates vary considerably.

We compare three quantities: native Statcast range, range relative to the
average player at each position, and that position-relative range plus the
fixed CF-versus-corner positional premium. This follows the distinction behind
[FanGraphs' outfield accounting correction](https://blogs.fangraphs.com/a-fangraphs-war-fielding-update/).
Raw Statcast and position-relative measurements cannot receive interchangeable
positional credit without explaining the reference shift.

| Comparison | Paired player-seasons | People | Descriptive CF premium balancing position-relative range | Player-cluster interval |
| --- | ---: | ---: | ---: | --- |
| CF versus combined corners, at least 150 innings each | 266 | 165 | 8.72 runs / 1458 innings | 7.31–10.22 |
| At least 300 innings each | 90 | 69 | 9.72 | 7.57–11.81 |
| CF versus LF separately | 136 | 101 | 9.22 | 6.89–11.42 |
| CF versus RF separately | 130 | 90 | 9.20 | 6.64–11.62 |

The primary calculation gives each person equal weight across repeated seasons.
Row weighting gives 9.08 runs and harmonic-exposure weighting gives 9.14. These
are declared sensitivities, not choices selected to defend the existing 10-run
premium. The higher-exposure sample and both corner comparisons also include
10 in their intervals. This evidence does not justify a large immediate cut.

Native range differs little between CF and corners for these same people:
−0.344 runs per 500 innings, interval −0.864 to +0.127. This is consistent with
the broad observation in Lau's thread. But subtracting each position's average
changes the reference: average CF range is higher than average corner range.
The average switcher's position-relative difference becomes −2.992 runs per
500 innings. Adding the current schedule restores 3.429, leaving +0.437 runs
per 500 innings, or about +1.28 over 1458 innings, rather than an unexplained
full 10-run advantage for the same player.

This is not proof of CF's market scarcity or a causal replacement-value constant.
Positions are selected, opportunities and experience differ, and range excludes
arm value. The seasonal references are actual accounting averages, not forecast
inputs or evidence of better predictions. Moving a reference from the range
column into the position column preserves the total exactly; removing a reference
while keeping an incompatible positional schedule changes the valuation.
All 266 accounting identities pass.

Annual equalization estimates range from about 4.30 runs in 2016 to 12.08 in
2018, with 2020 at 5.84, 2021 at 10.55 and 2025 at 8.12. Sample variation, game
environment and assignments matter. Player resampling does not capture common
year-level shocks. Do not turn these into annually retuned constants.

## Outfield player checks show why one switch cannot set the premium

The six focal cases include fixed profiles, opposite extremes and an ordinary
case. Rates below are runs per 500 innings. CF/corner reference means are
measured for the same year and corners are weighted by that player's LF/RF
innings. Every raw source row and three exposure-selected same-season peers
are saved in [the position case evidence](../reports/model-evidence/probability-position-2026-10-08/position-cases.json.gz).

| Player and season | CF innings and raw runs | Corner innings and raw runs | Raw CF minus corner rate | Position-relative difference | After standard CF credit |
| --- | --- | --- | ---: | ---: | ---: |
| Mookie Betts 2021 | 212; +1.838 | 751.7; +0.292 | +4.141 | +1.688 | +5.118 |
| Cody Bellinger 2024 | 403.7; −0.308 | 390.3; −0.865 | +0.727 | −2.114 | +1.315 |
| Harrison Bader 2025 | 568.7; +2.369 | 537; +3.006 | −0.716 | −4.097 | −0.668 |
| Nelson Velázquez 2022 | 198; −3.398 | 238.3; +0.807 | −10.274 | −13.106 | −9.677 |
| Michael Bourn 2016 | 609.7; +2.686 | 214; −2.820 | +8.791 | +7.304 | +10.733 |
| Luis Matos 2024 | 156.3; −1.979 | 166; −2.006 | −0.287 | −3.181 | +0.249 |

Bellinger is a balanced-stint example: similar native range in CF and RF becomes
a more negative CF grade relative to stronger CF peers; the standard credit
mostly offsets that reference change. Bader's corner range was better, so his
case would need about 11.95 runs to equalize; Betts goes the other way and implies
a negative premium for that individual season. Neither is a reason to customize
the constants around those players.

Velázquez and Bourn are the opposite extremes: their individual equalization
figures would be +38.22 and −21.30 runs over 1458 innings. Such values should not
be installed as league constants. Range measurement noise, small samples,
position-specific skills and selected assignments cannot be separated here.
Matos has almost identical negative raw range in both roles; position-relative
accounting plus the standard schedule brings the difference close to zero.
Equal grades do not imply good defense: he was negative in both roles.

Same-season exposure-selected peers remain mixed. Bellinger's peers are
Vierling, DeLuca and Suwinski; their implied gaps are +1.55, +16.85 and −19.21.
Bader's are Adell, Simpson and Marsh, at +13.79, +15.85 and +17.06. Matos's are
Castro, Martin and Fairchild, at +28.13, +10.87 and +30.10. Exposure matching alone
does not identify a common player-quality or position-experience group.

Rafaela has no eligible balanced CF/corner season under the fixed thresholds,
so he is reported missing rather than forced into this comparison. SS/1B has
only nine same-season pairs at 150 innings each and one at 300. It cannot support
a credible universal infield adjustment from this dataset, and its range
reference is not simply interchangeable with the shared outfield reference.
Catcher value and ABS require separate evidence.

## What changes in the testing standard

Use the full distribution, event counts and player-group checks together. Do not
approve risks from an attractive all-player percentile chart or inclusive
coverage rate. Retain non-arrivals for population workload/value evaluation;
positive conditional talent and workload remain different questions. The
current production hitter model still needs genuinely nested hitting/value
uncertainty before we can publish comparable percentile claims for it.

Keep the existing positional schedule as a research comparison and preserve the
recent outfield reference repair. This diagnostic supports checking coherent
accounting, not changing the schedule to 8.72 or claiming current constants are
universally correct. A future revision must include arm value, broader position
transfer and the interpretation of replacement value, rather than selecting
constants to make a few stars look right or to beat an outcome constructed with
those same constants.

The independent review reconstructs all 30,506 saved point forecasts, 226 scalar
distributions and 2,486 quantiles, all 266 position pairs from native and official
sources, 14 workload source/head walks and six position cases plus 18 peers.
Six unit tests cover discrete ties, impossible outcomes, tiny-tail numerical
resolution and invariant reference transfer. Two initial execution failures
occurred before scored summaries: tiny binomial masses lost CDF resolution, then
an expanded bootstrap allocation exhausted memory. Additive receipts preserve
those failures; corrected arithmetic and memory-efficient sums do not change
recipes, populations, thresholds or fitted forecasts.

The relocated old forest reference on disconnected D: remains explicitly
unverified and is not used in the new comparison. Existing historical feature
vintage and support qualifications remain. The current frozen forecast and
explorer hashes are unchanged. This is development evidence and neither model
improvement nor deployment approval. The separate locked first-base prior test
remains the next defense-model experiment.

Evidence: [calibration](../reports/model-evidence/probability-position-2026-10-08/workload-calibration.json.gz),
[positions](../reports/model-evidence/probability-position-2026-10-08/position-comparison.json.gz),
[independent checks](../reports/model-evidence/probability-position-2026-10-08/independent-review.json.gz).
