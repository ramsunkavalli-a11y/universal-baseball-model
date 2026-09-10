# Prospect broad-history positive-tail result

**Decision:** `reject_basic_tail_family`

The fixed basic StatsAPI feature set was fitted once on 2008–2010 and then left unchanged. A pre-scoring correction removed 2011–2012 because their outcomes overlap the first evaluation snapshot. A later source audit superseded the first scores by excluding every player whose official MLB debut preceded the snapshot.

| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) |
|---|---|---:|---:|---:|
| hitter | old | 1 | 0.0110 (0.0003, 0.0211) | 0.0486 (0.0148, 0.0816) |
| hitter | modern | 0 | 0.0017 (-0.0084, 0.0124) | 0.0164 (-0.0152, 0.0493) |
| pitcher | old | 4 | 0.0009 (-0.0032, 0.0053) | 0.0018 (-0.0069, 0.0111) |
| pitcher | modern | 0 | 0.0058 (0.0002, 0.0110) | 0.0120 (-0.0003, 0.0234) |

Negative differences favor the candidate. The production model was not changed.

## Why

- hitter: 1/5 old and 0/3 modern origins improved; pooled_interval_pass=False; supported_reversals=14
- pitcher: 4/5 old and 0/3 modern origins improved; pooled_interval_pass=False; supported_reversals=12

## Guardrails

- Outcomes are later than every snapshot; 2020 is outside all evaluation windows.
- Negative MLB WAR is retained.
- The model was not refitted on either evaluation era.
- Training gives each player equal total weight across repeat snapshots.
- No rankings, outside FV, organization, country, body, or depth-chart fields were used.
