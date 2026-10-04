# Integer hitting outcomes improve physical validity and slightly improve ranges

2026-10-04. Retain the version linking possible playing time and hitting as a
next-year offense-risk research candidate. It eliminates physically impossible
outcomes and modestly improves forecast-range scores. It does not change a
single average playing-time, hitting or offense forecast, and it does not fix
the important readiness and point-forecast errors. No deployed forecast changes.

## The comparison

The [contract](hitter-event-count-risk-contract.md) was saved before fitting.
Both new versions draw integer counts of outs, strikeouts, walks, hit-by-pitches,
singles, doubles, triples and home runs, with counts adding up exactly to the
simulated PA. The independent version holds predicted hitting rate constant
across possible workloads. The associated version lets rate move with possible
workload, but centers that relationship so total expected offense stays exactly
the same. Longer playing time is not supplied as known preseason information,
and this is not a causal claim that playing more improves hitting.

The reference event mix is an origin-known MLB profile tilted to the existing
scalar hitting center. It excludes the entire outer player group and the inner
player group where appropriate. It is a working uncertainty assumption, not a
new own-player K, BB or HR forecast, park-neutral talent or Statcast information.
The calibration uses a Gaussian moment quasi-likelihood; simulated outcomes
are still integer counts, not Normal draws or an exact full-profile likelihood.

All 30,506 forecasts and 11,020 people remain, including minor leaguers and
non-arrivals, across seven origins and 35 cells. Target 2020 is excluded and
the missing 2020 minor season is not treated as failed production. The target
is next-calendar-year fixed-event batting plus replacement in custom win units,
not full WAR, six years of control or trade value. Public exports provide point
forecasts, not matching uncertainty distributions; this is not an uncertainty
victory over Steamer or ZiPS.

## Scores and numerical stability

Lower range error is better. The metric averages P10, median and P90 pinball
loss, giving each target year equal weight. Totals below are raw sums.

| Population | Prior Normal law | Independent counts | Associated counts |
| --- | ---: | ---: | ---: |
| All 30,506 forecasts | .041233 | .041258 | .041071 |
| 2,627 public matches | .221910 | .222128 | .221180 |
| Current MLB | .234540 | .234744 | .233587 |
| Upper minors before debut | .028082 | .028062 | .027975 |
| Thin new draftees | .002959 | .002961 | .002967 |

The associated version improves about .39 percent overall and .33 percent on
public matches against the Normal reference. All seven origin scores improve
against both Normal and independent counts. Independent counts alone slightly
worsen the pooled/public range score, although that difference is uncertain.
It would be wrong to call physical coherence alone a predictive improvement.

The nominal player-clustered 95 percent interval for associated minus Normal
loss is -.000162, with interval [-.000228, -.000098]. On public matches it is
-.000730, with interval [-.001264, -.000225]. Associated minus independent is
-.000187 overall, with interval [-.000243, -.000135]. These are exposed
historical development intervals, not fresh holdout evidence or corrections
for the project's repeated experimentation.

An independent 8,192-draw simulation covers every public match, the selected
cases and 256 outcome-blind additional rows: 2,870 unique forecasts. Both
predeclared public comparisons retain their direction and pass the numerical
tolerance. The associated-minus-independent direction also remains favorable.
The public associated-minus-Normal difference is -.001028 on that second
simulation, versus -.000730 originally. Do not attach excessive precision to
tiny effects or claim every player's quantile ranking is stable. Rare-event
Brier/log scores use finite simulation probabilities, not exact tail sums.

The proper 80 percent interval score improves .632573 to .629180 overall and
3.267495 to 3.262879 on public matches. Public central-range coverage moves
78.58 to 78.74 percent, with slightly wider ranges. Overall coverage is 94.53
percent, dominated by non-arrival atoms and many actual zero seasons; it is not
proof of full-population or active-player calibration. Active-outcome coverage
is a separately conditioned diagnostic, not an unconditional 80 percent test.

Expected negative-offense seasons increase from 1,104 to 1,319 against 1,610
observed; two-custom-win seasons increase from 823 to 842 against 928 observed.
These counts are closer but still insufficient. The public two-win Brier score
slightly worsens .092780 to .092954 despite improved primary range loss. Thin
new-draftee range loss also worsens; 1,420 of those 1,429 rows lack matching
calibration people. Do not hide these tradeoffs or interpret .995 coverage in
that group as successful elite-prospect forecasting.

## What the player review establishes

The [eighteen complete walkthroughs](hitter-event-count-risk-walkthrough.md)
show actual level/season counts, saved rate contributions and opportunity
paths, intermediate probability and PA, count parameters, event distributions,
observed MLB results and outcome-blind comparisons. They include all thirteen
fixed player-origin cases and the required selected gains, harms and ordinary
case. The main findings are concrete:

- Judge after 2023 is the largest gain against Normal: P90 rises 7.183 to
  7.504 custom offense, but his actual 10.493 still exceeds it. The range is
  less wrong, not a correct superstar forecast. Judge after 2024 remains a
  similar point/upside miss.
- Hedges is the largest harm against Normal. P10 moves from -1.215 to -.998,
  away from actual -1.628 offense. A universal workload/rate relationship can
  miss defense-first players who keep playing while hitting poorly. This is a
  plausible explanation, not a tested causal mechanism or new routing rule.
- Gore's old 8.62 percent impossible joint PA/offense mass disappears. But his
  new P90 falls .224 to .179 against .228 actual, so his score gets worse.
  Physically possible is not the same as well calibrated.
- Kurtz remains at 10.18 expected PA against 489 actual; his P10, median and
  P90 all remain zero. Reynolds similarly retains an extreme readiness miss.
  Count-risk repair cannot compensate for an incorrect arrival probability.
- Soto and Langford already fell inside the old ranges, and their proper
  scores worsen with the new distribution. Soler's selected gain and Marte's
  selected harm are both retained, without tuning to either.
- Rortvedt's nearly correct .104 expected offense against .103 actual hides
  82 projected PA against 328 actual and an overly optimistic hitting rate.
  Both count versions repair physical support, not those compensating errors.
- Belt's unexpected unsigned season remains an unusual roster outcome, not a
  reason to impose a universal decline/retirement penalty. Franco's specific
  availability representation remains unresolved; hitting spread cannot fix it.

## Important remaining limits

All 35 associated fits hit the declared +1 slope bound. Optimizer starts agree,
but that does not certify the one-slope dependence form. Keep the restriction
and residual bias visible rather than expand the bound after scores. For one
2024 calibration cell, mean rate residual in the 1–49 PA band moves -4.757 to
-2.220, while 300-plus moves -.196 to -.348. Low-workload selection bias is
reduced, not eliminated, and some larger-workload bias worsens. Realized PA is
used only in calibration diagnostics, not forecast-time subgroup routing.

There are 19,800 forecasts without a matching refined calibration profile and
30,322 with fewer than twenty earlier people. All remain scored and borrow
globally. This experiment cannot certify DSL or elite-thin-entry uncertainty.
Physical support is fixed by construction; calibration support is not.

Mean cohort totals and public point errors are unchanged. Upper-never-debut
expected PA remain 74,239 against 92,891 actual. On the matched public sample,
PA RMSE remains 138.33 and MAE 106.41, versus the existing Steamer 135.38 and
92.08, with the earlier snapshot/coverage qualifications. The MAE remains
outside the practical plan's 15 percent allowance. No risk gain waives that gap.

## Verification and next milestone

All 130 actual prefit checks and fifty rate plus fifty conditional-PA replays
preceded new fits. Seventy count calibrations independently reproduce. Roughly
250 million positive draws pass integer-count and physical-envelope assertions
during fitting. The player review independently reconstructs 147,456 saved
integer draws and 108 quantiles. This is not an all-row distribution replay;
the receipt explicitly distinguishes the per-fit assertions, parameter replay,
selected exact replay and independent Monte Carlo audit. Twelve focused tests
and all 31 frozen files verify; no protected 2026 outcomes are opened.

The limits-report script's first attempt failed on a string rather than Path
argument to the hashing helper, before writing its result. Correcting that
reporting error changed no inputs, fits, simulations or scores. Original
pending-review receipts are preserved; the separate final receipt records
completion rather than rewriting them.

Stop this uncertainty comparison here. Keep associated count risk as qualified
research evidence and retain both alternatives. The next practical milestone
is to expose the coherent development candidate with a plain model card,
matched benchmark/cohort results and team-filtered player inspection, keeping
means and protected forecasts separate. Do not start another width, slope or
favorable-subgroup sweep. The full hitter goal stays active: public workload,
readiness, complete production/availability coverage, general defense and
supported long-term/control value are not finished.

Evidence: [scores](../reports/model-evidence/hitter-event-count-risk/scores.json),
[intervals](../reports/model-evidence/hitter-event-count-risk/intervals.json),
[simulation audit](../reports/model-evidence/hitter-event-count-risk/monte-carlo-audit.json),
[limits](../reports/model-evidence/hitter-event-count-risk/limits.json),
[reviewed player traces](../reports/model-evidence/hitter-event-count-risk/reviewed-cases.json),
[final verification](../reports/model-evidence/hitter-event-count-risk/final-report.json).
