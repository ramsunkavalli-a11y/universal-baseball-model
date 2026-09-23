# A canceled season is not a player's absence

2026-09-23. Follow-up to the failed history/calibration bundle; fixed before these
fits. The 2021 errors are already exposed development evidence, not a holdout.
2021 means a season-end 2021 forecast, so next-year arrivals occur in 2022.

## Diagnosis and external context

The rich input panel marks all 3,250 never-debuted 2021 minor leaguers missing at
lag1 (2020). In 2017 and 2018, only 4/1,061 and 2/1,149 prospects with that flag
had MLB PA the next year, versus 157/3,250 in 2021. Ordinary missingness often
means a new player or individual absence; system-wide missingness has a different
meaning. Adding history summaries left those original features in the model.
This is a plausible model mechanism, not proof that it explains the entire gap.

Official context known at the forecast date:

- [The 2020 MiLB season was canceled](https://www.milb.com/news/2020-minor-league-baseball-season-cancelled-x0977).
- [MLB reorganized affiliates into 120 licensed teams](https://www.mlb.com/press-release/press-release-mlb-announces-new-modernized-player-development-system-and-the-120).
- [Mississippi's announced 2021 schedule had 120 games](https://www.milb.com/news/mississippi-braves-announce-2021-schedule);
  [Norfolk's revised schedule also had 120](https://www.milb.com/news/updated-tides-2021-schedule).
  These are examples of shortened opportunity, not a universal schedule multiplier.

Do not infer that every individual had no development, impute alternate-site
results, inflate PA, or use the unusually high realized 2022 arrival count as an
input. Schedule length and changed population may explain residual errors; this
bounded test first isolates the misleading annual-history block.

## Fixed available-information routing

R: original 886-feature LightGBM model, frozen settings and identity weights.
O: primary outage-aware model. Fit on identical eligible training rows but omit
the canceled annual block from both training and prediction: lag1 for 2021 and
lag2 for 2022. Remove that lag's aggregate stats, missingness, volume, detailed
contact/pitch/context and availability fields. Remove rate-change fields if lag1
is omitted. Retain current season, the other correctly dated lag, and valid
career/level-path evidence. Do not move 2019 into 2020 or pretend it is one year old.
N: diagnostic model omitting both prior annual blocks and their rate changes.
Never choose between O and N after scoring; O is the primary repair.

Route only never-debuted minor-league prospects whose canceled lag has no annual
record. Other players and all other origins retain R predictions exactly. This
does not remove 2021 players or outcomes from the training archive, rebuild the
production pipeline, or claim that every post-2020 training issue is repaired.

Real fits: each target at 2021/2022 for O/N. Targets unchanged: any MLB PA next
year; any within three years; >=450 PA in at least two of three years. Same
ordinary evaluation populations, label maturity and pandemic-window exclusion as
the preceding experiments. No post-hoc calibration or probability scaling.

## Historical missing-input stress

At 2017/2018 next-year cutoffs, hide lag1 and lag2 separately in query prospects
only. Predict with the original fitted R, then with an O model trained without
that block. Also retain intact-data R. This hides annual stat/PBP inputs, not all
career knowledge: existing cumulative path summaries remain available in all
arms. It is a source-outage stress, not a simulation of lost physical development.
No outcomes are used to choose which year/block to hide. The test must expose
whether generic missing values damage useful predictions and exclusion repairs
them; restoring count totals alone is insufficient.

## Reporting and safeguards

Equal-origin Brier/log loss; observed/expected counts; individual annual results;
top-5% recall; paired 2,000 player-cluster intervals (seed417). Report 2021 on its
own, 2022 on its own, all six annual origins, and two overlapping three-year
origins. Non-outage-year equality is a routing safeguard, not independent
confirmation. Retain original R, history H, B2 tree/logistic and earlier ensemble
on matched keys as references, not a post-hoc benchmark switch.

Report upper/lower, age<=23 advancing, <400 current PA, first-at-level and partial
promotion return groups with complete denominators. For a mechanism-supported
next-year repair require 2021 improvement in both scores with paired interval
upper bounds below zero, at least 25% reduction in the absolute 2021 count error,
no >10% score harm in supported 2022/stage cells (>=200 rows,30 events), and O
better than masked R on both scores in at least 3/4 historical outage scenarios.
These gates support a targeted development repair, not universal or delivered-WAR
acceptance. Three-year evidence stays exploratory with only two normal origins.

Freeze hashes before fits. Test omitted-block independence, trend dependencies,
individual vs system absence routing, player order/identity weights, valid zeros
and incomplete-label exclusion. Replay original 2017/2018 R probabilities. Mutate
unavailable future labels and later features before refitting 2021 O regular;
require identical predictions. Audit and preserve the original 2026 forecast seal.
Save code, artifacts and the plain-language decision; no production replacement.
