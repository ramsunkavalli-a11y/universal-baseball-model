# Post-arrival progression simulation input

Status: durable validated equations materialized; not integrated and no current value
changed.

The accepted post-arrival result is now a reproducible model input rather than only a
research score. The package contains four equations fitted through completed 2025
outcomes:

| Player type | Transition | Rows | Advances | Inputs |
|---|---|---:|---:|---|
| Hitter | Fringe to higher | 887 | 175 | age, elapsed time, prior-year active status and workload |
| Pitcher | Fringe to higher | 1,132 | 161 | age, elapsed time, prior-year active status and workload |
| Hitter | Meaningful to established | 270 | 83 | age and elapsed time fallback |
| Pitcher | Meaningful to established | 342 | 140 | age and elapsed time fallback |

The workload equations are used only for fringe progression, where they passed the
2023 selection and both 2024/2025 confirmations. The smaller meaningful transition
keeps the pooled fallback. Pitcher role is excluded because it did not add repeatable
information after total workload. The package hashes the runner, 21 source files and
both output tables.

Next, the research simulator must begin each draw before MLB arrival, sample that
draw's annual workload, normalize it to the matching active-player environment, and
feed it to the following year's frozen fringe equation. State can move only forward.
The draw's state then controls the eligible historical workload/performance pool.
This removes the current circular shortcut of selecting an eventual tier first. It
must be replayed against historical cutoffs before it can change rankings.
