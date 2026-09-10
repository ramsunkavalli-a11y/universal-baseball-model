# Hitter component-specific regression result

**Status:** Promising point result, but not promoted; retain 1,200 PA  
**Production changed:** No

## Test

The same bounded method used for pitchers changed one hitter event at a time over the
already declared 400–3,600 PA grid. Every component started at the incumbent 1,200 PA.
A change was eligible only when it improved both proper scores in 2024, after which
the eligible choices were combined without further tuning.

The 2024 choices were 400 PA for walks, singles, home runs and other outs; 800 PA for
doubles; and the incumbent 1,200 PA for HBP and triples.

| Score | 1,200 PA | Component-specific | Difference |
|---|---:|---:|---:|
| 2024 log loss | 0.988074 | 0.986938 | -0.001135 |
| 2024 Brier | 0.465840 | 0.465592 | -0.000248 |
| 2025 log loss | 1.017511 | 1.016209 | -0.001302 |
| 2025 Brier | 0.481808 | 0.481550 | -0.000258 |

Lower is better. On the 112-player 2025 stability sample, the player bootstrap keeps
the log-loss gain below zero, but the Brier upper bound is slightly positive
(`0.000025`). The frozen promotion gate therefore still fails.

## Interpretation

Most of the candidate is simply the already-tested 400-PA hitter challenger. Splitting
the components adds only a very small improvement over that simpler candidate and does
not resolve its Brier uncertainty. The result supports the direction that translated
hitter production may deserve more weight, but not a production change.

Keep the 1,200-PA prior. Do not tune more component combinations on 2024–2025. The
next valid evidence is a broader historical affiliated source or a future untouched
season. Outside FV, demographics and 2026 outcomes were not used.

Machine-readable detail: `docs/hitter-component-specific-regression-result.json`.
