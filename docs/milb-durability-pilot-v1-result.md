# Minor-league availability pilot: small positive hint, inconclusive

2026-09-22. Completed the [small fixed screen](milb-durability-pilot-v1.md).
No model, explorer, forecast or injury penalty was changed.

This tests actual **minor leaguers**, not established MLB regulars. Eligible players
had no previous MLB PA, >=100 PA in each of two consecutive years entirely at the
same full-season minor-league level, and historical positions. Team stints were
combined. The same-level restriction prevents counting a partial promoted stint
as missing workload, but selects a narrow group and excludes many good prospects.
It does not certify full-season roster membership or establish a medical cause.

Two chronological tests predicted next-year MLB arrival: 2023 -> 2024 and 2024 ->
2025. Earlier training labels were mature at each cutoff. The test includes players
who never arrive; eventual MLB success is not an eligibility condition.

Among all 219 held-out player-season observations, 14 reached MLB. Among the
productive subset (top-third current level-season OPS), there were only **37 players
and six arrivals**. The classifier already controlled for performance, age, level,
past PA, position, roster status and the position/level workload references.

| Productive-player arrival score; lower is better | Baseline | Add two workload gaps + repetition |
|---|---:|---:|
| Brier | 0.13373 | 0.13112 |
| Log loss | 0.39766 | 0.39040 |

Both scores improve in both test years. But their player-cluster 95% intervals
include zero: Brier change -0.00261 [-0.00586, +0.00008], log-loss change -0.00725
[-0.02056, +0.00683]. The fixed promise criterion is not met. This is **inconclusive**,
not a demonstrated failure of the hypothesis or proof of durability effects.

For the broader eligible group, log loss improves with a favorable interval but
Brier remains uncertain. The secondary >=200 next-year MLB PA target cannot be
fit: neither training window contains a positive case. No threshold was changed
after seeing that. We therefore have no evidence here about sticking in MLB or
career survival. Training support is small: 83 players/11 arrivals in the first
fit, 172 players/16 arrivals in the second, with a strongly regularized linear model.

Position/level-season references account for differing typical workloads, not exact
individual assignment dates. OPS is not park-adjusted. Injured players with fewer
than 100 PA, promoted players, short-season leagues and pre-2021 eras are outside
the screen. Observed shortfalls can reflect role loss, platooning or interrupted
assignments as well as health. Do not attach a "fragile" label to anyone.

Stop here as requested: retain the idea as a small positive lead, make no new
system or production change. A larger sample with dated assignment exposure would
be needed to distinguish the proposed mechanism; this pilot does not authorize it.
No 2026 outcomes were used.

Reproduce: `scripts/test_milb_durability_pilot_v1.py`.
Package: `model_artifacts/milb-durability-pilot-v1-2026-09-22/`.
