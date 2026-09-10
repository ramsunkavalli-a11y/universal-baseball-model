# Prospect broad-history positive-tail result

**Decision:** `reject_basic_tail_family`

The fixed basic StatsAPI feature set was fitted once on 2008–2010 and then left unchanged. A pre-scoring correction removed 2011–2012 because their outcomes overlap the first evaluation snapshot.

| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) |
|---|---|---:|---:|---:|
| hitter | old | 1 | 0.0104 (0.0003, 0.0204) | 0.0467 (0.0136, 0.0789) |
| hitter | modern | 0 | 0.0015 (-0.0083, 0.0119) | 0.0156 (-0.0153, 0.0473) |
| pitcher | old | 2 | 0.0033 (-0.0009, 0.0076) | 0.0068 (-0.0019, 0.0159) |
| pitcher | modern | 0 | 0.0053 (0.0001, 0.0103) | 0.0109 (-0.0001, 0.0215) |

Negative differences favor the candidate. The production model was not changed.

## Why

- hitter: 1/5 old and 0/3 modern origins improved; pooled_interval_pass=False; supported_reversals=14
- pitcher: 2/5 old and 0/3 modern origins improved; pooled_interval_pass=False; supported_reversals=13

## Guardrails

- Outcomes are later than every snapshot; 2020 is outside all evaluation windows.
- Negative MLB WAR is retained.
- The model was not refitted on either evaluation era.
- Training gives each player equal total weight across repeat snapshots.
- No rankings, outside FV, organization, country, body, or depth-chart fields were used.
