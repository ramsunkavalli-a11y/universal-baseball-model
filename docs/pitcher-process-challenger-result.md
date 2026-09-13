# Pitcher pitch-process challenger result

Last updated: 2026-09-12  
Status: **PASSED FOR HIGH-MINORS NEXT-YEAR COMPONENT ESTIMATION**

## Question

Do physical pitch-call summaries add future information beyond translated K, BB, HBP,
HR and other-batter outcomes, age, level and evidence?

The tested inputs are regressed, level-season-relative whiffs per swing, strikes per
pitch, swings per pitch and pitches per batter faced. They contain no velocity,
movement, pitch type, public rank or FV. Raw current workload is not an extra candidate
feature.

## Source boundary

Official-feed fidelity audits now certify 2018–19 and 2021–24 AAA, AA, High-A and Single-A pitch
sequences. Synthetic Rookie/complex seasons are excluded. Reusable season aggregates
supply the player totals and obey `whiffs <= swings <= pitches` and
`strikes + balls = pitches`.

## Result

The expanded model trained on 2018, selected its fixed form on 2021, and was then
replayed on untouched 2022–24 origins against next-season 2023–25 outcomes. The missing
2020 season is never bridged as if it were normal.

| Origin | Players | Player log-loss change | Player Brier change |
|---|---:|---:|---:|
| 2022 | 1,374 | -0.001021 | -0.000568 |
| 2023 | 1,360 | -0.002053 | -0.000997 |
| 2024 | 1,334 | -0.001645 | -0.000861 |

Lower is better. Event-weighted log loss and Brier also improved in all three years.
Every equal-player paired 95% interval was entirely below zero for both scores.

Every single-family check—whiff, strike, swing and pitches per batter—improved all four
scores in every confirmation year. Strike rate contributed the largest standalone
gain; whiff plus strike captured most of the combined improvement. The full process
profile performed best in development and passed confirmation.

## Decision and limit

Promote the full profile as an optional high-minors input to the **current/next-year
component estimate**. The separate direct peak test has now been completed; see
`docs/peak-pitcher-process-result.md`. Players without certified process evidence retain
the existing results-only estimate; missing data never becomes a penalty or bonus.

Machine-readable detail: `reports/generated/pitcher-process-challenger/report.json`.
