# Multi-year player value: active execution plan

Adopted: 2026-09-22. Status: planning and initial source-support audit complete;
label certification and model comparison next. This is the immediate execution order
under the [product roadmap](product-roadmap.md). It supersedes older conflicting
"next task" lists, not historical experiment results or frozen evaluation contracts.

## Deliverable and scope

For every player at a dated forecast cutoff, estimate MLB production in Years 1–6
and cumulative production through Years 2, 3, 5 and 6, with uncertainty and an
explanation of development, participation, workload, and position/role. Start with
hitters and then use the same evaluation contract for pitchers and two-way players.
The first useful milestone is an honest Year 1/2/3 hitter forecast and three-year
total. Longer horizons follow as data and validation permit.

Keep three explicit quantities: calendar-year MLB production; production during
actual remaining club control; and economic surplus after costs. Complete and test
production first. Calendar seasons do not establish service or ownership. Six years
from today do not capture all controlled production for a prospect who arrives later.
Beyond-six-year production will need an explicitly supported tail before complete
controlled value is claimed. No arbitrary terminal value or fixed FV-to-WAR rule.

This task uses the previously agreed all-level, non-Statcast evidence. Sources and
reasoning are in the [literature review](multiyear-player-value-literature-2026-09-22.md).

## What already exists

| Existing work | Evidence/status | How to use it |
|---|---|---|
| Current one-year hitter/pitcher development stack | [Reconciled partial-value result](player-value-development-baseline-v2-result.md) | Year 1 benchmark; refit at historical cutoffs |
| Six-year prospect comparable means | [Strict replay](prospect-six-year-strict-result.md); [subsequent hitter confirmation](prospect-six-year-hitter-blend-confirmation-result.md) | Required long-horizon benchmark; retain specific accepted decisions |
| Current six-year output | [6,988 player/type rows](current-six-year-partial-value-result.md) | Partial batting/pitching plus replacement; no annual-path validation implied |
| Direct two-year component development | [Rate-only result](two-year-talent-development-result.md) | Diagnostic among observed future players; not zero-inclusive WAR evidence |
| Multi-year opportunity and rights/cost paths | [Opportunity](current-opportunity-paths-2026-09-08.md); [control rebuild](prospect-controlled-value-rebuild-plan.md) | Reuse source/identity interfaces; audit provenance and current applicability |
| Career labels | [Censored panel contract](career-outcome-panel-contract.md), `career_outcomes.py` | Reuse zero/censoring logic and separate batting/pitching counts |
| Linked historical careers | [Hitter replay](dependent-career-linked-hitter-replay-result.md); [pitcher replay](dependent-career-linked-pitcher-replay-result.md) | Rejected/unpromoted benchmarks, not selected engines |
| Legacy dependent simulator | [Superseded contract](dependent-career-path-value-plan.md) | Do not restore its invalid talent inputs or active-season service shortcut |

The strict hitter six-year result initially withheld promotion; its later frozen
blend confirmation is the accepted update. Neither that acceptance nor the older
integrated research preview establishes current annual whole-player WAR accuracy.
No earlier validation is discarded, and no earlier failure is silently promoted.

## Initial feasibility finding

The [reproducible horizon audit](multiyear-horizon-support-2026-09-22.json) verifies the
four current panel/target hashes and inventories origin/season keys without scoring
player outcomes. Under a conservative full-label-year-before-origin embargo:

| Horizon | Hitter mature origins / trainable outer origins / nested-supported origins | Pitcher equivalent |
|---|---|---|
| 1 | 8 / 6 / 4 | 14 / 12 / 10 |
| 2 | 7 / 4 / 3 | 13 / 10 / 7 |
| 3 | 6 / 2 / 0 | 12 / 8 / 4 |
| 4 | 5 / 1 / 0 | 11 / 6 / 1 |
| 5 | 4 / 0 / 0 | 10 / 4 / 0 |
| 6 | 4 / 0 / 0 | 10 / 3 / 0 |

These are availability counts, not independent tests or completeness certification.
The rich hitter panel begins in 2015; its five/six-year labels cannot train a model
before any of its fully observed outer origins. Even the three-year problem lacks
an inner tuning split within this panel under the declared embargo. Recover older
aggregate features for the base model. Use rich PBP as a recent-horizon addition,
or a fixed-form hypothesis where tuning support is absent. Older six-year comparable
tests already demonstrate why aggregate history is valuable.

2019 features exist upstream but were excluded from the one-year panel because its
next season was 2020. Reassess eligible origins from original features for each
horizon; do not inherit that exclusion blindly. The audit does not certify inactive
player coverage or a historical rights denominator.

Reproduce: `.venv/Scripts/python.exe scripts/audit_multiyear_horizon_support.py`.

## Target and data contract

Each row records player ID, player type, exact cutoff, origin year, horizon, target
year, evidence tier, model/target version, source hashes, follow-up status and last
certified outcome year. Freeze a historical affiliated/MLB player denominator at
each cutoff; preserve unranked players, inactive/reserve players and explicit priors.
If a denominator is only prior-season participants, label it restricted and report
what is missing. Future MLB appearance must never determine inclusion.

Annual labels include MLB participation, PA or BF, role/position exposure, and each
available value component. An observed no-MLB season has zero MLB production;
unavailable source data and future seasons are null. Cumulative labels require every
intervening season to be certified. No dropping future low-PA players from the main
score; conditional skill scores are separately labeled diagnostics.

Keep two target versions: portable batting/pitching-plus-replacement for long-history
comparisons, and the explicitly enumerated expanded partial-value stack where labels
exist. Never compare an incomplete prediction to a differently defined target without
identifying the missing components. Independent public whole-WAR labels, if sourced,
are a separate external test; reconciling definitions is required. Current general
defense neutrality and pitcher contact limitations remain visible. Account for
replacement and position only once, including two-way players.

Predictive inputs include age, level and time at each level, prior PA/BF, talent rates,
contact evidence where available, progression, workload interruptions, and dated
roster information. Preserve partial-season promotions and actual exposure instead
of counting every calendar return as a full repeated level. Fit translations, park
and opponent adjustments using allowed history only. Unknown future park/opponents
are integrated over a declared scenario, never replaced by realized destinations.

### Interrupted seasons and changing environments

- Calendar time advances through 2020. The missing MiLB season supplies no zero-skill
  or retirement label and no synthetic PA. Track time since observed play.
- Use actual 2020 MLB production for realized calendar-WAR targets, with a visible
  shortened-schedule indicator. Do not multiply realized value by 162/60 in the main
  target. Score windows crossing 2020 separately and repeat evaluation without them.
- A normal-schedule sensitivity may standardize workload, clearly labeled; it cannot
  repair a retrospective pre-pandemic forecast using advance knowledge of cancellation.
- Preserve historical A-/rookie levels and league eras. Do not relabel eliminated
  short-season leagues as modern A-ball. Rule/ball/ABS changes require dated inputs
  or explicit future scenarios. No 2026 outcome-based environment fitting.

## Small, ordered set of model tests

1. **B0, transparent baseline.** Regress recent skill toward age/level populations,
   apply conservative development/aging, and estimate future participation and
   workload from earlier history. Include zero and carry-forward forecasts as
   diagnostics. Reconstruct accepted legacy six-year comparables on matching cohorts.
2. **D1, direct annual forecasts.** Predict each future year's zero-inclusive partial
   WAR from the cutoff snapshot. Compare direct expected WAR with an MLB-active
   hurdle times expected *total WAR conditional on activity*. Use regularized linear
   models and a bounded CatBoost comparison first, reusing existing infrastructure.
   Negative active-player WAR is allowed. PA/BF and skill remain reported diagnostics;
   do not impose independent workload-times-rate multiplication.
3. **D2, direct cumulative forecasts.** Predict cumulative two/three/six-year value
   directly on mature windows as an independent benchmark for the sum of D1 means.
   Test sharing information across horizons through a horizon feature with masks for
   unavailable labels. If estimates disagree, diagnose timing/tail errors before
   learning a reconciliation on earlier out-of-sample data.
4. **T1, linked transitions.** Fit development, participation, promotion/demotion,
   workload and role with explicit duration/history. Allow absence and return. Use
   a compact regularized transition model and sample conditional performance/workload
   together. Carry persistent talent uncertainty along a path and separate it from
   annual noise. Updated features must arise from simulated observations; never feed
   realized future level, statistics or role into a forecast. Replaying a selected
   one-year mean unchanged is not T1.
5. **J1, joint performance and continuation.** Only if residual tests expose relevant
   dependence, add shared player effects to performance, workload and continuation
   using mixed/state-space or joint longitudinal models. Compare to T1 and D1; no
   assumption that greater complexity wins. Resampled complete careers are an
   alternative only with cutoff-eligible donors and a new reason to expect improvement
   after the documented linked-path failures.
6. **E1, reconcile/ensemble.** Consider a simple blend only after constituents have
   independent earlier predictions. Learn at most a strongly regularized weight or
   select a fixed simple average using nested development. Freeze before evaluation.

Candidate families, feature blocks, hyperparameter budget and loss priorities must
be recorded before each run. No new XGBoost/LightGBM/NGBoost/EBM tournament unless a
diagnosed limitation warrants it. CatBoost is a manageable nonlinear comparator,
not a presumed winner. The first direct mean models do not establish path uncertainty.

## Validation contract

For an outer origin `o` and horizon `h`, conservative training eligibility is
`training_origin + h < o`; apply the same rule to inner tuning, donor paths,
residual calibration and stacking. Exact publication dates may support a separately
declared tighter rule later, but never change chronology after inspecting its scores.
Retrospectively downloaded historical statistics must be marked reconstructed, not
claimed to be archived vintage releases. Source lineage and current-profile fields
need separate leakage checks.

Use rolling time splits. Within each selection fit, group players so the same player
cannot supply both inner fitting and validation rows. Report an outer player-disjoint
sensitivity as well as realistic returning-player forecasts using legitimate earlier
history. Exclude self-donors. A fixed cutoff forecast for Year 3 may not incorporate
Year 1/2 outcomes; annually refreshed forecasts are a different experiment.

All previously inspected historical seasons, including 2025 and earlier confirmations,
are development evidence for this new architecture. Preserve the original frozen
2026 forecast. The new development version can be frozen separately; 2026 will only
test its available annual outcomes/prefixes. It cannot confirm 2027–2031 in 2026.
Previously seen 2026 facts in discussion do not authorize opening its evaluation data.

Primary first gate: **three-year cumulative expected-WAR MSE**, with Year 2 and Year 3
MSE as required companion results and Year 1 as a retention check. After that, five/six-
year cumulative MSE has a separate gate and eligible population. Report RMSE in WAR
for readability, MAE descriptively, bias, and errors across forecast-value bands.
Do not average raw annual and six-year RMSE or select the most flattering horizon.

For probabilities use Brier, log loss and calibration. For distributions use CRPS,
50/80/90% coverage and interval width; score annual and cumulative draws. Include a
joint-path score such as energy score plus annual covariance, return and workload-tail
checks. Means sum across years; quantiles do not. Do not force cumulative WAR to rise:
negative seasons exist. Cumulative first-arrival probability must be monotone.

Report by cutoff-known stage, age, exposure, position, pitcher role and evidence tier.
Low-minor teenagers and current MLB players need separate results. Future arrivals,
future regulars and realized high-value players are useful error diagnostics, never
population-selection rules. This protects against a mostly-zero model looking good
while missing future contributors.

Use paired player-cluster bootstrap intervals and per-origin results. Overlapping
multi-year windows share season shocks; add calendar-block or nonoverlapping-window
sensitivity. Many players do not turn two time origins into many independent eras.
If nested support is absent, freeze a simple form or expand older history instead of
tuning on the outer fold.

Promote to **development selection** when the primary paired MSE interval is favorable,
gain persists across origins, and supported subgroups/calibration show no material
harm. Freeze numerical noninferiority and bias margins in the experiment manifest
from baseline/training evidence before scoring; otherwise the run is exploratory.
Uncertain results stay provisional. Prospective confirmation is a separate status.
No requirement to prove every small component significant before testing the whole
forecast, and no manual ranking fixes from familiar player names.

## Milestones and completion checks

| Milestone | Work and completion evidence | Status |
|---|---|---|
| M0 | Reconcile prior work, literature, links and present-panel horizon support | Initial audit done; full source certification remains M1 |
| M1 | Build fixed denominators and annual/cumulative labels; certify missing/zero/censored cases, older aggregate support, and cutoff availability | Next |
| M2 | Hitter B0/D1/D2 Year 1–3 comparison, frozen experiment manifest, per-origin/subgroup results, three-year total | First model milestone |
| M3 | T1 and, only if warranted, J1; validate annual/cumulative distributions and compare to direct forecasts | Pending |
| M4 | Extend supported hitter horizons to 4–6; publish fallback/uncertainty for unsupported horizons | Pending |
| M5 | Pitcher equivalent with role/workload dependence; sum two-way contributions with explicit joint uncertainty | Pending |
| M6 | Connect tested position/running/catcher components at each horizon; evaluate full-value gaps and control/service separately | Pending |
| M7 | Explorer with annual value, cumulative value, skill-only view, opportunity, uncertainty and evidence status | Pending |
| M8 | Freeze current multi-year version; connect verified rights/cost paths and schedule proper later outcome evaluation | Pending |

At each milestone commit the reproducible code, relevant tests, compact result and
decision, and update this checklist. Push the research branch at meaningful milestones.
Preserve failed experiments with reasons. Stop a candidate when it fails its gate;
continue the sequence with the best supported fallback.

The milestone is not complete merely because a simulator runs or a six-year table
exists. Completion requires a reproducible forecast for every declared player,
honest evidence status for each horizon, improved or justified retained benchmarks,
and a visible account of what remains unknown. No change to published player numbers
is implied by adopting this plan.

## Immediate next run

Recover older aggregate hitter snapshots and the missing eligible origin features;
join the existing certified MLB target sources to a fixed player-by-year grid.
Use the existing `career_outcomes.py` zero/censoring conventions. Produce a label and
fold manifest before fitting. Freeze the first B0/D1/D2 contract, then run the hitter
Year 2/3 and three-year cumulative comparison. This is the next modeling task; another
one-year component sweep does not take precedence without a blocking defect.
