# The hitting model clears a basic floor; playing time still needs work

2026-10-05. No new model was fitted or promoted. This answers one question in
the [reset plan](hitter-basics-reset-plan.md): is there value in the selected
hitting model beyond carrying forward its regressed past production profile?
Yes, on the historical matched population. This does not establish that the
model is complete or better than Steamer/ZiPS.

## The comparison

All 30,506 original forecasts remain, including 25,968 non-arrivals. There are
4,538 observed future MLB hitting rates. Origins are 2016–18 and 2021–24; the
latest outcome year is 2025. All three versions get EXACTLY the same expected
playing time. The thirteen separate foreign/source additions lack an incumbent
and are not smuggled into the comparison.

The past-profile floor carries forward existing eight-event probabilities:
three years of 1/.8/.6 weighted production, domestic level translation and a
1,200-PA league-average prior. Its qualified foreign evidence is relative to
the foreign league, not a validated MLB translation. It has no learned future
correction, explicit aging, prospect-rank or Statcast adjustment. It is not
canonical Marcel and is not a newly optimized simple competitor. The second
floor assigns league-average hitting, not league-average playing time.

| Same historical population and playing time | Selected model | Past-profile floor | League-average hitting |
| --- | ---: | ---: | ---: |
| Hitting error, batting wins above average per 600 PA | 1.8048 | 1.9092 | 2.1484 |
| Delivered batting-plus-replacement error | .43513 | .45469 | .51139 |
| Total projected contribution | 4,155 | 4,210 | 3,813 |

Actual contribution totals 4,185 across the seven origins. These are NOT full
WAR or one season's league totals. Hitting errors weight observed PA within each
origin; contribution errors include non-arrivals. Each origin receives equal
weight. Equal-player conditional hitting error also favors selected, 3.8723
versus 3.9811. Tiny actual PA make that view especially noisy.

Selected reduces hitting error 5.5% and contribution error 4.3% versus the past
floor, and wins both scores in all seven origins. The floor has a closer grand
total but worse individual forecasts: an example of why matching league totals
is not enough. These are exposed development point estimates, not fresh
confirmation or evidence allocating the gain to any one feature family.

The exception must stay visible: lower-minor never-debut hitting is 3.1791
selected versus 3.1307 floor; contribution is .04581 versus .04558. Only 54
lower-stage rows have observed next-year MLB batting. That cannot certify a
DSL teenager's eventual talent. Upper-minor never-debut hitting instead favors
selected, 2.5632 versus 2.6299. Non-arrival contribution error also favors
selected, .06939 versus .07249; neither number measures unobserved talent.

## Ten player walks

Origins below mean information from that season and a forecast of the FOLLOWING
season. Hitting numbers are batting wins above the target-season MLB average
per 600 PA. They are not full WAR. The machine report retains every dated raw
stint, source probability, translated contribution, prior, ordered profile input,
probability, conditional workload, compatible actual, and three origin-selected
peers. All 30,506 past-profile forecasts and all ten focal source pools reconstruct.

The floor is calculated as the batting value of:

`(1,200 × origin MLB probabilities + sum(weighted PA × translated event probabilities)) / (1,200 + weighted PA)`.

Domestic translation uses the existing cutoff/held-player graph; overseas uses
past within-league relative production. The mean prior does not invent 1,200
observed PA. The selected hitting heads are different constructions; their
existing coefficient/source reviews are carried into the report where available.

| Player / origin | Selected hitting | Past floor | Actual hitting | Expected PA / actual PA |
| --- | ---: | ---: | ---: | ---: |
| Judge / 2016 | +.264 | −.726 | +5.330 | 310 / 678 |
| Alvarez / 2018 | +.455 | −.468 | +5.648 | 72 / 369 |
| Kurtz / 2024 | +1.024 | +.238 | +5.150 | 10 / 489 |
| Lee / 2024 | −.646 | +1.840 | +.463 | 154 / 617 |
| Tatis / 2022 | +1.313 | +1.653 | +.727 | 40 / 635 |
| Hoskins / 2023 | +.037 | +.702 | +.133 | 26 / 517 |
| Belt / 2023 | +.547 | +1.027 | unobserved | 244 / 0 |
| Flores / 2016 | +.296 | +.043 | +.656 | 391 / 362 |
| Acuña / 2023 | +3.826 | +2.197 | +.723 | 588 / 222 |
| Soto / 2023 | +4.203 | +2.125 | +5.516 | 634 / 713 |

Judge: 410 AAA PA with 19 HR/98 K precede 95 MLB PA with 4 HR/42 K. His
1,274.8 weighted source PA include several minor levels, competing with the
1,200 prior. The MLB-tracking head raises hitting relative to the floor; mean
EV/EV95 each contribute about +.10 in the existing replay. Yet it recognizes
neither the eventual star rate nor full-season workload. Participation .925
times 335 conditional PA gives 310. His exposure peers Moya, Austin and Cowart
get 0, 46 and 117 following-year PA. A universal brief-debut superstar boost
would be wrong; losing useful prior prospect information remains a real concern.

Alvarez: 190 AA PA/12 HR and 189 AAA PA/8 HR plus earlier A/DSL yield 726
weighted PA. The floor is below average after translation and the strong prior.
The prospect head's scouting/translated inputs lift it to +.455, still far below
+5.648. His old 57 DSL PA contribute only +.0011 via the incumbent's pooled
walk term, not the failed overseas integration's +6.01. Participation .434
times 166 conditional PA leaves 72. Grisham reaches 183 PA; Angarita and Díaz
do not appear. Missing readiness and excessive conservative talent are distinct.

Kurtz: 35 A PA/4 HR/10 UBB and 15 AA PA supply only 50 PA against the 1,200
prior. A production-only floor cannot carry much information. The prospect
head already uses draft/rank and raises hitting to +1.024. The remaining .0606
participation times 168 conditional PA gives ten expected PA. Sparse elite
entry support is real, not permission to predict every short-sample prospect
at ten PA forever. Montgomery, Hartl and Soto have zero following-year PA;
these exposure-matched peers are NOT equivalently elite draft-pedigree controls.

Lee: 158 MLB PA/2 HR/13 K enter the tracking head, while the floor also retains
685.8 weighted KBO PA. Adding that foreign evidence lifts the floor to +1.840,
but it overshoots the +.463 actual rate; selected is too pessimistic. The floor's
contribution rises .314 to .951 versus 2.403 actual, still missing because .793
participation times 194 conditional PA yields only 154. This illustrates useful
missing evidence and a poor workload forecast, NOT a validated KBO equivalency.
Pache, Pagés and Mitchell subsequently have 0, 389 and 78 PA.

Tatis: 546 MLB PA/42 HR in 2021 and 257/17 in 2020 survive as 605 weighted
PA including fourteen AA PA in 2022. Both hitting estimates are optimistic
relative to +.727 actual. The glaring error is .134 participation times 296
conditional PA = forty. The finite suspension and past MLB career are not
represented effectively by the selected opportunity mechanism. His peers under
the declared age/current-PA/minor-PA rule are Apostel, Welker and Jones, with
0, 0 and 11 PA: poor comparables for an established returning star. They must
not be used to excuse his probability or imply a supported return calibration.

Hoskins: the two earlier MLB seasons contain 443/27 HR and 672/30 HR, yielding
803.4 weighted PA. Talent remains, but .101 participation times 261 conditional
PA yields 26 before 517. A better hitting input scarcely changes that total.
His Lopes/González/Marmolejos peers all have zero future PA, but their matching
rule omits established career workload; they are not satisfactory return peers.
Existing employment/source experiments already examined this failure. Do not
call a repeat addition of the same signing flag a new solution.

Belt: 404 MLB PA/19 HR/60 UBB in 2023 follow 298/8 and 381/29. The pool has
880 weighted PA. Selected's age/quality/measurement correction is less optimistic
than the floor. With .646 participation times 378 conditional PA, both still
assign contribution before an unexpected zero-PA season. No actual hitting rate
exists. Gomes, Peralta and Solano get 96, 260 and 309 PA; unsigned/old is not
automatically permanent exit. This is retained uncertainty, not a named override.

Flores: MLB PA of 274/510/335 and latest 16 HR/48 K plus earlier AAA and a
nineteen-PA AA stint provide 1,071 weighted PA. The tracking head raises +.043
to +.296, toward +.656 actual. .970 participation times 403 conditional PA
gives 391 versus 362. This ordinary forecast is reasonable, not perfect. Ramón
Flores, Soler and Adames get 9, 110 and 14 PA; equal age/current exposure does
not imply equal established MLB quality.

Acuña is the largest whole-cohort contribution improvement for the FLOOR:
735 MLB PA/41 HR/84 K follow 533/15/126 and 360/24/85. Its 1,397.4 weighted
PA plus prior yield +2.197, versus selected +3.826. Reducing talent lowers
contribution 5.573 to 3.976, closer to .955 actual. But the unchanged 588 PA
still misses 222. The later injury was not known; lower talent accidentally
softens that availability miss. The prior Statcast walk traces the actual
measurement-driven uplift, not an invented explanation from this floor score.
Kwan, Rutschman and Steer subsequently get 540, 638 and 656 PA.

Soto is the largest whole-cohort contribution harm for the FLOOR. MLB PA
654/664/708, HR 29/27/35 and UBB 122/129/121 yield 1,631.6 weighted PA.
The prior drags the uncorrected floor to +2.125, far below +5.516 actual.
Selected's learned production/measurement correction raises it to +4.203.
At unchanged 634 expected PA, contribution falls from selected 6.403 to floor
4.208 versus 8.762 actual. Guerrero, Tatis and Giménez get 697, 438 and 633 PA;
their varied performance does not justify suppressing every elite hitter.

## Judgment and decision

All ten walks are reviewed, including gains, harms, ordinary performance and a
non-arrival. Peer selection used same origin/stage/debut status plus age/current
MLB PA/current minor PA distance, never outcomes. Its shortcomings for former
regulars and elite pedigree are explicit. No favorable peers replace unfavorable
ones. Existing finer support warnings remain; this floor adds no training support.

Keep the selected hitting construction as the working reference. Do not replace
it with the compressed floor or declare its many inputs individually validated.
The basics check passes for overall/established hitting and fails to establish
lower-minors talent competence. It does not test or improve playing time.

The main practical weakness is the path from demonstrated ability/career to MLB
opportunity. Correct sources are necessary, but adding fields unused by the trees
does not repair that path. The controlling [reset assessment](hitter-basics-reset-assessment.md)
sets the next mechanism-level work. No new fit, source capture, freeze, 2026
score, explorer update or deployment follows from this result.
