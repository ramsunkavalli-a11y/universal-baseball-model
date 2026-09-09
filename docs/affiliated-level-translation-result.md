# Affiliated component translation — Phase 1 result

Status: **provisional universal baseline; historical holdout validation remains**

Official StatsAPI component counts are materialized for MLB, AAA, AA, High-A,
Single-A and Rookie Complex for 2023–2026. The 2026 rows are current predictor
evidence only and are not used to fit or score the translation.

The fit uses the same player's performance at two levels in the same completed
season. That removes between-player talent and avoids mixing a one-year age change
into the level effect. Component probabilities are estimated together in centered
log-ratio space, and a weighted level graph is anchored at MLB.

## Support

| Model | Same-player/same-season pairs | Players | Connected levels |
|---|---:|---:|---:|
| Hitter seven-part PA profile | 3,204 | 2,021 | 6 of 6 |
| Pitcher five-part BF profile | 4,495 | 2,803 | 6 of 6 |

Each level sample requires at least 30 PA/BF. Pair weight is the harmonic mean of
the two exposures so one large sample cannot hide a tiny comparison sample.

The fitted directions pass a basic baseball check. Moving lower-level evidence to
the MLB scale generally reduces hitter HR/walk rates and pitcher strikeout rates,
while increasing pitcher HR risk. No component is clipped independently; translated
probabilities continue to sum to one.

## How it enters the current forecast

- Recent MLB evidence keeps the already-selected MLB baseline.
- A player without recent MLB evidence can use the translated affiliated profile.
- A player without either source keeps the population prior.
- Lower-level evidence is discounted before regression: MLB 1.00, AAA 0.50, AA 0.30,
  High-A 0.20, Single-A 0.10 and Rookie Complex 0.05.
- Hitters regress toward 1,200 PA of MLB prior evidence. Translated pitchers regress
  toward 800 BF; the validated MLB-only pitcher baseline retains its own 200-BF prior.

This reduced pure population-prior coverage to 990 hitter player-years and 2,346
pitcher player-years. Translated affiliated evidence now supplies 18,078 hitter and
23,322 pitcher player-years.

## Boundary

This is not a claim that a raw MLE is a complete prospect forecast. Arrival,
survival and workload remain separate. Same-season movers are selected players, parks
and leagues are pooled within level, and the translation has not yet won a rolling
historical holdout. Those are validation and Phase 2 refinement tasks; the universal
fallback remains in place regardless.

