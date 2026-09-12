# Current minor-league pitch-quality source check

Last updated: 2026-09-12  
Status: **AAA TRACKED; BELOW AAA NOT UNIVERSALLY TRACKED**

The official StatsAPI live game feed was checked on two games at each affiliated level
from August 15, 2026. This is a current capability probe, not a full-season coverage
certification.

| Level | Physical pitch rows | Velocity | Spin/movement | Pitch type |
|---|---:|---:|---:|---:|
| AAA | 631 | 631 | 631 | 631 |
| AA | 658 | 0 | 0 | 0 |
| High-A | 535 | 0 | 0 | 0 |
| Single-A | 429 | 0 | 0 | 0 |
| DSL | 573 | 0 | 0 | 0 |

AA and lower still expose pitch calls and a minimal `pitchData` object, but that object
contains no velocity, spin, movement or classified pitch type in the sampled games.
The result agrees with the repo's prior historical source audit: AAA tracking is rich;
coverage below AAA is structural and cannot be treated as ordinary missing data.

Decision:

- AAA tracking is a candidate optional pitcher evidence tier after a full coverage and
  historical validation gate.
- AA/High-A pitching prospects cannot receive imputed velocity or pitch shape.
- Swing/whiff/count features may be tested only in league-seasons that pass the existing
  physical pitch-sequence fidelity gate.
- Public FV or scouting rank cannot substitute for missing pitch measurements.

This explains a major class of current disagreements. Young pitchers such as Seth
Hernandez can be highly regarded for raw stuff while the current universal model sees
only results, age, level and role. The model must label that limitation rather than
pretend those inputs are equivalent.
