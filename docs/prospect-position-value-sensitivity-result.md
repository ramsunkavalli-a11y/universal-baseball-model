# Prospect probabilistic-position value sensitivity result

Status: completed and retained as research; playable default unchanged.

## Result

The sensitivity covers 2,805 pre-MLB hitters with both a nested career value and a
current games-based position group. It changes only positional runs inside the WAR
rate. Skill, aging, baserunning, defense, replacement level, career probabilities,
and workload remain fixed.

| Measure | Fixed current position | Position probability mix |
|---|---:|---:|
| 45+ FV hitters | 404 | 268 |
| 50+ FV hitters | 86 | 36 |
| Josuar Gonzalez WAR | 1.83 | 1.37 |
| Josuar Gonzalez FV | 45 | 45 |

Mean WAR change is -0.141 and median change is -0.029. Six hundred ninety-eight players
cross a five-point FV display boundary. The reduction is not mainly a catcher
penalty: the 50+ group loses 24 shortstops and 10 catchers. Catchers still comprise
22 of the top 100 in this sensitivity.

The transition-weighted positional runs per 600 are based only on prior MLB usage:
9.08 catcher, 3.18 middle infield, -4.89 corner, -4.19 outfield, and -14.01 DH/other.
These are lower than the single-position schedule for catcher and shortstop because
real MLB players also spend time at less valuable positions.

## Source disagreement

The sensitivity now follows the [current-position source hierarchy](prospect-current-position-source-result.md):
official fielding outs, then the corrected games role, then listed position. Fielding
outs cover 2,591 players and disagree with the games role for 184 (7.1%). They disagree
with listed position for 457 of 2,385 comparable players (19.2%). A second calculation
using only the listed group still produces nearly the same aggregate compression: 267
at 45+ and 37 at 50+. Therefore the large movement is mostly the permanent-position
assumption, not the source disagreement.

The outside Top-100 check is diagnostic only and was not used for selection. On the
56 covered hitters, granular FV MAE worsens from 8.90 to 9.65.

## Decision

Do not replace the playable default. The follow-on
[positional-runs validation](prospect-positional-runs-validation-result.md) shows that
the coarse group mixture predicts the actual run component worse than carrying current
minor-league usage forward. Future work must target exact player-level positional runs
directly on development data; do not tune another conversion on the disclosed outer
group.

No outside FV, organization depth, subjective catcher adjustment, or skill change was
used. Machine-readable detail:
`docs/prospect-position-value-sensitivity-result.json`.
