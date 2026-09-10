# Prospect minor-to-MLB position-transition result

Status: superseded as a promotion test; retained as a descriptive transition table.

Chronology correction (2026-09-10): this audit's two-season destination labels
overlap later origin cutoffs. It therefore cannot authorize fitted player-value work.
The replacement next-season audit in `docs/prospect-shortstop-retention-result.md`
uses non-overlapping, time-ordered labels and is the controlling result.

## Outer result

The outer check trained on 2021 and 2022 minor-league origins and evaluated 576
players from the 2023 origin group who recorded MLB fielding usage in 2024 or 2025.
The prior weight of 10 arrivals was selected only on the earlier development check.

| Model | Multiclass log loss | Multiclass Brier | Exact destination |
|---|---:|---:|---:|
| Training destination rates | 1.4886 | 0.7511 | 37.0% |
| Origin-position transition | 0.8114 | 0.4029 | 75.2% |

Candidate-minus-baseline log loss was -0.6772 with a player-bootstrap 95% interval
of -0.7479 to -0.6031. Brier difference was -0.3481 with an interval of -0.3893 to
-0.3068. The five probability bins were also close to observed rates; for example,
the highest bin averaged 74.2% predicted and 75.2% observed.

## What the transitions say

Outer-period same-group retention among arriving players was:

- catcher: 85.9% across 92 players;
- outfield: 83.7% across 203 players;
- middle infield: 65.9% across 164 players;
- corner infield: 65.7% across 105 players;
- DH/other: 41.7% across 12 players.

The fitted catcher row assigns 88.1% to catcher after shrinkage. Middle infielders
receive 62.7% middle infield, 23.0% corner, and 12.0% outfield. These are conditional
position probabilities, not arrival probabilities and not talent bonuses.

## Decision

Do not advance this coarse transition table into player value. Its descriptive
position frequencies remain useful, but only the chronology-safe player-level result
may authorize a private sensitivity.

This result does not authorize published values, catcher quotas, organization depth,
or outside FV inputs. It also does not model whether a player reaches MLB; the nested
career hurdle handles that separately.

Machine-readable detail: `docs/prospect-position-transition-result.json`.
