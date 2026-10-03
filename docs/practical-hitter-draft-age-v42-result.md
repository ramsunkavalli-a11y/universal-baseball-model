# Draft-age consistency: a real source issue, no practical forecast upgrade

2026-10-03. All 70 PA/rate heads replay; 15 player walks are complete.
V33b remains the working forecast. No protected 2026 outcomes or deployed changes.

School class is missing for draft classes 2006–08, 2010–17 and 2019 in the saved
source. It is largely available for 2009, 2018 and 2020–24. The model therefore
learned a school-unknown association partly confounded with vintage. A more
consistent representation is worth testing, but source consistency is not proof
of better forecasting.

The fixed comparison replaced four school flags with approximate known age at
draft, its scaled value and an interaction with low-professional-exposure draft
rank. No new college data, thresholds, models or favorable-player rules. Known
draft ages range 16–27; 47 player/draft combinations vary by at most one season-age
year. Unknown age stays unknown, including 37 of 195 first-year 2024 drafted rows.
Some of those have known schooling, which this replacement loses. The original
labels remain preserved. Same V34 population, training membership and learners.

| Identical historical forecasts | Source control | Draft-age representation |
|---|---:|---:|
| All-cohort PA RMSE | 61.652 | 61.651 |
| Conditional MLB batting RMSE, wins/600 | 1.82465 | 1.82159 |
| Delivered batting + replacement RMSE | 0.440603 | 0.440476 |
| Public-matched PA RMSE | 144.487 | 144.526 |
| Public-matched PA MAE | 111.577 | 111.601 |
| Public-matched delivered-value RMSE | 1.016384 | 1.017584 |

The all-cohort value-MSE difference is −0.000112, nominal player-cluster 95%
development interval −0.000642 to +0.000418: tiny and uncertain. Public contribution
and PA worsen slightly. The batting-only mechanical contrast improves all-cohort
contribution a little; its improved rate is not enough to finish delivered value
or opportunity. First-year older top picks, brief debuts and absent veterans stay
in the evaluation. None becomes a validated subgroup by its small average gain.

The concrete cases show the limits:

- Kurtz: 42.5→44.3 expected PA versus 489 actual; virtually unchanged batting.
  Only five future-active training players match the broad older-draft/low-pro-
  exposure/never-debut rate profile. Precise immediate talent is unsupported.
- Volpe: 497 AA and 99 AAA PA are present, yet opportunity remains 82.5 versus
  601 actual. This is not a draft-class repair.
- Burger: PA 144→148 versus 183; batting −0.156→−0.101 versus +0.669. Useful
  modest change, but unsuccessful returning/debut peers remain visible.
- Khris Davis improves mostly because his batting projection falls; Martinez
  worsens for the same broad change. Do not describe this as learned foreknowledge
  of Davis's collapse or Martinez's breakout.
- Lopez gets nearly exact PA while missing batting badly. Astudillo gets nearly
  exact delivered value through offsetting PA/rate errors. Neither certifies the
  whole model.

There is also an important correction to the interpretation of famous misses.
Among the narrow first-season, age-20+, top-15-pick, under-150-pro-PA cohort, only
2 of 16 players from earlier noncanceled classes reached MLB the following year;
4 of 9 from the 2024 class did. Six 2020 players had a canceled pro season and are
shown separately, not treated as an ordinary first-year group. This small,
diagnostic cohort is not a general promotion estimate. It does show why Kurtz's
large individual miss does not prove every such player's low annual mean was
illogical. Longer-term promise and next-year playing time are different questions.

Retain the source diagnostics and age representation as research; do not adopt
the forecast or start another age/school parameter sweep. The next substantial
step is a joint opportunity/performance distribution: preserve paired outcomes
to show non-arrival, regular use, downside and upside while testing its mean
against the same baseline. Do not relabel intervals from training comparables as
calibrated uncertainty without held-out probability/coverage checks. This remains
annual offense/workload, not completed player valuation.

[Contract](practical-hitter-draft-age-v42-contract.md) ·
[15 source-to-forecast walks](evidence/practical-hitter-draft-age-v42/player-walkthrough.md) ·
[Pre-fit source review](evidence/practical-hitter-draft-age-v42/source-walkthrough.md).
