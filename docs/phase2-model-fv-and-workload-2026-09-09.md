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

The any-debut probability now enters pre-MLB expected WAR. The meaningful-role
probability remains a diagnostic until the model separates fringe MLB outcomes from
regular or impact outcomes. The private viewer shows the arrival probability.

## Important result from the ranking check

The new arrival model is valid, but it does not by itself fix the crowded top of the
prospect ranking. The current build has 338 pre-MLB players at 50 FV or higher,
including 73 catchers. Strong minor leaguers often receive a reasonable high arrival
chance, but the existing conditional WAR model still turns too many arrivals into
established regulars.

This is not a reason to cap the list or force position quotas. The next model must use
historical MLB outcomes to estimate, separately:

- fringe arrival;
- meaningful MLB role;
- regular or impact production conditional on reaching MLB.

Draft round, signing bonus, and other durable transaction evidence should then be
tested as a talent prior for young low-minors players whose statistics contain little
information. This is the likely missing evidence for players such as Josuar Gonzalez.

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

1. **P0:** Fit the historical MLB outcome-quality model and replace the overly generous
   conditional-on-arrival WAR assumption.
2. **P0:** Add durable draft/signing pedigree and test whether it fixes low-minors
   under-valuation without making ranked lists an input.
3. **P1:** Calibrate six-year uncertainty and star probabilities from historical paths.
4. **P1:** Improve pitcher role transitions and minor-league development paths.
5. **P2:** Test a portable organization-development effect under the guardrails above.

Run the private build with `play-with-results.cmd`. Generated data remain ignored;
the scripts, tests, and decisions are versioned.
