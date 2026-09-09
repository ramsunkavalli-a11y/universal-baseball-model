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

Steps 1–7 now have a complete Phase 1 research path. The dated rights universe covers
8,393 players; explicit fallbacks retain inactive, no-history and missing-age players.
Universal hitter and pitcher opportunity models are separated from conditional skill,
then joined to whole-player WAR, control, contract and cost paths. Direct opportunity
models are selected for horizons 1–4; horizons 5–6 retain the labeled historical
fallback because the older official source does not provide enough chronology-safe
validation folds. The integrated output remains a research scenario, not a publishable
ranking.

The immediate P0 is Step 8: prove the whole path under historical cutoffs. Start with a
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
The next P0 is to score the 2025 checkpoint against completed outcomes and run the
checkpoint accounting/coverage gates. Exact option terms and contract identities are
bounded follow-up work unless they materially change that result.

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
