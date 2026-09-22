# Next-season hitting ability across every affiliated level

Status: **complete; level-path fields are not selected for the hitting-strength model**

## The question

The existing value model asks how much MLB value a player will produce next year. That
is the right final question, but it provides very little direct hitting evidence for a
young player who stays in the minors. This test instead asks a narrower question:

> How well can we predict a player's hitting performance next season, wherever he
> actually plays, after translating every level onto the same MLB-equivalent scale?

This lets a DSL-to-DSL, DSL-to-complex, Double-A-to-Triple-A, and Triple-A-to-MLB season
all contribute evidence. The level reached next year is used only to standardize the
observed result. It is never given to the forecast as advance information.

## What was measured

Each following-season batting line was divided into seven outcomes: unintentional
walk, hit by pitch, single, double, triple, home run, and everything else. Every segment
at every level was translated to the MLB scale using same-player, same-season level
movers available by the forecast date. Players who appeared at multiple levels were
combined by plate appearances.

The final target is a neutral-weight wOBA-like measure of next-season hitting quality.
The test includes 17,552 forward-test player-seasons from 7,483 players. It requires at
least 30 affiliated plate appearances in the following season and uses six
chronological test years: 2017, 2018, 2021, 2022, 2023, and 2024. No 2026 result was
used.

The challenger added 19 compact development-path fields: years and consecutive years
at the level, career exposure there, repeats, end-of-season movement, partial
promotions, prior peak, and advancement speed. The base model already included age,
level, exposure, current and prior performance, and detailed contact evidence.

## Result

| Model | RMSE | PA-weighted RMSE |
|---|---:|---:|
| Base hitting model | **0.035152** | **0.032561** |
| Base plus level-path history | 0.035178 | 0.032570 |

The path version was worse by 0.000026 RMSE. Its player-clustered 95% interval ranges
from a 0.000009 improvement to a 0.000062 worsening. It improved only two of the six
test seasons. Three of the four model families worsened; XGBoost was the one exception.

That is not evidence for changing the ensemble or applying a general repeat-level
penalty.

## The Carlos Concepcion type of case

The base model does show the concern that prompted the test, but it is modest:

| Historical group | Rows | Actual | Base forecast | Path forecast | Base RMSE | Path RMSE |
|---|---:|---:|---:|---:|---:|---:|
| All rookie-level hitters | 6,013 | 0.1867 | 0.1877 | 0.1876 | **0.03400** | 0.03400 |
| Rookie-level repeaters | 2,627 | 0.1864 | 0.1895 | 0.1890 | 0.03383 | **0.03380** |
| Third-or-later rookie season | 905 | 0.1879 | 0.1924 | 0.1923 | 0.03553 | **0.03545** |

Third-or-later rookie-level hitters were overestimated by about 0.0045 on this scale.
Adding path history reduced that overestimate by only 0.0001. The small subgroup RMSE
gain is real in the sample but far too small to support a hand-built penalty, and the
same feature block slightly worsened the full population.

## What this means for the current model

The current model **does account for players moving up** when it is evaluated. It
predicts next-season hitting from information available at the forecast date, then the
test translates the player's actual next-season performance at the level or levels he
reached back onto a common scale. A promotion is therefore not treated as poor hitting
merely because the competition became harder.

The result also suggests that age, current level, exposure, recent performance, and
the multi-year record already absorb most of the useful information in “third year at
this level.” Explicit path labels add very little independent information about
next-season hitting quality.

## Decision

- Keep the compact path fields in the MLB-arrival challenger, where they previously
  produced a small consistent improvement.
- Do not put them into the general hitting-strength ensemble.
- Do not manually reduce Hit/600 for repeaters.
- Preserve the frozen 2026 forecast.
- In the explorer, show repeat-level history as context and uncertainty, not as an
  unsupported deterministic penalty.

## Reproducibility

- Target construction: `src/universal_baseball/hitter_future_translated_performance.py`
- Chronological evaluation: `scripts/evaluate_hitter_future_translated_performance_v2.py`
- Tests: `tests/test_hitter_future_translated_performance.py`
- Generated evidence: `reports/generated/hitter-future-translated-performance-v2/`
