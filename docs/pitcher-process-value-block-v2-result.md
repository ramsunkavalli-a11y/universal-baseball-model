# Pitcher process whole-value result

Date: 2026-09-22
Status: **retain for component skill; do not promote into whole value yet**

## Question

The high-minors pitch-process profile already improves next-year K/BB/HBP/HR outcome
probabilities. Does it also improve the clean-slate forecast of total next-season MLB
pitcher value?

## Test

We added four shrunken, level-relative measures—whiffs per swing, strikes per pitch,
swings per pitch, and pitches per batter—to the same historical panel. Coverage is
certified for 2018–19 and 2021–24 at Triple-A through Single-A. Missing evidence is
exactly neutral. The meaningful whole-value comparison uses the four modern test
origins, 2021–24, comprising 19,696 scored rows. No 2026 outcome is used.

We tested the process block in both parts of the model and in conditional value only.
The latter check reflects the baseball mechanism: pitch execution is clearer evidence
of skill than of whether a player receives an MLB opportunity.

## Result

| Engine | Baseline RMSE | Process in both parts | Process only in value-if-active |
|---|---:|---:|---:|
| Ridge | **0.30889** | 0.30890 | 0.30893 |
| CatBoost | **0.30963** | 0.31003 | 0.31010 |
| LightGBM | 0.31044 | **0.31019** | 0.31027 |

LightGBM improves by about 0.00025 RMSE, while ridge is effectively unchanged and
CatBoost worsens. Every player-clustered uncertainty interval crosses zero. The
season-by-season signs are mixed. On the 10,634 rows with current process evidence,
LightGBM improves modestly, ridge is nearly flat, and CatBoost worsens.

## Decision

Keep the pitch-process profile as a validated input to projected pitching components
and as an auditable player diagnostic. Do not let it change the new whole-value
forecast yet. Its real component-level signal is diluted by the much larger arrival
and workload uncertainty, and the small whole-value gain appears only in one engine.

This is a useful boundary rather than a contradiction: a measure can improve our
estimate of how a pitcher will pitch without measurably improving whether and how much
he will pitch in MLB next year.
