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
information after total workload. The package hashes the runner, 22 source files and
all output tables.

After an advancement draw succeeds, a separate time-ordered test assigns a direct
established jump with 33.8% probability for hitters and 20.7% for pitchers; otherwise
the destination is meaningful. This split improved log loss and Brier score versus one
pooled probability in 2023, 2024 and 2025. The advancement chance itself is unchanged.

The workload association is intentionally strong and must not be described as a
causal talent gain. At age 24 and elapsed year two, the fitted fringe probability is
6.5% with no prior workload versus 59.9% with one hitter active-season mean; the
pitcher comparison is 3.6% versus 44.2%. The package therefore includes the training
minimum, P1, P99 and maximum for every feature. The future replay must report draws
outside those bounds rather than silently trust extrapolation.

Next, the research simulator must begin each draw before MLB arrival, sample that
draw's annual workload, normalize it to the matching active-player environment, and
feed it to the following year's frozen fringe equation. State can move only forward.
The draw's state then controls the eligible historical workload/performance pool.
This removes the current circular shortcut of selecting an eventual tier first. It
must be replayed against historical cutoffs before it can change rankings.

The coefficients fitted through 2025 cannot be used unchanged in an older historical
forecast. Every replay origin must refit on only the outcomes available at that date;
the durable package is the current forward input and reproducibility reference.

The deterministic state engine for that sequence is now implemented and tested. The
first MLB season uses the frozen career definitions: positive workload is fringe,
200+ PA/BF is meaningful and 400+ is established. After that initial classification,
only prior-year workload may affect the following transition, with at most one forward
transition per player-year. The remaining
integration is to let the simulated state select the appropriate historical workload
and performance pool, then run the full cutoff replay.
