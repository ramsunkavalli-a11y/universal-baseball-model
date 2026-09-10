# Prospect broad-history skill-tail result

**Decision:** `reject_aggregate_skill_tail`

The fixed candidate adds strongly regressed current-season component rates to the basic model. Negative differences favor the skill candidate.

| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) | Candidate beats constant |
|---|---|---:|---:|---:|---:|
| hitter | old | 3 | -0.0032 (-0.0080, 0.0013) | -0.0037 (-0.0182, 0.0103) | False |
| hitter | modern | 2 | -0.0092 (-0.0160, -0.0030) | -0.0171 (-0.0359, 0.0004) | False |
| pitcher | old | 4 | -0.0010 (-0.0039, 0.0019) | -0.0022 (-0.0083, 0.0038) | False |
| pitcher | modern | 2 | -0.0038 (-0.0081, 0.0006) | -0.0070 (-0.0162, 0.0022) | False |

The production model was not changed.

## Why

- hitter: 3/5 old and 2/3 modern origins beat basic; pooled_interval_pass=False; supported_reversals=4; beats_constant={'old': False, 'modern': False}
- pitcher: 4/5 old and 2/3 modern origins beat basic; pooled_interval_pass=False; supported_reversals=6; beats_constant={'old': False, 'modern': False}
