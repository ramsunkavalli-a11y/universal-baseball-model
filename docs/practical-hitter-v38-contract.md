# V38: historical game involvement and role, before modeling

2026-10-03. This is a bounded workload test, not an injury diagnosis or another
batting/event-prior search. V33b remains the working model; source-repaired V34
is the matched research control. V35–37 player reviews are complete.

## Question and evidence

Does games played, alongside PA per appearance, improve expected next-calendar-
year MLB PA and delivered batting-plus-replacement contribution? The same PA
can represent frequent short appearances or fewer regular starts. Games may
also distinguish sustained minor-league participation from brief exposure.
Neither quantity identifies why a player was absent, actual games started,
future available jobs, diagnosed health or guaranteed contracts.

First extract `gamesPlayed` from the exact existing official historical hitting
captures used to construct V31's dated all-team stints, 2008–25. No new outcome
or 2026 data. Reconcile season/player/sport/team and PA exactly against those
stints; reject conflicting duplicates. Audit presence, nonnegative integers,
positive PA with zero games and unreasonable PA/appearance. Missing fields are
unknown, never fabricated zero. Preserve trade/rehab stints; summed team games
are appearance counts, not unique calendar dates. Do not force totals to a
league schedule or infer healthy days from them.

Before fitting, walk through fixed Judge (2016/2024), Winn (2023), Steer (2022),
Kurtz (2024) and Lux (2023), plus origin-selected same-stage/debut comparison
players. Show raw yearly/level PA and games, actual new transforms, source
coverage and information still missing. A coverage defect blocks this feature
test until repaired; it does not reject role evidence.

## Fixed comparison if source review succeeds

Same 30,506 evaluation rows, seven historical origins and 35 whole-player/time
folds as V34, with reconstructed 2020 origin training and mature outcomes.
All 2020 minor seasons remain canceled, not bad production. Keep non-arrivals,
exits, every legacy match and hard cases. Audit all actual folds before fitting.
No expansion, date changes, public score recentering or post-result tuning.

Add 40 origin-only features to V34's unchanged 199 workload inputs:

- MLB and aggregate minor appearance counts and lightly stabilized PA per
  appearance in each of the last three seasons (12 features).
- Pooled appearance counts and stabilized PA per appearance in each of the
  fourteen existing league buckets, weights 1/0.8/0.6 (28 features).

For the role ratio use (PA + 10*4)/(games + 10), a fixed ten-game prior toward
four PA/game; it is a modest stabilization, not an inferred start count. Keep
separate games exposure so absent/brief evidence cannot masquerade as a regular
role. MLB 2020 appearance exposure is multiplied by 162/60, matching the
existing schedule-scaled PA convention; the ratio uses actual PA/games. Minor
appearance totals are unscaled and leagues remain separate. No uniform 150-game
availability denominator for short-season leagues. Zero source PA/game cells
are certified absence in these complete captures, not unknown injury.

Fit one unchanged direct expected-PA histogram gradient model (250 iterations,
depth 3, leaf minimum 30, learning rate .05, L2 10, equal-origin weights, no
early stopping). Bounds [0,800] and existing scoped hard-unavailable rules stay.
Hold V34's strongest linear batting rate bit-exact. Product is PA * (rate/600 +
origin replacement), a mechanical expected contribution comparison, not full
WAR, joint path uncertainty or six service years.

Primary practical score: PA RMSE and MAE on the existing public-matched 1,789
active-origin rows and same-cohort delivered contribution. Also show all rows,
legacy matches, each origin/stage, current regular/partial/brief/absent and
upper/lower minor totals. Use player-clustered equal-year paired intervals;
many previous exposed tests make these development evidence, not untouched
confirmation. All-zero cohort dilution cannot settle usefulness. Practical
targets remain the V30 plan, not a requirement every small group must win.

After scoring, retain the six fixed cases, largest PA/value gains and harms,
false highs/lows and an ordinary case. Replay saved fits, trace source and
actual inputs, show unchanged batting head and arithmetic, use origin-only
comparison selection including unsuccessful peers. Review fixed-fit removal
of game inputs only as a mechanical sensitivity, not a causal explanation.
Finish walkthrough before adoption/rejection or choosing another experiment.

Adopt only if practical workload/value evidence and baseball allocation support
it. Otherwise retain the best coherent model and close this particular test,
not the role/health idea. No protected 2026 outcomes, frozen forecast/deployed
explorer changes or automatic production approval.
