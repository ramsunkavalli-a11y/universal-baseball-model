# What the historical data can support for defensive talent

2026-10-06. The audit confirms that next-year contribution tests were too narrow
to judge eventual minor-league defensive ability. It also shows why simply
stretching those tests to more years would not fix them. The current aggregate
MLB range source loses position-switchers, and five/seven-year historical tests
have no completed earlier training windows. No new model was fitted.

## Scope and actual coverage

The preserved cohort has 31,563 player-position origins from 2016–2019 and
2021–2024, covering 4,529 distinct people and 94,689 window records. Every
eligible identity remains present, including non-arrivals, infield cameos and
missing metadata. Multiple origins/positions are not independent people.

| Future window | People without prior MLB fielding with same-position quality | Rookie-origin people within that number | Chronological training at fully observed test origins |
| --- | ---: | ---: | --- |
| 3 years | 28 | 0 | At 2021: 29–34 people; at 2022: 34–40, depending on held-player fold |
| 5 years | 27 | 5 | Zero completed earlier windows |
| 7 years | 28 | 6 | Zero completed earlier windows |

People can appear across windows and levels. Counts use all isolated measurement
seasons in the fixed window, not best seasons. “Without prior MLB fielding” is
not proof of no batting debut. These are selected observed defenders, not a
validation sample representative of everyone who played in the minors.

Only 34 three-year player-position rows without prior MLB fielding have measured
quality. They average 1,125.8 weighted minor ground balls, versus 297.0 for the
19,879 unmeasured rows. No measured row has an RK origin label; 32.4% have AAA
labels. The unmeasured rows include non-arrivals, positional changes, cameos and
missing measurements—not a single negative class.

Matching age/level/position/prior-fielding profiles remain sparse: all 43
measured same-position rows at the 2021–2022 test origins have fewer than 20
matching training people; seven have none. The looser infield-only measurement
raises total fold training counts to 55–61 and 67–72 respectively, but mixes
positions and repeats the same future outcome for different origin positions.
It cannot replace a same-position target without an explicit development model.

The timing problem is concrete. A 2016 origin's five-year label ends in 2021;
it cannot train a forecast made in 2019, the latest available fully observed
five-year test origin. A seven-year label ends in 2023, later than every fully
observed seven-year test origin. Holding players out does not fix that calendar
leakage. The older 2008/2013 minor inventory contains position usage, not the
ground-ball quality features needed to recreate the current measurement.

## Baseball checks that changed the next decision

[The player walkthrough](defensive-talent-support-player-walkthrough.md) reviews
13 fixed player-origins, three input-selected DSL cases and their origin-known
peers. Witt has clean later positive SS range despite a negative minor play-share
indicator. Abrams has measurable negative later SS range; Downs and the DSL
non-arrivals have unknown quality instead. Mateo loses otherwise useful seasons
because even small CF stints prevent splitting player-aggregate range runs.
Mayer and Rafaela show why later third-base/center-field range cannot be labeled
origin shortstop talent.

There are also 5,308 unmatched origin-metadata rows. Even matched rows can have
wrong context: Tovar's 2019 panel is INACTIVE with missing age/name, while the
dated defensive source contains 726 short-season balls across SS/2B. This must
be repaired before age/level support is used in a new learner. A player's highest
batting level also differs from the level where most fielding evidence arose.

Native total outs sometimes exceed summed nonpitcher position outs. Across
2016–2025, 498 of 501 nonzero differences exactly match official pitcher outs;
the other three remain unresolved. Strict measurements exclude these seasons
rather than silently ignore the difference. This is source granularity, not
proof that the existing annual delivered-run denominator was a coding bug.

## Decision and coherent next work

Do not fit another broad talent model from this sparse, selective target, and
do not reject minor defensive talent based on it. The next task is a bounded
source repair, not another algorithm/weight tournament:

1. Recover actual MLB range by position from the official leaderboard's split
   option. Certify year, position, exposure and recomposition against player totals,
   with Mateo/Witt/Edwards/Rafaela as fixed checks. A filter on a player's primary
   position alone is insufficient. Keep older aggregate targets as anchors.
2. Repair origin metadata using dated defensive participation and legitimate
   age/name sources, without changing cohort identities. Keep highest level,
   fielding exposure shares, role changes and canceled 2020 separately visible.
3. Recount actual training support. Use a narrow short-window comparison only
   if defensible; longer lower-minors tests require older comparable inputs and
   mature labels, or a clearly labeled held-player retrospective measurement
   study rather than a claimed chronological forecasting win.

Future catcher/running work follows the same ability → development/opportunity
→ delivered-value distinction, but these infield counts do not certify their
sources or experiments. Their component-specific denominators still need review.

Fourteen focused unit tests passed. The review independently reconstructs all
origin pools, replays every window label and verifies source/artifact fingerprints.
Execution checks are not predictive accuracy. Original experiment results,
selected forecasts and the explorer remain unchanged. No 2026 data is used in
this audit; an external source search returned an incidental current-leaderboard
excerpt, which was not ingested or used for model choice. The nonbatting talent
and final player-value goals remain unfinished.
