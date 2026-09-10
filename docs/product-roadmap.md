# Product roadmap: universal, continuously updated trade value

**Status:** Authoritative active plan
**Adopted:** 2026-09-07
**Supersedes for prioritization:** component-specific "next experiment" lists

Historical experiment contracts and decisions remain binding records. They do not
override this roadmap's product sequence. When another document conflicts with this
one about what to build next, follow this roadmap and update `project-status.md`.

## Product contract

Produce a comparable estimate for every player in an MLB organization's transferable
rights universe, refreshed after each completed game and material transaction. The
primary measure is expected remaining surplus value of the transferable team rights.
Always expose these separately:

- expected remaining MLB wins above replacement;
- expected remaining contractual/control cost;
- surplus-value distribution, not only a point estimate;
- as-of date, evidence cutoff, model version, rights owner and coverage tier;
- material reasons for a value change.

Unknown or sparse evidence receives an explicit population prior and wide uncertainty.
It must never silently become zero talent, zero value, or an omitted player. Free
agents may have talent and market-value estimates but no incumbent-club trade rights.

## Methodology rules

The production design follows the lessons most relevant from Tom Tango's forecasting,
aging, translation and value work:

1. Maintain a transparent Marcel-class baseline: recency, regression to an appropriate
   population, age, opportunity and reliability. Added complexity must beat it on a
   material decision target.
2. Keep skill rates distinct from participation, workload and role. Combine them only
   in explicit future paths so selection and correlation are visible.
3. Treat minor-to-major translations as uncertain evidence. Promotion, survival,
   time-gap, regression-population and context selection prevent an MLE from being a
   complete prospect forecast.
4. Treat disappearance and inactivity as outcomes to model, not rows to remove. Aging
   and development estimates must address censoring and survivor bias.
5. Model pitcher components, role and workload separately from hitters. Do not reuse a
   hitter aging curve as a pitcher solution.
6. Diagnose component errors, but select the integrated model on future production
   above replacement, uncertainty calibration and ultimately controlled surplus value.
7. Spend validation effort in proportion to decision impact. Identity, chronology,
   denominator, scale, rights and material forecast errors are hard stops; bounded
   low-impact discrepancies are documented and deferred.

## Phase 1: coherent research product

1. **P0 — Player-rights universe.** Define a dated, one-row-per-player universe for
   all affiliated/reserve players, including injured, inactive, unranked and newly
   signed players, with explicit free-agent and unknown-rights states.
2. **P0 — Mature career outcomes.** Build year-by-year MLB batting, pitching, defense
   and opportunity labels. Preserve non-arrivals, delayed arrival, return from
   inactivity, terminal observation and right-censoring. Aggregate season sources are
   sufficient; do not require full pitch-by-pitch history for career labels.
3. **P0 — Baseline bundle.** Freeze simple hitter-rate, pitcher-component,
   participation/workload, role and aging baselines with fallbacks for every coverage
   tier. This is the minimum competence reference.
4. **P0 — Opportunity recovery.** Restore the dated richer opportunity feature
   pipeline, verify or replace B2-dependent inputs, compare unchanged forecasts to
   O2026D on identical targets, and extend coverage to inactive/no-history players.
5. **P0 — Hitter production.** Retain the useful T2026B MLB-conditional translation as
   a development component. Stop global output-calibration searches. Produce
   unconditional future batting paths that include non-arrival and attrition.
6. **P0 — Pitcher production.** Forecast K, UBB, HBP, HR and contact outcomes separately
   from starter/reliever role and workload, with pitcher-specific aging and uncertainty.
7. **P0 — Rights and cost.** Add dated service time, contracts, arbitration, options,
   buyouts, retained salary and material decision rules. Keep sunk acquisition costs
   outside the transferable-rights value.
8. **P0 — Integrate and replay.** Simulate multi-year whole-player production and cost
   paths, convert to surplus value, and replay historical games and transactions using
   only information available at each cutoff.

Phase 1 is complete only when every in-scope player receives a traceable estimate or
explicit prior, hitters and pitchers share a coherent win/value scale, intervals are
reported, and sequential replay passes end-to-end checks. The website remains paused.

## Phase 2: granular improvement

Phase 2 first establishes an independent Model FV layer. Player-level publication
grades/ranks are validation only. Our projected production and development determine
the outcome distribution and granular FV; the nearest five-point grade is displayed.
Talent/FV remains separate from contract status and salary. League role and position
counts are diagnostics, never fixed quotas. See the
[current Phase 2 preview](phase2-model-fv-and-workload-2026-09-09.md).

### P0 — dependent career-path value distribution

The highest-priority Phase 2 deliverable is one chronology-safe career-path model,
not another symmetric multiplier on annual WAR. Each path must keep these linked:

1. MLB arrival versus non-arrival and arrival timing;
2. limited, meaningful and established career role;
3. annual workload conditional on role, including inactive years and attrition;
4. performance conditional on workload, with persistent talent uncertainty separated
   from season event noise; and
5. team control, pre-arbitration/arbitration/guaranteed cost, options, non-tender
   decisions, present-value discounting and nonlinear market value for concentrated
   star WAR.

Reuse the validated talent, arrival and conditional-workload layers. Learn complete
paths from historical players with failures, inactive seasons and zeroes retained.
Preserve an observed player's annual sequence when resampling so survival, workload
and role transitions do not become independent coin flips. Publication FV opinions
remain excluded as predictors; FanGraphs, PECOTA, ZiPS and Steamer may be external
reasonableness checks only.

Required outputs are mean, median and P10-P90 surplus value; arrival, bust, regular
and star probabilities; controlled WAR; expected cost; and the relevant control and
source assumptions. Treat the already inspected 2025 season as development evidence.
Promotion requires rolling-origin validation and a later untouched confirmation.
See [the frozen implementation contract](dependent-career-path-value-plan.md).

Historical arrival plus conditional meaningful and established-role hurdles are now
integrated in the private preview. Organization remains excluded. Workload-only
uncertainty is displayed and preserves every point mean. A broader component-plus-
workload distribution exists as research, but is not presented as calibrated.

The repeated two-year conditional-hazard conversion was later found to overstate
six-year meaningful and established career masses, especially in the catcher-heavy
top end. The private preview now caps those nested masses at the model's direct
unconditional six-year estimates. Hitter FV 50+ count falls from 82 to 9 and Fernando
Gonzalez falls from 4.09 to 1.63 WAR. This is an immediate consistency safeguard, not
a substitute for P0: replace it with one validated year-by-year career-state transition
model. See the [impact result](prospect-role-probability-safeguard-result.md).

The first replacement pieces are now validated and durable. Prior-year MLB workload
improves fringe advancement for hitters and pitchers in selection and two later years;
pitcher role adds no repeatable signal after workload. A separate time-ordered test
supports hitter/pitcher-specific destinations after a successful fringe advance. The
frozen equations, destination probabilities and monotone state engine are implemented.
Next connect state to whole historical workload/performance paths and replay it at
historical cutoffs. Do not sample isolated seasons independently: that would discard
the real within-career dependence this P0 is designed to retain. Do not select the
eventual tier before the simulated years unfold: that is the circular shortcut being
replaced. Historical origins must refit the progression inputs at their own cutoff;
the 2025 coefficients may not leak into a 2021 replay. The locked construction and
scoring rules are in the
[annually linked replay plan](prospect-linked-career-state-replay-plan.md). No current
ranking changes until the linked replay passes.

A descriptive early-versus-late cohort comparison found 74.7% hitter and 66.3%
pitcher coverage for nominal 80% ranges. It is not chronology-safe confirmation:
six-year outcomes for the earlier debut cohorts extend into later calendar years.
Modern MLB uses about 13% more pitchers than 2015-2019 while mean/median BF per pitcher
is about 13% lower. Openers and bullpen games also make a recorded start an unreliable
rotation-role label. The next pitcher workload model must separate the league
environment from player-relative role and use start share/BF per start rather than
binary starts.

An automated demographic feature harness now tests official age-adjacent profile,
handedness, physical, position and birthplace fields in stable and full groups. The
strict nested search rejected demographic additions to prospect arrival/quality. A
separate hitter component test also rejected age-for-level and batting-side effects
after they reversed on 2025. The pitcher age/hand adjustment has been removed from the
playable build: its point gain is small, bootstrap intervals cross zero, the
left-handed subgroup worsens, and its current top-end effect is disproportionate. Keep
non-vintage physical measurements out of selected historical models until their timing
is defensible.

The reusable search layer now records hashes for the complete candidate family and
the exact outer cohort, enforces observable time origins and identical player rows,
and supplies a conservative promotion gate across both proper scores, paired
uncertainty, calibration, supported subgroups and fresh confirmation. The 176-model
prospect search has been rerun through it with unchanged results. Use this same layer
for later PBP and derived-feature ablations instead of creating one-off selection
rules.

The first universal pitcher batted-ball ablation also failed confirmation. A
development-selected, strongly regressed ground-ball rate improved one later season
but did not improve the next untouched season; popup and pull-direction additions did not
rescue it. This is exactly the unstable descriptive relationship the time-separated
gate is intended to reject. No production values changed.

A linked historical pitcher source now supplies annual component performance beside
each retained workload and role path. Use it for the next dependent-career challenger:
sample those three pieces together, keep cutoff-specific path libraries, and compare
with the current constant-rate simulation before changing any value.

The first current-date sensitivity confirms materiality: linked pitcher paths raise
aggregate prospect WAR 16.4 times and materially reorder the list. A cutoff-safe 2021
development replay supports the broader scale and the simpler arrival-only pooled
path, but not tier splitting. The reconstructed historical incumbent underpredicts
mean WAR (0.047 versus 0.090 observed); the pooled linked path overpredicts it (0.127)
and improves RMSE from 0.558 to 0.551, but the paired interval crosses zero. Retain
both results and require genuinely later confirmation before promotion. Do not tune
to the disclosed level, role, hand, arrival, or probability-band diagnostics.

The parallel hitter test rejects the same replacement: the incumbent has lower
overall RMSE than either linked historical construction. Keep hitter skill and
workload separate in the current model. A future hitter challenger must add a
predeclared reason the dependence should help and must separately source vintage
defense, running and position if it intends to forecast whole-player WAR.

A fixed two-year conditional-WAR bridge is now promising development evidence for
both player types. A strongly regressed core model fit on 2018 improves 2021-cohort
end-to-end RMSE and MAE, paired uncertainty, and arrived-player RMSE without changing
arrival odds or using demographics/FV as talent. It misses its frozen gate because
absolute mean bias worsens slightly. Preserve the exact form for later confirmation;
do not tune an outer-cohort calibration or change current values.

The unchanged 2018 fit then fails its frozen 2022/2023 stability extension. Hitter
arrived-player RMSE worsens in both later cohorts; pitcher absolute bias worsens and
paired MSE gains are uncertain. Reject the ridge replacement. Its consistent
typical-player MAE improvement motivates a separate positive-tail hurdle, not
recalibration, clipping or penalty tuning on the disclosed cohorts.

A separately frozen `0.25` WAR positive-tail hurdle also fails unchanged 2021-2023
testing. Hitter probability gains reverse in 2022; pitcher gains are uncertain and
reverse in 2023. This closes threshold and regularization searches on the same core
aggregate inputs. New tail work must add cutoff-safe evidence rather than mine the
disclosed cohorts.

9. Add pitch characteristics, batted-ball quality, scouting, injury, park, platoon and
   role-change evidence through bounded, population-specific ablations.
10. Improve defense, two-way-player handling, interval calibration, nonlinear buyer
    context and trade-price comparisons without changing the reference-value definition.

Phase 2 work must name the population and decision it can improve, compare on identical
eligible rows, and retain the universal fallback. Small aggregate metric gains cannot
justify worse calibration or coverage for sparse players.

## Current evidence and boundaries

- The recovered 2024 opportunity forecast matches O2026D's 3,985 IDs and official PA
  targets and lowers participation Brier error by 12.6% and PA RMSE by 12.5%. It remains
  a development result with weaker lower-level subgroups.
- O2026D remains the transparent simple opportunity benchmark. Its prior-season-active
  cohort is not the universal player denominator.
- T2026B competition normalization is a useful MLB-conditional hitter component, not a
  universal arrival, playing-time or career-value model.
- C2026A and C2026C global calibration searches are closed failures and must not be
  reopened through rescue tuning.
- The 2022-2024 hitter-v2 surfaces are disclosed development evidence. Protected 2026
  remains closed until a prospective confirmation contract explicitly authorizes it.
- Existing v1 WAR accounting may be reused, but its upstream batting and incomplete-row
  exclusions prevent treating the published ranking as the product foundation.

## Immediate execution order

The Phase 1 coherent research path is complete under its declared boundaries. Universal
hitter and pitcher projections now join rights, costs and Phase 1 reference ranges, and
two 2025 checkpoints pass the same-method replay with no unexplained material changes.
This is not authorization to publish rankings. The next hard evidence gates are the
protected 2026 prospective score after the regular season and the successor CBA.
Resolve service, Super Two and option exceptions by material value impact; leave
granular range calibration and component refinement for Phase 2.

Steps 1–7 now have a complete Phase 1 research path. The dated rights universe covers
8,393 players; explicit fallbacks retain inactive, no-history and missing-age players.
Universal hitter and pitcher opportunity models are separated from conditional skill,
then joined to whole-player WAR, control, contract and cost paths. Direct opportunity
models are selected for horizons 1–4; horizons 5–6 retain the labeled historical
fallback because the older official source does not provide enough chronology-safe
validation folds. The integrated output remains a research scenario, not a publishable
ranking.

Step 8 now passes at two 2025 historical cutoffs. Continue with a
small set of dated season checkpoints, not a daily scheduler. At each checkpoint,
reconstruct the player denominator and allowed evidence, score production and
opportunity, join the then-known rights/cost state, and persist the resulting value
record. Fail on future evidence, duplicate player rights, dropped players, WAR/value
accounting differences or unexplained source changes. Report forecast calibration,
coverage and value stability separately. Once checkpoint replay passes, expand the same
interface to completed-game and material-transaction updates.

The current control checkpoint now preserves 230 hash-verified parsed official API
responses. A no-network reconstruction reproduced every core control artifact byte
for byte. That closes the source-retention and replay path for this checkpoint, but it
does not backfill the then-known payroll terms or opening service balances needed for
a historical value replay.

Historical Opening Day Tracker captures now supply MLBAM-keyed pre-season control
references for 2,012 players in 2024 and 2,024 in 2025, including 1,634 and 1,615
service balances. Official no-debut evidence can cover many remaining affiliated
players; earlier-debut players without a balance stay review. Historical salary and
future contract obligations are now the main remaining replay input.

Downloaded member workbooks validate every overlapping 2024–2025 service, option,
role and identity field and add a 2,065-player 2023 checkpoint. They also retain
historical projected PA/IP, which is useful as an independent opportunity comparator,
not as a target or an automatic replacement for the selected model. Public captures
remain primary where available because they include eight combined additional players
and fields absent from the workbooks.

A 30-team Cot's-derived 2025 CSV extract is a viable private retrospective contract
bridge, but it was assembled after the season and lacks stable IDs. Unique team/name
matching corroborated by service accepts 1,192 of 1,289 players. A fail-closed annual
gate now accepts explicit guaranteed years, routes arbitration to the CBA calculation,
ends control at free agency and blocks unresolved options. It is not authorized as a
vintage or primary production source. The next replay dependency is the historical
control/value join; bounded identity and option exceptions can remain review.

The cutoff-safe 2025 hitter and pitcher projection paths are now materialized. The
selected one-year forms use targets only through 2024, while later years use pre-2025
fallback references. FanGraphs projected PA/IP remain external scale comparators. The
next replay dependency is therefore the historical control/value join, not another
projection search or another workbook download.

That control/value join is now implemented. It resolves 7,998 of 8,946 projected
players to an owner and calculates 39,648 of 39,990 owned annual rows. The 948
missing-owner players remain talent-only; 342 owned rows remain explicit reviews.
The October 2025 owner/control/economics checkpoint and same-method value comparison
are complete. Exact option terms and contract identities stay bounded unless they
materially change the result.

The frozen 2025 outcome score and mechanical checkpoint are now complete. League PA
and BF totals are within 1%, both skill-component forecasts beat the population prior,
and neutral WAR is 6.6% high. Workload RMSE improves over 2024 carry-forward while MAE
does not; FanGraphs is stronger on its narrower projected-player set. The first
historical-to-current sequence has no unexplained material deltas, but the versions and
universes differ. The next Phase 1 replay evidence should therefore be a later
checkpoint scored under the same model definition, not another broad component search.
That projection checkpoint is complete. The March fits are now durable artifacts, and
the October 15 run updates 2025 evidence without refitting. The remaining replay gap
was the matching October control and contract-value state. That state now passes with
7,749 usable player values and no unexplained material change. The remaining 1,337
reviews are explicitly separated: 1,007 missing owners plus 330 bounded control or
contract exceptions. Both checkpoints now carry Phase 1 reference ranges; their median
remaining-WAR width narrows from 2.76 WAR in March to 2.07 WAR in October. These are
uncalibrated references without cross-season covariance, not probability guarantees.

Do not reopen broad component searches during this replay. Fix material identity,
chronology, denominator, control, cost or scale failures; record small component
discrepancies for Phase 2. The protected 2026 confirmation forecast is frozen and its
evaluator must remain locked until every scheduled regular-season game is complete.

The transaction source is projected into a chronology-safe ledger, but transaction
codes do not yet drive rights-state changes. The next rights gate must authorize only
ownership-changing events, resolve minor-league team IDs to dated parent organizations,
and validate replayed owners against conflict-free 40-man snapshots.

The CBA arithmetic boundary is now implemented in `team_control.py`: dated StatsAPI
roster-state intervals produce service time, option-year usage/fourth-option
eligibility, Rule 5 timing, arbitration/Super Two/free-agency eligibility and explicit
confidence flags. `roster_entry_source.py` creates season-opening states from batched
official person history, and `control_events.py` materializes intervals with a narrow,
fail-closed transaction grammar; unclear evidence goes to review. The Padres/Giants
holdout now shows 178/187 and 185/188 broad depth-chart coverage. A from-zero
historical replay was rejected after materially undercounting service and missing too
many option years, so `control_baseline.py` stages verified dated service/options and
StatsAPI calculates forward changes. Rule 5 calculation remains StatsAPI-native: the
calculated year matched 180 of 186 comparable rows across the two clubs.
The full 30-team FanGraphs snapshot now imports cleanly: 5,437 player rows with zero
unparsed service/options/Rule 5 control values. Legitimate two-way-player duplicates
are combined by stable FanGraphs ID while conflicting duplicates still fail closed.
The 30 payroll files also import cleanly: 915 player rows, 3,720 annual terms, 180
clauses and 417 other payments. Stable IDs attach 870 players; current official roster
entries corroborate the remaining 45 exact-name matches. Payroll identity review is
zero. FanGraphs is the primary manual baseline, but source disagreements stay visible
and require corroboration rather than automatic override.

The 2026-09-08 refreshed control table has 8,393 players; source membership can move
with the live official full-roster response. The future full-service scenario now has
50,058 rows for 8,343 controlled players through 2032, and the complete 133-player Super Two pool
selects 30 at a tied `2.144` cutoff. The service method uses FanGraphs as the 2026
opening balance, adds StatsAPI in-season days, and uses zero opening service when the
official player record has no MLB debut or first debuts in the current season. Earlier
debuted players with no balance remain unresolved. The 21 multi-organization reviews are closed using 15 unique official
40-man memberships and six exact official transactions. Bounded CBA exceptions remain.
The season `fullRoster` feed can retain released players, so exact official MLB-team or
unambiguously parented current-season affiliate releases now override it. This identifies
37 players with talent but no incumbent trade rights. Of 208 observed affiliate-parent
IDs, 205 are stable and three conflicted IDs are ignored; current parent mappings are
not applied to older releases. One same-day ownership conflict remains in review.
`audit_team_control_source.py` is the
repeatable team source audit and writes source captures plus the exception report.
Contract terms remain an overlay and never rewrite the underlying CBA arithmetic.

Contract Economics v0 now supplies the downstream Step 7 interface. It accepts dated
annual WAR estimates and named economic assumptions, values guarantees, tender rights,
club options and player options, reports optionality separately, and fails closed on
mutual/vesting triggers. The official 2022–2026 minimum schedule is versioned in
`cba_rules.py`. That former block is now cleared for a named Phase 1 research scenario:
the FanGraphs 2026 market reference, internal one-year scale check, explicit future
growth and discount assumptions, and full current/future WAR path produce league-wide
dollar outputs with review rows retained. These values are inputs to Step 8 replay, not
final ranking validation.

The remaining-rights adapter now separates already-earned current-season WAR and paid
salary from the production and obligations an acquiring club can receive. The dated
2026 baseline supplies projected remaining WAR and CBA day-prorated base salary. It
connects 844 exact current-team payroll rows and rejects 70 unresolved or conflicting
joins. Current availability and recent-role usage now have narrow historical
baselines; contract exceptions remain before this becomes a live ranking.

Projection v1 now has a shared hitter/pitcher guardrail boundary in
`projection_guardrails.py`. It fails on missing player-years, duplicate components,
team-depth dependence or WAR arithmetic that does not reconcile. It reports PA/BF,
MLB-active probability, conditional WAR rate, expected WAR and controlled WAR
separately. Pre-cutoff role distributions flag unusual workload, rate and annual
WAR without caps. Universal hitter participation/PA and pitcher participation/role/BF
calculations are now implemented with explicit historical fallbacks, and their
2018–2024 historical league panels are fitted with 2020 excluded. The 2026-09-08
snapshot now has complete 2027–2032 baseline opportunity paths. A first conditional
WAR assembly covers every opportunity row with explicit population priors, primary
position and replacement value, and no depth input or clipping. Its published Tango
pitcher aging curve, average-zero hitter defense/running and MLB-only rate evidence are
Phase 1 fallbacks. The validated affiliated translation now replaces most pure
population priors, frozen baserunning is reused, and whole-player expected WAR is
joined to every future-control row. A modern pitcher-aging challenger failed, so the
Tango sensitivity remains the Phase 1 curve. Frozen general-range defense now covers
the adjacent season and stays neutral outside its validated scope. Official season-out
status and a 2022-2025 official transaction-based activation reference now cover the
narrow current availability boundary. The fitted point is used only when transaction
replay agrees with current official injury status; unmatched injuries retain a
zero-to-baseline sensitivity. Historical workload spread and posterior rate evidence
now produce Phase 1 future WAR sensitivities for every economics row. The remaining
bounded contract exceptions are next; correlated career paths and interval coverage
refinement are Phase 2.

The public 2020–2026 FanGraphs free-agent tracker now supplies 335 reported contract
rows, including 155 one-year deals. All 350 sampled rows map through stable FanGraphs
IDs to MLBAM using the pinned Chadwick register. Historical tracker pages no longer
carry their signing-time projected WAR, so realized WAR and current forecasts are
forbidden substitutes. Phase 1 is rebuilding ex-ante forecasts from StatsAPI history
and will test the clean one-year market before adopting a dollars-per-WAR assumption.

That market gate is now complete for Phase 1. FanGraphs' published 2026 three-tier
rates are the main reference; the internal 143-deal one-year reconstruction is an
independent scale check and does not erase the star premium. Contract economics now
supports dated tier curves. A 3% annual extension is available only as a named future
scenario, while official post-2026 CBA costs remain unresolved.

The payroll buyout source is now used instead of left on disk: all 86 contingent
buyouts map by exact within-workbook identity, and 83 attach to the 151 projected
option years. A small, dated Spotrac exception overlay supplies 13 more explicit,
non-conflicting buyouts. After Yandy Diaz's vested year becomes guaranteed, 150 option
rows remain and 54 lack buyouts. Projected 2027 Super Two
players also advance through arbitration classes 1–4 correctly; previously the class
calculation could reset after the first projected year.

The Phase 1 arbitration baseline now applies FanGraphs' 15%/35%/50%/75% shares to
prior-season projected WAR value. A full research scenario calculates 49,999 of
50,058 future annual rows from exact inputs. A separate named Phase 1 buyout estimate
uses observed option-type medians for 43 otherwise complete rows. Official MLB
reporting also resolves Kyle Tucker's two apparent option conflicts, raising scenario
coverage to 50,042 and leaving 16 reviews. Three linked Julio Rodriguez years
remain machine-blocked
rather than relying on a prose audit. Two Imai seasons are corrected to player
opt-outs from official MLB reporting; the correction is fail-closed against the
expected prior state.
All 13 vesting rows now have exact trigger definitions and a reusable evaluator.
It consumes retained official StatsAPI totals plus the official schedule calendar,
does not treat missing evidence as zero and keeps additional medical/contract
conditions pending. The first live pass resolves Yandy Diaz's 2027 vesting trigger,
and applies its guaranteed $13M state to economics, while Chapman and Freeland remain
correctly pending.
Fully specified mutual options use the conservative normal-expiration outcome.
Post-2026 minimum salaries and unchanged service rules are clearly marked as a 3%
planning scenario until a successor CBA supplies facts.

### Immediate prospect-ranking roadmap (2026-09-10)

1. Keep the chronology-safe player-level position model as a private sensitivity;
   resolve its 1B/3B subgroup regressions before promotion.
2. Rebuild the top-50 casebook with that sensitivity held fixed, so position no longer
   masks the remaining causes.
3. For every model-only hitter, separate arrival chance, expected workload, translated
   batting, running, defense, and position WAR. Flag the first component that makes
   the ranking implausible under historical outcomes.
4. Test an entry-path-safe hitter arrival challenger using official draft data for
   Rule 4 players and a separate neutral path for international players. Never use
   draft status as a WAR bonus or FV floor.
5. Keep the pitcher translation repair separate. Pitcher scarcity remains a P0 and
   cannot be solved by lowering hitters until the list shape looks familiar.
