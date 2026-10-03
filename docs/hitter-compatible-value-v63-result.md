# Keep the existing hitter forecast; correct its value reference

2026-10-03. The three new alternatives do not improve the overall forecast.
Keep V53's playing time and league-relative conditional hitting. Retain the
short-season reference correction in research value conversion. All 105 heads
replay and nineteen real player reviews are complete. Nothing changes the frozen
2026 forecast, protected outcomes or deployed explorer. The practical hitter goal
remains active; this closes the compatible-label/direct-value comparison.

## What actually changed

The [contract](hitter-compatible-value-v63-contract.md) holds all 30,506 historical
forecasts, 35 chronological whole-player cells, and baseline PA fixed. It compares
learning conditional hitting on the common origin league baseline, predicting
league-relative delivered offense directly, and predicting common-origin offense
directly. The two direct heads differ only in label centering. Comparing either
with the baseline also changes features, weighting and learner: the difference
cannot be attributed solely to joining playing time and talent.

All eight actual event counts independently match the dated count inventory for
63,282 source rows. No new data was collected. Target environments are historical
mature labels only, never forecasting inputs. Target 2020 is excluded; complete
2020-origin histories remain in training. All exits and non-arrivals remain.

The old origin replacement reference over-normalized the 2020 short season:
.00857066 per PA instead of .00316726. At Semien's mature 724-PA outcome this
would turn 5.274 common-origin offense into 9.186. Freeman and Guerrero show
the same problem. The [source review](hitter-compatible-value-v63-source-review.md)
traces eight cases before fitting. Neither existing PA nor hitting used this
reference as an input. This correction is necessary arithmetic, not an explanation
for all old misses or a newly improved forecast. Normal-season changes are tiny;
Judge's 2025 actual offense changes less than .001.

Baseline, actual and converted Steamer offense are all recomputed with the same
corrected reference. Original source labels and old recorded outputs are preserved.
The new baseline offense RMSE .453810 versus old .453826 reflects that measurement
change only. V53 PA and hitting predictions are exactly unchanged.

## Matched results

| Error measure | Baseline | Common conditional hitting | Relative direct offense | Common direct offense |
| --- | ---: | ---: | ---: | ---: |
| All-hitter offense RMSE | .45381 | .45800 | .46476 | .46714 |
| All-hitter offense MAE | .12916 | .13022 | .13686 | .13888 |
| Public-matched offense RMSE | 1.06131 | 1.07940 | 1.09121 | 1.09795 |
| Public-matched offense MAE | .71242 | .71975 | .74205 | .74907 |

On exactly 2,627 public matches, conditional hitting RMSE is 1.74350 baseline,
1.78159 common conditional, 1.77459 Steamer and 1.75336 ZiPS. These are fixed-event
batting wins per 600 PA on common origin units, not official wOBA or certified
park-neutral ability. Converted Steamer offense RMSE is 1.11866; uncertain archive
snapshot dates and custom conversion prevent a claim of superiority to Steamer.

Every alternative has a positive nominal player-cluster whole-population offense
MSE difference: +.00382 [.00275,.00493], +.01006 [.00697,.01334], and +.01228
[.00877,.01596]. Matched-public differences are also positive. These are repeatedly
exposed development results, not untouched confirmation or selection-adjusted
intervals. Full scores, yearly/stage totals and intervals are saved in
[the evidence directory](../reports/model-evidence/hitter-compatible-value-v63).

Direct models have a modest upper-minor RMSE improvement: .30695 baseline to
.30388/.30420. But MAE worsens .07681 to .08670/.08770. Upper-minor actual total
offense is 209.67 versus baseline 196.35, relative direct 247.53 and common direct
262.81. Never-arrived-upper-only totals improve under the relative direct head;
that narrower favorable result does not settle the full cohort. Lower-minor
RMSE and absolute error worsen. A blanket prospect boost is not supported.

## Why we are not keeping an attractive slice

The [full player walkthrough](../reports/model-evidence/hitter-compatible-value-v63/player-walkthrough.md)
uses actual counts, independently reconstructed pooled inputs, saved fitting
terms, actual training people and outcome-blind peers. It includes false highs,
false lows, gains, harms, ordinary cases and non-arrivals.

- Tatis's previous 42-HR MLB season reaches the direct trees through pooled
  quality, age and past role. Offense improves .184 to 2.787/2.522 against 3.333
  actual. But expected PA remains only 35 versus 635. This test did not solve
  his return opportunity or produce a valid new conditional talent grade.
- Kurtz's fourth-overall pick and four-year-college junior status are known
  (`4YR JR`, not junior college). Four HR in 35 A PA and
  fifteen AA PA also reach the inputs. All new heads still nearly miss his
  489 PA and 5.838 offense. Langford improves modestly in direct value, but
  unchanged 43 PA against 557 is still a major readiness miss. Their absence
  from the completed preseason ranking is not absence of draft pedigree.
- Judge's 2016 AAA power and scouting reach the model, but all arms miss the
  extreme next-year breakout. Established Judge gets worse, too: 2024-origin
  offense falls 5.666 to 5.412/5.186/4.887 against 9.393 actual. Raw common
  centering is not a successful way to repair superstar compression here.
- Salas's high rank adds about 1.1 offense wins in the direct trees. Their
  1.155/1.176 expected offense exceeds even the physical maximum 1.042 at
  retained expected PA 7.224. Actual next-year MLB PA is zero. This is failed
  integration of prospect quality and immediate opportunity, not a verdict
  on his eventual talent.
- Chris Davis becomes an even larger false high under common centering.
  Bichette and Seager become worse delivered-value misses under direct heads.
  These outcomes cannot be fixed by giving every young/good historical hitter
  more projected value.
- Nearly perfect offense matches for Hicks, Azócar and Torrens hide large PA
  misses. Hicks is 197 projected versus 453 actual PA; his predicted rate is
  too high, offsetting too little use. A lucky total is not a good decomposition.

The physical envelope uses the minimum/maximum fixed event weights and expected
PA, a mathematical constraint rather than an empirical training ceiling. There
are 469 relative-direct and 1,574 common-direct incompatibilities, mostly away
from current MLB players; baseline and common conditional product have none.
Some are numerically small. Salas shows the material mechanism. Values were not
clipped to conceal contradictions. Direct value cannot simply be divided by
the unchanged PA and labeled hitting ability.

Saved common-rate terms also show 2024's shared reorganization contribution near
-.64 instead of roughly -.26 in several baseline cases. That shifts established
hitters and minors together. The data permit a historical association, not a
causal reorganization effect or a certified future ball/run-environment forecast.
Year/stage losses remain visible. Twenty-person profile thresholds are warnings,
not guarantees; extreme Judge and fast elite-entry cases retain support limits.

## Practical decision

Keep the strongest coherent research baseline and the reference correction.
Withhold these three alternatives, without declaring all joint, event or boosting
models disproven. The direct comparison is valid for these locked targets and
representations, not every possible integration design.

The current baseline is reasonably competitive in matched hitting and PA RMSE,
but not a finished universal hitter system. Public PA RMSE is 138.49 against
Steamer 135.38; MAE is 106.87 against 92.08, about 16.1% higher and still outside
the predeclared 15% practical goal. Immediate elite prospect readiness, rare
returns, origin totals, source dating and true park-neutral ability remain
qualified. Do not conceal those gaps or waive them because one converted value
score looks favorable.

Next: freeze the best coherent next-year research candidate and complete its
uncertainty/model-card and team-filtered historical handoff. No further generic
library, penalty, calendar-centering or health sweep is justified by this batch.
Full defense, longer paths, six years of club control and market value are still
separate unfinished work, not supplied by next-year offense.
