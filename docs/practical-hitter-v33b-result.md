# Practical hitter milestone: corrected working baseline

2026-10-02. This is a working research model, not the completed hitter system.
The larger goal remains active. No protected 2026 outcomes were used and no
frozen 2026 forecasts were replaced.

## What we now have

The retained assembly estimates next-calendar-year MLB plate appearances, then
combines those opportunities with a contribution-weighted batting estimate.
Its output is **batting plus replacement wins**, not full WAR, current prospect
talent, six years of club control, or trade value.

The workload model uses histogram gradient boosting. It sees three seasons of
actual hitting counts, age, workload, position listing and known draft context.
Counts are pooled at weights 1, .8 and .6, separately across 14 source-league
buckets, before adding one fixed small-sample prior. AAA is not MLB; Mexican
League hitting is not affiliated AAA. A canceled MiLB season adds no observations.
Actual 2020 MLB counts remain available, with the shorter schedule identified.

The batting head is ridge regression using fixed physical scales rather than
rare-league training standard deviations. It is fitted on future active players,
weighted by their actual MLB PA. Expected contribution is expected PA times
batting rate plus the origin replacement yield. This is a useful approximation,
not a coherent joint distribution of health, opportunity and performance.
The rate must not be advertised as a certified current MLB-equivalent talent
grade for prospects.

Known draft selections are used only after their dated cutoff. Unknown school
class or international investment remains unknown. No new college collection,
invented signing bonus, future team assignment or hindsight-based prospect boost
was used. The independent gain from draft features over pooled evidence is still
statistically uncertain.

## What was actually improved

All comparisons retain the same identities, including non-arrivals and exits.
Forecast years receive equal weight. Tests separate whole players and train only
on outcomes mature by that forecast cutoff. These are development comparisons,
not a fresh untouched final test.

| Matched comparison | Older UBM | Working baseline | Public reference |
|---|---:|---:|---:|
| PA RMSE, 4,396 older V24 forecasts | 128.62 | 124.65 | — |
| PA RMSE, 1,789 public-matched forecasts | 149.12 | 143.96 | Steamer 135.02 |
| PA MAE, same public forecasts | 116.01 | 110.56 | Steamer 92.40 |
| Batting + replacement RMSE, V24 match | 0.91725 | 0.90951 | — |
| Batting + replacement RMSE, older broad N match | 0.44582 | 0.44458 | — |

The PA improvement over V24 has a player-cluster interval favoring the new
model. The batting-value improvements over V24 and older N are small and
uncertain. Against the **corrected same-fold direct tree control**, the linear
assembly improves contribution RMSE from 0.45170 to 0.44121 across 30,506 rows;
the nominal player-cluster interval excludes no improvement. The many lower-minor
zeros make that broad error look small, so it cannot replace the matched active,
stage and player checks.

Public PA RMSE is 6.6% above Steamer, meeting the predeclared 10% tolerance. Public
PA MAE is 19.7% above Steamer, **failing** the 15% tolerance. Public archives also
have later preseason knowledge dates than our December cutoffs. Their converted
batting value has an environment offset; its loss cannot prove superiority in
pure hitting-talent prediction. We have not demonstrated ZiPS equivalence.

## Repairs and earlier failed approaches

- Raw all-team season histories correct 9,396 MLB career-exposure rows that had
  used only the largest stint. Histories start in 2008, so older careers remain
  explicitly left-truncated.
- V31 accidentally admitted 597 incomplete origin-2020 records into twenty later
  training cells. Missing roster captures became listing zero, despite the
  declared origin exclusion. V33b excludes those rows from every training cell
  and refits the direct control as well as the candidates. Earlier V31/V32
  results remain preserved and qualified; the interrupted V33 batch is not scored
  as a completed experiment. This is not a complete reconstruction of the 2020
  population.
- The six-library V30 direct-workload comparison did not improve the earlier
  workload anchor. Its first ridge result also suffered a rare schedule-feature
  scaling defect. Removing that defect still did not yield a useful gain; this
  does not reject linear models generally.
- Broad staged/direct contribution trees did not beat the old batting-value
  anchors. Reconnecting old batting yields to new workload gave only a small,
  uncertain gain and lost to the stronger broad reference. Those tests also
  inherited the origin-2020 training defect, so their negative results are not
  clean rejections of all integration methods.
- Pooling and fixed-scale linear regression are more useful than another library
  sweep here, but they do not solve baseball context merely by lowering a loss.

## Reality checks: wins and important misses

Twenty-six reviewed player cases include actual source stats, pooled numerators
and denominators, saved-model intermediates, a draft-input probe, linear terms,
future results and origin-selected peers that failed as well as succeeded.

**A sensible improvement:** for Matt Olson after 2022, the corrected direct
control expects 531 PA and 2.47 contribution wins. Retaining stronger earlier
batting evidence raises the working assembly to 572 PA and 3.45. Actual was
720 PA and 7.71. This is directionally sensible continuity, not a solved breakout.

**A major prospect miss:** for Nick Kurtz after 2024, pick 4 and college entry
raise PA from roughly 14 without draft inputs to 50. Actual was 489 PA and 5.72
contribution wins. There are no active training people in his coarse local
profile. Cam Smith and Christian Moore advance while DeLauter does not; those
peers make the fast-entry gap clearer without just choosing successful examples.

**A misleading apparent success:** McLain's predicted 0.54 contribution is near
0.57 actual, but expected PA is only 155 against 577. Workload and batting errors
cancel. This cannot be called a good full forecast.

**A talent gap:** McNeil's 2018 excellent contact is in the data, but the assembly
predicts only 1.08 contribution wins against 4.90. A positive partial AA-strikeout
coefficient among correlated inputs harms his estimate. That is not a causal
claim that strikeouts help; it is a warning that this representation/target does
not yet handle his batting profile well.

**An availability gap:** Tatis after 2022 is treated too much like an ordinary
exit despite retained elite batting history and a finite suspension. Ortiz's
retirement is missed, while a generic older-player penalty also hurts Cruz.
These contrasting cases demand dated status meaning, not blanket penalties.

Judge remains too conservative at brief debut and at elite established cutoffs.
Alvarez and Andujar are important false highs. Yastrzemski, Garcia and Hoskins
give ordinary sensible forecasts, but none eliminates the large misses.

## Cohort checks still fail

The 2021-origin workload total is short 14,663 PA. The corrected control is
similarly short; the pandemic-era opportunity regime is not fixed by this repair.
Across origins, upper minors are short 10,306 PA. Lower minors receive 4,768
excess PA against only 6,072 actual. Tiny pooled error on non-arriving DSL players
is not evidence that future stars are correctly distinguished.

The 2024-origin full cohort expects 179,762 PA and 556.7 contribution wins,
against 182,880 and 570.2 actual. That is reasonably close for this year, not
permission to dismiss the other cohorts. Pre-DH hitter totals can exceed 570
because pitcher batting outside this cohort can be negative; we have not forced
all years to a fixed WAR total.

Raw hitting counts here are not park-neutral or opponent-adjusted. Source position
is a batting-split listing, not defensive innings. December roster capture is a
soft listing, not certified reserve rights. Foreign history, temporary absence,
team opportunity and conditional talent for fast arrivals remain incomplete.

## Decision and next coherent step

Keep this assembly as the **working research baseline**, with pooled-only and
corrected direct controls visible. Do not promote it over the frozen forecast or
call the practical hitter goal complete.

Next is one baseball-mechanism repair, not another algorithm tournament:

1. Reconstruct the complete 2020-origin population using prior MiLB histories and
   actual MLB evidence, with explicit missing-source flags. Do not reintroduce
   the selected 597-person subset as a complete population.
2. Distinguish affirmative definitive exits from finite suspension and temporary
   absence using dated facts. Do not confuse missing roster captures with lost
   rights or confirmed health.
3. Predeclare one opportunity/reliability assembly for advancing upper minors,
   fast drafted entrants and brief MLB debuts. Judge workload, conditional batting
   and delivered value separately, alongside population totals and old/public
   anchors. Use Olson, McNeil, Steer, Winn, Kurtz and Tatis plus unsuccessful
   origin-only peers as compulsory walkthroughs before any disposition.

Park/contact evidence should rejoin only after compatible fold-safe source and
target reconstruction. Multi-year career uncertainty and defense remain necessary
for final player valuation; next-year zeros cannot substitute for those tasks.

## Reproduce and inspect

Local artifacts: `reports/generated/practical-hitter-v33b/`. They include the
preflight, training-support profiles, source repair, 315 saved-head numerical
replays, scores, intervals, 26 complete walkthroughs and the research explorer.
There are 135 reused early heads with unchanged training and 180 new fits.
Nineteen focused unit/source tests pass; a pytest cache-write warning is unrelated
to those test assertions. This is not a claim that the entire repository suite ran.

Small, text-normalized evidence snapshots are committed alongside this card:
[all score/cohort tables](evidence/practical-hitter-v33b/scores.json),
[paired intervals](evidence/practical-hitter-v33b/intervals.json),
[numerical verification](evidence/practical-hitter-v33b/verification.json), and
[the complete player walkthrough](evidence/practical-hitter-v33b/player-walkthrough.md).
The original artifact hash in the verification refers to the original local
walkthrough, not a line-ending-normalized repository copy.

The scripts require the locally retained, hash-recorded upstream source/model
artifacts and archived public exports; a fresh clone alone cannot reproduce the
results. Raw membership-only exports, fitted models and large source captures are
not uploaded in this milestone. Result artifacts are not silently regenerated
from a different external snapshot.

Run the completed result/explorer builders with the project Python environment:

```
python scripts/report_practical_hitter_v33b.py
python scripts/build_practical_hitter_explorer_v33b.py
python -m http.server 8783 --bind 127.0.0.1 --directory reports/generated/practical-hitter-v33b/explorer
```

The explorer has organization, year, stage, name and model filters, cohort totals,
predictions beside actual results, draft/context information and source stats.
Organization is the affiliation at the historical cutoff, not a future club or
certified current rights assignment. Its default is the retained working assembly.
