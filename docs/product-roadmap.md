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

The player-rights universe contract, its certified 40-man adapter, the MLB career-
outcome inventory and the first pitcher-component baseline are implemented. Continue
Step 1 by adding dated reserve-list/affiliation, transaction and free-agent evidence;
this unlocks honest non-arrival and attrition labels. In parallel, connect the recovered
richer opportunity pipeline and declare universal fallbacks for inactive/no-history
players. The first integrated model should be deliberately simple; granular feature
research begins only after the complete Phase 1 path exists.
