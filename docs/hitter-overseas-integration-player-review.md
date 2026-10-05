# Player walkthrough of the overseas hitter comparison

2026-10-04. This review follows the fixed completed comparison, not a new fit.
It finds both real availability gains and unsound hitting mechanisms. Review
completion does not mean predictive success. The new candidates are not suitable
replacements for current UBM.

## Selection and interpretation

There are 38 player-origins: fixed source/status/stress cases and eligible additions,
then each new arm's largest delivered-value gain, deterioration, false high, false
low and ordinary case. The selection manifest, player IDs, release cutoffs and
whole-player folds are retained in the bounded public case artifact and private
`reviewed-cases.json`. Outcome-selected cases diagnose failures; they do not validate
a model. The [result](hitter-overseas-integration-result.md) keeps aggregate/cohort
scores beside the examples.

An origin of 2024 means forecasting 2025 from the dated preseason release, not
forecasting 2024. The special 2021-origin release is March 18, 2022; Suzuki's dated
agreement is available then. Later injuries, legal developments and actual jobs
are not backdated. All histories below are actual dated source counts through the
origin; foreign windows are three years. Actual outcomes stop in 2025.

PA is unconditional expected MLB plate appearances: participation probability
times conditional PA. Rate means future-season-relative batting wins above average
per 600 PA; value adds the origin replacement reference and scales by expected PA.
No-arrival rate is unobserved, even though the internal label placeholder is zero.
Absent current forecasts for additions stay absent.

Both arms receive age, literal roster corrections, domestic counts separated by
level, pooled recency 1/.8/.6 rates with 100 prior opportunities, games, pedigree,
preseason ranks, ordered employment and separate medical/nonmedical restrictions.
The overseas arm also receives raw and translated NPB/KBO evidence. Its translated
components are already league-relative; player-specific foreign park exposure is
not adjusted. Neither raw-history hitting arm inherits every current contact,
Statcast or park-adjusted talent branch. This omission limits what losing to the
current model tells us.

Peers are selected without consulting future results: same origin, prior debut,
dated major-link and literal roster status, then nearest age, current MLB/foreign
exposure and prospect rank. Three are retained when available. Their later PA is
shown only after selection. These peers often are NOT comparable in professional
readiness, position or medical restriction. Empty or badly matched peer sets are
evidence of insufficient support, not something to conceal.

## Foreign evidence overwhelms newer MLB evidence

Jung Hoo Lee, 808982, origin 2024, fold 1: the model has his 158 MLB PA, two HR
and thirteen K plus 1,014 older KBO PA. Current rate is −0.65; domestic is −1.29;
overseas is +9.44; actual is +0.46 over 617 PA. Expected PA improves from 154 to
183, still far below actual. The borrowed foreign component itself is only +1.53.
The second-stage raw KBO contact column standardizes to −76.49 training SD;
coefficient −0.18523 contributes +14.17 wins/600, with other foreign terms partly
offsetting it. Exact total foreign-feature accounting is +10.75. This is rare,
correlated feature extrapolation, not a plausible estimate of his MLB hitting.
There are two comparable-profile training participants and one active hitter.
Selected peers Kjerstad, Loftin and Baty get 167, 188 and 432 PA; none establishes
equivalent KBO experience. Improved delivered-value error is partly cancellation
between too little workload and far too much hitting, not a reasonability pass.

Shohei Ohtani, 660271, origin 2018, fold 1: his newer MLB debut is 367 PA,
22 HR and 102 K; 613 older NPB PA remain. Current/domestic/overseas rates are
+1.58/+0.86/−6.53, versus +1.67 actual. Workload is quite reasonable, 391/411/411
versus 425 PA, but overseas value becomes −3.21 versus +2.49 actual and +2.23
current. The total foreign-feature effect is −7.47; raw and translated "other"
components alone contribute −2.97 and −2.09. The borrowed rate input is +1.07,
so the extreme negative estimate is introduced by integration. Exact profile
support is zero. Arcia, Dahl and Bader receive 546/413/406 PA, but are not two-way
NPB matches. Keeping the debut counts as columns did not give them proper priority.

Masataka Yoshida, 807799, origin 2024, fold 3: the source has 580 MLB PA in 2023
and 421 in 2024, with fifteen/ten HR and 81/52 K, plus eight AAA PA and 508 older
NPB PA. Current rate +0.33 becomes +5.14, while actual is −0.44. PA rises from
476 to 526 versus 205 actual; value rises from 1.75 to 6.15 versus 0.49. Foreign
features account for +5.12; raw NPB K and translated K contribute +2.64 and +1.57.
Four profile people cannot justify this effect after 1,001 more recent MLB PA.
Heim, O'Neill and Dubón peers receive 433/209/398 PA. This selected false high
confirms the weighting defect is not confined to MLB newcomers.

Ha-Seong Kim, 673490, origin 2022, fold 2: 298/582 recent MLB PA with eight/eleven
HR and 71/100 K coexist with 622 old KBO PA. Overseas rate +2.01 versus +0.51
actual improves a too-low current −0.64 but overshoots; foreign terms account
for +3.41. PA moves 446 to 474 versus 626. Support is four participants/three
active hitters; Correa, Tellez and Thomas receive 580/351/682 PA. The value gain
does not establish a sensible fading rule.

## New overseas professionals are still treated as weak arrival bets

Shohei Ohtani, 660271, origin 2017, fold 1: 732 recent NPB batting PA and known
mixed-role/scouting evidence are present, not invented zeros. US last-stat gap
is coded five and position Y. Participation is 7.19%, conditional PA 171.68 and
expected PA 12.34 versus 367 actual. Domestic rate +1.93 becomes −3.16 overseas
versus +3.69 actual. Neither opportunity head uses any foreign-feature split in
this saved cell, so adding foreign data does not change PA. Profile support is
zero. Chavis, Florial and Trammell all have zero next-year MLB PA, but are not
established Japanese professionals. Their outcomes cannot validate this fallback.

Seiya Suzuki, 673548, origin 2021, fold 1: 1,659 NPB PA and a cutoff-known agreement
are present. His broad outfielder role becomes source_position UNKNOWN; that rare
indicator contributes −2.16 to the overseas hitting rate. Participation 24.6%
times conditional 102.9 gives 25.3 PA versus 446. Domestic rate −2.34 becomes
+3.69, versus +1.17 actual; borrowed input is +1.79. Three profile people and
selected Herrera/Plummer/Hummel outcomes of 124/31/201 PA do not validate a
professional-newcomer job. The encoding loses known OF information; the boosted
job forecast fails despite available foreign performance.

Masataka Yoshida, 807799, origin 2022, fold 3: 1,455 NPB PA and dated hitter
employment produce 35.5 domestic and 49.7 overseas expected PA versus 580 actual.
The rate goes +0.23 to +4.65 versus +1.09 actual. Five profile people are present;
Jones/DeLuca/Abreu get 0/45/85 PA. More hitting information modestly changes
workload, but neither head treats this as a supported established-professional
arrival. No absent old UBM forecast is filled with zero for comparison.

Jung Hoo Lee, 808982, origin 2023, fold 1: 1,558 KBO PA produce 31.8 to 40.9
expected PA versus 158 actual. Rate +0.22 to +10.32 versus −1.14 actual is driven
by +13.62 from raw KBO K. Borrowed input is +1.58. Four profile people and peers
Shenton/DeLoach/Feduccia with 50/75/14 actual PA do not support the extreme rate.
His later shortened MLB season does not make the huge rate estimate reasonable.

Eric Thames, 519346, origin 2016, fold 4: 1,638 KBO PA and dated agreement are
present, with US last-stat gap three. Current PA 20.8 becomes 49.0 in both arms
versus 551 actual: 40.1% participation times 122.1 conditional PA. Neither job
head has a foreign split; no matching profile person trains this case. Overseas
rate −1.50 versus +2.42 actual reverses domestic +0.63 even though borrowed input
is +2.53. Gurriel/Mesoraco/Barnes receive 564/165/262 PA but do not supply matched
KBO-return support. Data collection did not resolve either talent or opportunity.

Hyeseong Kim, 808975, origin 2024, fold 4: 1,754 KBO PA, a known birthday,
second-base role, January agreement and positive roster evidence replace the
old near-empty fallback. Expected PA improves 0.36 to 48.78 versus 170 actual,
with 30.5% participation and conditional 159.9. Overseas rate −3.86 versus −0.34
actual loses the domestic +0.06 estimate; translated triples contribute −2.53,
older KBO exposure −1.72. Eight profile people are insufficient proof of this
penalty. Brito/Veen/Tawa get 0/37/225 PA. The source corrections help arrival,
but the new talent integration harms him.

## Known finite absence is not the same as career exit

Fernando Tatis Jr., 665487, origin 2022, fold 0: the model receives 257/546 MLB
PA in 2020/2021, seventeen/42 HR, and a fourteen-PA AA rehab line in 2022. His
original eighty-game suspension and a dated tentative April 20 return report
are distinct inputs; neither means the actual return is known. Roster is negative,
an old major activation is 1.45 years old, and there are no matched profile people
or eligible origin-only peers. Overseas participation is 9.46%, conditional PA
290.7 and expected PA 27.5 versus 635 actual, worse than current 39.7. Saved
path accounting includes −0.652 log odds from evidence age and −0.494 from roster;
zero current workload reduces conditional PA by 89.5 along the traced path.
These are exact mechanics, not causal effects. Finite nonmedical absence remains
confused with disappearance, despite positive historical talent. Rate +0.44 versus
+0.73 actual is not the main miss.

Rhys Hoskins, 656555, origin 2023, fold 4: the source retains 443/672 MLB PA,
27/30 HR in 2021/2022, a missed 2023 and the known January 26 Milwaukee signing.
An ended medical transaction scope is not certified physical recovery. Current
26.3 PA rises to 224.8, from 73.4% participation times 306.4 conditional PA,
against 517 actual. Overseas rate −0.10 versus +0.13 actual gives value 0.66
versus 1.72 actual. This is a useful correction, still underpredicting opportunity.
Five participants/three active profile people and Andujar/Serven/Sullivan outcomes
of 319/71/17 PA do not establish equivalently secure regular jobs.

Wander Franco, 677551, origin 2023, fold 2: 491 MLB PA, seventeen HR and 69 K
coexist with positive roster and unresolved administrative/restricted channels.
Participation remains 98.9%, conditional PA 557.5 and expected PA 551.4 versus
zero actual. Two profile people and available peers Turang/García Jr./Maikel
Garcia with 619/528/626 PA are not adequate uncertain-eligibility comparables.
The legal outcome cannot be imported backward; the failure requires explicit
availability uncertainty rather than a hindsight permanent-ban rule.

Tucupita Marcano, 672779, origin 2024, fold 1: 177/220 MLB PA in 2022/2023 and
known permanent eligibility evidence are present. The reviewed hard-status rule
forces both forecasts to zero, matching actual zero. Soto/Adams/Groshans get
0/5/0 PA. One participation-profile person and no active profile examples cannot
validate a learned ban model; this correct forecast is an explicit sourced rule.

Brandon Belt, 474832, origin 2023, fold 3: 404 recent MLB PA, nineteen HR and
141 K follow 381/298 PA in the previous years. He is unsigned, not retired.
Current 244 PA becomes 184 versus zero actual. Rate +0.73 and positive value
remain plausible conditional projections, not evidence he should have been
assigned zero ability. Peralta/Escobar/Duvall get 260/0/330 PA; 60 participants
and 21 active profile people permit substantial uncertainty. As the user noted,
his failure to sign after a good year was surprising. Do not tune a named rule.

Matt McLain, 680574, origin 2023, fold 2: 403 MLB PA, sixteen HR and 115 K,
strong prior AAA production and a known October clearing activation lead to
613 expected PA versus zero actual. His later injury is unavailable to the cutoff.
Turang/Thomas/Bae get 619/103/81 PA; 238 participants/231 active profile people
are present. The high forecast is not proof of a source bug; injury risk remains
uncertain, and the later event must not become a retrospective input.

## Domestic talent can fail for the same reason

Yordan Alvarez, 670541, origin 2018, fold 2, is both arms' largest value gain.
He has 190 AA PA with twelve HR and 189 AAA PA with eight HR in 2018. A 57-PA
2016 DSL line has twelve walks. Recency .6 yields 34.2 PA and 7.2 walks; the
100-opportunity prior gives (7.2 + 8)/(34.2 + 100) = 11.326% pooled walks.
This shrunk rate nevertheless becomes 96.95 training SD and adds +6.01 wins/600.
The overseas total rate is +9.04 versus +5.65 actual; expected PA falls 72.2 to
61.6 versus 369 actual. Value improves 0.28 to 1.12 versus 4.61, but the gain
uses an overly large talent forecast to offset too little workload. Giménez,
Kieboom and Robert get 0/43/0 PA; 1,281 participant-profile people and 163 active
people do not certify the sparse DSL coefficient. This is a lucky partial gain,
not evidence that the new head recognized his talent properly.

Andrew Benintendi, 643217, origin 2017, fold 3, is the domestic largest harm.
His 658 MLB PA, twenty HR and 112 K are present. The 2015 short-season line has
153 PA and 24 unintentional walks; its pooled shrunk walk rate 11.679% adds
−1.26 wins/600. A high prior prospect rank also adds −0.62. Current rate +1.08
becomes −1.43 versus +2.22 actual; PA stays reasonable, 636/637 versus 661.
Value falls 3.10 to 0.44 versus 4.48 actual. The saved additive accounting confirms
the direction and scale of the old-level term, not a causal baseball conclusion
that walks are bad. Peers Machado/Swanson/Bellinger get 709/533/632 PA, and 152/147
participant/active profile counts do not rule out coefficient instability.

Aaron Judge, 592450, origin 2016, fold 3, is both arms' largest false low.
He has 410 AAA PA with nineteen HR and 98 K, then 95 MLB PA with four HR and
42 K. Current 310 PA becomes 297 versus 678 actual; rate +0.26 becomes +0.95
versus +5.33 actual. Top rate terms include older A walks (+0.64) and known
scouting (+0.37). Almora/Alfaro/Swanson get 323/114/551 PA, preserving unsuccessful
comparisons. With 208/180 profile people, this is a real missed breakout rather
than missing history, but exact rookie upside and workload remain uncertain.

Aaron Judge, 592450, origin 2024, fold 3: his 2022–2024 MLB lines contain
696/458/704 PA and 62/37/58 HR. Current rate +4.94 becomes +4.31 versus +6.29
actual; PA 531 becomes 523 versus 679. Current value 6.02 becomes 5.38 versus
9.24. Recent and pooled MLB-quality terms add +1.65/+1.34, so the model does use
his recent performance, but regresses him more than the current anchor. Machado,
Hernández and García peers get 678/546/547 PA; 308/305 support people do not prove
adequate extreme-tail calibration. This is talent/workload underprediction, not
another missing foreign feature.

Nick Kurtz, 701762, origin 2024, fold 2: his first pro sample is 35 A PA with
four HR plus fifteen AA PA. Draft and dated scouting evidence are known. The
draft/thin-sample rate term adds +0.76, yet rate +1.02 current becomes −0.09
versus +5.15 actual. Participation about 6% and conditional PA 160 yield only
9.6 PA versus 489 actual. Teel/Smith/Miller get 297/493/0 PA; 2,343 participant
and 305 active profile people are coarse prospect groups, not proof of matching
fast-track college support. Pedigree columns are present but insufficiently used.

Steven Kwan, 680757, origin 2021, fold 1: 2019 A+ has 542 PA, three HR and
51 K; 2021 AA/AAA has 221/120 PA, seven/five HR and 23/eight K. Canceled 2020
minor production is not fabricated. Rate −0.25 becomes +0.27 versus +1.62 actual,
but PA stays 116 versus 638 actual. Age and college terms add +0.39/+0.37, while
older rank adds −0.38. Herrera/Davis/Plummer get 124/11/31 PA; 294/217 profile
people do not mean his contact-heavy emerging-regular profile is adequately modeled.
This 2021 miss is retained, not used to excuse failures in every other origin.

Junior Caminero, 691406, origin 2024, fold 4: prior AA has 351 PA and twenty HR;
current AAA has 236 PA/thirteen HR and MLB 177 PA/six HR, with a small complex
rehab line. PA 419 becomes 420 versus 653 actual; rate +0.59 becomes +0.92 versus
+2.18 actual. Age adds +0.70, current complex exposure +0.68, older complex K
−0.41. Soderstrom/Sanoja/Manzardo get 624/342/531 PA; 474/426 profile people are
available. Both models identify substantial opportunity but still miss its scale.
The sizable rehab/complex terms merit the same coherent reliability treatment.

## Ordinary controls and additional retained cases

Ronald Acuña Jr., 660670, origin 2023, fold 3, is the domestic false high.
His 735 current MLB PA, 41 HR and 84 K give +3.54 rate and 585 PA versus +0.72
and 222 actual. Recent MLB quality adds +1.12. Devers/Hoerner/Stott get 601/641/571
PA. His later injury cannot be used as a known preseason input; the large error
still belongs in scoring, with uncertainty rather than a named hindsight rule.

Hernán Pérez, 541650, origin 2017, fold 4, is the domestic ordinary case.
458 current MLB PA, fourteen HR and 79 K yield 359 PA and −1.05 rate versus
334 and −1.03 actual; value 0.475 versus 0.452. MLB-quality terms modestly reduce
the rate. Castro/Freeman/Frazier get 647/707/352 PA. With 314/306 profile people,
this is a plausible ordinary forecast, not enough to offset the major harms.

Wilmer Flores, 527038, origin 2016, fold 2, is the overseas ordinary case, despite
having no foreign history. His 335 current MLB PA, sixteen HR and 48 K yield
377 PA and +0.56 rate versus 362 and +0.66 actual; value 1.513 versus 1.513.
Age/AAA power/MLB contact terms add +0.34/+0.27/+0.17. Naquin/Healy/Conforto get
40/605/440 PA. There are 124/119 profile people. Ordinary successes coexist with
rare-feature instability; this is not a uniform scale or label bug.

Luke Voit, 572228, origin 2021, fold 3: 234/241 MLB PA with 22/eleven HR in
2020/2021 and a dated trade-day activation are retained. PA falls 345 to 277
versus 568 actual, while rate +0.97 overestimates actual +0.12. Negative-listing
conflict adds −0.53 to rate accounting despite resolved employment; value falls
1.85 to 1.32 versus 1.89. Harrison/Tilson get 425/0 PA. Keeping activation fixes
the source conflict but does not prove the new heads use it appropriately.

Jarren Duran, 680776, origin 2024, fold 1: 735 MLB PA, 21 HR and 160 K plus
the reviewed clearing activation produce 591 PA versus 696 actual. Rate +1.06
versus +1.15 actual is sensible; recent/pooled MLB quality add +0.49/+0.33.
De La Cruz/Ohtani/Vaughn peers get 50/727/447 PA. This is a generally reasonable
forecast with residual workload underprediction, not a live permanent restriction.

Donovan Solano, 456781, origin 2024, fold 0: 309 MLB PA, eight HR and 65 K
plus 51 AAA PA yield 243 PA versus 179 actual, worse than current 138 PA.
Rate −1.23 versus −1.69 actual has age −0.89 and reorganization −0.40 terms.
LeMahieu/Vázquez/Muncy get 142/214/388 PA; 65/61 profile people exist. The prior
availability-model harm remains a harm, not quietly removed after source repair.

The remaining admission cases preserve failed returns as well as successes.
Their actual rates are unobserved when PA is zero. Each has full source/input,
head, coefficient, support and origin-only peer traces in the case artifact:

| Player and origin | Recent actual source evidence | Overseas expected PA and actual PA | Traced mechanism and judgment |
| --- | --- | --- | --- |
| Brian Bogusevic 460131, 2016, fold 4 | 193 NPB PA; 2014 AAA 311 PA/6 HR; 2015 AAA 515 PA/12 HR plus MLB 61 PA/2 HR | 5.1 / 0 | Older domestic evidence stays present; NPB HBP term adds 1.57 to rate. Ishikawa/Gonzalez/Head also receive 0 PA. A non-return is retained, not evidence of zero talent. |
| Jae-Gyun Hwang 666561, 2016, fold 2 | 1,705 KBO PA; no captured US production | 0.5 / 57 | Unknown position and absent active profile support; KBO HBP adds −3.81 to rate. Predicted −5.27 is close to observed −5.45 on only 57 PA, but arrival is badly missed. Schoop/Pena/Irazoqui peers have 0 PA and are not established KBO matches. |
| Eric Thames 519346, 2021, fold 4 | Two NPB PA; 2019/2020 MLB 459/140 PA and 25/3 HR | 8.6 / 0 | Foreign mover-count term adds +4.95 while other foreign terms offset it; actual rate unobserved. Rosario/Florimón/Elmore receive 0 PA. Tiny foreign exposure should not create large rate swings. |
| Stefen Romero 552662, 2021, fold 1 | 815 NPB PA; no recent US line | 0.5 / 0 | Foreign mover-count term adds +4.28; six active profile people. Snider/Blash/Bour receive 0 PA. Small arrival forecast fits the realized exit but does not validate the conditional rate. |
| Dixon Machado 553988, 2021, fold 3 | 1,099 KBO PA plus 2019 AAA 393 PA/17 HR/79 K | 1.6 / 17 | KBO doubles add −1.90 to rate; zero active profile support. Hyun Soo Kim/Vincej/Washington receive 0 PA. A brief return is underpredicted; seventeen actual PA is weak talent evidence. |
| Rusney Castillo 628329, 2021, fold 2 | 76 NPB PA plus 2019 AAA 493 PA/17 HR/63 K | 0.8 / 0 | NPB doubles add +2.42; three active profile people. Welington Castillo/Snyder/Descalso receive 0 PA. The non-return does not certify the positive hitting rate. |
| Roberto Ramos 657733, 2021, fold 0 | 699 KBO PA plus 2019 AAA 503 PA/30 HR/141 K | 1.1 / 0 | Older KBO exposure contributes −2.17 to rate; one active profile person. Thompson/Coulter/Boyd receive 0 PA. Domestic power was not erased; actual hitting remains unobserved. |
| Jantzen Witte 642220, 2022, fold 2 | 128 NPB PA plus 2021 AAA 455 PA/19 HR/80 K | 5.1 / 0 | NPB mover-count term contributes +3.13; zero active profile support. Ali Castillo/Maggi/Sale receive 0/6/0 PA. The rate changes from −1.48 domestic to +1.30 overseas without strong support. |
| Yonathan Perlaza 666632, 2024, fold 2 | 522 KBO PA; AA 547 PA/23 HR and AAA 543 PA/23 HR in prior two years | 25.0 / 0 | KBO HBP contributes −2.61 to rate; no active profile people. Hernández/Gamboa/Cedrola receive 0 PA. Predicted −7.16 is not observed zero ability; new integration is unstable even for non-arrivals. |

## Cross case decision

All 38 selected player-origins have been read and classified. Exact saved-fit
ridge accounting and boosted path accounting explain mechanics, not causal
baseball effects. Zeroing foreign columns in the same saved fit is an artificial
diagnostic, not a validated replacement model. Coefficient signs in correlated
features cannot be interpreted as standalone effects of walks, pedigree or a league.

Confirmed representation failures are disproportionate rare-level feature effects,
ineffective fading after actual MLB production, broad OF collapsed into UNKNOWN,
and very low forecasts for known professional newcomers/finite absences. The last
two workload patterns are confirmed predictions with sparse training; the exact
best repair is not yet established. Unforeseeable later injury and surprising
non-signing remain genuine uncertainty, not blanket excuses for the cohort losses.

The experiment's walkthrough is complete. Its predictive and baseball checks fail,
and deployment remains unapproved. Retain useful source work and the current
talent anchor; repair coherent evidence weighting and professional/availability
representation within the controlling practical plan. Do not start another algorithm
tournament or collect another league to avoid this demonstrated integration defect.
