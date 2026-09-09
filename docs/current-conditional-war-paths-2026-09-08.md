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
- The frozen Player Value v1 steal and non-steal advancement models now supply hitter
  baserunning. Recent evidence fades through the frozen three-season lookback and then
  returns to the centered neutral fallback.
- Frozen U1 general-range defense now supplies 2027 value for 1,519 hitters using
  official current fielding evidence and prior MLB position outs. Expected defense is
  centered to zero by position. Unsupported players and 2028–2032 remain neutral.

## Materialized result

| Component | Players | Player-years | Translated affiliated | Population prior | Control matched | Control missing |
|---|---:|---:|---:|---:|---:|---:|
| Hitters | 3,940 | 23,640 | 18,078 | 990 | 21,552 | 2,088 |
| Pitchers | 5,276 | 31,656 | 23,322 | 2,346 | 28,656 | 3,000 |

Recent MLB evidence remains the preferred rate source. Players without it now use
regressed, MLB-anchored affiliated component evidence where available; only the
remaining unsupported rows use the pure population prior.

Observed broad plausibility ranges before any clipping:

- hitter conditional WAR/600 PA: -1.34 to 5.06;
- pitcher conditional WAR/800 BF: -4.86 to 7.45;
- maximum expected annual WAR after participation/workload: 2.34 hitter and 2.31
  pitcher.

## Team-control improvement

The control build now preserves official `mlbDebutDate`. When FanGraphs has no opening
service balance, only a player with no official MLB debut may start from zero; current
StatsAPI service is then added. A debuted player with missing opening service remains
unresolved. This increased six-year future-control coverage from 1,667 to 8,350
players. The 21 multi-organization cases and other unresolved current-owner/service
cases remain outside controlled WAR.

## Known Phase 1 fallbacks

- Catcher defense, tracked-range upgrades and defense beyond the adjacent year remain
  neutral. General 2027 range, primary-position, baserunning and replacement value are
  included.
- Pitcher contact quality, leverage and role-specific replacement are deferred.
- The minor-league translation passed 2024 and 2025 future-MLB component diagnostics;
  lower levels still receive stronger evidence discounts.
- The 2026 rest-of-season production and unpaid-base-salary paths are connected through
  the remaining-rights interface.

## Next priorities

1. Calibrate current injury return and role without using team-depth blocking; the
   official-status boundary is already connected.
2. Retain Tango's regressed adjacent-season curve. The modern 2015–2025 challenger
   failed its later-period test and is deferred to Phase 2.
3. Extend defense only where native catcher/tracked evidence and aging are supported.
4. Resolve current-owner/service exceptions. Whole-player WAR and Phase 1 uncertainty
   now feed the annual contract-economics input table, but dollar rankings wait for
   market-price, arbitration, future-CBA and buyout inputs to validate.
