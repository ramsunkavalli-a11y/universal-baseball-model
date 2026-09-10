# Pitcher component-specific regression result

**Status:** Challenger rejected; retain the universal 800-BF affiliated prior  
**Production changed:** No

## Test

The incumbent gives strikeouts, unintentional walks, hit batters, home runs and
other contact the same 800-BF regression strength. The challenger changed one
component at a time over a fixed 200–1,600 BF grid. A change was eligible only when
it improved both component log loss and Brier score in 2024; ties favored stronger
regression. Eligible changes were then combined without further tuning.

The 2024-selected profile was:

| Component | Selected BF |
|---|---:|
| Strikeouts | 400 |
| Unintentional walks | 600 |
| Hit batters | 800 |
| Home runs | 1,600 |
| Other contact | 200 |

On 173 arriving pitchers and 23,129 MLB BF in 2024, the combined candidate improved
log loss from 0.976699 to 0.975983 and Brier score from 0.515806 to 0.515315.

On 146 pitchers and 17,852 BF in 2025, both gains reversed: log loss worsened from
0.994667 to 0.994728 and Brier worsened from 0.524767 to 0.524855. Strikeout
underprediction and other-contact overprediction also became larger.

## Decision

Keep 800 BF for all five affiliated pitcher components. The model now supports
component-specific reliability for future research, but this fitted mapping must not
enter player values. The 2025 season was already disclosed before this test, so it is
stability evidence rather than untouched promotion evidence in any event.

This result reinforces the simple-baseline rule: a more flexible reliability model
fit one season better and the next season worse. Do not search additional strengths
or component combinations on these same two years. Further work needs more historical
affiliated seasons or a genuinely new evidence class.

Machine-readable detail: `docs/pitcher-component-specific-regression-result.json`.
