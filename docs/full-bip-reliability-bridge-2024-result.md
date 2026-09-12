# Full BIP reliability bridge — 2024 confirmation

**Status:** global pitcher bridge rejected; repeated level split preserved

## Frozen Phase 2 method

The first full-rate replay exposed a reliability mismatch between a 100-contact BIP
profile and the active 800-BF pitcher profile. Before reading 2024 outcomes, Phase 2
replaced the fixed 100-contact BIP prior with an origin-specific equivalent:

`800 BF × origin-season MLB BIP rate`

One bounded BF-weighted residual weight was then learned from the already disclosed
2021-to-2022 and 2022-to-2023 transitions. The fitted weight was `0.8137`. The method
and weight were frozen before the newly built full 2024 BIP panel was scored.

The 2024 public source streamed 3.41 GB across 29 level/month assets, resolved 494,884
contacts for 4,514 pitchers, and deleted all raw downloads after compact reduction.

## Untouched 2023-to-2024 result

| Metric | Active baseline | BIP bridge | Change |
|---|---:|---:|---:|
| Equal-player MAE, runs/800 BF | 60.49 | 59.95 | -0.54 |
| Equal-player RMSE | 74.28 | 75.34 | +1.05 |
| BF-weighted MAE | 54.29 | 52.25 | -2.04 |
| BF-weighted RMSE | 66.80 | 66.54 | -0.26 |

The candidate fails because equal-player RMSE worsens and the level guardrail
reverses at A and Rookie. High-A, AA and AAA improve on all four errors. That same
high-minors-positive, low-minors-negative split appeared in the earlier transitions,
so it is structural rather than a named-player outlier.

## Decision

Keep the global pitcher BIP production weight at zero. Do not change talent, WAR, FV,
or player value.

A high-minors-only challenger is now plausible, but it was not the frozen 2024 rule.
The public 2025 archive currently ends in May (10 assets, 137,364 resolved contacts)
and cannot serve as a full-season confirmation. Wait for a complete later source or
another untouched origin before testing a new level-specific rule. Do not label the
partial 2025 panel as season evidence.
