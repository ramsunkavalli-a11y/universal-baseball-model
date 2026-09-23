# Multi-year player value: execution plan

Version 1.1, reviewed 2026-09-22. Execution update: M1 and M2 complete;
[three-year hitter result and limitations](multiyear-hitter-v1-result.md).
The [bounded M2 follow-up](multiyear-hitter-followup-v2-result.md) is also complete:
established-hitter participation improved; conditional PA retained; uncertainty
ranges still withheld after upper-minors subgroup failure. Original value means
and the protected season remain untouched. These remaining weaknesses do not
justify relabeling the current output as full WAR or career value.
The subsequent [horizon consistency test](hitter-horizon-consistency-v1-result.md)
rejects a fixed rich-model extension to Year 2. The year-to-year model switch
explains only part of high-value-player declines; young-star later-year calibration
remains a named gap. No trajectory-smoothing change is delivered.
The [anchored-development follow-up](hitter-anchored-development-v1-result.md)
also fails delivery gates. Carrying the estimated rate forward is promising overall,
but learned change adds no overall benefit, and new opportunity heads worsen
top-player PA errors. Nonpandemic young-star results improve; full-calendar and
normal-season conclusions must remain distinct. Next bounded checkpoint is the
opportunity/calendar error decomposition, with its target rules fixed before
another fit. The explorer and original freezes remain unchanged.
That [opportunity/calendar checkpoint](hitter-opportunity-calendar-v1-result.md)
is now complete: ordinary-window top-player PA improves, disrupted targets reverse
the result, and conditional workload drives most of the difference. Young-star
individual errors and weak transfer to value remain unresolved. Next test explicit
training-season exposure in conditional PA while fixing activity/performance;
declare normal-season and calendar-stress criteria before fitting. Do not promote
head-swap diagnostics or hindsight-adjusted predictions.
The subsequent [user-proposed regular-player workload gap](hitter-availability-gap-v1-result.md)
also fails the Year-2 incremental test against position/context controls. It is an
availability proxy, not diagnosed health; next-season and MiLB versions remain open.
The new league ledger flags excess named-cohort PA versus the fixed expected pool,
while preserving signed outsider value and distinguishing partial value from full WAR.
Next: one-year proxy validation and separate league allocation with an explicit
outsider reserve. No automatic total normalization or current forecast change.
This is the immediate execution order under the
[product roadmap](product-roadmap.md). Historical results and frozen forecast
contracts retain their original scope. [Research and sources](multiyear-player-value-literature-2026-09-22.md).

## First deliverable

Produce a usable hitter report with Year 1, Year 2, Year 3 and cumulative three-year
MLB value, participation/workload, evidence status, and uncertainty where supported.
Deliver it at M2; career simulation and a six-year model are not prerequisites.
The first current report uses evidence through **2025-12-31** and forecasts
**2026–2028** under a separate development version. Preserve the original frozen
2026 forecast. No 2026 results enter this work.

The destination remains annual Years 1–6 and cumulative value for all affiliated
players, including pitchers and two-way players. Then connect production to actual
remaining club control and costs. Calendar production, controlled production and
economic surplus must have separate fields. A late-arriving prospect can have
controlled production beyond six calendar years; that tail needs its own evidence.

Keep all-level, non-Statcast inputs. A limited historical denominator may support an
initial restricted-population result, but it cannot establish universal coverage.
Unsupported current players receive labeled priors, not zero talent or omission.

## Reuse before rebuilding

| Asset | Action |
|---|---|
| [Current one-year stack](player-value-development-baseline-v2-result.md) | Refit at each cutoff; mandatory Year 1 comparison on matching targets |
| [Six-year prospect means](current-six-year-partial-value-result.md), [strict replay](prospect-six-year-strict-result.md), [hitter confirmation](prospect-six-year-hitter-blend-confirmation-result.md) | Required pre-MLB six-year benchmark; do not relabel as annual or full WAR |
| [Direct opportunity horizons 2–4](opportunity-multihorizon-v2-development-result.md) | Recover source/fold builders and packages; verify hashes and refit at cutoffs before reuse |
| [Career panel](career-outcome-panel-contract.md) and `career_outcomes.py` | Reuse player-by-calendar-year zero/censoring conventions |
| [Two-year skill model](two-year-talent-development-result.md) | Conditional-rate diagnostic; does not establish expected WAR |
| [Linked hitter](dependent-career-linked-hitter-replay-result.md) / [pitcher](dependent-career-linked-pitcher-replay-result.md) experiments | Retain failures; require a specific new hypothesis before another simulation |
| [Control/service work](prospect-controlled-value-rebuild-plan.md) | Retain downstream interfaces; never equate one active season with one service year |

Start source recovery with `evaluate_opportunity_multihorizon_v2.py` and `_sources`
in `audit_prospect_comparable_chronology.py`. They already reference older snapshots,
affiliated components and 2004–2025 MLB outcomes. Locate missing generated artifacts
through recorded manifests and sibling workspaces, not invented paths or coefficients.
Prior live previews using 2026 predictor evidence are outside this experiment.

The [initial horizon audit](multiyear-horizon-support-2026-09-22.json) is a conservative
inventory of the current one-year panels, not a complete inventory of this repo. It
finds no trainable hitter five/six-year outer fold and no nested three-year tuning
split within that rich panel under its strict year embargo. Older aggregate history
and the existing opportunity folds must be examined before declaring a horizon
unsupported. Rebuild eligible origins from source features: 2019 was excluded for
one-year reasons that need not exclude all longer targets.

## M1: freeze labels, coverage and feasible tests

Create one manifest with exact cohort cutoffs, source hashes, target formulas,
feature availability, eligible training/validation rows and evidence status by horizon.
One inventory and one bounded recovery pass precede the decision: proceed with
certified cohorts, or record the precise missing source and use a restricted cohort
or labeled baseline. A full historical rights reconstruction cannot indefinitely
block the first production forecast.

**Population.** Freeze membership from evidence at the cutoff. Preserve MLB/MiLB,
unranked, reserve and inactive players where sourced. Record participants-only
restrictions and missing coverage explicitly. Future appearance, PA, survival or
public rank cannot select the denominator. Report duplicate IDs, missing ages,
unmatched players, and counts by level and origin.

**Targets.** Maintain portable batting/pitching-plus-replacement value for long-history
comparison and expanded partial value where position/running/catcher labels exist.
Every prediction and comparison uses the same enumerated target version. Show missing
components; neither track is complete WAR while general defense is unmodeled. Include
the public whole-WAR label/source audit in M1 and a matched external comparison at M2
where recoverable. If unavailable, name the missing source and withhold a whole-WAR
claim; do not invent truth from our own model.

**A concrete accounting defect to resolve.** Current target builders allocate a fixed
570 hitter / 430 pitcher replacement-WAR pool per year. Read-only inspection confirmed
those same totals in 2019, 2020 and 2021. Thus the existing 2020 table cannot be reused
as realized calendar production without review. Build a versioned target whose
replacement budget respects completed MLB team-games, verify component sums, and
rescore every comparator on that definition. Preserve existing artifacts. Revisit
older comparable scaling too; do not compare its normalized six-year totals directly
with new realized-calendar totals. Fixing labels is not a claimed forecast gain.

**Missingness.** A certified no-MLB season is zero MLB production. An unavailable
source/year is null; cumulative labels require every year. Include small samples and
negative WAR. Distinguish no recorded play from retirement and keep players eligible
to return. Do not give an MLB-active label solely from future debut information.

**2020 and eras.** Age advances through the canceled MiLB season; missing MiLB play
does not imply zero skill, release or a repeated full level. Main labels use actual
MLB production, with pandemic-window scores reported separately and excluded in a
sensitivity. A forecast made before cancellation cannot know the shortened schedule.
No blanket 162/60 multiplication of realized value. Preserve historical A-/rookie
levels, partial-season exposure, and dates of promotions/reorganization. Future
ball/park/opponent/rule conditions are forecast scenarios, not realized predictors.

**Acceptance evidence.** Audit zeros versus missing sources, player-year uniqueness,
complete windows, no future-derived features, replacement/position counted once,
two-way identity, and formula agreement on sampled player-seasons. The source
certification must go beyond finding at least one row for a season.

## M2: bounded hitter comparison and first player report

Use the same players, targets and outer origins for every candidate. Freeze a simple
age/level/recent-workload baseline **B0**, with regression and population fallbacks,
before challenger scoring. Recover the existing multi-horizon opportunity benchmark;
do not rebuild it merely because it predates this plan. Six-year comparable evidence
is a later-horizon benchmark, not an annual forecast to divide by six.

| Form | Question answered |
|---|---|
| D1: direct annual Ridge | Does a regularized snapshot forecast predict Year 2/3 total value? |
| D2: direct annual CatBoost | Do nonlinear interactions improve those same annual targets? |
| D3: annual CatBoost hurdle | Does MLB participation × total WAR conditional on activity improve them? |
| C1: direct cumulative Ridge | Does direct three-year prediction expose errors in the annual sum? |

These are the entire first batch. Each annual candidate is one pipeline across
Years 2/3, sharing the same cutoff-refit Year 1 forecast within each outer cohort.
Use that same Year 1 forecast in B0's cumulative comparison to isolate later-year gain.
Where the modern one-year model lacks vintage support, all candidates use the same
declared B0 Year 1 fallback. Report modern matched-cohort retention separately.
At every inner cutoff, refit the entire pipeline there too: Year 1 forecast, generated
skill/context inputs, imputation and preprocessing. Outer-fitted predictions or
transforms cannot supply inner cumulative selection scores.

Use one frozen core feature block and one preset per form: existing Ridge settings
and the existing CatBoost `smooth` preset, copied with numeric parameters into the
manifest. No hyperparameter, feature-family or engine sweep at M2. Aggregate history
is the common base; add rich contact later on matched rows after this result. Player
IDs/names/public FV are not predictors. Cutoff-estimated skill inputs must themselves
be reconstructed without future fitting. Allow negative conditional WAR; separate
PA/BF diagnostics do not impose independent workload-times-rate multiplication.

Select among D1–D3 using earlier inner-origin **three-year cumulative MSE**; compare
the resulting selection procedure with B0 on outer predictions excluded from that
run's fitting and selection. These historical outcomes remain development evidence.
Freeze deterministic tie-breaking by simpler form. C1 is a diagnostic, not another
chance to select the most favorable pooled result. The first delivered cumulative
mean is the sum of delivered annual means. A C1 advantage motivates a separately
frozen reconciliation test; it does not justify scaling annual paths after seeing
outer outcomes.

Deliver predictions and a compact explorer view for Years 1–3 and their sum at this
milestone, even if B0 wins. Include target definition, skill-only evidence where
already available, participation/workload, omitted components, coverage and model
status. Apply accepted position/running/catcher forecasts only where their horizon
and labels support it; never repeat a one-year addition unchanged for six years.
Direct D1/D2 WAR regressions do not supply participation/workload. Display those from
the separately cutoff-refit accepted opportunity model, or its explicit historical
fallback; show D3's own activity probability separately when comparing architectures.
Marginal annual and cumulative intervals may use earlier eligible residuals without
a simulator. Unsupported ranges remain unavailable. Do not sum annual quantiles or
present marginal intervals as a joint career distribution.

## Common statistical rules

**Time.** End-of-season origins use December 31. Each feature and training label must
be available by that exact cutoff; never use a label that extends beyond it. Direct
Year 3 requires mature Year 3 labels, cumulative Year 3 requires the whole window,
and a one-year transition fit can use recently completed one-year labels. Calibration,
donors and stacking follow the maturity rule of their own target. The initial audit's
`training_origin + h < origin` is a conservative fallback when availability dates
are uncertified, not a universal extra year of waiting. Record the exact-date rule
and any reconstructed-vintage assumptions before scoring; historical contracts stay
unchanged. A fixed Year 3 forecast never receives realized Year 1/2 updates.

**Selection and support.** Use rolling chronological splits. Keep the same player
out of inner fitting and validation; exclude self-donors. Outer returning-player
forecasts may use legitimate earlier history, with a player-disjoint sensitivity.
Freeze an adequacy table before model scoring: usable training/inner/outer origins,
population sizes, active counts, 2020 overlap, and distinct outcome-year blocks.
For the first batch, selection requires at least two usable inner origins per outer
fold. A repeatability claim requires at least three scored outer origins and two
nonoverlapping outcome windows. These are minimum safeguards, not a power guarantee.
When unavailable, run the fixed D1/B0 comparison without selection and label it
exploratory; deliver the supported baseline rather than mine the few outer folds.

**Primary decision.** Compare the predeclared inner-selected annual procedure against
fixed B0 on **equal-weight mean outer-origin three-year MSE**. Show pooled player-row
MSE, readable WAR RMSE, bias, Year 2/3 errors and Year 1 retention alongside it. Report
existing stronger applicable benchmarks too: beating B0 alone cannot displace them.
MAE is descriptive because mostly-zero predictions can miss valuable future players.

Use paired player-cluster bootstrap intervals for the same weighted statistic,
per-origin results, and nonoverlapping-window/calendar-block sensitivity for shared
season shocks. The interval describes a frozen comparison, not immunity from earlier
research reuse. Predeclare the materially supported stage/age/exposure subgroups,
numeric bias/noninferiority margins and participation-calibration tolerances from
baseline/training evidence in the M2 manifest. A run without those frozen values is
exploratory. Avoid arbitrary newly invented WAR thresholds in this umbrella plan.

Development selection requires a favorable primary paired MSE interval, improvement
in a majority of outer origins, no breach of frozen retention/subgroup/calibration
limits, and no clear reversal in the season-block sensitivity. Otherwise retain B0
or the existing stronger benchmark and record the diagnosis. Choosing the best outer
score and bootstrapping it afterwards is not this test. One failed batch permits at
most one specifically justified follow-up; stop tuning the same exposed result.

**Probability and uncertainty.** Score participation with Brier/log loss and calibration;
score annual and cumulative distributions with CRPS, coverage and width against an
equally specified distributional baseline. Future-arrival/regular/star subsets are
diagnostics, not selection cohorts. First-arrival probability is cumulative and
monotone; yearly activity and cumulative WAR need not be. Negative seasons and return
remain possible. Joint paths later require covariance/return checks and a joint score.

**Evidence status.** Historical seasons already inspected are development evidence,
including older confirmations. “Development selected,” “provisional,” “exploratory”
and “prospectively confirmed” are separate labels. Completion of 2026 can test only
outcomes/prefixes then observable; it cannot validate 2027–2031. Full-calendar outcomes,
age-relative skill and controlled value are distinct targets.

## Subsequent milestones and stopping rules

| Milestone | Required exit |
|---|---|
| M0 — Research/inventory | Complete; this reviewed plan and source audit |
| M1 — Data/target contract | Versioned labels, coverage/source and fold manifest; resolve 2020 accounting before cumulative scoring |
| M2 — First hitter product | Fixed four-form batch, decision report, reproducible Year 1–3 player table/explorer; ranges only where supported |
| M3 — Extend delivered baseline | Pitcher Year 1–3 on the same contract; hitter/pitcher Years 4–6 as support permits; accepted legacy six-year benchmark retained |
| M4 — Targeted path challenger | Only after M2: named error in timing, return, or cumulative distribution; one compact transition model against delivered baseline |
| M5 — Whole-player/control integration | Expanded value and external whole-WAR comparison; two-way accounting; validated service/control then costs and separately justified post-Year-6 tail |

M3 does not wait for M4, and delivery does not wait for every component to improve.
At M4 use observable MLB, affiliated-MiLB, and no-recorded-play states with duration
and prior exposure; absence is not an absorbing retirement state. A joint latent
performance/continuation model or blend requires an identified remaining error and
a new frozen contract. No broad algorithm tournament by default. Existing failed
linked-path designs do not become selected because simulation sounds more complete.

Commit reproducible work and a brief decision at each milestone; push the research
branch. Update this checklist and the status page. A failed challenger closes with
the best supported baseline and a usable report. Reopen only for new evidence, a
corrected defect, or a predeclared materially different hypothesis.

**Execution checkpoint, 2026-09-22:** M1 and M2 are complete. D1 was selected by all
inner tests and improves all six outer three-year tests. Current 2026–2028 player
forecasts and an explorer are delivered under a separate development version. No
protected outcomes or original frozen forecasts changed.

**Next action:** a bounded opportunity-consistency audit identified in the player
report: verify historical 40-man absence for established hitters and reuse the
existing established-hitter opportunity work for a talent-aware challenger. Replace
the failed stage-only uncertainty bands under a new conditional/distributional test;
they are withheld because aggregate coverage concealed high-value undercoverage. Do not
hand-correct player values or replace the selected procedure based on exposed outer
scores. Then execute M3: pitchers Year 1–3 and longer horizons where support permits.
This follow-up addresses a specific observed weakness; it does not reopen a broad
algorithm tournament or postpone delivery of the supported hitter value means.
