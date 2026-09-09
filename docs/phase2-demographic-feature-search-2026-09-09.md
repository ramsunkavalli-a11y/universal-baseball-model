# Phase 2 demographic feature search

**Status:** first controlled search complete; no demographic group promoted

## Source

Official StatsAPI people records now cover 24,328 historical and current affiliated
players. Coverage is 100% for batting side, throwing hand, and primary position;
99.9% or better for birth date, birth country, height, weight, and strike-zone bounds;
birth state/province is 49.5% complete.

The reusable source retains reported birth date, city, state/province, country, height,
weight, batting side, throwing hand, position, strike-zone bounds, and gender. It does
not infer race or ethnicity.

## Search

The arrival and meaningful-role models compared three feature groups on the existing
older-to-newer folds:

1. core baseball evidence;
2. core plus stable demographics: batting side, throwing hand, their interaction,
   gender, and birth country;
3. all reported demographics, adding height, weight, body-size interaction,
   strike-zone bounds, primary position, and regularized birth-city/state buckets.

The full group was scored but could not be selected because StatsAPI people profiles
are current records, not historical measurement snapshots. Height, weight, strike-zone
bounds, and primary position therefore require a separate invariance or vintage-source
check before historical validation can authorize them.

## Result

No demographic group improved both Brier error and log loss in every time fold for
either hitters or pitchers. Several pooled scores improved slightly, which supports
continued narrower interaction searches, but the current core model remains selected.
No current player value changed from this experiment.

The next search should test small, baseball-motivated groups rather than one large
bundle: handedness interactions, physical measurements by hitter/pitcher role, and
age-relative-to-level interactions. Each group must beat the incumbent across time;
full demographic bundles remain exploratory until their historical timing is safe.
