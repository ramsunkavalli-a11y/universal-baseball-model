# Testing the minor league season clock

2026-10-04. The current prospect model undercounts arrivals in 2021 and several
other cohorts. Its conditional workload totals are not uniformly too low.
This comparison changes only the arrival model's representation of minor-league
history. It does not give every prospect more playing time or tune a COVID boost.
No new fits have been run when this contract is saved.

## The distinction being tested

The earlier cancellation experiment removed an unavailable annual block. It
improved 2021 but worsened 2022. History-summary and probability-calibration
experiments also did not reliably repair both cohorts. Preserve those results.
Here, rebuild three affiliated-minor history slots from the last three seasons
in which that league system existed, skipping only its canceled 2020 season.
For a 2021 origin the source years become 2021, 2019 and 2018; for 2022 they
become 2022, 2021 and 2019. For training origin 2020 they are 2019, 2018 and 2017.
All other origins retain their original calendar slots. Individual absences,
injuries and years without a player record are NOT skipped.

Rebuild affiliated-level PA, present flags, stabilized event rates, weighted
pooled counts/rates and game/role summaries coherently. Slot weights remain
1, .8 and .6, and event priors remain 100 opportunities. This tests an available
season evidence clock, including retaining one older season and its changed
weight; it cannot isolate those two effects from each other. Record the actual
source year for every slot. Do not describe 2019 production as occurring in 2020.

MLB and Mexico retain calendar history. Keep actual age, draft elapsed, latest
stat gap, MLB debut history, career MLB exposure, roster/status information,
positions, scouting-list dates and the three calendar cancellation indicators
unchanged. Recompute the draft rank versus exposure term because its denominator
uses the history slots. Minor aggregate summaries explicitly combine the new
affiliated clock with Mexico's unchanged calendar clock. Display stage and
evaluation profiles continue to describe actual origin-season evidence, not
the latest available minor slot in canceled 2020. Save those profile semantics.

## Fixed model comparison

Use the current 63,282 source rows and the same 30,506 forecasts, including all
24,199 never-debut cases and non-arrivals. Fit a participation classifier with
the same 251 inputs, full training membership, equal-origin weights and saved
histogram-tree settings. Training outcomes must mature by the origin, exclude
2020 targets and exclude the entire test-player fold. Replace probability only
for never-debut players at ALL seven evaluation origins, not just 2021.
Established-player forecasts remain exact copies of current outputs.

Keep current conditional PA, clipping, availability rules and current hitting
fixed. Delivered value remains expected PA times the fixed batting-plus-
replacement yield. Also report the existing translated hitting anchor with
these same PA as a predeclared integration sensitivity, not a new rate fit.
These custom batting units are not full WAR or six years of control value.
Retain the actual following-preseason ranking information date from each
current fold; these are not strict December 31 forecasts.

There are 35 cells. At the 15 pre-pandemic cells the complete training/query
matrices are identical, so reuse and replay the saved control rather than fit a
redundant model. Fit only the 20 cells with changed training inputs. No parameter
tuning, global probability multiplier or post-result year-specific routing.

## Checks and decision evidence

Before any fit, certify source counts/games, prove ordinary-calendar rebuilding
agrees with current inputs, show all changed columns/rows, walk Julio, Witt,
Vavra and a 2022 opposite-risk case through both source clocks, and save all
70 actual control/candidate preflights. Count distinct training people by actual
origin stage, age, rank and exposure, including positive-arrival support.
Keep sparse and out-of-range profiles in headline scores and qualify claims.
Replay every saved control, and verify chronology, unchanged labels, true ages,
scouting inputs, established forecasts and 2026 protection.

Score equal-year PA RMSE/MAE, appearance Brier/log loss, delivered-value RMSE,
raw expected/actual arrivals and PA, and nominal player-clustered paired 95%
intervals. Report each origin, upper/lower minors, thin entrants, listed prospects,
probability bands and the unchanged matched public sample. Show 2021 and 2022
separately; improvement in one does not excuse harm in the other. Also show
2023's existing overprediction and cohorts outside the cancellation window.

Before disposition, actual model walks include fixed Julio 2021, Witt 2021,
Vavra 2021, Walker 2022, Langford 2023 and Kurtz 2024, plus largest PA gain/harm,
false high/low and an ordinary active case when available. Each walk traces
dated stats, both complete input vectors, saved classifier paths, fixed
conditional PA/rate, delivered forecast, subsequent reality and outcome-blind
age/level/exposure/performance/pedigree peers. Review missing support and
component-error cancellation. No next model experiment before that checkpoint.

Retain the new representation only if improvements are practically coherent
across probability, workload/value, cohorts and player evidence. Small pooled
gains with worse allocation remain insufficient. All historical outcomes here
are exposed development evidence, not untouched confirmation. Protected 2026
outcomes, frozen forecasts and deployed explorer remain unchanged.
