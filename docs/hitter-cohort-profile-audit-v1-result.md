# Where the hitter playing-time model systematically misses

2026-09-23. Diagnostic only; no model, forecast, explorer or remote changes.

## Main finding

There are repeatable errors beyond COVID. The strongest is playing-time
allocation among existing major leaguers: too little for players coming off
400+ MLB PA, and too much for those coming off 100–399. Those opposing errors
can conceal one another in an apparently reasonable total.

Importantly, the retained research combination still uses the older B forecasts
for previous major leaguers. The F/D improvements apply only to never-debuted
minor leaguers. The existing ensemble E largely avoids the MLB allocation bias
and beats this inherited MLB forecast on RMSE in every next-year cohort. Some
of the next useful work is therefore testing integration of an existing stronger
model, not searching for another feature or learner.

## Scope and evidence

The [audit plan](hitter-cohort-profile-audit-v1-plan.md) fixes 63 cutoff-known
profiles before scanning their errors. We audited 52,181 annual prediction rows:
Year 1 origins 2016/17/18/21/22; Year 2 origins 2016/17/21/22; Year 3 origins
2016/21/22. Prospect participation-only evidence also includes 2023/2024 origins.
No matching D workload predictions exist for those last two origins, and they
were not invented. Training-only years are not described as test cohorts.

The model under audit is the retained research F participation/D conditional PA
for never-debuted prospects, with inherited B probabilities/workload elsewhere.
This is not a claim that a new research version has been deployed in the live
explorer. No batting-rate accuracy, fielding, pitcher, WAR or six-year-control
diagnosis is established here. All starting players, including non-arrivers,
stay in profile denominators.

Positive errors below mean actual PA exceeded predicted PA. Negative means
the model predicted too much. Non-2021 is not synonymous with wholly unaffected
by COVID: 2022 remains included and is also shown separately.

## 1. Established workload is compressed toward the middle

Mean next-year PA error per player, grouped using MLB PA known at the cutoff:

| Forecast origin | Prior MLB PA 100–399 | Prior MLB PA 400+ |
|---|---:|---:|
| 2016 | -44.4 | +51.6 |
| 2017 | -54.6 | +44.8 |
| 2018 | -36.1 | +9.7 |
| 2021 | -47.5 | +57.0 |
| 2022 | -46.0 | +43.9 |

Every cohort has the same direction. Excluding 2021 and weighting origins
equally, the model overpredicts the 100–399 group by 45.3 PA/player and
underpredicts the 400+ group by 37.5. The groups contain 188–275 rows per cohort,
not only a few famous players. The 100–399 category is prior workload, not a
verified bench role; it includes injuries, partial seasons and demotions.

The signs persist at Years 2 and 3 in every available cohort. Outside 2021,
the three-year total for the 100–399 group is overpredicted by 137 and 184 PA
per player at the 2016 and 2022 origins; the 400+ group is underpredicted by
78 and 102. There are only two non-2021 complete cumulative origins.

The older-regular subset (age32+, prior400+) is also underpredicted next year
in all five cohorts, but has only 32–54 rows per origin. It does not meet the
audit's stronger subgroup support threshold. Do not turn that into a blanket
age adjustment without testing.

### An existing comparator does much better

Mean next-year signed PA error outside 2021:

| Cutoff profile | Inherited MLB model in research combination | Existing ensemble E |
|---|---:|---:|
| Prior MLB PA 100–399 | -45.3 | -5.4 |
| Prior MLB PA 400+ | +37.5 | +2.3 |
| All current MLB | -5.4 | -0.6 |

E also lowers RMSE in each of these groups in all five next-year cohorts.
Across all current MLB players, yearly RMSE moves from 168.1/160.0/168.5/152.6/
159.0 to 150.0/143.6/154.6/135.9/141.5. These are existing archived forecasts,
not refits selected for individual names. Universal F/D diagnostic predictions
also reduce some inherited bias but do not uniformly beat E; no alternative
scope is selected here. Replacing inherited MLB forecasts still needs a fixed
integration/value test rather than automatic deployment from this audit.

## 2. Better-rated prospects are still short of PA

The top fifth of the model's own cutoff-time predicted batting talent is
underpredicted for next-year PA in all five workload cohorts. Per-player gaps
are +1.4, +1.2, +4.3, +7.8 and +1.1 PA at 2016/17/18/21/22. These small averages
include roughly 637–682 prospects per origin, most with zero future MLB PA.
They are not the error size for an actual major-league regular.

For cumulative PA, this group's shortfalls are 12,766 PA (2016), 36,251 (2021)
and 2,466 (2022). This supports continuing to investigate the opportunity path
for better prospects; it does not show that the rejected talent-feature addition
solved it or that current public prospect grades were tested.

Young upper-minor prospects and players promoted to a higher primary level are
underpredicted in the three older next-year cohorts and in 2021, but slightly
overpredicted at the 2022 origin. AAA arrival estimates also switch direction
in later cohorts. These are not stable all-era rules that justify a permanent
boost to every young/promoted/AAA player.

## 3. The broad population matters: not every minor-league profile is missed low

Equal-origin signed annual PA error per starting player outside 2021:

| Cutoff cohort | Year 1 | Year 2 | Year 3 |
|---|---:|---:|---:|
| Upper-minor prospects | +1.67 | +4.02 | +7.53 |
| Lower-minor prospects | -0.13 | -0.39 | +0.75 |
| Current MLB | -5.41 | -12.21 | -17.85 |
| Former MLB in minors | +2.45 | +1.65 | +1.03 |
| Inactive/unknown | -0.04 | -1.41 | -1.35 |

Horizon comparisons have different available origins. Small pooled errors can
hide large individual misses and offsetting cohort errors. Lower-minor next-year
arrival is often slightly overpredicted despite spectacular misses such as Soto.
Substantial repeaters and partial-promotion returners have mixed directions;
this audit does not support a new universal repeater penalty.

High-strikeout prospects (>=30% K, >=200 current PA) have too many predicted
next-year arrivals in each of the latest three origins: 13.3 versus 6 actual,
14.2 versus 10 and 7.5 versus 6. Older results are mixed and positive events are
small. High-walk/high-HR/low-K groups are also period-sensitive. Raw observed
rates vary with level and environment, so these descriptive bins cannot identify
an isolated causal skill effect.

## 4. Smaller example-led profiles deserve a targeted follow-up

These two definitions were examined after reading the largest misses. They are
explicitly exploratory, not part of the fixed 63-profile discovery screen.

**Young full-season players with only a brief MLB debut:** age<=25, >=400 total
PA, but <100 MLB PA at the cutoff. Next-year PA is underpredicted in all five
cohorts. Across 210 player-origin records, actual PA is 34,345 versus 28,253
predicted. Examples include Andujar, Mancini and Outman. A brief debut moves
them out of the never-debuted scope while leaving substantial development
potential; this is a reason to test the model boundary, not proof that the
boundary alone causes every miss. The ensemble reduces several of these errors.

**Former regulars whose latest season has no MLB PA:** minor-league returners
with >=400 MLB PA in either of the previous two calendar years. There are only
26 player-origin records across five origins. Seven have next-year MLB PA;
19 do not. Actual total is 1,883 PA versus about 108 predicted. Tatis at the
2022 cutoff receives 7.5 expected PA versus 635 actual; Duffy at the 2017 cutoff
receives 1.2 versus 560. Sogard and Vogt supply other positive cases.

The model knows these are prior major leaguers, so this is not the previously
repaired false-prospect label. Their current level/low recent workload can still
look like a stalled minor-leaguer. The group also contains genuinely finished
careers. We cannot call every low-PA season an injury or safely boost all
returners; explicit cutoff-known absence/return context is a candidate to test.

## 5. COVID is mainly a participation problem in the current residual accounting

The 2021-origin prospects' three-year shortfall is 49,366 PA. In the exact
accounting decomposition, 42,716 is the participation-weighted term and 6,651
is the workload-among-participants term. This is not a causal percentage
attribution, but it locates the larger arithmetic shortfall.

For the next year alone, the participation term is +9,753 PA and the workload
term is -3,597. In aggregate, the model is predicting too few participants,
while overpredicting conditional workload across the participants it observes.
Some future stars are still far too low individually. Those facts can coexist;
simply raising every prospect's conditional PA would address the wrong aggregate
error. The earlier future-regular-only examples must not be generalized to all
participants or all starting prospects.

## Interpretation and next priority

1. First test the already stronger ensemble for existing MLB players, keeping
   the improved F/D prospect forecasts separate. Include brief-debut players
   explicitly and verify delivered value, not just PA or a league total.
2. Investigate returning established players with lost recent seasons using
   cutoff-known absence/status history; separate these from genuine attrition.
3. Address prospect participation/promotion timing without a blanket talent,
   AAA, repeater or COVID multiplier. Keep ordinary and disrupted cohorts visible.

These are proposed follow-ups, not implemented fixes. The audit does not supply
new authority to replace the protected forecast or publish a model update.

Full per-origin tables, all 63 profiles, both error directions and player examples
are in `reports/generated/hitter-cohort-profile-audit-v1/`: `report.json`,
`examples.json`, `supplement.json` and `audited-predictions.parquet`.
The supplement labels its post-scan comparisons. Profiles overlap and cannot be
summed as independent sources of error. Recurrence flags are descriptive, not
multiple-testing-adjusted significance or causal identification. Position and
medical-status profiles lack adequate joined evidence here and were not inferred.

Eight focused tests pass; prediction products and residual decomposition agree
with the unchanged archives. Input hashes are preserved. The original 3,907-player,
31-file 2026 freeze verifies unchanged. No new fitting or protected outcomes.
