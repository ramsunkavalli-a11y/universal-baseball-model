# Prospect positive-component outcome result

**Run date:** 2026-09-09  
**Decision:** reject for player value; retain as a tested research target

This audit asks a narrower quality question than WAR: did a pre-MLB player later
record at least 200 PA or BF in a season while producing at least league-average core
batting events or fielding-independent pitching events?

Hitter quality uses neutral wOBA event weights. Pitcher quality uses the standard
fielding-independent `13 HR + 3 (UBB + HBP) - 2 K` numerator per BF. Each player is
compared with the same MLB season, so run-environment changes do not become talent.
The target excludes defense, baserunning, catcher framing, and contact management and
is explicitly not whole-player WAR.

The certified outcome source now includes completed 2025 while excluding 2026. The
2020 workload gate is scaled to a 162-game equivalent; event rates are not scaled.
Non-arrivals and players below the workload gate remain zero outcomes.

## Outer 2023 result

| Population | Positive rate | Core log loss | Candidate | Core Brier | Candidate |
|---|---:|---:|---:|---:|---:|
| Hitters | 0.76% | .03506 | .03205 | .00714 | .00725 |
| Pitchers | 1.18% | .04895 | .04804 | .01101 | .01097 |

Earlier-fold selection chose the baseball-plus-pedigree family for both populations.
For hitters, the log-loss difference interval crosses zero and point-estimate Brier is
worse. For pitchers, both paired intervals cross zero. Neither candidate passes.

The result says current minor-league statistics, demographics, and Rule 4 pedigree
contain much clearer information about reaching MLB than about producing positive MLB
components. Do not add a quality multiplier, WAR bonus, or FV floor from this test.
The next challenger needs richer process evidence and/or longer complete outcome
history, while retaining this simple outcome as the benchmark.
