# Pitcher demographic current-impact result

Status: integrated into the private build after exact on/off replay.

With all other current inputs fixed, the frozen age-for-level/hand adjustment raises
total nested expected WAR from 68.15 to 162.68 across 3,849 pre-MLB pitchers. The
median player change is effectively zero and the mean is +0.025 WAR; the aggregate
change is spread over a large population rather than supplied as a floor.

| Display threshold | Adjustment off | Adjustment on |
|---|---:|---:|
| 40+ | 225 | 296 |
| 45+ | 24 | 40 |
| 50+ | 1 | 2 |
| 55+ | 0 | 0 |

There are 269 displayed-grade changes: 216 up and 53 down. The largest positive and
negative player changes remain in the machine-readable report. Hitter projection
inputs and hitter values are unchanged. After the source-first player-type correction,
the two builds have zero hitter/pitcher classification switches.

This is still a cautious private result. The historical 2025 gain was small, both
bootstrap intervals crossed zero, and the left-handed subgroup worsened. It does not
justify adding physical measurements, birth-country effects, outside FV, or a target
number of ranked pitchers.

Machine-readable detail: `docs/pitcher-demographic-current-impact-result.json`.
