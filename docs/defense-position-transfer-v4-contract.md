# Use related position history to estimate defensive range

Locked before fitting, 2026-10-06. This comparison addresses the missing
other-position representation in the reviewed native-range baseline. It is
development evidence, not a new protected test or permission to change forecasts.

## Question and fixed comparison

Does related-position MLB history help identify later MLB range quality when
the player's sample at the target position is small? Preserve every origin,
player-position, label, chronological fold and person weight from the native
range comparison. Quality is native range runs per 500 defensive innings pooled
over the following three calendar years, with the same two-season, 1,500-out,
complete-coverage requirement. Non-survivors and position converts keep unknown
quality and remain in the prediction ledger. No 2026 outcomes enter this test.

Reuse the exact saved neutral, shrunk-history and calibrated predictions. Add
one fixed candidate: the calibrated feature matrix plus related-position
evidence. No parameter search, new cohort, new target or next-year total-runs
substitute. Primary scoring remains the ordinary 2022 origin, with 2021 separate
and earlier origins retained as supporting development diagnostics.

## What can transfer

For second, third and shortstop, use the other two positions in that infield
family. For left, center and right field, use the other two outfield positions.
First base retains its own measured history, without importing these families.
Catcher and cross-family moves are deliberately outside this comparison.
Never use the target position's own record twice or treat a positive CF record
as direct evidence of good SS defense.

For the other positions, pool actual range runs and defensive outs from the
same preceding three calendar years, with weights 1, 0.5 and 0.25. Only certified
position measurements enter. The other-history rate is 1,500 times weighted
runs divided by weighted outs plus 3,000; its reliability is n/(n+3,000).
Missing measured evidence contributes zero *increment*, not a claim of average
ability. Save both measured exposure and omitted/invalid exposure separately.

Eight additional deterministic features are fixed:

- Other-history rate times (1 minus target-history reliability), separately
  for infield and outfield.
- Other-history reliability times that same target-history attenuation,
  separately for infield and outfield.
- Reliability-weighted source SS share when predicting 2B/3B; source non-SS
  share when predicting SS; source CF share when predicting LF/RF; source
  corner share when predicting CF. Each also receives the target attenuation.

These direction features let the learner distinguish transfers between
different comparison groups; no published UZR positional coefficient is copied
into native Statcast runs. The additive increment fades as reliable evidence
at the target position grows. Age/position/history coefficients are refitted
jointly, so the contrast is representation, not a causal effect of one term.

## Support and fitting

All feature construction uses only origin-known source seasons. All training
labels must mature by the forecast cutoff, and the entire held-player ID-mod-5
fold is excluded. Standardization is fitted within each training fold; weighted
Ridge alpha remains 10. Each training person has total weight one across rows.
The existing minimum of 100 training people and two mature origins applies;
otherwise retain the shrunk-history fallback.

Before any fit save all membership and distinct-person counts, existing
position/age/target-exposure profiles, and their intersections with other-history
exposure (<300, 300–1499, 1500+ outs). Count distinct training people with a
nonzero value for each added feature. Disable a new feature in a fold with
fewer than 20 such people, in both training and prediction, before fitting.
The threshold is a conservative usability guard, not proof of adequate support.
Unknown ages, feature extrapolation and sparse joint profiles remain explicit.
Preserve full labels and the old anchor hashes. Finish source/player checks
before any learner is fitted.

## Evaluation and baseball checks

Report matched, person-balanced RMSE/MAE/bias, a 2,000-draw person-cluster paired
95% interval against calibrated history, and counts by position, age, target
sample and other sample. Predeclare the hypothesized beneficiary group:
target-history outs <1,500 and other-history outs >=300. Also show strong
target-history players and those with no related history; never drop them to
obtain a gain. Actual-exposure run totals are diagnostic, not forecast value.

A useful upgrade needs coherent group/player behavior and meaningful aggregate
evidence, not improvement in one named case. If its primary loss worsens or
important groups deteriorate, retain the old practical baseline and explain
which representation failed; do not sweep shrinkage constants or positions.
Even a positive result remains qualified by one ordinary mature origin and
conditional survivors. It does not validate minor-to-MLB talent transfer.

Fixed 2022 cases are Jankowski LF, Refsnyder LF, Enrique Hernández SS, Mateo 2B,
Betts 2B, Witt SS and Kiermaier CF where eligible. Preserve missing cases rather
than changing eligibility. Add largest gain/loss, false high/low and ordinary
median-error cases after scoring. For each include three peers selected by
origin/target position, age and both origin-known sample sizes, without future
selection. Show annual same/other sources, exact inputs and fitted arithmetic,
actual future paths, support and the zero-other-history fixed-fit probe. The
probe recomputes all derived features and is an explanation, not a forecast.
Finish this review before disposition or the next component fit.

## Baseball rationale and scope

[FanGraphs' positional-context explanation](https://blogs.fangraphs.com/position-adjustments/)
shows why ratings against different position peers cannot simply be equated.
[Its fielding update](https://blogs.fangraphs.com/a-fangraphs-war-fielding-update/)
also distinguishes native range from the position centering used in WAR. These
motivate a learned, bounded within-family transfer, not universal equivalence.

Do not alter the selected hitter package, explorer, frozen 2026 forecast or
completed final evaluation. Defensive quality, future position exposure, other
components and value integration remain separate deliverables of the active goal.
