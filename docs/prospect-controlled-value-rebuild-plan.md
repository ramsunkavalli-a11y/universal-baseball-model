# Prospect controlled-value rebuild plan

**Status:** active P0 after the separated talent foundation

## Rule

Do not convert FV to WAR or assume that a 50 FV equals any fixed amount of controlled
WAR. Public FV is comparison evidence only. Controlled value must be built from four
separate, testable pieces:

1. probability and timing of MLB arrival;
2. talent and annual MLB performance conditional on arrival;
3. a linked workload, attrition and service-day path;
4. CBA eligibility, salary, contract and discount arithmetic.

An error in one piece may not be hidden by tuning another. Non-arrivals and zero
seasons stay in every expected-value score.

## What is accepted now

- Six-year MLB arrival probability is separately validated.
- Four-calendar-year partial batting/pitching outcomes beat population baselines in
  four nonoverlapping historical folds.
- Hitter conditional comparable quality is supported; pitcher comparable quality is
  withheld. The separate peak-talent model remains the pitcher talent view.
- Current MLB service and contract accounting is usable where exact source inputs
  exist.
- A monotone workload-to-service-day challenger beats the old full-season shortcut
  for first-year players in 2023 and 2024 and returning players in 2024. It is retained
  for the next complete-path replay, not yet promoted.

## What failed

- Direct StatsAPI roster/transaction reconstruction across 2009–2019 debut cohorts
  misses 3,301 seasons with MLB workload and produces a 524-day median absolute error
  against FanGraphs 2025 opening service. It cannot be the service truth by itself.
- The older dependent career simulator's workload/performance path did not earn
  promotion and its one-active-season-equals-one-service-year rule is wrong.
- A six-calendar-year comparable extension failed. Calendar years are not control
  years.

## Next gates

1. Join the retained service-day mapping to complete historical workload paths and
   score cumulative service timing, including zero-workload injured seasons.
2. Remove survivorship selection by adding another opening-service source or a
   defensible missing-next-snapshot treatment.
3. Build and validate annual whole-player WAR. Batting/pitching plus replacement is
  not sufficient; hitter baserunning, defense and position must remain explicit.

The first whole-player extension is now tested rather than assumed. Official MLB
position outcomes cover 2004–2025 and official MiLB position origins cover five broad
historical eras plus 2019. A fresh 2019 confirmation reduced squared error but failed
its frozen aggregate-bias guardrail by less than 0.0001 WAR per player. Position stays
out of the main model and must not be patched from current names or public rankings.

The frozen portable stolen-base formulas also reduce squared error in every broad
historical era, but fail the existing exact aggregate-bias guardrail in three. The
effect is small, and broad historical non-steal advancement evidence is unavailable.
Keep both running channels outside the Phase 1 foundation; revisit their materiality
after the main talent, arrival and control-year structure is stable.
4. Replay arrival, performance, workload and service jointly across strict historical
   origins. Require proper distribution accuracy and expected-WAR squared error.
5. Only after the path passes, apply versioned CBA rules, Super Two, minimum salary,
   arbitration, guarantees/options and discounting.
6. Compare the resulting ordering with public top-50 lists as an audit. Never use
   those lists as predictors, floors or grade quotas.

FV remains unavailable until the model can map its validated whole-player outcome
distribution onto the standard 20–80 role scale without using current public player
opinions as labels.
