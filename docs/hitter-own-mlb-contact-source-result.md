# Recovered MLB contact history and player review

2026-10-04. The ordinary 2023 and 2024 MLB contact source is recovered from
existing captured files. Official PA, K, unintentional walks, HBP and all four
hit counts match exactly, as do accepted player-game profiles and summaries.
This is new source coverage, not a new model or a forecast improvement.

| Season | Physical contacts | Direction and outcome classified | Players with contacts | Games |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 124,236 | 119,823 | 651 | 2,430 |
| 2024 | 124,204 | 119,550 | 647 | 2,429 |

Actual game venues, batter hands and pitcher hands are present for all recovered
contacts. Four 2023 two-strike substitutions charge the official strikeout to
the original hitter without changing physical contact identity. The accepted
physical-contact residuals of two and one remain explicit; they are not erased
to manufacture an exact physical-contact denominator.

Sixty-nine homers lack usable direction coordinates and stay outside the ninety
direction/trajectory/result cells. They remain in official HR counts. Bunts and
the existing classifier's foul-air exclusions are also retained in the ledger.
The classifier's geometry universe is not the entire Statcast launch universe:
terminal foul outs can have useful launch measurements even when this direction
classifier excludes them. No average cell is invented for excluded contacts.

## Training support is not yet broad

The current thirty-five outer folds use predictor history ending at each row's
own origin and complete training outcomes by the outer cutoff. Source years
2023 and 2024 give the 2024 folds 398 to 424 distinct active training players
with contact evidence, all from origin 2023. Every earlier testing origin has
zero such active training profiles. In particular, 648 origin-2023 test profiles
do not create earlier training profiles. A two-season comparison cannot certify
an all-years extension. Missing earlier seasons remain unknown, not zero talent.

## Player walkthrough

The machine-readable cases contain actual dated stints, all 199 hitting inputs,
all 251 workload inputs, complete source context, saved-model terms and peers.
Thirty selected saved heads replay exactly. None was refitted. Rates below are
custom batting wins above MLB average per 600 PA, centered on the future season;
they are not full WAR. Expected PA is appearance probability times conditional
PA. Observed rate is undefined when actual next-year PA is zero.

Cases were fixed before source processing, plus the largest excluded-profile
fraction at 200 or more current MLB PA in each source year. Peer selection used
only origin stage, debut status, position when supported, age, exposure, quality
and ranking, never future outcomes. These peers are diagnostic controls, not a
claim of interchangeable talent. Source construction has no candidate forecast,
so there are no invented forecast gains or harms.

### Aaron Judge at origin 2023

MLB PA and HR were 633/39, 696/62 and 458/37 over 2021 to 2023; the final season
also had 130 K and 79 unintentional walks. All 37 recovered homers are classified:
one pulled liner, ten pulled fly balls, twenty center fly balls and six opposite
fly balls. Of 240 physical contacts, 236 have complete direction cells; 122 came
at Yankee Stadium. The current input already gives pooled MLB quality a +2.064
rate contribution and recent quality +.581. It does not ignore his prior power.
Appearance .985 and active workload 544 yield 536 expected PA and +3.360 hitting;
actual 2024 was 704 PA and +7.558. Peers Kepler, García, Betts and Joe later had
399, 637, 516 and 416 PA; only Betts had strongly positive observed hitting.
The miss is real, but source recovery alone cannot establish its remedy.

### Aaron Judge at origin 2024

The three-year history is 696/62, 458/37 and 704/58 PA/HR; 2024 had 171 K and
113 unintentional walks. Physical contact counts are 391, with 381 classified.
One of 58 homers lacks direction; it is not missing production. The later launch
source also separates one catcher-interference contact from normal in-play BBE.
Pooled quality contributes +2.683, current quality +1.300 and workload +.845;
the age term is -.541. Appearance .991 times active 536 gives 531 PA and +4.534
hitting, versus 679 PA and +6.287 actual in 2025. Peers Duran, Buxton, Mullins and
Bleday have mixed positive/negative hitting and 344 to 696 PA. Any tracking
extension must demonstrate improvement rather than simply dialing Judge upward.

### Juan Soto at origin 2023

His 2021 to 2023 MLB PA/HR were 654/29, 664/27 and 708/35, with 129 K and 121
unintentional walks in 2023. Of 445 physical contacts, 435 are classified and
all 35 homers retained. Petco supplies 213 contacts and Mexico City's Estadio
Alfredo Harp Helú four. Those remain MLB/NL contacts at their actual venue, not
Mexican minor-league evidence. Pooled quality contributes +1.595 and workload
+1.110. Appearance .993 times active 638 gives 634 PA and +3.941 hitting, versus
713 and +5.516 actual. Peers Carroll, Kwan, Jones and Happ include a negative
hitting outcome and workloads 297 to 684. Park context cannot be home-team-only.

### Brandon Belt at origin 2023

His MLB PA/HR declined from 381/29 to 298/8 before 404/19 in 2023, with 141 K
and 60 unintentional walks. Of 200 physical contacts, 190 are classified, all
19 HR included; 105 contacts were in Toronto. Age contributes -.890, pooled
quality +.717 and recent workload +.497. Appearance .646 times active 378 gives
244 PA, +.686 hitting and 1.035 delivered offensive wins. Actual 2024 PA and
delivered offense are zero, but his actual batting rate is not zero. Martinez,
Blackmon, McCutchen and Canha all subsequently received 462 to 515 PA with
positive observed hitting. This is not evidence for a blanket older-player
penalty or a hindsight rule that a good hitter will not be signed.

### Spencer Torkelson at origin 2023

His 2021 A+/AA/AAA samples were 141/212/177 PA and 5/14/11 HR. In 2022 he had
404 MLB PA/8 HR plus 155 AAA PA/5 HR, then 684 MLB PA/31 HR in 2023, with 171 K
and 66 unintentional walks. All 31 homers are classified among 424 core contacts:
twenty pulled fly balls, five center fly balls, five opposite fly balls and one
center liner. Workload contributes +.842 and age +.445. Appearance .988 times
active 553 gives 547 PA and +1.296 hitting; actual 2024 was 381 and -.721.
Delivered offense was forecast 2.872 versus .422 actual. Peers Guerrero, Vaughn,
Steer and Casas include both breakout and below-average outcomes. Strong pulled
power alone is not permission to make the hitting forecast more optimistic.

### Matt McLain at origin 2023

His history includes 452 AA PA/17 HR in 2022 and 180 AAA PA/12 HR plus 403 MLB
PA/16 HR in 2023, with 115 MLB K and 31 unintentional walks. There are 250 physical
contacts and 243 core contacts, all 16 HR retained. Pooled quality, workload and
age contribute +.521, +.518 and +.416. Appearance .985 times active 608 gives
599 PA and +.915 hitting, for 2.770 delivered offensive wins. Actual 2024 PA is
zero, not observed zero ability. Peers Franco, Duran, De La Cruz and Neto include
another non-arrival and workloads 285 to 696. Good contact is not a health forecast.

### Nick Kurtz at origin 2024

There are only 35 A PA/4 HR and 15 AA PA/0 HR, with ten total K and twelve
unintentional walks. There is no own-MLB contact history. Current age contributes
+.619, reorganization -.263 and draft rank +.165. Appearance .061 times active
168 gives ten PA and -.063 hitting, versus 489 PA and +5.150 actual. The already
evaluated prospect alternative forecasts +1.024 hitting with unchanged PA; that
positive component result remains separate. Peers Isaac, Eldridge, Ariza and
Avila include three non-arrivals. New MLB measurements cannot fix an untracked
entrant by imputing an average MLB profile or by calling his missing data zero.

### Juneiker Caceres at origin 2024

At age sixteen, his DSL sample is 167 PA, zero HR, eighteen K and seventeen
unintentional walks. Own-MLB contacts are absent. The current linear age terms
alone contribute +1.486 to a hypothetical immediate MLB rate, which remains
poorly supported for this profile. Appearance .00107 times active 62 gives .067
expected PA and +.499 hitting, versus zero actual 2025 PA. Peers Amoroso, Matias,
De Cesare and Arias also had zero next-year MLB PA. These outcomes support a tiny
immediate contribution, not verification of the latent hitting estimate.

### TJ Friedl at origin 2023

He had 448 AAA and 36 MLB PA in 2021, 241 AAA and 258 MLB PA in 2022, and 556 MLB
PA/18 HR in 2023, with ninety K and forty-six unintentional walks. His 409 physical
contacts include 31 bunts and thirteen foul-air exclusions, leaving 365 classified
contacts. All eighteen HR remain. Workload contributes +.714 and pooled quality
+.399. Appearance .989 times active 456 gives 451 PA and +.408 hitting, versus
341 and -.255 actual. Peers Bellinger, Outman, Robert and Nootbaar include two
negative hitting outcomes. The excluded fraction is not necessarily bad source
coverage; bunting is real behavior outside this core contact representation.

### Michael Siani at origin 2024

His 2022 history includes 531 AA, 38 AAA and 24 MLB PA; 2023 includes 493 AAA
and six MLB PA. In 2024 he had fifteen AA and 334 MLB PA, with two MLB HR, ninety-
two K and twenty-one unintentional walks. Of 218 physical contacts, 192 are
classified; twenty-one bunts and five foul-air contacts remain separate. Busch
accounts for 99 contacts and Rickwood Field one. Pooled quality contributes -.559,
workload +.399 and age +.322. Appearance .936 times active 199 gives 187 PA and
-1.527 hitting, versus nineteen PA and -2.537 actual. Peers Rojas, Freeman, Pache
and Moniak include a non-arrival, a worse rate and two positive rates. A defensively
supported job or its loss cannot be inferred solely from bunts or hard contact.

## Disposition

The source walkthrough is complete. Accept the recovered raw measurements as
research inputs with explicit exclusions, not as adjusted talent. Earlier MLB
history and clean park/opponent measurement remain prerequisites for a broad
forecast comparison. The initial construction attempt confused an existing
helper's summary/profile return order; it stopped before saving source outputs
and was corrected without changing legacy sources or fitting anything.

Original pending receipts are preserved. The additive final receipt verifies
their bytes, player review, count arithmetic and unchanged forecast boundary.
The overall model goal is not complete.
