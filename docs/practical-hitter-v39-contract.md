# V39: a separate origin-known MLB workload process

2026-10-03, before fitting. V38 is reviewed and retained as research, not
promoted. This one test addresses model structure, not another feature tweak.

## Estimand and comparison

Expected next-calendar-year MLB PA, including exits and zero outcomes. Players
with positive MLB PA at the forecast origin get a dedicated direct workload
head trained on origin-positive MLB players only. The selection does not use
future debut, health, lineup, target participation or eventual success. All
current non-MLB players, including prior major leaguers with a missed season,
retain V38 predictions bit-exact. Thus this cannot fix Lux-type absent-return
or Kurtz/Bellinger-type first-arrival cases; show them, do not omit them.

The hypothesis is that a single shallow learner across thousands of non-arrivals
and current MLB hitters may allocate capacity poorly between first arrival and
role retention. Dedicated training is a different statistical population
mapping, not proof of correct available jobs or injury probabilities. A positive
result cannot be attributed to games alone: V38 already contains games, and
this test changes training population and corresponding equal-origin weights.

Same V34 35 chronology/whole-player folds, 30,506 evaluation rows, certified
targets and origin-2020 reconstruction. Within each current-MLB subset retain
every next-year exit and absence; never condition on future active players.
All test membership and base predictions remain saved. Audit all actual subset
folds/profile support BEFORE any fit, including age/current-PA/elapsed stage,
brief debuts and prior low-volume versus sustained regular use. Keep sparse
profiles in headline scores with explicit flags. Mature targets exclude 2020.

One unchanged histogram direct regressor: V38's 239 origin-known inputs,
250 iterations, depth 3, 30 minimum leaf rows, .05 learning rate, L2 10, equal
origin weighting recomputed within this subset, no early stopping/tuning.
Bounds [0,800], same scoped hard-unavailable rules. V34 linear batting head
is bit-exact. Delivered contribution remains expected PA * (conditional rate/600
+ origin replacement): a comparison of the working product, not proof of a
joint value distribution, full WAR or club-controlled valuation.

Primary practical benchmark is public-matched 1,789 current MLB rows versus
V38/V33b/Steamer: PA RMSE and MAE, plus contribution. Also retain full cohort,
each year/stage and current-PA bands, brief debut, establishment, cohort sums
and future zero counts. Engineering tolerances stay from V30; nominal clustered
development intervals do not create independent confirmatory evidence.

Fixed walkthroughs: Judge 2016/2024, Winn 2023, Steer 2022, Vientos 2022, Reyes
2021, McLain 2023 plus unchanged Lux 2023 and Kurtz 2024. Add largest gains/harms,
false highs/lows and ordinary cases. Trace source counts/games, actual features,
saved exact tree paths, batting head, products and outcomes, with origin-selected
peers and actual distinct-player subset support. Path effects are accounting,
not causal or SHAP. Complete review before adoption/next experiment.

If promising, use only as a historical research candidate and document unresolved
first-arrival/absent-return gaps. Do not promote merely because one pooled error
wins; inspect false-retention harms and calendar totals. No protected 2026,
frozen/external explorer changes, additional arbitrary blend or model tournament.
