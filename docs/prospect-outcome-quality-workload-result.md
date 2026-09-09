# Prospect outcome-quality workload result

**Status:** historical prior built; blanket FV challenger rejected

## What was wrong

The private Model FV preview multiplies any-arrival probability by six full assumed
seasons: 2,700 PA for catchers, 3,300 PA for other hitters, and approximately 1,500 BF
for relievers through 4,800 BF for starters. That makes a brief call-up carry the same
conditional workload path as an established player.

## Historical evidence

True MLB debut dates were joined to complete 2015–2024 MLB season totals. The usable
mature cohorts contain 397 hitters and 308 pitchers who debuted from 2015 through 2019.
Each player retains six calendar seasons beginning with debut; missing seasons are
zeros. The shortened 2020 season is shown at a 162/60 workload equivalent. This is a
workload study, not six service seasons and not historical WAR.

The two outcome groups match the probabilities currently available:

- **fringe:** reached MLB but never recorded a 200 PA/BF season in the window;
- **meaningful:** recorded at least one 200 PA/BF season.

| Group | Players | Mean six-year workload | Median |
|---|---:|---:|---:|
| Hitter fringe | 215 | 61 PA | 11 PA |
| Hitter meaningful | 182 | 1,986 PA | 1,981 PA |
| Pitcher fringe, all roles | 76 | 149 BF | 32 BF |
| Pitcher meaningful, reliever | 54 | 948 BF | 900 BF |
| Pitcher meaningful, swingman | 87 | 1,154 BF | 1,072 BF |
| Pitcher meaningful, starter | 91 | 2,505 BF | 2,579 BF |

The hitter meaningful average is stable across early 2015–2017 and later 2018–2019
debut cohorts (late/early ratio .962). Pitcher meaningful workload falls more (.794),
so pitcher priors need more time/context work. Small role cells automatically fall
back to the pooled pitcher tier instead of using an unstable mean.

## FV sensitivity and decision

A research-only challenger used disjoint probabilities:

`P(fringe arrival) × fringe workload + P(meaningful role) × meaningful workload`

It then applied the existing player-specific conditional WAR rate. This removes the
full-season-on-any-arrival error, but it is too blunt because the model still lacks a
separate regular/impact outcome probability.

| Pre-MLB population | Incumbent 50+ FV | Challenger 50+ FV |
|---|---:|---:|
| Hitters | 320 | 18 |
| Pitchers | 18 | 0 |

Josuar Gonzalez moves from 2.84 to 0.62 expected WAR and from displayed 45 to 40. That
is the wrong direction for a credible top prospect. On 76 currently pre-MLB players
in the FanGraphs Top 100, used only as an outside diagnostic, FV MAE worsens from 9.06
to 14.78 and bias from -6.62 to -14.72.

**Decision:** do not replace the current preview with this blanket haircut. The test
proves both that the existing workload assumption is too generous and that a binary
meaningful-role split is insufficient. The next P0 model must estimate regular/impact
outcomes from forecast-date performance, level, age, development, and durable
draft/signing evidence. Outside FV opinions remain evaluation-only, never inputs.

The reusable code and generated private sensitivity are retained so the workload layer
can be used once the additional outcome probabilities are validated. Production player
values remain unchanged.
