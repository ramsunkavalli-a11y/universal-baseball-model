# Six-year hitter conditional blend confirmation contract

**Frozen:** 2026-09-13 before scoring the 2017 target

## Selection already completed

The strict 2013 and 2016 development folds showed that six-year arrival and
conditional quality both carry signal, but the raw local conditional total creates
too much aggregate underprediction. The fixed correction keeps local arrival
probability separate and shrinks only conditional six-year production:

`expected WAR = local arrival probability × (0.40 × local conditional WAR + 0.60 × historical arrived-player WAR)`

The `0.40` local weight was selected from `0.0, 0.1, ..., 1.0` as the lowest pooled
squared-error candidate satisfying the already-frozen per-fold bias margin on both
2013 and 2016. No public FV, rank, player name or current value was used.

## Untouched confirmation

- Target: 2017 pre-MLB hitter snapshot and complete 2018–2023 outcomes.
- References: 2003 and 2008 only; every outcome ends by 2014.
- Remove every 2017 target player from the reference pool.
- Keep 150 neighbors and every existing feature/regression setting unchanged.

Promote the hitter six-year mean only if:

1. blended expected-WAR RMSE beats the population-mean baseline;
2. absolute bias is no worse than baseline plus 0.01 WAR per player;
3. unchanged local arrival probability beats population Brier and log loss; and
4. supported local conditional-rate RMSE beats the arrived-population baseline with
   at least 20 actual arrivals.

Passing does not authorize position, defense, baserunning, salary, full controlled
WAR, dollars or FV.
