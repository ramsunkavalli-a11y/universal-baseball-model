# Minor league history improves arrival prediction but not overall value

2026-10-04. Keep this as an arrival research challenger. It handles the canceled
minor-league season more usefully than the current calendar-slot model, but it
is not a finished hitter-model upgrade. Established-player/public forecasts
are unchanged, batting-value improvement is negligible, and important prospect
misses remain. The full practical hitter goal stays active.

## What changed

The [prefit contract](hitter-available-season-history-contract.md) replaces three
calendar minor-history slots with the last three available affiliated seasons.
It skips only the canceled 2020 season, not individual injuries or absent player
records. At origin 2021, actual source years become 2021, 2019 and 2018.
At origin 2022 they become 2022, 2021 and 2019. Slot weights stay 1, .8 and .6,
with the same stabilized event priors. Actual age, draft elapsed, calendar gaps,
scouting dates, roster status and MLB/Mexico history remain unchanged.

This retains an older season and changes some weights; the test cannot separate
those effects. It is different from the earlier test that removed an unavailable
block, which helped 2021 but clearly harmed 2022 probability accuracy.

All 63,282 source rows and 30,506 held-player forecasts remain. Training outcomes
must mature by the origin, with no 2020 targets and no held-player identities.
All 70 actual control/candidate preflights precede fitting. Thirty-five control
classifiers replay exactly; fifteen pre-pandemic comparisons have identical
matrices and reuse those controls. Only twenty new classifiers are fitted.
All thirty-five candidate classifiers replay. The classifier uses the same
251 inputs/settings; conditional workload and hitting are fixed. Probability
changes route to all never-debut players, not a favorable year or level subset.

Four source walks precede fits; twelve actual model walks follow scoring.
[Execution repairs](hitter-available-season-history-execution-clarification.md)
preserve failed attempts and the sealed prefit runner. They do not change fits.
Inputs combine season-end statistics with following-preseason rankings at the
dates recorded in each fold, not a strict December 31 or fully refreshed
Opening Day forecast. All historical scoring is exposed development evidence.

## Scores and cohort totals

There are 24,199 never-debut forecasts for 10,076 people. Scores weight target
years equally. Totals sum player-season forecasts; they are not unique careers.
Value is fixed-event batting plus replacement in custom win units, not full WAR.

| Never debuted | Current | Available season history |
| --- | ---: | ---: |
| PA RMSE | 27.2521 | 27.0808 |
| PA mean absolute error | 4.7639 | 4.7986 |
| Arrival Brier | .019800 | .019462 |
| Arrival log loss | .070921 | .069286 |
| Delivered batting value RMSE | .152257 | .152223 |
| Expected debuts versus 787 actual | 677.03 | 701.47 |
| Expected PA versus 98,328 actual | 81,849 | 84,481 |

Probability scores improve about 1.7% and 2.3%; PA RMSE improves .63%.
Mean absolute error worsens .73%. Nominal 1,000-draw player-clustered paired
95% intervals favor the new representation for PA MSE (-9.31, [-16.81,-2.13]),
Brier (-.000338, [-.000479,-.000201]) and log loss (-.001635,
[-.002234,-.001050]). Value MSE is -.0000102 with interval
[-.0001211,+.0000939]: no clear integrated value gain. These intervals do not
account for every shared era shock or repeated historical model selection.

| Origin predicting following year | Current expected debuts | New | Actual | Current expected PA | New | Actual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2021 | 77.63 | 96.70 | 158 | 10,432 | 12,564 | 18,944 |
| 2022 | 106.31 | 112.21 | 106 | 13,575 | 14,087 | 14,072 |
| 2023 | 115.11 | 115.95 | 107 | 14,725 | 14,866 | 11,697 |
| 2024 | 99.77 | 98.40 | 105 | 12,248 | 12,095 | 15,190 |

The 2021 probability and PA gains are the main benefit. At 2022 Brier/log loss
improve slightly and uncertainly; PA RMSE worsens 27.2246 to 27.3627 and MAE
worsens. A near-exact 2022 PA total is not proof of good individual forecasts.
The 2023 overprediction persists and value worsens; 2024 value also worsens
slightly. Pre-pandemic inputs, fitted controls and scores are identical.

Upper-minors PA RMSE improves 55.1267 to 54.7853 but MAE worsens 18.7321 to
18.8654; expected PA rise 74,239 to 76,755 versus 92,891 actual. Lower-minors
PA RMSE worsens 7.9664 to 7.9912, MAE .6217 to .6271, and expected PA rise
7,055 to 7,222 versus 5,194 actual. Lower-minors value MSE worsens .00000891
with nominal interval [.00000217,.00001655]. Its small scale is not a reason
to conceal a consistent harm. No post-result upper-only route is adopted.

The translated hitting anchor with unchanged PA has value RMSE .151662;
with the new PA it is .151630. It does not turn this into a meaningful value
upgrade. The matched 2,627 public-player forecasts remain exactly unchanged:
PA RMSE 138.33/MAE 106.41 versus Steamer 135.38/92.08. The MAE remains about
15.56% higher, slightly outside the practical plan's 15% allowance. Other
public-data timing/environment qualifications remain intact.

## Twelve player walks

Cases include six fixed before fitting, largest gain/harm and false high/low,
an ordinary active case, and two explicitly postfit lower-level supplements.
The supplements do not change forecasts or selection rules. Each saved walk
includes actual counts/games by dated level, both complete input vectors,
saved classifier paths, fixed workload/rate paths and origin-selected peers.
Probabilities mean any following-year MLB PA, not lifelong MLB success.

| Player and origin | Current expected PA | New | Actual next year | What the actual model walk shows |
| --- | ---: | ---: | ---: | --- |
| Julio Rodríguez 2021 | 254 | 280 | 560 | Restored A/DSL history helps arrival; fixed workload and hitting remain too low. |
| Bobby Witt Jr 2021 | 279 | 292 | 632 | More weight on 2019 rookie evidence modestly helps; hitting rate is reasonably close. |
| Terrin Vavra 2021 | 86 | 103 | 103 | Restored history improves PA but value worsens .265 to .319 versus .238. |
| Jordan Walker 2022 | 155 | 164 | 465 | No own-input change: improvement comes from refitting training, not recovered personal history. |
| Wyatt Langford 2023 | 215 | 198 | 557 | Unchanged inputs, refitted arrival worsens; hitting rate was close. |
| Nick Kurtz 2024 | 10 | 9 | 489 | Elite thin-sample arrival and hitting misses remain; no positive refined-profile training person. |
| Jeremy Peña 2021 | 47 | 109 | 558 | Largest PA gain: debut probability .266 to .621; workload 176 if active remains much too low. |
| Henry Davis 2022 | 131 | 73 | 255 | Largest PA harm from refit, not own history. Current near-exact value hides canceling PA/rate errors. |
| Austin Meadows 2016 | 298 | 298 | 0 | Unchanged false high: good upper-level prospect information does not guarantee debut timing. |
| Bryan Reynolds 2018 | 13 | 13 | 546 | Unchanged large arrival/workload/talent miss, despite substantial broad training support. |
| Diego Cartaya 2022 | 117 | 130 | 0 | More rookie history and refitting worsen an A-plus immediate-arrival false high. |
| Juan Soto 2017 | 2 | 2 | 494 | Rare rapid low-A jump is missed; one positive refined training example, not a solved teenage profile. |

Peña has 133 AAA and 27 complex PA in 2021, ten HR, eight walks and 41 K;
older A/A-plus 474 PA and short-season 156 PA are preserved with their real
dates. The old fitted model on rebuilt inputs gives .582 arrival probability,
versus original .266; the new model on old inputs gives .415. Both input meaning
and refitting contribute. That is a useful mechanism, but not causal attribution.

Davis has 255 mixed A/AA/A-plus/complex PA and first-pick pedigree. He has no
2019 professional record, so all own inputs stay the same. The refit reduces
upper-level role/exposure path contributions. Current value .368 versus .363
actual looks excellent only because low PA and optimistic hitting cancel:
rate -.198 versus realized -1.569. Do not mistake that value match for talent
accuracy. The new value .205 is worse, not a hidden improvement.

Cartaya is a 20-year-old catcher with 445 A/A-plus PA, 22 HR, 60 BB, 119 K,
rank score .87 and 40-man protection. The saved logit path puts substantial
weight on roster protection. His nearest listed age/level peers include Marte
(123 future PA) and Luciano (45), while Lopez and Valenzuela have zero. A low
level does not categorically bar next-year arrival. Conversely, Cartaya's zero
next-year PA does not mean zero long-term talent.

Soto has only 123 current A/complex PA at 18, but nine strikeouts, three HR,
ten walks and a .72 fresh rank score. The model recognizes his rank yet largely
discounts immediate readiness. Same-age listed Taveras has zero next-year MLB
PA; weaker peers also have zero. Those comparisons show timing uncertainty,
not that Soto's subsequent 494 PA were adequately represented. No player-specific
boost or automatic large teenage forecast follows from this outcome.

Peer selection uses age, dominant/highest level, exposure, positions, ranks/draft
and event rates without future outcomes. It is still imperfect: roster protection,
injury/rights context and detailed scouting may differ. Some thin-entry peers
have much weaker pedigree. Their zero outcomes cannot explain away Langford,
Kurtz, Peña or Reynolds. Refined all-training support is empty for 67 prospect
forecasts; positive-arrival support is empty for 13,473. Keep those warnings.

## What the roster diagnostic does and does not support

The corrected diagnostic keeps Mexico separate from affiliated AA/AAA. The
first local diagnostic used a helper that pooled those levels and is explicitly
superseded; no forecast changed. Among 49 A-plus-only protected cases (46 people),
current expected debuts are 12.74 versus 15 actual, but PA total is 1,707 versus
991. The new model gives 13.52 expected debuts and 1,833 PA. Thus Cartaya does
not justify globally reducing protected prospects' debut chances: the group
already undercounts arrivals while overallocating PA. This is a small descriptive
group, not an independent causal test or an approved workload adjustment.

By contrast, actual AA/AAA cases without roster protection have 360.38 current
expected arrivals versus 469 actual, and 42,554 PA versus 57,383; the new model
gives 378.53 and 44,240. These broad groups contain different talent and eras.
They locate residual opportunity errors without establishing one universal fix.

## Decision and remaining work

Retain the available-season representation as a supported arrival research
challenger, alongside the unchanged current opportunity and translated talent
anchors. Do not replace the integrated model, deploy it, or select a 2021-only
or upper-minors-only hybrid from these results. This resolves the bounded
history-clock comparison, not every pandemic-era effect. Stop further COVID
feature/boost sweeps unless a new source defect is actually demonstrated.

Next complete a coherent delivered-value/readiness comparison using these
saved anchors and the already reviewed talent alternatives. Focus on the
remaining combination of thin elite entry, level, pedigree, roster meaning
and workload rather than explaining every miss through one component. Reconcile
earlier feature-rich winners' target and training provenance before bringing
them back. Public established-player workload, unknown foreign production,
calibrated uncertainty and longer supported horizons remain unfinished.

The original 3,907-player frozen 2026 forecast and all 31 sealed files verify
unchanged; protected outcomes were not opened. No deployed explorer changes.
The repository receipts are not a self-contained clean-clone reproduction:
saved fits and detailed historical source exports remain local.

Evidence: [scores](../reports/model-evidence/hitter-available-season-history/scores.json),
[intervals](../reports/model-evidence/hitter-available-season-history/intervals.json),
[primary walks](../reports/model-evidence/hitter-available-season-history/cases.json),
[lower-minors walks](../reports/model-evidence/hitter-available-season-history/cases-supplement.json),
[corrected roster diagnostic](../reports/model-evidence/hitter-available-season-history/roster-readiness-diagnostic-separate-mexico.json),
[final review](../reports/model-evidence/hitter-available-season-history/final-report.json).
