# Era and actual-schedule diagnostic results

2026-09-23. Exposed historical development tests. No production or 2026 forecast changes.

## What was tested

- R/A: inherited rich baseline and source-outage augmentation.
- E/AE: corresponding refits without the explicit post-2021 era indicator.
- S0/S1: identical no-era models trained on eligible origins from 2015 onward; S1 adds actual current minor schedule exposure.

S0 is essential: S1 versus full-history R mixes schedule, era and training-history changes.
Every origin means a year-end forecast for the following MLB season.

## Next-year MLB arrivals: never-debuted minor leaguers

| Origin | Actual | R | E | A | AE | S0 | S1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 95 | 92.5 | 92.5 | 94.9 | 94.9 | — | — |
| 2018 | 108 | 90.9 | 90.9 | 96.2 | 96.2 | — | — |
| 2021 | 157 | 58.1 | 58.1 | 83.9 | 83.9 | 47.6 | 46.0 |
| 2022 | 106 | 112.5 | 108.7 | 159.7 | 155.0 | 115.6 | 116.2 |
| 2023 | 107 | 145.3 | 151.0 | 140.3 | 138.9 | 149.4 | 143.9 |
| 2024 | 104 | 101.3 | 100.7 | 101.5 | 103.3 | 108.1 | 103.9 |

Counts are sums of player probabilities, not a count of players above an arbitrary threshold.

## Proper-score comparisons

| Comparison | Score | Candidate | Reference | Difference | Player-cluster 95% interval | Improving origins |
|---|---|---:|---:|---:|---|---:|
| E/R | brier | 0.024031 | 0.023948 | +0.000083 | [-0.000024, +0.000189] | 1 |
| E/R | log_loss | 0.083570 | 0.083329 | +0.000241 | [-0.000064, +0.000560] | 1 |
| AE/A | brier | 0.023602 | 0.023730 | -0.000128 | [-0.000227, -0.000021] | 3 |
| AE/A | log_loss | 0.081560 | 0.081901 | -0.000341 | [-0.000647, -0.000041] | 2 |
| AE/R | brier | 0.023602 | 0.023948 | -0.000346 | [-0.000634, -0.000067] | 3 |
| AE/R | log_loss | 0.081560 | 0.083329 | -0.001769 | [-0.002689, -0.000878] | 3 |
| S1/S0 | brier | 0.026072 | 0.026106 | -0.000033 | [-0.000260, +0.000208] | 3 |
| S1/S0 | log_loss | 0.092102 | 0.091861 | +0.000241 | [-0.000839, +0.001320] | 2 |
| S1/R | brier | 0.026072 | 0.025556 | +0.000516 | [+0.000134, +0.000911] | 2 |
| S1/R | log_loss | 0.092102 | 0.088794 | +0.003307 | [+0.001701, +0.004937] | 2 |

Lower scores are better. Comparisons use equal weight per origin and matching players.
Player-cluster intervals do not account for all season-level shocks. Annual/stage tables are in the archived score report.

## Fixed decisions

- Era mechanism criterion supported: **True**. This tests the explicit flag only, not all possible era proxies.
- Schedule evidence criteria satisfied: **False**.
- Schedule broader research-candidate criteria satisfied: **False**.
- No criterion authorizes deployment: three-year arrival/regular workload and delivered value are not tested here.

Schedule gates: {"R_harm_guards": {"2021": false, "2022": true, "2023": true, "2024": true, "Lower minors": true, "Upper minors": true}, "broader_candidate": false, "gates": {"majority_origins": false, "pooled_intervals": false, "schedule_harm_guards": true}, "harm_guards": {"2021": true, "2022": true, "2023": true, "2024": true, "Lower minors": true, "Upper minors": true}, "supported": false}.

## Schedule audit

| Year | Prospects | Complete current schedule denominator | Mean PA | Mean PA/team game |
|---|---:|---:|---:|---:|
| 2015 | 3335 | 3335 | 233.4 | 2.240 |
| 2016 | 3407 | 3402 | 228.6 | 2.208 |
| 2017 | 3416 | 3413 | 226.3 | 2.194 |
| 2018 | 3273 | 3271 | 225.2 | 2.228 |
| 2019 | 3371 | 3371 | 222.3 | 2.167 |
| 2021 | 3250 | 3249 | 186.4 | 2.035 |
| 2022 | 3188 | 3188 | 207.1 | 2.076 |
| 2023 | 3163 | 3162 | 208.7 | 2.132 |
| 2024 | 2957 | 2956 | 222.3 | 2.231 |

The aggregate annual comparison mixes player/level composition and is not a causal decomposition.
Team denominators use completed regular games, deduplicated by game ID including reversed home/away listings.
Captures contain other same-sport leagues; player joins retain the existing input population, not a newly filtered one.
No raw PA is increased. Multi-team fractions sum PA divided by each team’s full-season games.
Partial schedule coverage produces a missing denominator, not a guessed value.
This is schedule-relative workload, not individual injury, roster tenure or games personally available.

## Verification and reproducibility

20 new fits plus 2 future-mutation replays; both replays have zero difference.
No new source fetches and no 2026 outcomes were used. Source/code hashes were locked before fitting.
Run audit then fit --freeze only for a fresh reproduction; never replace the existing contract.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_era_schedule_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_era_schedule_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_era_schedule_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_era_schedule_v1.py
```
