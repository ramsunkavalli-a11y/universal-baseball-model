# Prospect talent-first audit result

Last updated: 2026-09-12  
Status: **REJECT THE INCUMBENT TALENT RANKING.**

## Decision

Do not use the existing six-year conditional WAR rate as a prospect talent rank.
The audit exposed three large accounting problems:

1. it averaged six projected seasons and mislabeled that average as present talent;
2. the hitter age rule gave the youngest, least-observed hitters a large positive
   development credit, while pitchers used a different aging construction;
3. replacement and position value let almost-unknown catchers look like the best
   baseball talent in the system.

The original output was 50 hitters, zero pitchers, zero overlap with the eligible
FanGraphs top 50, and all 50 rows had thin evidence plus a premium-position boost.
Among hitters with reliability below 0.05, the correlation between age and the
incumbent batting rate was **-0.84**. Age was functioning as the dominant evidence.

## Corrected diagnostic

The diagnostic now uses only the first forecast season, removes the hitter future-age
adjustment, excludes replacement and position from talent, and leaves players below
0.20 reliability unresolved rather than ranking tiny differences among them.

- 6,719 eligible players;
- 1,671 with supported evidence and 5,048 unresolved;
- supported top 50: 42 hitters and 8 pitchers;
- 7 players overlap the eligible FanGraphs top 50;
- 29 of 42 eligible FanGraphs top-50 players have supported evidence;
- their median internal talent rank is 136.

This is cleaner accounting, not a finished prospect model. Several well-regarded
prospects grade below MLB-average present skill. That can be reasonable for young
players, but the model currently has no validated way to turn present skill into
future ceiling. Public ranks are a diagnostic only and did not set any threshold or
score.

## What this establishes

- Playing time is not the immediate cause of the implausible names.
- Catcher preference was an accounting leak, not evidence that the catchers were
  elite hitters.
- A prospect list needs two distinct talent states: **present translated skill** and
  **future talent distribution**.
- Sparse players are unknown. They cannot be declared elite or poor from a population
  prior plus a few events.
- Position, arrival, playing time, control, cost, and dollars remain downstream of
  talent.

## Next build

Use the already confirmed Current Talent Baseline 2 as the hitter present-skill
foundation. Build the same cutoff-safe present-skill contract for pitchers. Then fit a
historical development layer that predicts later translated skill from present skill,
age, level, components, evidence strength, and approved demographics. The target is
future skill conditional on observed baseball opportunities, not future playing time.

The development layer must be tested on later untouched seasons, report the full
distribution rather than only a mean, and beat simple no-change and transparent aging
baselines. FanGraphs/MLB Pipeline ranks remain outside evaluation only.

