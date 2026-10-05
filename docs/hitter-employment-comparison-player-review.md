# Player review of the employment flag comparison

2026-10-05. Both arms keep identical hitting forecasts; only the opportunity
heads differ. This reviews the completed limited flag comparison, not a complete
employment-source correction. During the review we identified two date-derived
inputs still based on the old employment path. They require a separate consistency
repair before claiming to have tested the complete correction.

## Selection and evidence

The private file `reports/generated/hitter-employment-comparison/player-walks.json`
keeps 113 exact source/head traces: the 59 earlier overseas cases, earlier
domestic diagnostics, Olivo and Bourgeois, error-selected gains/harms/highs/lows,
and three origin-only peers per new diagnostic where available. Selection is
saved before walking. Outcome-selected extremes are diagnostics, not validation.
Peers match origin, debut, stage and corrected employment, then distance in age,
prior MLB PA and professional work; future outcomes never enter selection.

Every saved trace contains dated domestic and foreign counts, old/new model
inputs, the actual four head paths, clipped conditional PA, expected PA,
unchanged talent, batting-plus-replacement contribution, observed MLB PA and
training profile counts. All 113 compact forecast/input-change comparisons were
inspected. The detailed source and head review below covers the consequential
mechanisms rather than pretending 113 independent case studies prove accuracy.

## Real source changes versus retraining effects

Machado's latest KBO seasons supply 539 and 560 PA. The March 17, 2022 Cubs
assignment falsely replaced a December 29 minor agreement. Correct flags remove
his .898333 signed-first-team-work input without removing professional work.
Under the old parameters alone, the corrected inputs lower conditional PA from
350.04 to 214.21 and expected PA from 11.87 to 7.18. Retraining gives 3.14%
participation times 214.85 PA, or 6.75 expected PA, versus 17 observed.
The corrected source is valid, but this worsens workload error. His negative
realized batting contribution over 17 PA makes smaller positive predicted
contribution look better; that does not establish better talent or opportunity.
There are eight corrected participation profile people and zero conditional
participants in the exact intersection. The training gap is explicit.

Bourgeois has 238 AAA PA in 2017, 483 in 2016 and 212 MLB PA in 2015.
The February assignment had replaced a January minor agreement. Removing the
false linked-work input lowers old-parameter conditional PA from 138.00 to
38.16; retraining gives 4.47% times 38.95, or 1.74 PA versus 6.77 before and
zero actual. This is a plausible small improvement, not proof the two-year-old
MLB workload predicts a current job. Corrected conditional support is two people.

Olivo has 313 AAA PA in 2016 and only 25 MLB PA in the three-year window.
His assignment similarly displaced a minor agreement. Correct inputs under old
parameters give 6.51 PA versus 7.39; retraining gives 7.32, actual zero. The
source repair is clear but the forecast effect is negligible. Two conditional
profile people are not strong support.

Judge's inputs do not change. His 2023 record is 458 PA, 37 HR and 88 walks,
with 696/633 prior MLB PA. The largest value gain against the old job arm is
therefore a retraining effect: .9899 times 552.28 becomes .9890 times 561.40,
546.71 to 555.22 expected PA versus 704 actual. Fixed hitting talent is 3.8988
wins per 600 PA; batting contribution rises 5.245 to 5.327 versus 11.047 actual.
The largest harm is Judge's 2021 origin: 633 PA and 39 HR precede 696 actual PA;
expected PA instead drops 542.40 to 531.29. Both cases have hundreds of profile
people. Opposite small changes in the same established star are not evidence
that his signing information improved. Origin-only peers include Flores,
Contreras and Conforto for the gain, and Schoop, Frazier and Mancini for the harm.
Their forecast directions and outcomes are retained, not cherry-picked.

## Major misses remain

Judge's 2016 brief debut contains 95 MLB PA, 42 K and four HR, alongside 410
AAA PA and 19 HR. Roster and ranking inputs lift participation above 91%, but
conditional PA remains about 348 and fixed hitting talent only .264 wins/600.
The new 317 expected PA misses 678; predicted batting contribution 1.118 misses
8.115. This is the largest false low, not a signing-parser problem. Closely
matched Moya, Austin and Cowart subsequently receive zero, 46 and 117 PA; the
same origin profile does not guarantee a superstar season.

Acuña's 2023 origin follows 735 PA and 41 HR, with strong quality and a major
link. Participation stays 99.35%, conditional PA about 595, expected PA about
591 and batting contribution 5.598 versus 222 PA and .955 observed. The later
injury is not added to preseason inputs. His Kwan/Rutschman/Riley peers receive
540/638/469 PA. This plausible high forecast can miss; the tiny reduction is
not better injury prediction.

Slater's ordinary case demonstrates cancellation. He had 325 MLB PA, seven HR,
40 walks and 89 K in 2022. The corrected head gives .9780 times 307.18 = 300.41
PA versus 207 actual. Yet contribution .882 nearly equals .883 actual because
the fixed rate is too low for that season. The excellent product is not an
excellent workload forecast. Hedges, Haase and Anderson are retained peers;
their negative realized batting contribution prevents this example from
suggesting that similar role predicts similar offensive success.

The largest gain versus the full incumbent remains Cruz's 2018 origin: current
274 PA, old job 443, corrected 435, actual 521. The parser correction does not
change his inputs; the improvement mainly belongs to the already existing job
representation. Conversely Martinez's 2017 origin falls from current 512 to
corrected 422 versus 649 actual. Neither is attributable to a personal source
correction. Duda, Núñez, Maybin and Cruz's Encarnación/Kinsler/Zobrist comparisons
are retained with mixed outcomes.

Kurtz has just 50 domestic pro PA, but rankings are present. Their positive tree
paths still leave only 6.38% participation times 160.94 conditional PA = 10.27,
versus 489 actual. Yordan has 379 AA/AAA PA and twenty HR in 2018. Removing a
false signing changes his state to acquisition, but fixed old-parameter PA is
unchanged; retraining lowers 75.49 to 69.68 versus 369. These are unresolved
prospect readiness/opportunity and talent problems, not reasons to restore
false signings. Large coarse support groups do not establish support for elite
fast-track prospects.

Suzuki's foreign PA 533/514/612 and latest 38 HR survive unchanged. Corrected
participation .6060 times 314.86 yields 190.81 versus 446 actual, compared with
183.38 before. Yoshida's foreign PA 508/455/492 similarly yield .7683 times
347.60 = 267.05 versus 580 actual. Held exact conditional profiles contain only
three and five people. Neither miss is fixed by correcting assignments.
Lee's 2024-origin 158 MLB PA and 387/627 older KBO PA yield only 183.91 expected
PA versus 617 actual; conditional support is one person. Ohtani's first-year
legal minor agreement and two-way context yield 17.89 versus 367, with zero exact
profile people. Opposite-risk foreign nonparticipants remain in the comparison.

Tatis's finite restriction and old 546-PA season yield only 12.32% participation,
48.94 expected PA versus 635 actual. Franco's unresolved restriction yields
98.83% and 550 PA versus zero. They have zero/two relevant profile people. The
learner still fails to distinguish temporary absence from unresolved availability.
It would be wrong to backdate eventual resolution or convert every unresolved
case into permanent zero. Marcano's explicit permanent rule remains separate.

## Consistency defect and disposition

`employment_evidence_age_years` and `employment_evidence_unknown` still encode
the old latest employment date. The original contract deliberately allowed only
nine flags and signed-work to change, but that boundary is insufficient for a
complete source correction. Inspection finds 10,267 source rows in the actual
63,314-row panel whose latest employment date changes; capped numeric timing
may change in fewer. A signing flag can therefore be corrected while the learner
still receives an assignment-derived freshness input. For Bourgeois it still
uses .9178 years, rather than the older minor-agreement date.

Close this as a reviewed limited contrast with no promotion, not evidence that
complete employment correction fails. Retain the parser repair. Next rebuild
the two derived timing inputs from the corrected ledger, verify the entire
employment feature dependency chain, then finish that same matched comparison
under an appended contract. No new idea, new tuning, changed talent, selected
cohort, or 2026 reuse is justified by this finding.
