# Current conditional WAR paths — 2026-09-08

Status: **Phase 1 baseline built; not publishable rankings**

The dated build now connects team-neutral skill rates to the previously completed
2027–2032 MLB participation and workload paths for every hitter and pitcher in that
forecast universe.

## What is built

- Official MLB StatsAPI component counts for 2023–2026 are retained as predictor
  evidence. The incomplete 2026 season is not used as a model-evaluation target.
- Hitters use a transparent three-season Marcel-class batting estimate, 1,200 PA of
  regression, standard Marcel age adjustment, primary-position value and the existing
  position-player replacement pool.
- Pitchers use the already-validated 3/2/1 five-component model for K, unintentional
  walk, HBP, HR and other BF. Those probabilities remain coherent after aging.
- Pitcher aging uses ratios from the more-regressed sensitivity in Tom Tango's
  adjacent-season pitching work. It is a disclosed Phase 1 fallback, not a claim that
  the old curve is a modern fitted optimum. Tango's warning is binding: unregressed
  survivor samples can make pitcher aging seriously misleading.
- Conditional WAR rate remains separate from MLB probability and conditional PA/BF.
  Expected WAR is their explicit product; current-team depth is never an input.
- A missing control record remains null. It is never silently treated as a free-agent
  or zero-value season.

## Materialized result

| Component | Players | Player-years | Rate-history fallback rows | Control matched | Control missing |
|---|---:|---:|---:|---:|---:|
| Hitters | 3,940 | 23,640 | 19,068 | 21,552 | 2,088 |
| Pitchers | 5,276 | 31,656 | 25,668 | 28,656 | 3,000 |

The large rate-history fallback count is expected: this first rate source contains
recent MLB performance, not translated minor-league skill. These rows receive a
population skill prior rather than zero talent.

Observed broad plausibility ranges before any clipping:

- hitter conditional WAR/600 PA: -1.19 to 4.91;
- pitcher conditional WAR/800 BF: -3.91 to 7.45;
- maximum expected annual WAR after participation/workload: 2.10 hitter and 2.31
  pitcher.

## Team-control improvement

The control build now preserves official `mlbDebutDate`. When FanGraphs has no opening
service balance, only a player with no official MLB debut may start from zero; current
StatsAPI service is then added. A debuted player with missing opening service remains
unresolved. This increased six-year future-control coverage from 1,667 to 8,350
players. The 21 multi-organization cases and other unresolved current-owner/service
cases remain outside controlled WAR.

## Known Phase 1 fallbacks

- Hitter defense and baserunning are zero runs versus league average when richer
  artifacts are unavailable. Primary-position and replacement value are included.
- Pitcher contact quality, leverage and role-specific replacement are deferred.
- Minor-league performance is not yet translated into conditional WAR rate.
- The 2026 rest-of-season production and unpaid-salary paths remain separate missing
  inputs; this build begins with full 2027 seasons.

## Next priorities

1. Translate recent affiliated hitting and pitching component performance to an MLB
   reference, retaining stronger regression at lower levels.
2. Replace hitter zero-defense/zero-running fallbacks where existing certified
   component artifacts cover the player.
3. Fit and validate modern adjacent-season component aging; retain Tango's published
   curve as a sensitivity comparator.
4. Build the separate 2026 rest-of-season workload/WAR and unpaid-salary paths.
5. Resolve current-owner/service exceptions, then pass controlled WAR into contract
   economics. Do not fit or publish dollar rankings until the market-price function
   and uncertainty paths validate.

