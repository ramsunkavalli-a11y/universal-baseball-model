# Player walks: corrected observations, unchanged forecasts

Reviewed 2026-10-05. All 43 origin cases, representing 38 people, were read with
their prior counts, cutoff-eligible evidence, model inputs, saved-head traces,
conditional workload, outcomes and actual full/active-only training profiles.
The machine review receipt's original pending flag is preserved; the subsequent
completion receipt records this human review. Every baseline-on-new-input probe
and every refitted forecast is exactly unchanged. No player override was applied.

An origin year is the latest completed season; its forecast targets the next
season. Thus Tatis origin 2022 forecasts 2023. PA below are rounded only for
readability. Tree-path accounting explains a saved prediction; it is neither a
causal feature effect nor a separately validated intervention.

## Availability stress cases

Tatis, origin 2022: no MLB PA that season, but his prior MLB career remains in
the inputs. The 80-game suspension is still unresolved at the forecast cutoff.
Participation is 15.35%, conditional PA 400.38, expected PA 61.48; actual is 635.
None of the tested suspension inputs is used. Recent first-team work helps, but
the age of employment evidence and missing 40-man indicator lower participation;
zero current-work inputs lower conditional PA. Both training subsets have zero
people matching the exact audited profile. This is an unsupported interrupted-
career estimate, not evidence that a suspension should erase MLB ability.

Tatis, origins 2023 and 2024: strictly later positive 2023 appearances resolve
continuing-absence observations, not the original legal record or an exact return
date. The old finite flag, known 80 games and stale return timing clear consistently.
Forecasts stay 603.04 versus 438 actual, then 562.73 versus 691. Both profiles again
have zero exact-profile people. The large rebound was already driven by resumed
MLB workload, not the observation repair.

Franco, origin 2023: 491 MLB PA and 17 HR cannot clear the newer August restricted
and administrative channels. No later eligible positive window is captured.
Participation nevertheless remains 99.06%, conditional PA 549.68, expected PA
544.54 versus zero actual. The model largely follows roster, recent workload and
MLB-role evidence while ignoring the restriction inputs. Both exact-profile
training counts are zero. An indefinite legal situation is not equivalent to a
permanent ban, and the later zero cannot retrospectively create such a ban.

Marcano, origin 2024: the cutoff-known permanent status remains a separate hard
override. Delivered probability and expected PA are zero, matching zero actual.
The otherwise fitted conditional PA is 189.04; it is not delivered playing time.
This success does not validate the learned restriction inputs.

Grandal, origin 2016: 457 latest MLB PA, 27 HR, and earlier 443/426 PA. Later MLB
use contradicts continuous absence from the old 2012 record. The observation flag
clears; expected PA stay 403.54 versus 482. Exact-profile support is zero/zero.
Reyes, origins 2016 and 2017: later 2016 use similarly clears old unresolved
observations. Forecasts remain 436.45 versus 561, then 458.95 versus 251 despite
561 PA and 15 HR in the latter origin. Support is one person in each subset, not
adequate rare-case certification. Ruiz, origin 2017: latest MLB work falls to
145 PA; repaired observations do not prevent an aging/exit forecast of 24.51
versus zero. The correct absence history does not guarantee another job.
Duran, origin 2024: an explicit scoped return already resolved his observation;
735 PA and 21 HR lead to 585.28 expected PA versus 696. Support is 14/14, and no
tested input changes.

## High-upside and foreign-role misses remain

Judge, origin 2016: AAA 410 PA/19 HR/98 K and MLB 95 PA/4 HR/42 K. The model
recognizes pedigree and roster status: probability is 90.20%. But conditional
PA are 347.93, yielding 313.83 versus 678. Fixed hitting is only +0.264 per 600;
contribution is 1.107 versus 8.115 actual. Both workload and hitting miss the
breakout. Training profile counts are 208/180, not a guarantee that exceptional
talent is represented. Origin-only peers below retain failures as well as successes.

Alvarez, origin 2018: AA 190 PA/12 HR/45 K and AAA 189 PA/8 HR/47 K. His rank,
AA and AAA evidence raise participation, but absent 40-man status lowers it.
Probability 38.85% times conditional 186.59 gives 72.49 versus 369. Conditional
work is held down by zero signed/current MLB work despite the prospect rank.
Fixed hitting +0.455 gives contribution 0.278 versus 4.610. Support is 65/12;
the small 57-PA DSL record was not freshly edited in this availability contrast.

Kwan, origin 2021: High-A 542 PA/3 HR/51 K in 2019; no invented 2020 season;
AA 221 PA/7 HR/23 K plus AAA 120 PA/5 HR/8 K in 2021. At the March 18, 2022
cutoff, the roster signal raises probability to 72.10%, but conditional PA are
157.52: 113.57 expected versus 638. Zero MLB/current employment-work signals
counter the useful AAA-role evidence. Support is 294/216. This is a missed ready
upper-minors player, not grounds to erase the entire post-COVID cohort.

Kurtz, origin 2024: 35 A PA/4 HR/7 K and 15 AA PA/0 HR/3 K, strong draft input
and a listed prospect rank. The draft and rank already help; they are not absent.
Probability is still 6.32%, conditional PA 162.31, expected 10.25 versus 489.
The signed/current MLB work zeros suppress conditional workload. Support 688/108
describes a broad audited profile, not hundreds of truly comparable elite college
hitters. Contribution 0.050 versus 5.724 also includes a fixed-hitting miss.

Suzuki, origin 2021: NPB 533/514/612 PA, latest 38 HR, 88 K and 87 BB. The existing
March 18, 2022 cutoff includes the captured agreement; treating this as January
would falsely allege a future-information leak. Roster and professional work
help, but domestic-work zeros remain. Probability 61.11% times conditional 313.33
gives 191.48 versus 446. Fixed hitting -0.879 gives contribution 0.320 versus
2.271; support only 3/3. Yoshida, origin 2022: NPB 508/455/492 PA, latest 21 HR,
41 K and 80 BB; 77.73% times 347.18 gives 269.85 versus 580. Support is 5/5.
Lee, origin 2024: latest MLB 158 PA/2 HR/13 K, earlier KBO counts retained;
83.92% times 207.84 gives 174.41 versus 617. A zero 2024 foreign season means
no KBO participation that year, not missing prior foreign evidence. Support 2/1.
These cases require an influential role/source diagnosis, not another unused flag.

## Selection extremes and ordinary controls

There are no gains or harms versus the matched employment V2 baseline: every
loss change is zero. Deterministic tied selection labels pick Garcia origin 2016
for both contribution extremes and Reyes origin 2016 for both changed-source PA
extremes. These labels do not identify a winner or loser. Garcia's latest Mexican
97 PA/1 HR, down from 272/16 and 277/4, yield 0.06 expected PA versus zero.

Cruz origin 2018 is the largest contribution gain versus the separate full-model
anchor, but that gain already existed in employment V2. Latest 591 MLB PA/37 HR
after 667/43 and 645/39 yield 438.48 versus 521; the anchor predicted 274.09.
Contribution 2.687 still trails 5.755 actual. Support 46/43.
Martinez origin 2017 is the largest corresponding harm: latest 489 PA/45 HR after
657/38 and 517/22 yield 419.17 versus 649; the anchor predicted 511.79.
Signed-work zero and absent roster evidence depress him despite strong performance.
The January 27, 2018 cutoff precedes the later Boston deal. Support 18/13.

Acuña origin 2023 is the large false high: 735 PA/41 HR/84 K lead to 589.19 versus
222; contribution 5.582 versus 0.955. His subsequent injury is not backdated into
the forecast. Support 541/529. Wilkerson origin 2018 is the ordinary control chosen
near zero contribution error: MLB 49 PA/0 HR/16 K, AAA 86/4/15 and AA 21 PA/6 K
give 127.66 expected versus 361 actual. Contribution 0.118973 versus 0.118958 is
an offsetting rate/workload coincidence, not an accurate playing-time projection.
Support 294/250.

## Origin-only peers: inspected without hindsight selection

These peers were selected from origin features, not later success. Together with
the cases above they account for all 43 walks. Expected/actual PA are retained
even where the peer failed. None changes under the observation repair.

| Parent case | Peers: latest origin evidence; expected / actual next-year PA |
| --- | --- |
| Garcia 2016 | Rivera MEX 377 PA/10 HR: 0.19/0; Gil MEX 9 PA: 0.21/0; Robles MEX 376 PA/0 HR: 0.29/0 |
| Reyes 2016 | Ruiz MLB 233 PA/3 HR: 272.08/145; Strange-Gordon MLB 346/1: 455.23/695; Colabello MLB 60 PA plus AAA 153/5, after prior MLB 323/15: 60.10/0 |
| Judge 2016 | Moya AAA 426/20 plus MLB 100/5: 213.70/0; Austin AAA 234/13 plus MLB 90/5: 109.49/46; Cowart AAA 458/9 plus MLB 87/1: 116.59/117 |
| Martinez 2017 | Solarte MLB 512/18: 430.20/506; Pollock MLB 466/14 after 46 prior PA: 510.06/460; Goins MLB 459/9: 157.46/120 |
| Cruz 2018 | Encarnación MLB 579/32: 517.35/486; Kinsler MLB 534/14: 386.06/281; Zobrist MLB 520/9: 415.02/176 |
| Wilkerson 2018 | Urshela MLB 46/1 plus AAA 240/2: 20.79/476; Wallach MLB 52/1 plus AAA 174/3: 78.57/54; Wisdom MLB 58/4 plus AAA 421/15 after AAA 506/31: 153.66/28 |
| Acuña 2023 | Riley MLB 715/37: 608.81/469; Rutschman MLB 687/20: 609.06/638; Kwan MLB 718/5: 591.43/540 |

The counts above are evidence summaries, not assertions of equivalent talent.
Urshela is another important false low. Moya and Wisdom show why blindly raising
every plausible prospect forecast would create false positives. Older foreign
league peers do not establish support for a first-time NPB/KBO major-league arrival.

## Review conclusion

Correct records are necessary, but this comparison did not change any mechanism
used by the learner. Retain the source, close this contrast without promotion,
and check downstream influence before repeating a fitting batch. Existing
temporary-career, ready-prospect and foreign-professional misses remain distinct;
neither a pooled total nor an ordinary cancellation resolves them. The next
diagnostic must inspect prior experiments and actual training support before
committing to a structural change. The 2026 forecast and evaluation remain sealed.
