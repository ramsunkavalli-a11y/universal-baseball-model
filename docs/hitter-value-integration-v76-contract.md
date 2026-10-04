# Comparing next year MLB batting contribution forecasts

2026-10-03. This is the practical hitter plan's integration comparison, after
the completed team-record review. Test three constructions on the same repaired
history and fresh preseason prospect information. The question is whether they
improve actual delivered MLB batting contribution, not whether a joint model is
automatically more sophisticated. This contract precedes new model fits.

## Outcome and existing evidence

Forecast the following calendar year's MLB batting-plus-replacement contribution
in the corrected common-origin fixed-event units used by the current candidate.
This is not full WAR, a park-neutral talent grade, six service years, control
rights, trade value or money. All certified MLB non-arrivals and exits have zero
PA and zero delivered contribution, not an observed zero hitting rate.

Retain the 63,282 training-source rows and 30,506 evaluation forecasts from
origins 2016–18 and 2021–24. The actual response uses eight disjoint event counts:
other, strikeout, unintentional walk, HBP, single, double, triple and home run.
Their sum is MLB PA. Reconstruct counts from the dated 2008–2025 inventory and
reconcile every response against the prior compatible-value source. Unknown
foreign production and unverified roster-only membership remain qualified;
unchanged membership is not a claim of complete worldwide player coverage.

Preserve current V68 opportunity times V53/V63 batting yield as the main anchor.
Also preserve the already tested V74 translated-linear prospect hitting
alternative, with current opportunity, as a fixed stronger prospect reference.
Do not retune either or rewrite earlier failures. V43's joint forest and V63's
direct heads failed their comparisons; this batch differs in current repaired
inputs, fresher rankings, fold/own-origin translated evidence and explicitly
coherent count forecasts. It does not retroactively overturn those results.

The current batting regression is weighted by actual future PA. In a compatible
population, its mean target is E[PA × rate | X] / E[PA | X]. Multiplying by
expected PA can recover expected batting contribution without independence.
Finite learner approximations, feature differences and weighting/environment
choices are reasons to compare alternatives, not proof that decomposition fails.

## Three fixed constructions

All new heads use the same feature columns. They include the current 251
opportunity inputs, the twelve already audited translated event/reliability
features, eight known origin-season MLB environment shares and the corrected
origin replacement reference. No target-season environment, target event count,
future injury, future standing or new scouting/college source is a predictor.
Fresh rankings retain their existing preseason publication-date qualification:
this is not a December-only forecast merely because the statistics end then.

1. **Direct contribution.** Fit one squared-error histogram tree on all eligible
   players' signed contribution. This changes the supervised response, rather
   than multiplying separately estimated workload and hitting. Retain current
   PA alongside it only as an integration/coherence diagnostic; do not divide
   predicted value by that PA and rename it validated hitting talent.
2. **Arrival times active contribution.** Keep the current saved arrival
   probability. Fit one squared-error tree to the total contribution of players
   who actually have MLB PA, then multiply its conditional mean by that arrival
   probability. Active sample weights are the full eligible cohort's equal-origin
   weights restricted to active rows and normalized globally, not separately
   rebalanced by active origin. Preserve current PA as the same diagnostic.
3. **Expected event counts.** Fit eight Poisson-loss histogram trees on all
   eligible players, one for each nonnegative event count. Sum their predicted
   means for expected PA and convert the same event means to batting value.
   This yields coherent PA/value accounting without needing count independence.
   If the sum exceeds 800 PA, scale all eight means proportionally to 800; report
   every cap. Do not round expected counts to integers. Count means alone do not
   supply validated debut probabilities, event variances or outcome intervals.

All heads use 250 iterations, depth three, leaf minimum 30, learning rate .05,
L2 10, seed 31 and no early stopping, matching the established fixed tree budget.
Do not sweep settings or change loss after seeing scores. The two signed-value
models are not clipped to a positive target or secretly forced into current-PA
bounds. Report any physical incompatibility rather than hiding it. Previously
declared hard unavailability/retirement rules set final contribution/counts to
zero in every arm. A small expected count is not a claim of certain participation.

The count loss has a log link and supports zero observations with positive means;
see [the estimator documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
and [the count-regression example](https://scikit-learn.org/stable/auto_examples/linear_model/plot_poisson_regression_non_normal_loss.html).
Use it to estimate conditional means, not to assume actual baseball outcomes
have Poisson dispersion or that eight independent Poisson draws form a calibrated
season distribution. Signed baseball value is not a Poisson response.

## Preparation and fair comparison

Use the same 35 chronological whole-player cells and full/active memberships.
Outcomes in training must mature by origin; exclude target 2020 and the entire
held-player group. Preserve canceled MiLB 2020 as missing exposure and normalize
short MLB origin schedules once. Every learned level translation is evaluated
at its row's own origin and excludes the actual tested whole-player fold.
Recheck source hashes and translation graph provenance, not just file existence.

Before any new fit, independently reconstruct common-origin labels and count
accounting, replay the seventy current opportunity and thirty-five hitting heads,
and save all 70 actual full/active preflights. Shared feature/membership checks
cover the ten new heads per cell; each head records its exact subset. Audit
distinct people by age, stage, debut, recent MLB/upper-minors exposure, quality,
rank and thin/new-draftee intersections. Include ranges and absent/sparse profiles.
These flags qualify claims but do not remove difficult forecasts.

The three new arms share features internally. Comparisons with the old candidate
change both representation and target/loss, and cannot isolate covariance, an
individual feature or a library effect. Do not claim all previously developed
contact, park/opponent or defense inputs are present in this count-history branch.

## Scoring and required player review

Primary: equal-target-year delivered-value RMSE/MAE/bias and paired 1,000-draw
player-clustered MSE intervals against current. Show all players, never-debut,
upper/lower never-debut, new draftees, thin histories, current MLB workload bands,
former regulars, each origin/stage and the unchanged 2,627 public matches. Retain
Steamer/ZiPS context and snapshot/environment qualifications. Count-arm PA scores
are genuine new expected-PA scores; unchanged PA of signed heads is explicitly
labeled. Cohort totals are the fixed evaluated players, not league-wide entrants.
Count deviances, event biases and aggregate composition are secondary diagnostics,
not a replacement for actual value/PA scores. Report zero-mass probability limits.

Check physical value bounds computed at EACH arm's actual predicted PA and the
same origin environment. Also report actual-count and event-composition arithmetic.
More plausible totals without better player allocation are not sufficient. Keep
2018/2021 arrival deficits, the 2023 cohort excess, elite thin-pro newcomers,
older regulars and unverified histories visible. No median-as-mean substitution.

Fixed walkthroughs: Kurtz 2024, Langford 2023, Julio Rodríguez 2021, Alonso 2018,
Judge 2024, Maitan 2017, Reynolds 2018 and Lugo 2017. Add each arm's largest value
gain/harm, major count-arm PA false high/low and an ordinary active case. Show
actual stats, actual feature rows, saved fit terms, intermediate probability or
count means, final PA/value, observed MLB outcomes, support and origin-selected
peers. Peer matching additionally includes current MLB PA, AA/AAA exposure and
translated event profile, not only age/rank/total minor PA; show unmatched
dimensions and zero-outcome peers when that fixed rule selects them.

Until those reviews are completed, every result remains provisional. Keep
integrity, support, prediction, reasonability and deployment separate. Retain a
construction only if overall and public gains are meaningful without systematic
cohort/level harm or accounting contradictions. Existing practical targets
(public PA RMSE within 10%, MAE within 15% of Steamer, delivered-value RMSE within
10%) remain unchanged. Meeting them is not fresh-holdout certification or a waiver
of meaningful baseball gaps. No post-result blending or tuning. Protected 2026,
the frozen forecast and deployed explorer remain unchanged; whole goal active.
