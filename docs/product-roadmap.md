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

The player-candidate inventory, rights-universe contract, certified 40-man adapter,
MLB career-outcome inventory and first pitcher-component baseline are implemented.
Continue Step 1 by reconciling candidate discovery against dated transaction,
reserve-list/affiliation and free-agent evidence; this unlocks honest non-arrival and
attrition labels. In parallel, connect the recovered richer opportunity pipeline and
declare universal fallbacks for inactive/no-history players. The first integrated model
should be deliberately simple; granular feature research begins only after the complete
Phase 1 path exists.

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
50,100 rows for 8,350 players through 2032, and the complete 133-player Super Two pool
selects 30 at a tied `2.144` cutoff. The service method uses FanGraphs as the 2026
opening balance, adds StatsAPI in-season days, and uses zero opening service only when
the official player record has no MLB debut. Debuted players with no balance remain
unresolved. The 21 multi-organization reviews and bounded CBA exceptions remain.
`audit_team_control_source.py` is the
repeatable team source audit and writes source captures plus the exception report.
Contract terms remain an overlay and never rewrite the underlying CBA arithmetic.

Contract Economics v0 now supplies the downstream Step 7 interface. It accepts dated
annual WAR estimates and named economic assumptions, values guarantees, tender rights,
club options and player options, reports optionality separately, and fails closed on
mutual/vesting triggers. The official 2022–2026 minimum schedule is versioned in
`cba_rules.py`. A league-wide dollar output remains blocked on validated multi-year WAR
coverage and an ex-ante free-agent market fit; neither is replaced by a hidden default.

The remaining-rights adapter now separates already-earned current-season WAR and paid
salary from the production and obligations an acquiring club can receive. The dated
2026 baseline supplies projected remaining WAR and CBA day-prorated base salary. It
connects 833 exact current-team payroll rows and rejects 81 unresolved or conflicting
joins. Current availability/role and contract exceptions remain before this becomes a
live ranking.

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
status and unresolved-injury sensitivity now cover the narrow current availability
boundary. Historical workload spread and posterior rate evidence now produce Phase 1
future WAR sensitivities for every economics row. Fitted market assumptions and
calibrated return/role are next; correlated career paths and interval coverage
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
option years. The remaining 68 stay in review. Projected 2027 Super Two players also
advance through arbitration classes 1–4 correctly; previously the class calculation
could reset after the first projected year.
