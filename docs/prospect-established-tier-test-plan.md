# Prospect established-tier workload test plan

Status: frozen before current FV sensitivity is scored.

## Problem

The current private FV preview gives every arrival a near-full six-year workload. The first binary correction split arrivals into fringe and meaningful outcomes, but it cut credible prospects too severely because one 200 PA/BF season covers both short-lived depth and durable regulars.

## Fixed hurdle

Use three ordered, unconditional probabilities for each pre-MLB player:

1. any MLB arrival;
2. at least one meaningful season;
3. an established role.

The already defined two-year established outcome is:

- hitter: one 400 PA season or two 300 PA seasons;
- pitcher: one 400 BF season or two 200 BF seasons.

Each probability is modeled separately with the existing chronology-safe core StatsAPI inputs. The final probabilities are constrained only to the logical order `arrival >= meaningful >= established`; they are not calibrated to outside grades.

Convert them to disjoint probabilities:

- fringe arrival = arrival minus meaningful;
- meaningful but not established = meaningful minus established;
- established = established probability.

## Workload evidence

Use mature six-calendar-year MLB paths for 2015-2019 debut cohorts. Missing seasons remain zero and 2020 workload is scaled to a 162-game equivalent.

- Fringe: no 200 PA/BF season.
- Meaningful-only: at least one 200 PA/BF season but no 400 PA/BF season.
- Established: the same rule as the forecast target—one 400 PA/BF season, or two
  300 PA seasons for hitters / two 200 BF seasons for pitchers.

Pitcher workload priors remain role-specific only when at least 30 historical players support the cell; otherwise they regress fully to the pooled tier. Hitter priors use the hitter pool. No observed high workload is clipped.

Expected workload is the sum of each disjoint probability times its historical tier workload. The existing conditional WAR rate then converts workload to expected WAR. Skill rate, defense, running, role probabilities, contract status, and cost are unchanged.

## Checks and decision

- Every current pre-MLB player keeps a value and uncertainty label.
- Ordered probabilities and disjoint probabilities must be inside zero and one and sum to arrival.
- Report workload and FV distributions by player type and tier support.
- Report named examples already discussed, including Josuar Gonzalez.
- Outside FanGraphs FV may be reported only as a diagnostic on matched players. It cannot select, fit, calibrate, or floor the model.
- Reject if the third tier still collapses nearly all 50+ prospects, creates implausible counts, violates ordering, or relies on unsupported cells.
- This is a private sensitivity until a later forecast period confirms the underlying established-role probabilities.
