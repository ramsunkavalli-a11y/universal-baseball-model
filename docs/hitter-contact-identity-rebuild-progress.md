# Historical contact repair progress

2026-10-04. The first complete season review confirms that the stored contact
data sometimes credit runners with the batter's result. This repair improves
the measurement layer before another hitting-model comparison. It has not
improved a forecast yet, and the current count-based candidate is unchanged.

## What is ready

Independent game controls are assembled for 2016–19 and 2021–24: 3,983,836
player-game rows, with no unresolved contact counts after conservative snapshot
resolution. That does not prove complete coverage of every scheduled game.
The canceled 2020 minor-league season remains missing, not zero performance.

The contact inventory retains 4,591,561 physical contacts and quarantines 1,843
conflicting or uncertain keys. Actual league identity is retained: Mexican
League data are not treated as domestic AAA, and DSL and short-season levels
remain distinct. These counts refer to existing archived partitions, not a
claim that all historical play-by-play is available.

Before looking at official identities, the checks selected 11,692 exception
games and 2,520 unflagged audit games. Exception counts include missing or
uncertain controls and definition differences; they are not an error count.
The official capture remains in progress on the same locked membership.

## What the 2016 review found

All 2,163 selected games have official sequence coverage. Correcting participant
identity changes 1,920 contacts across 1,695 games. None of the 360 unflagged
audit games has an identity mismatch. Contact locations and recorded outcomes
are preserved. In the controlled selected games, absolute player-count
differences fall from 3,973 to 137. Those remaining differences are retained as
coverage or definition evidence, not removed by inventing contacts.

The corrected player walkthrough follows actual before/after measurements,
the ninety contact-result cells, independent boxscore inputs and four peers
chosen using origin-season league, contact exposure and HR. Peers are not
matched on age, position or pedigree; this is a source check, not evidence of
equivalent talent or future MLB success.

| Player | Actual league | Source change |
| --- | --- | --- |
| Ricardo Serrano | Mexican League | 329 to 341 contacts; HR unchanged at eight |
| Gabriel Gomez Topete | Mexican League | 40 to 19 contacts; two attributed HR become zero |
| Corey Brown | Domestic AAA | 270 to 273 contacts; 22 attributed HR become 23 |
| Jesus Henriquez | DSL | 260 contacts unchanged; 249 have enough detail for the cells |
| Edgar Herrera | DSL | 172 contacts unchanged; 171 have enough detail for the cells |

The first walkthrough's gain/loss selection had an unsigned subtraction bug.
It was caught before disposition, corrected and tested. Preserve that original
review separately; use the signed review for the table above. See the
[correction](hitter-contact-identity-review-correction.md).

## What remains

Finish the same official checks for the other seven seasons, including the
fixed Hall/Martin, Navarro/Kokoska and Maggi/Leonard plays and the Meadows,
McNeil, Reynolds, Kurtz and Langford histories. Any unflagged mismatch blocks
source approval and requires an explicit broader repair decision. The complete
eight-season source gate and its player review are still pending.

Only then run the separately contracted, matched future-MLB hitting comparison.
Keep current, translated-hitting and available-season arrival anchors; do not
silently reuse old learned park adjustments. Source correctness does not prove
that more contact detail improves projection accuracy. Public workload errors,
cohort gaps, final value and the research explorer remain unfinished parts of
the overall goal.

The 34 focused checks pass, including a regression test for the subtraction
bug. The independent freeze verifier confirms all 31 locked files and 3,907
forecast players unchanged, without opening 2026 outcomes. No explorer is
promoted. Large working tables and captures use the approved D drive; small
receipts and hashes remain in the repository.
