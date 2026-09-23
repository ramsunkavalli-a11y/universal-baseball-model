# Does richer hitter information identify future major leaguers?

2026-09-23. Fixed feature experiment, before fitting/scoring. This supersedes the
immediate next-path-simulator priority, not previous result decisions. No live
forecast, 2026 outcome, public FV target or dollar value changes.

## Question and prior evidence

Compare richer inputs with basic inputs on identical starting populations and
training rows, holding model family/settings/weights constant. Prior level-path
work improved next-year arrival scores slightly; universal pitch rates were mixed
and did not beat the incumbent ensemble. Basic/aggregate positive-tail models
were rejected. Those results motivate this test, not a presumption of improvement.
See hitter-level-tenure-and-path-result.md, hitter-universal-pitch-game-feed-result.md,
and prospect-broad-history-{positive,skill}-tail-result.md.

Targets: any MLB PA next year; any MLB PA within three years; regular workload
(>=450 MLB PA in at least two of the next three years). For never-debuted minors,
the first two are arrival; for previous major leaguers they measure participation,
not a second debut. Regular workload is opportunity, not proof of valuable hitting.
No new success threshold is chosen after scoring. Everyone stays in the denominator,
including inactive players and players lacking PBP. Missing outcomes are not zero.

Primary cohort: never-debuted minors. Also report all players, upper/lower-minor
prospects separately, recent debuts and young brief-MLB (age <=23, current PA 1–99).

## Information and feature arms

Use the dated annual panel (2009–2024 origins) and exact-season sidecars only:
raw contact-type/direction x result (2015 onward), park-adjusted contact residuals
(2016 onward), universal pitch-result rates (2016 onward), level tenure/path
features, and existing prior-pitcher-quality/park context (2021 onward). The park
residual v2 actually selects the park stage; do NOT call it opponent-adjusted.
The separate prior-pitcher context carries opponent information. No Statcast,
pitch locations/velocity, external grades, salary, or raw weather exposure.
Use lags 0/1/2 for contact/pitch/context; current compact 19-feature level path;
eight lag0-minus-lag1 rate changes. Absent sidecars remain NaN with availability
indicators. Preserve the canceled 2020 season as a missing lag, not a previous
observed-season substitution. Partial promotion features retain their old definition.

Six fixed arms, no winning-subset search:

- B0: 23 age/level/workload features + known prior MLB debut indicator.
- B1: 77 aggregate/history features + prior debut.
- B2: B1 + availability and evidence-volume controls from all sidecars.
- D: B2 + compact progression features and eight annual rate changes.
- C: B2 + raw contact bins, park residuals, pitch rates and prior-opponent context.
- R: B2 + both D and C detail (the predeclared primary challenger).

B2 separates additional content from coverage/sample-size clues. Compare R with
B1 and B2; D and C diagnose blocks, not candidates to select after R fails.
The same fixed balanced LightGBM classifier (seed417, four threads) fits every
arm. Additional fixed regularized logistic C=.1 fits B2 and R as a family check;
median imputation and scaling fitted on training rows only. No tuning, class
reweighting, oversampling, post-hoc calibration or probability inflation.
Each player has total training weight one over eligible snapshots, rescaled to
mean row weight one; recompute weights separately inside each cutoff/exclusion.

## Chronology and support

Next-year normal tests: 2017,2018,2021,2022,2023,2024. Three-year normal tests:
2021,2022; 2019 is separately labeled pandemic stress. Labels must have matured
by fit cutoff; exclude pandemic-crossing training paths. All arms share exactly
the same training/test IDs and origins, including pre-PBP rows with missing detail.
No 2025-origin prediction is needed here. A 2022 all-query-identities-excluded
sensitivity covers all three targets and both full/control arms (B2/R, LightGBM).
Auxiliary sidecars are fixed, dated reconstructed predictors; this is not a claim
that every auxiliary model has been rebuilt with all cold-test identities removed.

Support limitation is known before fitting: only 2015/2016 detailed origins can
have normal three-year labels mature at 2021/2022; park/pitch detail starts in2016,
and the 2021+ prior-opponent block has no mature three-year training examples then.
Constant/unobserved training features must be dropped within each fit and logged.
Therefore the three-year comparison is exploratory, not three-origin confirmation.
The six one-year tests have stronger chronological support. Historical data have
already been exposed elsewhere; these are development tests, not protected evidence.

## Scores and decision

Equal-origin Brier and log loss; pooled observed versus expected event counts;
fixed decile calibration; ROC AUC and average precision as secondary discrimination
checks. Paired 2,000-replicate player-cluster bootstrap, seed417, preserves all
snapshots of each sampled identity and equal-origin weighting. Season-shock
dependence remains; report per-origin and nonoverlapping 2021-window results.

For supported next-year development evidence require >=3 origins and >=30 positives,
R improves both proper scores against B1 AND B2 with upper 95% difference <0,
majority-origin improvement in both scores, expected/observed in [.75,1.25],
no >10% score harm in upper/lower prospect groups with >=200 rows/30 positives,
and logistic R versus B2 improves both scores in direction. Otherwise classify
as inconclusive or rejected according to supported point scores; do not promote.
For three-year endpoints report the same calculations but the <3-origin support
gate must remain failed even if point estimates look good. No whole-player-value
claim is authorized by probability wins alone; delivered-value testing comes later.

Supplementary references, only on matched available keys: accepted C2 annual
participation and earlier stronger PA-ensemble probability; A1/F1 path probabilities
for three-year events. Different recipes/weights make these practical comparators,
not the controlled feature ablation. Do not convert annual marginal probabilities
to cumulative arrival by assuming independence. Inherited references are not cold.

Freeze plan/code/input hashes and feature list/coverage before fits. Unit-test
future/partial outcome exclusion, zero-play inclusion, exact lags, player weights,
and identity exclusions. Mutate future labels and later predictors, rerun 2022
three-year R, and require unchanged forecasts. Package forecasts, coverage, fitted
settings/support, scores and a simple result note; verify original forecast seal.
