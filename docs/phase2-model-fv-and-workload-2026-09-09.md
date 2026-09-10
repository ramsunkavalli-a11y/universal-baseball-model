# Phase 2 Model FV and workload preview

**Status:** private preview; useful for inspection, not ready to publish
**As of:** 2026-09-08

## What is working

Phase 2 keeps three things separate:

1. projected player production;
2. internal Model FV and its talent-value benchmark;
3. contract surplus after salary and team control.

Publication grades and ranks do not set an individual player's Model FV. FanGraphs'
cohort table supplies the common FV/value scale, and its Top 100 is an outside check.

The workload correction blends the older forecast with recent MLB workload for
established players. On the retained 2025 check, hitter MAE improved from 29.56 to
28.05 PA and pitcher MAE from 28.76 to 28.45 BF. Established-player bias improved
from -70.01 to -12.24 PA for hitters and from -32.85 to -1.92 BF for pitchers.

## Historical prospect arrival and survival

The earlier shortcut used the largest annual MLB-active probability. It has been
replaced by two historical, time-ordered logistic models:

- chance of any MLB appearance within two years;
- chance of at least one 200 PA or 200 BF MLB season within two years.

Both use age, broad level, position or pitching role, current and prior workload,
playing-history length, current production rates, and 40-man status. They do not use
team organization, future depth, publication grades, or ranks. Two-year estimates are
extended to six years with a disclosed constant-hazard assumption.

The any-debut model beat the level-only baseline in all three historical folds:

| Group | Model Brier | Baseline Brier | Model log loss | Baseline log loss |
|---|---:|---:|---:|---:|
| Hitters | 0.0496 | 0.0576 | 0.1776 | 0.2052 |
| Pitchers | 0.0521 | 0.0592 | 0.1850 | 0.2135 |

The meaningful-role model also beat its baseline in every fold. Its pooled Brier
scores are 0.0210 for hitters and 0.0198 for pitchers, versus 0.0222 and 0.0209.

The any-debut probability now enters pre-MLB expected WAR. Conditional models then
estimate meaningful given arrival and established given meaningful, preserving the
required probability ordering by construction. The private viewer shows all three.

## Important result from the ranking check

The nested career model fixes much of the crowded top without a quota. Hitter 50+
counts fall from 352 to 86. Catchers are 22.9% of modeled hitters and 25.6% of the 50+
group; shortstops are the larger premium-position concentration. The four 55 FV
hitters are catchers or shortstops because the current six-year path carries their
position value forward. Removing real position value is not a valid fix; player-level
position retention and defense are the next granular tests.

Josuar Gonzalez remains 45 FV at 1.83 expected six-year WAR. His median workload-only
outcome is zero because non-arrival remains more likely than arrival, while the success
tail is valuable. Publication FV did not set his grade.

The workload-only mixture covers all 6,719 pre-MLB paths and exactly reproduces point
WAR. In a descriptive early-versus-late cohort comparison, P10-P90 coverage is 74.7%
for hitters and 66.3% for pitchers. This is not chronology-safe confirmation because
the earlier cohorts' six-year outcomes overlap later calendar years. Pitcher ranges
are therefore labeled descriptive and potentially too narrow. A component-plus-
workload research layer exists but remains off the screen until end-to-end historical
calibration.

## Guardrails

- Organization is not a feature. A later organization effect must be separate,
  heavily regressed, trained only on information known at the cutoff, cross-fitted,
  and tested on traded players.
- Team and position distributions are diagnostics, never quotas.
- Catcher workload is 450 PA and other hitter workload is 550 PA in the six-control-
  year conversion.
- Risk already present in an arrival-weighted outcome is not discounted a second time.
- The 2018 cohort has left-censored earlier MLB history, and the six-year conversion
  assumes a constant two-year hazard. Both are visible limitations.

## Next priorities

1. **P0:** Build a pitcher workload model relative to the season environment. Separate
   rotation starters, openers, bulk/swing pitchers, and relievers with start share and
   BF per start; do not infer rotation workload from one recorded start.
2. **P0:** Backtest the full prospect distribution, including non-arrival, skill and
   workload together. Until then, do not call displayed ranges confidence intervals.
3. **P0:** Add player-level position retention and supported defense uncertainty for
   premium-position hitters; do not impose catcher or shortstop quotas.
4. **P1:** Add chronology-safe platoon evidence after the certified matchup sidecar is
   rematerialized. Times-through-order evidence needs a separate coverage gate.
5. **P1:** Test durable signing evidence for international amateurs. Draft pedigree
   remains an arrival prior candidate, never an FV floor.
6. **P2:** Test portable organization development and flexible team-capacity effects
   under the existing guardrails.

Run the private build with `play-with-results.cmd`. Generated data remain ignored;
the scripts, tests, and decisions are versioned.
