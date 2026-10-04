# Longer hitting follow up does not yet improve the best batting alternative

2026-10-04. Keep the existing translated/ranking hitting alternative, not the
new shared-development model. The new model helps several consequential
prospects but does not improve overall next-year hitting accuracy against that
stronger anchor. Its small delivered-value gain is uncertain. Fourteen actual
player walks are complete; the practical hitter goal remains unfinished.

## Comparison and execution

The [locked contract](hitter-shared-development-contract.md) compares the current
hitter, the reviewed translated/ranking Ridge, a next-year level-specific age
control, and a model sharing completed annual MLB hitting labels across Years
1–6. The latter uses explicit horizon terms, never later outcomes as inputs.
Both new Ridge models keep alpha 100 and normalize their total training weight
to the same immediate-active training count. Additional observations therefore
do not simply weaken regularization. No tuning followed the scores.

All 30,506 evaluation identities remain. Seventy actual membership/integrity
checks and 35 translated-head replays precede fitting; all seventy new heads
replay after fitting. Each label matures by its actual outer cutoff and the
entire held-player fold is excluded. Horizon-specific group support and input
ranges are saved. The source audit's lack of direct immediate teenage DSL
support remains; pooled later participants do not erase it. Cached draft,
scouting-vintage, unknown age, translation context and role-selection limits
remain, rather than being globally recertified.

Playing-time probabilities, conditional PA and expected PA remain exactly
unchanged. Primary batting changes only never-debut players. Established
players retain the current forecast; raw replacement estimates are diagnostics.
No protected outcomes or frozen/explorer forecasts change.

## Scores and totals

Batting rate is custom wins above target-season MLB average per 600 PA, not
published WAR. Rate scores use actual active MLB observations, equal target
years and actual PA within year. Delivered value includes all non-arrivals and
uses the existing fixed common-origin batting-plus-replacement response. That
different environment convention is explicit, not a silently substituted label.

| Never-debut comparison | Batting RMSE | Batting MAE | Delivered value RMSE | Predicted value total |
| --- | ---: | ---: | ---: | ---: |
| Current hitter | 2.61438 | 1.95425 | .152257 | 199.54 |
| Translated and ranking anchor | 2.58308 | 1.94100 | .151662 | 194.67 |
| Level-specific age control | 2.58700 | 1.94531 | .151767 | 194.43 |
| Shared development | 2.58974 | 1.94816 | .151466 | 210.62 |
| Actual total | — | — | — | 214.75 |

The rate score covers 787 active forecasts. Delivered value covers all 24,199
never-debut forecasts. Against the translated anchor, shared rate MSE changes
by +.03442, nominal paired 95% interval [-.05948,+.13269]; value MSE changes
by -.00005938, interval [-.00026722,+.00015100]. Neither establishes an
improvement. Equal-active-observation rate RMSE also worsens, 4.99883 to
5.02664, so the negative rate contrast is not just high-PA weighting.

Shared rate improves against the translated anchor in 2016–18 but worsens in
2021–24. Value improves in 2018/2021 and worsens in the other five origins.
Do not dismiss the recent losses as only the COVID year. The lower-minors
conditional rate RMSE moves 3.17908 to 3.18694; delivered .042987 to .043014.
New-draftee rate 2.36770 to 2.45634 and thin-history rate 2.03706 to 2.12624
also worsen, despite tiny favorable delivered-value point estimates. These
small active groups and nominal intervals do not settle every development model.

Upper-minors predicted value rises 177.49 to 193.48 against 203.94 actual,
while lower-minors 16.18 to 15.98 remains above 9.56 actual. Closer aggregate
totals do not establish better individual predictions. All PA totals and arrival
scores are unchanged by design. The public 2,627-player PA comparison remains
138.33 RMSE and 106.41 MAE versus Steamer 135.38 and 92.08, with the existing
snapshot qualifications. The practical public-workload gap is not solved.

## Fourteen actual player walkthroughs

Each case below traces dated three-year stats, actual origin inputs, saved fits,
exact signed linear groups, fixed opportunity and next-year reality. Full inputs
and four outcome-blind peers where available are saved in the case evidence.
Signed term sums are model accounting, not causal importance. Refit changes
many coefficients, so a changed forecast cannot be attributed solely to one
new age term. All horizon terms are exactly zero for these Year-1 predictions.

The original selection file uses zero as a numeric scoring placeholder for
inactive batting rates. Active-only rate scoring excludes those rows. The
completed review provides a separate corrected case artifact with null observed
rates for nonparticipants; original selection/trace files are preserved. Zero
PA never becomes measured zero hitting talent or a model-training rate.

**Alonso in 2018, the largest shared value gain.** Age 23, 574 AA/AAA PA,
36 HR, 73 unintentional walks and 128 K. Hitting estimates are current +.286,
translated +.592, control +.549 and shared +.958, versus observed +3.283.
Shared uses intercept -.075, original age +.320, level-age +.038, level
baseline -.109, translated -.157, pedigree +.247 and remaining +.694.
The gain is not a positive translation term alone. Fixed 80.36% times 268
conditional PA still gives only 215 versus 693 actual. Value .875 to 1.006
helps but remains far below 6.598 actual. Immediate coarse support is 48
people, six-year pooled 53, refined four. Thaiss 164 PA, Mercado 482, Neuse
61 and Wong 18 are origin-selected controls, not equivalent power ceilings.

**Julio Rodriguez in 2021.** Age twenty, 340 A+/AA PA, thirteen HR,
42 unintentional walks and 66 K, with canceled 2020 exposure explicitly absent.
Translated +1.216 becomes control +1.202 and shared +1.719 versus +2.683.
Shared original age +.766, level-age +.231 and pedigree +.266 are favorable;
translation's signed sum is -.157. The retained 80.51% times 316 conditional
PA is 254 versus 560 actual. Value 1.311 to 1.524 moves toward 3.937 but
does not fix workload. Coarse support grows 20 to 38, refined fifteen.
Peers include Abrams 302 and Greene 418 PA, plus Nunez and Noriega zero.
This is a useful player gain, not proof every highly ranked youngster arrives.

**Kurtz in 2024, the largest false low in both arms.** Age 21, fifty A/AA
PA, four HR, twelve walks and ten K. Current -.063, translated +1.024,
control +.916 and shared +1.411 compare with +5.150 actual. Shared translated
sum +.941 retains his good small sample; age +.415 and level-age +.063 also
contribute. Yet fixed 6.06% times 168 conditional PA leaves ten expected PA
versus 489. Value .049 to .056 is negligible against 5.838 actual. Immediate
coarse support fifteen grows to 312, but refined elite-entry support is still
zero. Bender, Jenkins, Kross and Marget have small exposures and zero next-year
PA but weaker pedigree; they cannot explain away this substantive readiness miss.

**Langford in 2023.** Age 21, 200 professional PA, ten HR, 36 walks and
34 K including eighty AA/AAA PA. Translated +1.439, control +1.432 and
shared +1.722 overshoot actual +.549; the current +.688 was closer.
Shared's translated sum +.484 and pedigree +.408 remain favorable, while its
intercept is less negative than the anchor. Fixed 59.91% times 359 conditional
PA gives 215 versus 557. Value 1.181 to 1.282 approaches 1.796 despite the
worse hitting forecast: underforecast workload allows an optimistic rate to
partly compensate. Coarse support 97 grows to 485, refined only one. Greene,
DeLauter, Shaw and Teel have zero next-year PA; their outcomes are not evidence
that Langford deserved such a low workload forecast.

**Pena in 2021.** Age 23, 133 AAA PA with ten HR and 35 K, plus 27 rookie
PA, known 40-man listing and no captured top-100 listing. The source retains
474 A/A+ PA in 2019 and canceled 2020 history. Translated -.300 becomes
control -.386 and shared -.572 versus actual -.108. Shared translated -.369
and pedigree -.190 outweigh favorable age; this is a deterioration, not a
lost player ID. Fixed 26.64% times 176 PA is 47 versus 558 actual. Value
.124 to +.102 falls further from 1.327. Immediate coarse support 59 grows
to 75, refined 57. Peers Figuera, Estevez, Gozzo and Perez have zero PA,
but are not matched on all performance or readiness evidence. Counts alone
cannot excuse the miss.

**Holliday in 2023, the largest control value gain.** Age nineteen, 581
A-through-AAA PA, twelve HR, 99 walks and 118 K. Translated +.826 becomes
control +.733 but shared +.938 versus actual -2.838. Control's smaller
global age +.726 plus level-age +.053 reduces net optimism; shared partly
restores it. Fixed 88.68% times 396 PA gives 351 versus 208 actual.
Control value 1.571 to 1.516 slightly helps; shared 1.636 worsens the
negative -.503 outcome. Coarse support 24 grows to 164, refined seventeen.
Merrill gets 593 PA while Arroyo, Williams and Anthony zero. Talented peers
show varying readiness; none establishes Holliday's immediate batting success.

**Acuna in 2017, the largest control harm.** Age nineteen, 612 A+/AA/AAA
PA, 21 HR, 43 walks and 144 K. Ranking score .99 is present: the miss is
not an absent prospect ranking. Translated +.187 falls to control +.016;
shared +.299 remains far below observed +3.681. Control combines global
age +.525, level-age +.021 and AAA baseline -.092 with other signed terms;
there are zero direct active teenage-AAA analogues even with six-year pooling
in this fold. The exact origin peer intersection is empty, explicitly reported.
Fixed 48.22% times 211 conditional PA yields 102 versus 487 actual.
Value .344 to .315 worsens 4.145 actual; shared .363 only slightly helps.
This is a meaningful representation/support miss, not a reason to fabricate
an automatic youth bonus or remove Acuna from the score.

**Meadows in 2016, the largest shared harm and false high.** Age 21,
352 minor PA including 190 AA and 145 AAA, twelve HR, 32 walks and 67 K,
ranking score .91. Translated +.267 becomes control +.274 and shared +.668.
Shared's pedigree sum increases .285 to .592 and its intercept is less
negative, although its translation sum is more negative. Fixed 82.55% times
361 conditional PA leaves 298 expected PA; actual next-year PA/value are zero.
Value 1.051 to 1.250 worsens. There is no observed batting rate to label wrong
in that year. Coarse support 115 grows to 164, refined only two. Brinson 55
and Frazier 142 PA, Ramirez/McGuire zero, retain unsuccessful timing cases.
Useful eventual talent must not be mistaken for immediate delivered value.

**Eloy Jimenez in 2017, the control's false high.** Age twenty, 369 A+/AA
PA, nineteen HR, 29 walks and 72 K, ranking .97 and 40-man listing. Translated
+.493 becomes control +.630 and shared +.859; age/level and pedigree sums
increase some optimism. Fixed 92.71% times 285 conditional PA gives 264
expected PA versus zero. Value 1.031 to 1.091/1.192 worsens despite plausible
hitting talent. Immediate coarse support twelve grows to 66, refined seven.
Peers Moreno, Martinez, Yordan Alvarez and Rodgers also have zero next-year
PA. The claim is missed timing, not that later useful hitters lack talent.

**Azocar in 2021, the control's ordinary value case.** Age 25, 544 AA/AAA
PA, nine HR, 41 walks and 116 K, plus 538 AA PA in 2019. Translated -1.328,
control -1.301 and shared -1.587 compare with actual -1.499. Fixed 12.32%
times 95 conditional PA is twelve versus 216 actual. Control value .0113 is
near actual .0129; shared .0057 also small. That apparent value accuracy
does not validate arrival/workload. Coarse support 107 grows to 203,
refined 194. Casey, Beltre, Martinez and Mangum have zero PA; broad profile
support cannot identify which low-value hitter will receive opportunities.

**Frelick in 2022, the shared model's ordinary value case.** Age 22, 562
A+/AA/AAA PA, eleven HR, 49 walks and 63 K. Translated -.053 becomes
control -.004 and shared +.503 versus actual -.358. Shared's pedigree sum
increases -.080 to +.246. Fixed 81.32% times 238 PA gives 193 versus 223.
Value .588 becomes .768, nearly actual .767, but the batting forecast is
worse. Value and rate use different disclosed environment references; a
near-exact value cannot certify both hitting and workload. Coarse support
228 grows to 425, refined twenty. Meadows 145 and Canario seventeen PA,
Rosario/Norby zero, provide mixed origin-selected controls.

**Judge in 2024.** Age 32, 696/458/704 MLB PA and 62/37/58 HR. All primary
forecasts are exactly +4.534 rate, 531 expected PA and 5.668 value versus
observed +6.287, 679 and 9.393. The raw shared head would reduce rate to
about +3.898, so this cannot be sold as an all-player improvement. Immediate
coarse support 584 grows only to 592. Broad age/exposure peers Castellanos,
Suarez, Diaz and Trout are not equivalent current production. The established
anchor was deliberately retained; the public score is unchanged, not newly won.

**Maitan in 2017 and Caceres in 2024.** Maitan's 176 rookie PA have two
HR, ten unintentional walks and 49 K; Caceres's 167 DSL PA have no HR,
seventeen unintentional walks and eighteen K. Neither supplies next-year MLB
PA or an observed rate. Maitan's translated -.380 becomes control -.514
and shared -.191; Caceres -.142 becomes -.370 and -.184. Fixed expected
PA remains 1.99 and .067 respectively. Immediate level-age/baseline
coefficients are exactly zero for their unsupported rookie/DSL groups in the
control, so it has not learned those groups' true development simply because
the output looks less optimistic. Shared later labels produce small nonzero
level terms, still not immediate validation. Caceres retains global age +1.099
offset by translated -.935 and other terms; no blanket youth penalty was fitted.
Maitan has four pooled coarse people and zero refined; Caceres 53 and 45,
but both have zero direct immediate support. Vientos is Maitan's sole exact
peer; all four Caceres peers have zero next-year PA. Their later censored
outcomes cannot select a hitting winner today.

## Decision and the next substantial task

Do not promote either new arm. Preserve the translated/ranking alternative's
modest future-MLB hitting gain and keep current opportunity unchanged. This
valid comparison does not reject development modeling or long-term MLB value;
it rejects using this particular shared annual fit as a demonstrated upgrade
to the strongest next-year rate alternative.

The recurring readiness misses are larger than these rate changes. Before
another model sweep, check whether older cached source origins can extend
the actual training population for fast-track prospects. The current predictor
counts start before 2011, but eligible training origins start in 2011, so those
counts alone do not supply earlier forecast examples. Audit the older cohort's
coverage, history and target maturity before augmentation; do not cherry-pick
Trout/Harper or silently mark unavailable early histories zero. Then compare
augmented-history anchors on the same evaluation rows. This follows the
practical plan's population-coverage task and addresses support, rather than
adding another small playing-time feature or forcing hand-selected players up.

Evidence: [scores](../reports/model-evidence/hitter-shared-development/scores.json),
[nominal intervals](../reports/model-evidence/hitter-shared-development/intervals.json),
[original saved-fit traces](../reports/model-evidence/hitter-shared-development/cases.json),
[corrected observed rates and human reviews](../reports/model-evidence/hitter-shared-development/reviewed-cases.json),
[completed review](../reports/model-evidence/hitter-shared-development/final-report.json).
