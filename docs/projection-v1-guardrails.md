# Projection v1 guardrails and plausibility contract

**Status:** frozen before the first universal multi-year WAR path
**Date:** 2026-09-08

## Current implementation

The repository already has useful pieces that should remain separate:

- hitter rate models do not own playing time;
- the hitter playing-time model separately estimates MLB participation and positive
  plate appearances, and records that future team and future level are not predictors;
- the pitcher baseline separately forecasts strikeout, unintentional-walk, HBP,
  home-run and other-batter-faced rates with role-aware regression;
- the existing hitter uncertainty layer samples participation and positive playing
  time rather than treating expected PA as certain;
- the rights/control layer separates service, contracts and club/player decisions from
  talent; and
- Contract Economics consumes WAR without changing it.

These pieces are adequate foundations. They should not be reopened merely because an
eventual dollar value looks surprising.

The current gaps are material:

- no fully materialized multi-year WAR path yet covers every player in the rights universe;
- the universal hitter opportunity calculation is implemented, but its multi-year
  historical snapshot input still needs league materialization and certification;
- pitcher arrival, survival, role transition and workload are not implemented;
- neither hitter nor pitcher has a final component-level multi-year aging layer;
- the old hitter uncertainty surface is one-year and inherits an unbounded positive-PA
  count distribution without a separate physical-plausibility diagnostic;
- durability is not separated from team depth/managerial use; and
- no common historical audit flags implausible annual or cumulative paths.

The hitter playing-time forms may use dated 40-man status as arrival evidence. That is
not the same as current-team depth. It must remain an identified context feature and
must not modify intrinsic rate skill. Lineup rank, blocked position, named teammates or
future team decisions are prohibited inputs to the intrinsic projection path.

## V1 annual identity

Every player and forecast year must have at least one component row. Two-way players
may have one hitter row and one pitcher row; this is the only allowed duplicate
player-year pattern.

For each component:

`expected WAR = P(active in MLB) × conditional WAR rate × conditional workload / workload unit`

The input must retain all four terms. A pre-computed WAR total that cannot reconcile to
them is rejected. Hitter workload is PA; pitcher workload is BF so starter, reliever and
swingman roles remain comparable before any derived IP display.

`P(active in MLB)` combines arrival and survival for that future year. Low-minors
players should normally have delayed paths rather than forced one-year zeros. Older and
inactive players should lose value through survival and workload, not an unexplained WAR
haircut.

Conditional WAR rate contains context-neutral on-field skill, including the applicable
batting/pitching, baserunning, defense, position, replacement and runs-to-wins layers.
Park, league and competition level are corrections to evidence before talent is
estimated. They are not post-hoc penalties on final WAR.

Conditional workload describes usable workload if active. It may use age, recent PA/BF,
role capability and reliable dated IL/roster evidence. It must not use current-team
depth, lineup competition or a manager's allocation as a negative intrinsic-value
feature.

## Guardrail policy

Guardrails are divided into two kinds:

1. **Mechanical validation:** finite values, probabilities in `[0,1]`, positive
   workload units, universal player-year coverage, unique component rows, no current-
   team-depth dependency, and exact WAR reconciliation. Violations fail the build.
2. **Historical plausibility:** compare conditional workload, conditional WAR rate and
   expected annual WAR with pre-cutoff historical distributions for the same broad role.
   Values above the historical high quantile or observed maximum are flagged, never
   clipped.

Historical references must end before the forecast year. Their inputs must already be
park/league/level normalized where appropriate. Each reference records sample size,
years, high workload quantile and maximum, lower/upper conditional WAR-rate quantiles,
and high annual-WAR quantile. Small role groups stay unavailable rather than borrowing
an undocumented threshold.

Large multi-year totals are not capped. Controlled expected WAR is the exact sum of the
annual rows marked controlled. Large totals are review signals; aging, survival,
durability and workload should explain them naturally.

## Required model work

### Hitters

1. **Implemented:** extend the selected participation/PA model with horizon-specific,
   age/level historical fallbacks for inactive, unknown and unsupported players. The
   league snapshot materialization and result review remain.
2. Fit component-level adjacent-season aging on context-neutral rates, with regression
   and survivor/attrition checks; do not copy historical Tango coefficients directly.
3. Assemble batting, baserunning, defense, position and replacement into conditional
   WAR rate.
4. Produce correlated multi-year arrival/survival and workload paths.

### Pitchers

1. Keep the existing component-rate baseline.
2. Add team-neutral MLB arrival/survival, starter/reliever/swingman transition and BF
   workload models with universal fallbacks.
3. Fit modern adjacent-season aging separately for K, UBB, HBP, HR and contact, with
   regression and explicit survivor-bias diagnostics.
4. Convert component rates and workload to runs and WAR, then produce correlated
   multi-year paths.

## Tests and diagnostics

The v1 gate requires:

- every rights-universe player appears in every required forecast year;
- two-way hitter and pitcher rows add once each and cannot duplicate within component;
- the annual WAR identity reconciles within numerical tolerance;
- no path declares current-team depth as an input;
- zero active probability produces zero expected WAR without erasing conditional skill;
- controlled WAR equals the sum of controlled annual rows;
- historical reference data ends before the forecast year;
- extreme forecasts remain unchanged but receive clear reason codes; and
- coverage and extreme rates are reported by component, role, age band and coverage
  tier before any model is promoted.

This contract adds no player-value cap and authorizes no new protected-2026 model
evaluation. It defines the common path and diagnostic boundary needed before hitter and
pitcher work can be integrated with Contract Economics.
