# Phase 2 demographic feature search

**Status:** controlled development search complete; challengers named, none promoted

## Source

Official StatsAPI people records now cover 24,328 historical and current affiliated
players. Coverage is 100% for batting side, throwing hand, and primary position;
99.9% or better for birth date, birth country, height, weight, and strike-zone bounds;
birth state/province is 49.5% complete.

The reusable source retains reported birth date, city, state/province, country, height,
weight, batting side, throwing hand, position, strike-zone bounds, and gender. It does
not infer race or ethnicity.

## Search

The arrival and meaningful-role models first compared three broad groups, then split
them into nine smaller candidate groups on the existing older-to-newer folds:

1. core baseball evidence;
2. core plus stable demographics: batting side, throwing hand, their interaction,
   gender, and birth country;
3. narrower handedness, origin, physical, and interaction groups;
4. all reported demographics, adding height, weight, body-size interaction,
   strike-zone bounds, primary position, and regularized birth-city/state buckets.

The full group was scored but could not be selected because StatsAPI people profiles
are current records, not historical measurement snapshots. Height, weight, strike-zone
bounds, and primary position therefore require a separate invariance or vintage-source
check before historical validation can authorize them.

## Result

The narrower search found two development leaders that improved both Brier error and
log loss in every evaluated period against the core model:

- stable demographic interactions for hitter meaningful-role probability;
- birth-country groups for pitcher arrival and meaningful-role probability.

These were found by searching the same development periods, so they are named
challengers rather than promoted models. The core feature set remains in production
until a fresh, untouched outcome period confirms them. Physical-feature groups remain
exploratory because their source is not a historical measurement snapshot. No current
player value changed from this experiment.

The next step is to freeze these challenger definitions before the next complete
outcome period. Further brute-force work should move to a nested selection design so
the final comparison remains untouched. Physical interactions by hitter/pitcher role
can continue as exploratory work while their historical timing is audited.
