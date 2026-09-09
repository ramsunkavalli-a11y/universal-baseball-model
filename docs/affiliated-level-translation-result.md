# Affiliated component translation — Phase 1 result

Status: **Phase 1 baseline passed two rolling future-MLB diagnostics**

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

## Future-MLB diagnostic

For each target, the fit and player profile used only earlier seasons. The scoring
population was players with prior affiliated exposure, zero prior MLB exposure and a
positive MLB target the next year. Target membership never entered the forecast.

| Model | Target | Players | Target PA/BF | Translation minus same model without translation log loss |
|---|---:|---:|---:|---:|
| Hitters | 2024 | 130 | 13,449 | -0.004308 |
| Hitters | 2025 | 112 | 15,300 | -0.002372 |
| Pitchers | 2024 | 173 | 23,129 | -0.001791 |
| Pitchers | 2025 | 146 | 17,852 | -0.000900 |

Lower is better. Translation also improved Brier score in all four comparisons and
beat the MLB population prior in every fold. This is enough to retain the simple
translation in the broad Phase 1 baseline; it does not close Phase 2 calibration or
subgroup work.

## Boundary

This is not a claim that a raw MLE is a complete prospect forecast. Arrival,
survival and workload remain separate. Same-season movers are selected players, and
parks and leagues are pooled within level. Only two later-season folds are available
in this current source window. Longer replay, calibration and subgroup work remain
Phase 2 tasks; the universal fallback remains in place regardless.
