# Hitter top-end position audit

Status: diagnostic complete; no model or grade changed.

Catchers are 658 of 2,870 modeled pre-MLB hitters (22.9%) and 22 of 86 hitters
at 50+ FV (25.6%). That is a modest increase, not evidence of a catcher quota.
Shortstops are more concentrated: 21.2% of the population and 43.0% of the 50+
group. All four current 55s are catchers or shortstops.

The mechanism is visible. The model uses the standard position run adjustment while
current general defense remains neutral. For the top four hitters:

| Player | Pos | Expected WAR | Position WAR | WAR without position | FV without position |
|---|---:|---:|---:|---:|---:|
| Caden Bodine | C | 10.06 | 3.76 | 6.30 | 50 |
| Rainiel Rodriguez | C | 9.20 | 3.29 | 5.91 | 50 |
| Franklin Arias | SS | 8.45 | 2.47 | 5.99 | 50 |
| Eli Willits | SS | 8.08 | 2.27 | 5.81 | 50 |

The two catchers still clear 50 without positional runs, so their placement is not
solely a catcher artifact. But position supplies enough value to lift both from 50
to 55. Across all catchers, removing position as a diagnostic reduces 50+ counts
from 22 to 5 and 55+ from 2 to 0.

Removing position is not a valid candidate: catcher and shortstop defense have real
value. The defensible next improvement is player-level probability of remaining at a
premium position plus supported defense. The earlier coarse group transition mixture
worsened historical positional-run error, so it stays rejected. No quota, manual
haircut, or outside FV target is applied.

Machine-readable evidence: `docs/hitter-top-end-position-audit-result.json`.
