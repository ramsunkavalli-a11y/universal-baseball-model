# UBM modeling-method inventory: local work and GitHub

Reviewed: 2026-09-19
Scope: player projection methods, with hitters as the main focus
Code changes from this review: none

## Bottom line

Gradient models **have now been tried locally**, even though they are not in the
public GitHub `main` branch.

- The public repository's `main` branch is at commit `b5b02df` and contains the
  established empirical-Bayes, ridge, logistic/hurdle, count, comparable-player,
  transition-hazard, calibration, and simulation systems.
- Before this report, the local working copy started from that same commit with 53
  modified or new paths. Those local additions include scikit-learn histogram gradient boosting,
  XGBoost, LightGBM, the detailed contact/park/opponent feature table, and a new
  direct-versus-decomposed WAR target test.
- Scikit-learn histogram gradient boosting, XGBoost, and LightGBM have been run on
  the same 155-feature hitter-rate problem. Scikit-learn was best, LightGBM was
  nearly tied, and XGBoost was worse.
- LightGBM has also been run on the newer clean-slate, zero-inclusive next-season
  hitter-WAR panel. The two-part structure—probability of MLB activity multiplied
  by total WAR conditional on activity—beat direct WAR prediction by about 0.0031
  RMSE, with the player-cluster bootstrap interval just fully favorable.
- CatBoost, Explainable Boosting Machines, GPBoost, and NGBoost are installed or
  listed in a local requirements file, but there is no fit, saved prediction table,
  or result report for any of them. They have **not** been tested.
- Random forests, Extra Trees, dedicated GAMs, mixed-effects models, full Bayesian
  hierarchical models, Cox/AFT survival models, quantile regression/boosting,
  conformal prediction, and neural/sequence models also have not been tested as
  player projection engines.

The project has therefore done much more than a simple Marcel-style projection, but
it has not yet completed the broad, same-data, same-fold model tournament described
in the newest local plan.

## What counts as "tried" in this inventory

A library appearing in requirements does not count. A method counts as tried only
when the repository contains all or most of the following:

1. an implemented fit and prediction path;
2. a real historical dataset rather than toy-only tests;
3. a future-season or later-cutoff evaluation;
4. a saved result or prediction artifact; and
5. a stated keep/reject decision.

This distinction matters because several sophisticated libraries are installed
locally but have no experiment behind them yet.

## Repository boundary: public GitHub versus local work

### Public GitHub

The live repository page showed:

- repository: <https://github.com/ramsunkavalli-a11y/universal-baseball-model>
- default branch: `main`
- latest commit: `b5b02df`, "Refresh prospect status and reproducible explorer build"
- commit count shown by GitHub: 2,253
- online branches shown by GitHub: 11

The local `origin/main` reference and local `HEAD` both point to the same commit.
A search of `origin/main` found no use of histogram gradient boosting, XGBoost,
LightGBM, CatBoost, EBM, GPBoost, NGBoost, Random Forest, Extra Trees, neural nets,
Gaussian processes, Tweedie regression, or quantile regression.

The older modeling branches do not hide an unmerged model tournament. `main` is
hundreds of commits ahead of the old hitter, Phase 1, and pitching foundation
branches. Only two visible branches contain commits not in `main`:

- `pitching-v1-mlb-source-result`: one source-inventory result commit;
- `export-batting-leaderboard`: four export/workflow commits.

Neither contains a missing player-projection method.

### Local working copy

The local branch is `audit/data-methodology-v3`. It is based on public `main` but,
before this report was added, contained 53 modified or new paths. Relevant local-only
additions include:

- `docs/hitter-gradient-challenger-v1-result.md`
- `docs/hitter-gradient-ablation-v1-result.md`
- `docs/hitter-gradient-engine-comparison-v1-result.md`
- `docs/hitter-gradient-2026-freeze-result.md`
- `src/universal_baseball/hitter_value_panel.py`
- `src/universal_baseball/hitter_target_architecture.py`
- `scripts/compare_hitter_gradient_engines.py`
- `scripts/compare_hitter_target_architectures.py`
- `requirements-hitter-model-tournament.txt`

These files are real local evidence but should not be described as part of the
published GitHub model until they are reviewed, committed, and pushed.

## Methods that have been implemented and evaluated

| Method family | What UBM actually did | Evidence/result | Current status |
|---|---|---|---|
| Simple population priors | Used level/league/population rates as explicit fallbacks and benchmarks | Present throughout Current Talent, Hitter v2, opportunity, and prospect work | Permanent benchmark/fallback |
| Recency-weighted empirical Bayes | Translated past outcome counts, decayed older evidence, then shrank player probabilities toward a population prior | `current-talent-baseline2-confirmation-checkpoint.md` | Confirmed; Baseline 2 beat Baseline 1 in all six development/confirmation folds |
| Component-specific empirical Bayes | Used a nested terminal-outcome tree and allowed component-specific shrinkage/half-lives | `hitter_v2_model.py`, component-regression audits | Implemented; lighter/component-specific priors had positive point results but failed the frozen uncertainty gate |
| Minor-league translations | Put levels and run environments onto a common scale before projecting | Current Talent, affiliated translation, Hitter v2 reports | Core architecture; finer league-within-level version was tested and rejected |
| Ridge regression | Used for age/development, process increments, conditional quality, defense, and several residual challengers | `projection_ridge.py` and many audit scripts | Extensively tried; useful in some narrow layers, not a universal winner |
| Multi-output ILR ridge | Predicted movement of a 12-outcome probability composition in 11 coherent log-ratio coordinates using age and level | `projection-batting-v1-*` | Selected on 2022 and won 2023, then lost 2024; rejected |
| Logistic regression | Modeled arrival, return, participation, role, ordered outcomes, career states, and calibration | `prospect_arrival.py`, `prospect_career_state.py`, `playing_time_model.py` | Extensively used; several forms retained |
| Two-part/hurdle workload | Logistic participation plus a zero-truncated negative-binomial model for positive MLB PA/BF | `playing_time_model.py`, hitter/pitcher opportunity results | Strong development result; hitter v2 opportunity awaits protected 2026 confirmation |
| Generalized linear models | Used binomial GLMs in playing-time confirmation work | playing-time validation and confirmation scripts | Tried in a narrow role |
| Truncated count models | Used zero-truncated NB2 for positive workload and negative-binomial distributions for uncertainty | playing-time and workload uncertainty modules | Implemented and useful |
| Optimized multinomial/context models | Used constrained numerical optimization for age/level/handedness, calibration, and team allocation | SciPy-based hitter/pitcher context and allocation code | Tried; not a general-purpose model tournament |
| Inverse-probability survivorship adjustment | Modeled return, then reweighted observed adjacent seasons when estimating aging | `survivorship-adjusted-hitter-aging-result.md` | Return model worked; fitted hitter aging curve lost to no aging and was rejected |
| Marcel-style aging | Applied the classic simple age adjustment as a benchmark | hitter aging audits | Tested; no-aging won in the latest hitter test |
| Historical nearest-neighbor comparables | Matched each prospect with 150 same-level historical hitters using regressed age/workload/BB/K/HR/XBH information | `prospect-hitter-historical-comparables-result.md` | Accepted foundation; improved four-year and six-year partial-WAR prediction |
| Multiclass career-state models | Predicted no MLB, fringe, meaningful, or established MLB with multinomial logistic regression | `prospect-one-year-career-state-result.md` | Tested; mixed results, not promoted |
| Ordered discrete-time transition hazards | Fit forward-only annual state transitions and propagated the probability path | `prospect-ordered-transition-path-result.md` | Coherent but unstable across cohorts; not promoted generally |
| Contact-shape residual blends | Valued ten batted-ball bins and fit a bounded residual weight on top of the result-based estimate | `full-bip-hitter-challenger-result.md` | Overall gains, but level reversals prevented promotion |
| Statcast EV/sweet-spot residual | Added mean exit velocity and sweet-spot rate as a residual correction | `current-talent-batted-ball-development-checkpoint.md` | Development failure; rejected |
| Park and opponent models | Estimated outcome-specific venue effects with opponent adjustment, handedness, reliability, and chronological attachment | `park-opponent-component-final-result.md` | Park signal validated; forced stat-line correction rejected; context retained for richer models |
| Probability recalibration | Tried Platt/logistic and isotonic-style calibration in several layers | rolling opportunity and prospect calibration reports | Usually rejected because later proper scores worsened |
| Manual or learned residual blending | Combined incumbent and challenger signals with bounded weights in contact and prospect work | full-BIP, contact-value, and prospect blend reports | Tried repeatedly; some blends passed, others failed |
| Simulation-based uncertainty | Combined discrete inactivity, workload, performance, career-state, and contract paths with Monte Carlo or exact mixtures | WAR uncertainty and dependent career modules | Substantial implementation; the rolling combined WAR mixture improved interval score about 19% |
| Histogram gradient boosting | Fit nonlinear residual corrections from age, level, workload, detailed contact outcomes, opponent quality, handedness, and park context | local `hitter-gradient-*` reports | Local development leader for next-year hitter outcome rates |
| XGBoost | Compared on the exact same 155-feature rate task with nested chronological tuning | local `hitter-gradient-engine-comparison-v1-result.md` | Tried locally; worse than histogram gradient boosting |
| LightGBM | Compared on the same 155-feature rate task and used again on the clean-slate WAR target comparison | local engine report and `hitter-target-architecture-v1/report.json` | Tried locally; near-tied on rate task and useful in WAR architecture test |

## What the local gradient work actually established

### Detailed hitter-rate model

The local gradient challenger uses 155 model inputs after materialization. They
include basic age/level/workload controls, detailed contact type by result, prior
opponent-pitcher quality and handedness, and prior-vintage park effects.

Across 6,799 out-of-sample player forecasts from the 2022, 2023, and 2024 origins:

| Engine | RMSE | Change from contact-only |
|---|---:|---:|
| Contact-only model | 0.014597 | — |
| scikit-learn histogram gradient boosting | **0.014318** | **-0.000279** |
| LightGBM | 0.014330 | -0.000267 |
| XGBoost | 0.014361 | -0.000236 |

The feature ablation attributed the full histogram-boosting RMSE gain approximately
as follows: 43% to the basic nonlinear control, 35% to detailed contact type by
outcome, 6% to opponent context, and 16% to park context. Those percentages depend
on the chosen cumulative order; they are not pure causal shares.

This was not a clean-slate total-value model. It predicted residual changes around
the existing contact model, over a modern four-season feature surface.

### Clean-slate hitter-WAR target structure

The newer local panel covers usable 2015–2019 and 2021–2025 history, explicitly
skips the nonexistent 2020 MiLB season, and preserves old Short-Season A rather than
pretending it maps cleanly to the modern structure. Its current value target is
batting plus replacement only; defense, baserunning, and position are not yet in the
target.

One fixed LightGBM configuration compared three ways to predict next-season,
zero-inclusive MLB component WAR over 23,758 chronological forecasts:

| Architecture | RMSE | MAE | Bias |
|---|---:|---:|---:|
| Direct total WAR | 0.35808 | 0.10190 | +0.00884 |
| Active probability × conditional total WAR | **0.35500** | 0.09480 | +0.00859 |
| Active probability × conditional PA × conditional WAR/600 | 0.35624 | **0.08720** | -0.01399 |

The two-part model beat the direct model by 0.00308 RMSE. Its player-cluster 95%
bootstrap interval was `[-0.00595, -0.00011]`. The three-part structure had better
MAE but systematically underpredicted total value, and its RMSE advantage over the
direct model was uncertain.

This is useful target-architecture evidence. It is not yet the full engine
tournament and does not compare whole-player WAR.

## Methods mentioned, installed, or planned—but not actually tested

| Method | Repository evidence | Correct classification |
|---|---|---|
| CatBoost | Package pinned locally; no import, fit, predictions, or report | Not tried |
| Explainable Boosting Machine (EBM) | `interpret` pinned locally; no EBM code or report | Not tried |
| GPBoost | Package pinned locally; no fit or report | Not tried |
| NGBoost | Package pinned locally; no fit or report | Not tried |
| Quantile LightGBM / quantile boosting | Discussed as a direction; no trained quantile model | Not tried |
| Conformal prediction | No implementation or result | Not tried |
| Random Forest | No estimator import, fit, or result found | Not tried |
| Extra Trees | No estimator import, fit, or result found | Not tried |
| Dedicated GAM/spline model | Piecewise-linear age bases exist, but no fitted GAM engine | Not tried as a model family |
| Gaussian process regression | No implementation or result | Not tried |
| Mixed-effects or random-effects regression | Partial pooling is hand-built, but no fitted mixed-effects model | Not tried |
| Full Bayesian hierarchical model | Literature reviewed and empirical Bayes used; no Stan/PyMC/NumPyro posterior model | Not tried |
| Cox proportional hazards | Return and transition logits exist, but no Cox model | Not tried |
| Accelerated failure-time model | No implementation or result | Not tried |
| Random survival forest / boosted survival | No implementation or result | Not tried |
| Tweedie regression/boosting | No implementation or result | Not tried |
| End-to-end probabilistic boosting | Uncertainty is assembled after point models; NGBoost or distributional boosting has not run | Not tried |
| Neural network / multilayer perceptron | No implementation or result | Not tried |
| LSTM/Transformer player-history model | Outside examples were reviewed, but no UBM fit exists | Not tried |
| General stacked ensemble / Super Learner | Several two-model blends exist, but no cross-fitted library-wide stack | Not tried |

## Important blind spots beyond model brand names

### 1. No one scoreboard covers the full forecasting job

Different experiments predict different things:

- a 90-day outcome probability profile;
- next-season contact-result rates;
- probability of MLB activity;
- positive PA or BF;
- conditional WAR rate;
- zero-inclusive total WAR;
- multi-year partial prospect WAR; or
- uncertainty around an already fixed point estimate.

An engine cannot be declared best by comparing scores taken from different targets or
populations. The clean-slate panel is the first serious attempt to put total
next-season value at the center of one common tournament.

### 2. Most richer-model work is residual-on-incumbent

The gradient-rate model, several contact models, process models, and blends begin
with an existing projection and learn only a correction. This is often sensible, but
it can hide whether the incumbent architecture itself is constraining the result.
The new direct/two-part/three-part test begins to address this.

### 3. Whole-player hitter WAR is not yet the tournament target

The current clean-slate target contains batting plus replacement. It omits defense,
baserunning, and positional value. That is appropriate for learning the batting
foundation, but it is not yet the ultimate player-value target.

### 4. Park context is validated but not yet rebuilt into the long-history panel

The modern gradient-rate result shows an incremental park contribution. The new
2015–2025 clean-slate panel currently lacks the full chronology-safe
park/opponent-neutral feature family. The engine tournament should not be called
complete until that family is added or its absence is explicitly accepted.

### 5. The 2025 play-by-play history needs a completeness decision

The modern frozen 2026 gradient package reports 479,839 official 2025 contacts, but
the newly assembled historical panel initially found a much smaller 2025 source in
an older generated tree. The final 2026 projection must use the certified complete
source and hash it; the partial source is suitable only for diagnosed development
work.

### 6. Interactions are tested, but dependence is only partly modeled

Tree models can discover feature interactions. That does not automatically solve the
dependence between arrival, workload, and performance. Multiplying three separately
estimated conditional means assumes away covariance unless a reconciliation or joint
simulation restores it. The two-part model's early lead is evidence that this matters.

### 7. Uncertainty is strong downstream but not learned jointly with the point model

UBM has unusually substantial simulation and interval work. Still, most distributions
are assembled from separate participation, workload, and performance pieces. A direct
probabilistic engine has not been tested on the same total-value target.

## Highest-value untried tests

These are ranked by likely information value, not novelty.

1. **CatBoost on the common hitter panel.** It is the most important missing tree
   comparison because level, handedness, league, park, missingness, and role are
   naturally categorical and CatBoost is designed to use such fields without a
   fragile one-hot or ordinal shortcut.
2. **Explainable Boosting Machine.** It supplies nonlinear main effects and a small,
   predeclared set of pairwise interactions while remaining much easier to audit than
   a general tree ensemble. It is the clean comparison between rigid ridge and opaque
   boosting.
3. **Extra Trees as a deliberately different nonlinear baseline.** It is cheap and
   tests whether the gradient procedure itself matters or whether generic tree
   partitioning captures most of the gain.
4. **Quantile boosting plus chronological conformal calibration.** This directly tests
   player-specific ranges around total value instead of attaching uncertainty after
   the point forecast.
5. **NGBoost or another distributional booster.** This asks whether mean and variance
   should be learned together, especially for the active conditional-WAR component.
6. **Cross-fitted stacking of genuinely different winners.** Only attempt this after
   ridge/EB, EBM, CatBoost, and the best gradient engine each produce locked
   out-of-fold predictions. Use regularized nonnegative weights and compare against
   the best single model, not against a weak baseline.
7. **A mixed-effects or GPBoost challenger.** Player, league, level, park, and season
   create real grouped structure. This is worth testing after the simpler tournament,
   particularly for partial pooling of sparse environments. It should not receive
   player random effects that cannot transfer to unseen players without an explicit
   fallback.
8. **A genuine survival model for future MLB activity.** Compare discrete-time
   logistic hazards with Cox/AFT or boosted survival using time-varying age, level,
   roster, injury, and workload. This is more relevant to multi-year value than to the
   one-year batting-rate engine.
9. **Full Bayesian hierarchical components.** This could unify component-specific
   shrinkage and uncertainty, but it is computationally expensive and should have to
   beat the existing empirical-Bayes baseline on future seasons.
10. **Neural sequence models only after the tabular tournament.** The usable training
    sample is moderate, missingness and league structure are important, and tree/EB
    baselines are strong. An LSTM or Transformer is lower priority unless the input is
    changed to a genuinely sequential event or pitch history that trees cannot
    represent compactly.

## Recommended clean experiment order

1. Freeze the common prediction universe, chronology, target definitions, and simple
   benchmarks. Keep 2026 sealed.
2. Complete the target-architecture decision first. Current evidence favors the
   two-part active × conditional-total-WAR structure, but it still needs the full
   feature surface and engine comparison.
3. Run one identical-feature point-model tournament:
   empirical-Bayes/ridge baseline, EBM, Extra Trees, histogram gradient boosting,
   XGBoost, LightGBM, and CatBoost.
4. Use nested chronological tuning with the same outer folds and player-clustered
   uncertainty. Do not compare each engine's favorite hand-built data split.
5. Add park/opponent-neutral context as a predeclared feature-family ablation on the
   best two or three engines.
6. Run the probabilistic tournament only after the point target is stable: quantile
   boosting with conformal calibration and NGBoost/distributional boosting.
7. Produce locked out-of-fold predictions, then test a small nonnegative stack. A
   stack must beat the best constituent, not merely the old incumbent.
8. Add defense, baserunning, and position as separately validated components before
   claiming whole-player hitter WAR.
9. Train the final recipe on all allowed pre-2026 evidence using the certified complete
   2025 source. Score the frozen 2026 forecast once when the season and data are final.

## Practical answer to “what haven't we tried?”

The biggest remaining gap is a **fair common tournament**, not the absence of ideas.
UBM has already tried strong shrinkage, ridge, logistic/hurdle and count models,
comparables, state transitions, residual blends, calibration, simulation, histogram
boosting, XGBoost, and LightGBM. It has not yet tried CatBoost, EBM, GPBoost, NGBoost,
Extra Trees/Random Forest, GAMs, mixed-effects/full Bayesian models, survival models,
quantile/conformal forecasting, neural sequence models, or a general cross-fitted
ensemble on the same long-history hitter-value target.

## Primary evidence reviewed

Public repository and branches:

- <https://github.com/ramsunkavalli-a11y/universal-baseball-model>
- <https://github.com/ramsunkavalli-a11y/universal-baseball-model/branches/all>

Core public/local documents:

- `docs/github-projection-methods-review-2026-09-10.md`
- `docs/model-search-validation-policy.md`
- `docs/current-talent-baseline2-confirmation-checkpoint.md`
- `docs/projection-v1-methodology-review.md`
- `docs/projection-batting-v1-selection-checkpoint.md`
- `docs/projection-batting-v1-validation-2024-result.json`
- `docs/survivorship-adjusted-hitter-aging-result.md`
- `docs/hitter-component-specific-regression-result.md`
- `docs/hitter-opportunity-v2-development-result.md`
- `docs/full-bip-hitter-challenger-result.md`
- `docs/current-talent-batted-ball-development-checkpoint.md`
- `docs/park-opponent-component-final-result.md`
- `docs/prospect-hitter-historical-comparables-result.md`
- `docs/prospect-one-year-career-state-result.md`
- `docs/prospect-ordered-transition-path-result.md`
- `docs/rolling-combined-war-uncertainty-result.md`
- local `docs/hitter-gradient-challenger-v1-result.md`
- local `docs/hitter-gradient-ablation-v1-result.md`
- local `docs/hitter-gradient-engine-comparison-v1-result.md`
- local `reports/generated/hitter-target-architecture-v1/report.json`

Code-level checks covered all imports from scikit-learn, statsmodels, SciPy, XGBoost,
LightGBM, CatBoost, GPBoost, NGBoost, InterpretML, PyMC/Stan/NumPyro, TensorFlow,
PyTorch, JAX, and common survival/model-family names in `src/` and `scripts/`.
