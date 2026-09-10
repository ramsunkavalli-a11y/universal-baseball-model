# Prospect broad-history skill-tail result

**Decision:** `reject_aggregate_skill_tail`

The fixed candidate adds strongly regressed current-season component rates to the basic model. Official debut dates enforce a true pre-MLB cohort. Negative differences favor the skill candidate.

| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) | Candidate beats constant |
|---|---|---:|---:|---:|---:|
| hitter | old | 3 | -0.0034 (-0.0082, 0.0012) | -0.0041 (-0.0185, 0.0098) | False |
| hitter | modern | 2 | -0.0090 (-0.0156, -0.0027) | -0.0163 (-0.0348, 0.0008) | False |
| pitcher | old | 4 | -0.0009 (-0.0040, 0.0022) | -0.0020 (-0.0085, 0.0044) | True |
| pitcher | modern | 2 | -0.0043 (-0.0090, 0.0005) | -0.0077 (-0.0179, 0.0026) | False |

The production model was not changed.

## Why

- hitter: 3/5 old and 2/3 modern origins beat basic; pooled_interval_pass=False; supported_reversals=4; beats_constant={'old': False, 'modern': False}
- pitcher: 4/5 old and 2/3 modern origins beat basic; pooled_interval_pass=False; supported_reversals=6; beats_constant={'old': True, 'modern': False}
