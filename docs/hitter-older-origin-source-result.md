# Older hitter sources and their training value

2026-10-04. Three earlier seasons can provide useful additional training data,
but importing the old files unchanged would introduce avoidable mistakes. The
2006–2007 short-season gap and most missing ages are now repaired in supplemental
tables. No model has been fitted and no existing forecast has changed. The next
comparison must establish whether the added data actually improves predictions.

## What was repaired and checked

The old bulk source omitted short-season A-ball. Official separate pulls restore
62,149 PA in 2006 and 63,033 in 2007, across 22 historical teams each year.
Hitting PA and pitching BF reconcile exactly in both seasons. Counts and raw
captures are saved without modifying the old files. Those seasons supply the
three-year history needed for an origin in 2008.

Cached raw hitting counts reproduce their component tables. Overlapping
2008–2010 person/sport totals reproduce the current repaired source exactly.
The historical roster plus season-use snapshot rule also replays exactly:

| Origin | Rebuilt hitter rows | Next year positive MLB PA | Next year zero MLB PA |
| --- | ---: | ---: | ---: |
| 2008 | 4,440 | 609 | 3,831 |
| 2009 | 4,409 | 615 | 3,794 |
| 2010 | 4,508 | 636 | 3,872 |
| Total | 13,357 | 1,860 | 11,497 |

This adds 39 identities to the older uncorrected snapshots and removes none.
The population is not selected for eventual success. Inactive roster hitters
remain, although older exits outside the roster/use captures are not yet
certified. All 13,357 next-year PA labels also reproduce the current independent
completed MLB target table. The older and newer MLB component inventories agree
exactly in their shared 2009 season. These are source checks, not accuracy scores.

Of 237 missing reported ages, 31 rows are recovered from cached official birth
dates and 205 from newly captured birth dates. Only ID, name and birth date were
requested; no current statistics, activity or other profile fields were returned.
Harper's 2010 age is 17, not the old fallback of 27. Arturo Pena, ID 542660 in
2008, remains unknown. Reported ages are preserved; birth-derived ages use
June 30 of the origin season and carry their own provenance.

## How much additional support exists

Most of the 1,860 positive labels are already-debuted hitters: 1,581. There are
279 positive never-before-debuted origin labels. They are not 279 independent
new people or 279 full-season regulars. Keep complete rows and their exposure;
do not select only the successful labels for an opportunity fit.

The audit checks the actual 35 held-player/time cells used for the current
30,506 forecasts. Earlier targets end by 2011, before every evaluation origin;
the entire held-player fold is excluded. Counts are distinct people in the
union with current training, not old and new counts added as if independent.

| Evaluation profile | Forecast rows | No active analogue before | No active analogue after |
| --- | ---: | ---: | ---: |
| All | 30,506 | 11,457 | 10,962 |
| Never debuted | 24,199 | 11,353 | 10,860 |
| DSL age 17 or younger | 2,293 | 2,293 | 2,293 |
| Dominant AAA exposure age 18 to 20 and never debuted | 3 | 1 | 0 |

The earlier data closes 495 empty coarse profiles, but teenage DSL still has no
next-year active MLB analogues. Teenage AAA gains only one additional active
person. Moving from zero to one is not adequate validation of Acuna-like stars.
This establishes potential training support, not that an augmented fit is
correct or that all required input families have been reconstructed.

## Twelve actual source walks

The paths below are observed MLB PA in the next three calendar years, not
predictions. Zero PA leaves hitting rate unobserved. Full dated counts, age
provenance, level exposures and peers are in the linked reviewed cases.

| Player and origin | What was available at origin | Next three MLB PA totals |
| --- | --- | --- |
| Trout 2009 | Age 17; 187 Arizona rookie PA and 20 A PA; 1 HR, 22 BB, 34 K | 0, 135, 639 |
| Harper 2010 | Age corrected to 17; roster-only, no affiliated batting counts | 0, 597, 497 |
| Hosmer 2008 | Age 18; 15 Pioneer PA; 0 HR, 3 BB, 2 K | 0, 0, 563 |
| Moustakas 2008 | Age 19; 549 A PA; 22 HR, 43 BB, 86 K | 0, 0, 365 |
| Montero 2008 | Age 18; 569 A PA; 17 HR, 37 BB, 83 K | 0, 0, 69 |
| Belt 2010 | Age 22; 333 A-plus, 201 AA, 61 AAA PA; 23 HR, 93 BB, 99 K | 209, 472, 571 |
| Pujols 2008 | Age 28; 634, 679, 641 MLB PA over three years; 49, 32, 37 HR | 700, 700, 651 |
| Encarnacion 2008 | Age recovered to 32; prior MLB/AA history, no origin PA | 0, 0, 0 |
| Alou 2008 | Age 41; 54 MLB and 12 minor PA; repair restores 4 A-minus PA in 2007 | 0, 0, 0 |
| Trout 2010 | Age 18; 368 A and 233 A-plus PA; 10 HR, 73 BB, 85 K | 135, 639, 716 |
| Hosmer 2010 | Age 20; 375 A-plus and 211 AA PA; 20 HR, 59 BB, 66 K | 563, 598, 680 |
| Moustakas 2010 | Age 21; 298 AA and 236 AAA PA; 36 HR, 34 BB, 67 K | 365, 614, 514 |

BB in this table is total walks. The actual event inputs separate intentional
walks. Belt has 89 UBB, Moustakas 2008 has 39 and Moustakas 2010 has 24.
Pujols's 2008 104 walks include 34 intentional walks. A model that silently
treats all these as UBB would not reproduce the current definitions.

The two Trout origins show why highest level and exposure are different:
his 2009 snapshot says A, but almost all batting was in rookie ball. Belt's
highest level is AAA although most 2010 batting was A-plus. The current model
already receives separate level counts; this is a warning about coarse support
summaries and new reconstruction, not a claim that those inputs were absent.

The original sport-only controls mixed domestic rookie and DSL players. The
supplementary review instead matches dominant bucket, highest observed level,
prior-debut state and age within two years, then age/exposure distance, without
future outcomes. Trout 2009 has only two such controls, Camargo and Baker; both
have zero next-three-year PA. Do not widen the pool silently or call them equal
pedigree. Montero's controls include Freeman and Stanton, whose paths differ
markedly, plus Beltre and Galvis. Moustakas 2010 is accompanied by Nieuwenhuis,
Laird, Ackley and Cardenas, covering both substantial arrivals and non-arrivals.
These are age/exposure controls, not equivalent performance or scouting grades.

Encarnacion's inactive controls include returning Alex Gonzalez and Valdez as
well as non-returning Sanchez. Thus inactivity alone is not retirement or a
medical diagnosis. Alou was chosen by the repair-exposure rule, not because his
future zero was convenient; the repair affects established-player histories too.
The three additional 2010 fast-track cases are disclosed outcome-informed source
diagnostics, not independent validation or the selected training population.

## Limits and next comparison

The 2003–2005 bulk files have no DSL rows. File presence cannot certify complete
lower-level history, so those origins are not imported here. Earlier bulk rookie
rows can also combine multiple clubs or leagues under one representative team
identity. Their player/sport totals reconcile, but exact park, organization and
league exposure do not follow automatically from that representative identity.

There are 9,512 origin rows with no debut date in the completed MLB inventories.
They have zero next-year PA, but absence from that inventory is not an official
certificate that they never played MLB before its start. Keep this unknown
separate from known prior debut; never use the diagnostic future-recorded-debut
category as a model input or a peer-matching advantage. Birth dates are stable
current-corrected facts, not historical retrieval vintages. The October roster
captures are not complete year-end rights, health or retirement information.

The source review is complete. Seven focused regression tests pass. Compatible
draft, preseason ranking, status, rights and generated level features still need
explicit reconciliation for the extended model. Those requirements cannot be
met by giving every old player zero pedigree or blindly copying later values.
Next run the locked matched restricted-versus-extended training comparison,
preserving current and translated/ranking anchors, all evaluation identities,
non-arrivals, actual chronology checks and the required player walks. Keep a
missingness control for genuinely unavailable input families. If needed, compare
a common reconstructable input recipe in both arms and label its change from
the current richer anchor; do not attribute that whole difference to extra years.

No predictive improvement, full-model validation, deployment, frozen forecast
change or protected 2026 outcome access is claimed. The practical hitter goal
remains active.

Evidence: [source audit](../reports/model-evidence/hitter-older-origin-source/report.json),
[age repair](../reports/model-evidence/hitter-older-origin-source/age-receipt.json),
[completed player review](../reports/model-evidence/hitter-older-origin-source/reviewed-cases.json),
[completion receipt](../reports/model-evidence/hitter-older-origin-source/final-report.json).
