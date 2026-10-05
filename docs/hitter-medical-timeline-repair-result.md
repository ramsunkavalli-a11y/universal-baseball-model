# Injury records now stop when actual MLB play contradicts them

2026-10-05. Walkthrough status: complete. Source repair only; no new forecast.

The source correction is implemented, not just flagged. Transactions and actual
dated MLB appearances are now replayed together. A missing activation no longer
lets an old injury continue through subsequent MLB play. A later injury starts
another episode instead of being lost when the old merged record is shortened.
Original records, ledgers and forecasts are preserved.

This fixes the source defect already identified in V59; it is not a new discovery
or another test of an open-injury flag. It does **not** yet demonstrate better
playing-time predictions. Tatis's unconditional health forecast remains open.

## What changed

All 83,300 original player-origins were reconstructed, with an exact source-table
join to the same 63,314 model rows. Among source rows previously marked open,
80 rows representing 67 people now have subsequent observed MLB use. Among
model rows with both recent source years available, 297 rows representing 133
people have shorter observation spans; 22 rows representing 16 people have
additional separate episodes. These are repeated preseason histories, not 297
different injured players or 297 improved forecasts.

Travis's March 25, 2016 record used to continue until September 1. Both the local
dated contact evidence and his independently saved official game log establish
MLB play by May 25. Franco's 2015 injury no longer continues through his 630-PA
2016 season and 623-PA 2017 season. Alvarez's July 2022 entry ends by his observed
July 21 MLB appearance rather than persisting into the following preseason.

A suspension, release or demotion still does not prove recovery. Tatis's August
12 suspension and Hoskins's November free agency end the captured medical
follow-up, not the underlying injury. Ellsbury's November roster activation is
kept as a reported activation, not proof that he played or recovered.

## What these fields actually measure

The output contains reported IL entries, observed MLB use, reported roster
activations, unresolved records, and follow-up lost after a roster/status change.
Calendar-span summaries count overlapping days only once, within the two prior
calendar seasons. They are observation bounds, **not true injury days, games
missed, clinical clearance or an availability percentage**. A transfer without
the initial placement has an unknown earlier start. Surgery counts are captured
reports, not a complete surgical history or a count of distinct operations.

Contacts are positive evidence only. A game with no captured contact is not an
absence; the first observed contact can be later than the actual return. Known
split/resumed games are excluded. A positive PA period cannot clear an injury
that began inside that period or establish activity after a status boundary
inside the period. Same-day play can precede injury and does not clear it.

`recent_history_coverage_complete` means both annual transaction-source years
are present, not that every injury is captured or that a minor leaguer has a
complete medical history. The dated appearance evidence is MLB-only; minor
league rehab does not establish MLB return. In particular, the 73,834 source
rows with no captured medical entry are **not certified healthy**. Any future
medical fit must define its observed MLB population separately; it cannot give
DSL players a zero-injury history merely because these sources are silent.

## Player-by-player reasonability review

An origin is the last completed season: origin 2016 means the January 2017
forecast. PA below is the stronger saved benchmark, unchanged by this source
repair, followed by actual next-year MLB PA. It is not the unsuccessful role
reference from the preceding experiment. Full raw transactions, source inputs,
batting rates/value heads, peers and cutoff checks are in the linked receipts.

| Player and origin | Known baseball record | Rebuilt source interpretation | Unchanged forecast / actual PA |
|---|---|---|---:|
| Devon Travis, 2016 | 239 PA/8 HR in 2015; 432/11 in 2016 | March 25 entry ends by May 25 play, not September 1 | 530 / 197 |
| Fernando Tatis Jr., 2022 | 546 PA/42 HR in 2021; 14 AA rehab PA but no MLB PA in 2022 | April 7–August 12 medical follow-up becomes unknown at suspension; no MLB return observed before cutoff | 61 / 635 |
| Rhys Hoskins, 2023 | 443 PA/27 HR in 2021; 672/30 in 2022; no MLB PA in 2023 | Follow-up ends at November 2 free agency, not recovery | 367 / 517 |
| Jacoby Ellsbury, 2018 | 626 PA/9 HR in 2016; 409/7 in 2017; no MLB PA in 2018 | November 1 activation is administrative evidence; no subsequent MLB play at cutoff | 261 / 0 |
| Yordan Alvarez, 2022 | 598 PA/33 HR in 2021; 561/37 in 2022 | July 10 injury ends by July 21 observed play | 504 / 496 |
| Maikel Franco, 2016 | 335 PA/14 HR in 2015; 630/25 in 2016 | August 2015 injury ends by October 3, 2015 play; no continuing absence through 2016 | 550 / 623 |
| Maikel Franco, 2017 | 630 PA/25 HR in 2016; 623/24 in 2017 | Same old injury stays closed; no captured episode overlapping the recent 2016–17 window | 507 / 465 |
| Kyle Blanks, 2016 | 71 MLB PA/3 HR in 2015; no MLB PA in 2016 | June 14 play stops June entry; later August transfer remains separate and left-truncated | 4 / 0 |
| Mark Canha, 2016 | 485 PA/16 HR in 2015; 44/3 in 2016 | May 9 entry has no observed return by cutoff; recovery unknown | 139 / 187 |
| Aaron Judge, 2024 | 458 PA/37 HR in 2023; 704/58 in 2024 | Two 2023 entries preserved; later actual play verified; no fabricated new injury | 533 / 679 |
| Kevin Pillar, 2022 | 347 PA/15 HR in 2021; 13 MLB PA and 176 AAA PA in 2022 | June entry loses follow-up at November 6 free agency; AAA use does not clear MLB absence | 78 / 206 |
| Stephen Vogt, 2016 | 511 PA/18 HR in 2015; 532/14 in 2016 | No captured medical entry; not a health certificate | 406 / 303 |
| Kyle Garlick, 2022 | 107 PA/5 HR in 2021; 162/9 in 2022 | September 16 injury has no later observed MLB contact; a straddling PA window cannot clear it; January 11 roster exit censors follow-up | 62 / 30 |
| Jarrett Parker, 2016 | 151 MLB PA/5 HR plus 222 AAA PA/16 HR in 2016 | October 12 entry is later than regular-season use; past play does not clear it | 129 / 177 |

Travis's calendar observation union falls from 296 to 197 days; the latter is
not his next-year 197 PA and is not certified injury duration. Alvarez falls
186 to 22 observation days. Franco's origin-2016 union falls 508 to 52; his
origin-2017 union falls 731 to zero because the repaired episode ended in 2015.
Zero here means no captured overlapping episode, not no possible health risk.
Blanks's union falls 154 to 100 while recent overlapping episodes rise two to
three. The extra episode is evidence of a later transfer, not a fully observed
new injury beginning on that date.

Garlick and Parker are useful unchanged controls. Neither gets cleared by a
misplaced aggregate PA window. Canha similarly stays unresolved. These are not
failed repairs: the evidence does not justify inventing a return. Judge's recent
span remains 65 days; the source repair cannot claim it fixes his underforecast.

### Peers expose limits, not a license to average unrelated players

Peers were selected without future outcomes: same origin and earlier open/censored
flags, then nearest age and current MLB workload. Their future outcomes are only
review context. This rule deliberately does not claim clinical or talent matching.

Travis's peers Puig, Grichuk and Marisnick actually had 570, 442 and 259 next-year
PA versus Travis's 197. Observed return cannot justify a healthy-season workload
for Travis. Alvarez's peers Jiménez, Trout and Solak had 489, 362 and zero: one
cleared old record still permits very different later outcomes. Franco's 2016
peers Castellanos, Díaz and Santana had 665, 301 and 607; his 2017 peers Santana,
Castellanos and Herrera had 235, 678 and 597. Closing a demonstrably stale injury
is justified irrespective of which direction the next PA error would move.

Tatis's nearest peers Marchán, Araúz and Devers had zero, 66 and zero. None
matches his 42-HR established talent. Hoskins's nearest peers DeShields,
Marmolejos and Moran had zero; they are not equivalent to a 30-HR regular.
Ellsbury's peers Blanco, Castillo and LaRoche had zero, seven and zero, but
lack his recent regular role and specific medical course. Therefore a mean of
these peers is not a sensible recovery projection for any of those three.

Canha's peers Parker, Spangenberg and Davidson had 177, 486 and 443, despite
similarly unresolved capture. Parker's peers Canha, Tucker and Van Slyke had
187, zero and 48. Unresolved capture cannot be equated to no future MLB play.
Garlick's peers Ford, Wynns and Piscotty had 251, 145 and zero; Pillar's Almonte,
Pérez and Shaw had 16, 17 and zero. Censoring alone does not distinguish role
loss from medical interruption. Blanks's peers Schafer, Freiman and Moore had
zero, zero and 203; later non-arrival is not proof that Blanks never returned
between the earlier episodes.

Judge's peers Castellanos, Schwarber and Semien had 589, 724 and 534 versus his
679. Vogt's Upton, Tulowitzki and Valencia had zero, 260 and 500 versus his 303.
Neither actual return nor no captured entry guarantees next-year full workload.
All peers' unchanged forecasts and source states remain in the receipts.

## Training support limits the next experiment

All seventy existing participation/active-PA training subsets were independently
recounted using distinct people, not repeated player-seasons. In every origin-2016
subset there are **zero training people with both recent transaction years**:
2015 is the first annual injury source, so origin 2016 is the first full recent
history, not a source of already observed next-year outcomes before that forecast.
This is a coverage mismatch, not proof that all those players are unusual.

Even later broad profiles can be thin: Tatis has six training people for
participation and four for active PA; Hoskins eighteen and one; Ellsbury two
and one. Alvarez has 169/168 and Judge 187/178. These groups share only source
state, source-year coverage, five-year age band and current MLB PA band. Counts
are not evidence of matched injury type, previous star talent or ready-for-spring
prognosis. No individualized health probability is established.

Before a future fit, define a medical-observation estimand and actual observed
MLB eligibility, preserve all evaluation players/exits, use an unchanged baseline
fallback for unsupported histories (including origin 2016), and keep legal
unavailability separate. Do not feed these calendar bounds directly into a
missed-games deduction. Report effects on participation, PA and delivered value
with the same named controls. A subsequent test must not compare returning
former regulars only with never-established young players or aging fringe players.

## Integrity and completion

Thirty-seven focused tests pass, including seventeen new timeline tests.
Fourteen player-origins (thirteen people) were replayed; future/backdated reports
leave their source inputs unchanged. Travis's return upper bound independently
agrees with the official game log. All original rows, cutoff dates, training/test
membership, stronger forecasts and frozen 2026 packages remain unchanged.

The first twelve-case review had wrong IDs for two intended named controls.
The saved names remained correct: they were Pillar and Vogt, not Garlick and
Parker. The [review amendment](hitter-medical-timeline-review-amendment.md) and
[identity review](../reports/model-evidence/hitter-medical-timeline-repair/identity-review.json)
retain those controls and add the intended players. The supplement also verifies
all five source-feature files against existing preflight hashes and independently
recounts all seventy source-support subsets. Do not mistake the first report's
twelve-case count for the completed fourteen-case review.

Evidence: [source report](../reports/model-evidence/hitter-medical-timeline-repair/report.json),
[initial player walks](../reports/model-evidence/hitter-medical-timeline-repair/player-walks.json),
and the identity-review supplement above. The completion receipt binds this
judgment; future use must verify the supplement and both original source/output
seals. No accuracy improvement, clinical validation, full-WAR gain or explorer
change is claimed. The practical change is a repaired, explicitly bounded
injury-observation source ready for a separately defined comparison.
