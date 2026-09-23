# Multi-year hitter component integration v1 — frozen experiment

2026-09-22. Freeze before fitting the new component models. This is exposed
historical development, not a new untouched test. Never alter earlier packages
or use 2026 outcomes. Literature and source review are in
`multiyear-hitter-components-literature-v1.md`.

## Scope and measurement

Keep the delivered batting-plus-replacement means and PA estimates unchanged.
Test additive calendar-year runs, divided by a fixed 10 runs/win, for position,
steals, advancement, general defense (range + arm + double plays), framing,
catcher throwing and blocking. Receiving at first base and GIDP residual running
remain unmodeled. This ledger is not a claim to reproduce FanGraphs WAR.
No blanket inflation of 2020. Whole-model comparisons use identical observed
component labels for every candidate, retaining every starting minor leaguer and
zero MLB participation. Unknown active-player measurements are excluded and
counted, not called zero. No 2026 results or contemporaneous Statcast tracking
features enter the experiment. Published historical defensive run estimates are
measurement labels and lagged MLB evidence, not proof of true defensive talent.

## Bounded models — no search over algorithms or weights

1. Neutral contribution.
2. Recovered/simple benchmark: refit the previously accepted position-transition
   architecture at each cutoff, separately by horizon; recovered B2_k5/B2_k45
   steal and A2_k25 advancement recipes with cutoff-specific MLB environments.
   For defense/catcher use a fixed three-year 1/.5/.25 weighted run history,
   regressed with 600 PA of zero-run prior. Scale all benchmark rates by the
   unchanged expected PA. This defensive rate is per batting PA, not a claim
   that batting PA measures defensive talent or catching opportunities.
3. Direct future-component Ridge (alpha 100, standardized and training-median
   imputed inputs): all-starting-player future run total, not future-selected
   survivors. Features: source-only age, level, three years of workload and
   ordinary hitting/steal rates; observed position shares and their missingness;
   lagged component runs, PA-shrunk rates and source-availability flags. No player
   identity, future position or actual future PA predictors. No hyperparameter
   tuning. Rates and source flags expose the difference between missing and zero.

The benchmark uses the existing running recipes, not a made-up equal-weight
blend. The direct total challenger tests whether learning joint exposure/value
outperforms multiplying separately fitted averages. Existing MiLB range/battery
bridges remain diagnostics: do not reopen their failed MLB translations without
a separate, stronger hypothesis. A new full PBP fit is not a delivery dependency.

## Chronology and selection

Predict Years 1, 2 and 3 separately at origins 2016–19 and 2021–24 when mature.
Every training label must end by the origin cutoff. Exclude pandemic-crossing
paths from primary training/selection; report those paths as a separate stress
test. Source history may begin before the native defensive labels; preserve
availability flags. Require at least two distinct training label years and 100
rows before fitting; otherwise use the benchmark. Record every fit's latest
label year and coverage. Player IDs are never predictors; uncertainty resamples
whole player histories, not independent player-season rows. This is rolling
returning-player evaluation, not a claim of player-disjoint validation.

Use a rolling selector per component/horizon: neutral, benchmark, direct. Earlier
out-of-time predictions must have mature outcomes at the current cutoff and at
least two normal origins. Choose the lowest equal-origin squared component
error; absent support use the benchmark for position/running and neutral for
new general-defense/catcher channels. Report fixed candidates alongside the
rolling policy. No selection on the current fold. Final 2025 choice uses the
same rule. These are development choices, not an assertion of confirmation.

## Scoring and release boundary

Equal-origin RMSE/MAE, bias, origin-level results, player-cluster paired loss
intervals, and all-player/current-MLB/upper-minor/lower-minor/under-23-upper-minor
slices. Report component performance separately from delivered-value performance
(fixed batting base plus components), including cumulative three-year value.
Common delivered batting/PA folds are 2016–19, 2021–22; later component-only folds
must not be misrepresented as whole-model tests. A three-year normal comparison
has few independent seasons; uncertainty must say so.

The integrated challenger is publishable only as a separately versioned
development view if normal-path cumulative value improves, annual overall MSE
does not worsen, and adequately supported stage/age groups (>=100 rows and >=3
origins) have no >5% MSE harm. Otherwise preserve the batting-only default and
show component estimates as explicitly unadopted diagnostics. Per-component
provisional inclusion additionally needs component benefit over neutral and no
>5% total-value MSE harm at each supported horizon. Do not quietly remove a
losing component after inspecting the results and re-score it as a new test.

Framing forecasts represent a traditional-called-strike historical scenario;
show a zero-framing full-ABS sensitivity, not an invented adoption date or an
arbitrary challenge-system discount. Missing defensive evidence must be visible,
especially for minor leaguers. No fabricated uncertainty intervals.

## Deliverables

Source/coverage audit, testable component code, dated fit and score manifests,
unchanged-freeze verification, simple model/evidence summary, and a new local
player explorer with 2025 organization filter, stage/search filters, annual and
three-year values, PA and every component. Preserve original views. Commit/push
the research/plan checkpoint and final evidence/code at separate milestones.

Implementation clarification before any successful fit/scoring: component-only
2023/24 diagnostics require a PA estimate not present in the delivered fold cache.
Use a fixed chronological Ridge PA proxy there and exclude those folds from
rolling model selection and all delivered-value gates. This is not evidence for
changing the PA model. Steal labels use a fixed +.2/- .4 run conversion, centered
in each target season; benchmark environments are recomputed at their cutoff.
