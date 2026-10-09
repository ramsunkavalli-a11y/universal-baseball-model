# 2027 build: completed-season batting inputs

2026-10-08. This closes the event-count intake, not the model or its membership
refresh. No forecast has changed and no accuracy improvement is claimed.

We recovered 6,358 official player/team/level season rows from 231 teams. They
aggregate to 5,956 player/level rows. Every checked event total matches both
the independently requested team totals and the player-level totals at all six
sport levels. MLB events also reproduce the previously certified 2026 target.
The compressed source captures and working tables occupy about 2.5 MB, not a
new play-by-play archive. Existing older data remain on D: and are read in place.

The MLB FanGraphs export covers all players with official PA. Ryan Jeffers and
Sean Keys each have one more official PA than in that export. Those are retained
as explicitly unclassified PA, not invented at-bats or hits. Three analogous
minor-league PA are also retained. They reconcile with official team totals.
The eight-event representation puts them in its already-defined other-PA bucket.

The MiLB FanGraphs export contains combined-level rows, so it is a cross-check,
not the source of level-specific inputs. Ramcell Medina has 185 official PA and
177 in that export. The export also has positive PA under three identities absent
from the official minor aggregate: Alexander Ramirez (5), Raimel Medina (11),
and Edgar Sanchez (5), plus four zero-PA identities. Preserve this identity/
coverage review for roster assembly; do not assign these players zero talent,
add their records to someone else, or claim perfect cross-source agreement.

## Source-to-input player checks

The eight cases were fixed in the finalization plan. Comparisons were selected
without outcomes: same level, then nearest age, PA and position, three per case.
The full source rows, assembled inputs and comparison rows are saved in
`reports/model-evidence/hitter-2027-v1/origin-source-player-walkthrough.json`.
These are observed **2026 inputs for 2027**, not 2027 forecasts or historical
evidence that a modeling change has won.

| Player | Official 2026 evidence carried into the inputs | Consequence for the build |
|---|---|---|
| Jackson Lovich | 363 PA/18 HR at A; 147 PA/6 HR at high A | Keep the levels separate. The historical 26-PA failure still needs testing; the new season is not a retrospective excuse for it. |
| Bryce Eldridge | 448 MLB PA/17 HR and 137 AAA PA/5 HR | He now has substantial MLB evidence, not merely the old prospect profile. Do not carry forward his old arrival estimate unchanged. |
| Carlos Concepcion | 169 ACL PA, 36 hits, 4 HR and 65 K | His new record is complex-league evidence, not another DSL season. A minor combined-level label is insufficient. |
| Aaron Judge | 285 MLB PA, 18 HR and 85 K | Update talent with the performance while separately investigating availability; fewer PA alone do not establish the cause or permanence of lost playing time. |
| Fernando Tatis Jr. | 704 MLB PA, 25 HR and 130 K | Current exposure is large. Keep earlier known suspension years distinguishable from ordinary absence. |
| Shohei Ohtani | 618 MLB PA, 30 HR and 152 K | These are hitting inputs only. His full contract cannot be valued against these alone. |
| Patrick Bailey | 256 PA for team 114 plus 89 for team 137; 345 total, 10 HR | Both team stints are retained. A season aggregate's team label must not decide who currently owns his rights. |
| Francisco Lindor | 469 MLB PA plus 10 AAA and 4 AA PA | The small minor stints must not rival his MLB evidence or imply that he is an ordinary developmental prospect. |

The chosen peers include Maduro/Weingartner/Lodise for Lovich,
Ewing/Basallo/Crawford for Eldridge, Lorenzo/De La Cruz/Alcantara for Concepcion,
Garcia/Castellanos/Raley for Judge, Abreu/Adell/Lee for Tatis,
Bell/Benintendi/Alvarez for Ohtani, Ruiz/Diaz/Kirk for Bailey, and
Swanson/Seager/J.P. Crawford for Lindor. These are source-profile comparisons,
not claims of equivalent talent; for example Ohtani's ordinary hitting-role
neighbors do not represent his two-way financial profile.

The review confirms the calculations and level separation for these cases and
their 24 comparison records. Gain/harm/false-high/false-low review belongs to
the forthcoming fitted comparison, since this intake made no predictions.
Current ownership, dated promotion/rehab order, new no-PA members and the
foreign-player population still require their own dated evidence. Do not infer
those from these team-season sums.

## Accounting foundation

The new release ledger reuses the repo's additive WAR and path-pricing engines.
It requires every component to name its estimator, evidence type, units and
cutoff. It rejects missing/duplicated components, future evidence, incompatible
fielding references and a second park adjustment to already-neutral batting.
It preserves negative WAR and contract costs, including after rights expire.
It allows control tails longer than six calendar years and refuses to present
hitter-only Ohtani value net of the full two-way contract as complete surplus.

Thirty-seven accounting/intake regression tests pass. This proves these code
checks work on their test cases; it does not establish predictive quality or
complete the service/contract integration. The next modeling work is the
already-documented small-sample batting repair, followed by the component
assembly in the controlling finalization plan.
