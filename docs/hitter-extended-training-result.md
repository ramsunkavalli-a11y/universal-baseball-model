# Earlier training helps some forecasts but does not fix prospect readiness

2026-10-04. Keep the current research candidate. Adding the reviewed 2008–2010
origins improves some batting-rate and arrival estimates, but the whole-value
gain is tiny and uncertain, ordinary playing-time error worsens, and important
prospect forecasts deteriorate. The repaired histories are useful available
data, not a validated replacement model. All fourteen player walkthroughs below
are complete; this decision is not based on the pooled score alone.

## What changed and what stayed fixed

The [predeclared comparison](hitter-extended-training-contract.md) uses all
30,506 existing forecasts, seven historical origins and 11,020 people. The
restricted arm uses the original 63,282 source rows; the extended arm adds
every reviewed 2008–2010 row, including failures and inactive players, for
76,639 source rows. Outcomes are next-calendar-year MLB PA and batting, not
same-level minor-league performance or six years of control.

Both arms use the same histogram appearance/active-PA models and the same
PA-weighted Ridge hitting model. Their 253/201 inputs are the existing 251/199
plus two explicit source-coverage flags. Missing 2008 roster information is
unknown, not nonlisting. Missing early ranks are unknown, not unranked; origin
2010 can use the certified 2011 top-50 list. Early lagged batting quality and
games reconcile independently with existing definitions. Current inputs and
evaluation labels remain exact. Original and translated/ranking forecasts stay
as separate anchors. No post-result rerouting or parameter tuning occurred.

All 210 actual chronological/held-player/head preflights precede fitting.
Every saved head replays. The restricted classifier and conditional PA outputs
are exactly current; maximum Ridge difference is 2e-15. Thus the restricted
control does not secretly change the recipe. Complete original columns remain
unchanged in saved predictions. These execution checks establish a fair
comparison, not model adequacy.

Earlier source construction retains its documented coverage and soft-listing
limitations. The runner consumes sealed tables and uses its own static level
mapping, without importing the unrelated dirty source-mapping module. It does
not recertify that older source builder as a self-contained bare-checkout build.
The observed absence of historical MLB records is still not an official
never-debut certificate before 2004. No later debut category becomes a predictor.

## Matched results

Lower error is better. Each target year receives equal weight; batting-rate
error uses actual PA within year. Totals below are raw across all seven years.
Value is fixed-event batting plus replacement in custom win units, **not full
WAR**. The rate labels are centered on realized target-season MLB average;
delivered value uses the unchanged common-origin environment. Inactive players
have no observed batting rate and are excluded only from conditional-rate scores,
not from PA, arrival or value scores.

| Population and metric | Current and restricted | Extended | Actual |
| --- | ---: | ---: | ---: |
| All players PA RMSE | 60.4991 | 60.2940 | — |
| All players PA MAE | 20.6124 | 20.7140 | — |
| All players value RMSE | .453379 | .453136 | — |
| All players PA total | 1,228,733 | 1,243,094 | 1,270,493 |
| Never-debut PA RMSE | 27.2521 | 27.0350 | — |
| Never-debut PA MAE | 4.7639 | 4.8701 | — |
| Never-debut rate RMSE | 2.61438 | 2.59872 | — |
| Never-debut value RMSE | .152257 | .152099 | — |
| Never-debut PA total | 81,849 | 86,212 | 98,328 |
| Expected debutants | 677.0 | 701.6 | 787 |

The aggregate PA RMSE gain is about .34%; prospect PA RMSE improves .80%,
but prospect MAE worsens 2.23%. Whole-model value RMSE improves about .05%.
The nominal player-clustered extended-minus-restricted value-MSE interval is
[-.0013600, +.0009567]; prospect value interval [-.0003185, +.0002137]. Neither
establishes a reliable whole-value gain. The all-player PA interval also crosses
zero. More data are not automatically better forecasts.

The prospect batting-rate MSE difference is -.08167, interval
[-.13242, -.03930]: this is useful positive development evidence. But the
previously reviewed translated/ranking anchor still has lower prospect rate
RMSE, 2.58308, and lower prospect value RMSE, .151662. Extended-minus-translated
prospect value MSE is +.0001327, with an interval crossing zero. We therefore do
not discard the older data or claim their rate benefit is meaningless; we also
do not replace the better-reviewed alternative with a weaker point estimate.
These are exposed historical results and nominal intervals, not fresh holdouts.

Appearance Brier/log loss improve for all players, .033540/.114736 to
.033409/.114263, and prospects, .019800/.070921 to .019648/.070405. Lower-minors
appearance scores worsen. Both restricted and extended have two active-PA
outputs clipped at the existing lower bound; neither exceeds 800. No players
are removed or tuned because a prediction was clipped.

## Cohorts and the public benchmark

Upper-minors prospect PA rises 74,239 to 77,381 against 92,891 actual. Lower-minors
PA rises 7,055 to 8,262 against only 5,194 actual: a closer grand total conceals
a worse lower-minors overforecast. Lower-minors PA MAE rises .6217 to .6911.
Their value total rises 19.47 to 22.55 against 9.56 actual.

Prospect PA RMSE improves at five of seven origins, but worsens for 2018 and
2023. Prospect value error worsens in 2018, 2021 and 2023. The 2021 PA total
improves 10,432 to 11,640 but remains below 18,944 actual; this is not a solved
COVID correction. In 2023 the model forecasts 15,165 prospect PA against 11,697,
and 35.61 custom wins against 5.12. That non-COVID failure remains important.

On the unchanged 2,627-player public sample, extended PA RMSE/MAE are
138.10/106.72, versus current 138.33/106.41 and Steamer 135.38/92.08.
Extended MAE is 15.90% above Steamer, outside the plan's 15% allowance; do not
waive the target for a small RMSE improvement. Public value RMSE is 1.06093
versus current 1.06050 and raw-converted Steamer 1.11866. Public conversion
environment offsets and snapshot-date qualifications remain; the latter number
is not proof of superior UBM hitting talent or full WAR projection.

## Fourteen actual player walkthroughs

Each forecast uses statistics through the named origin and is compared with
the following calendar year's MLB outcome. Arrival means any MLB PA;
expected PA equals appearance probability times active PA. Rate is custom
batting wins above average per 600 PA, not total WAR/600. Full source lines,
all actual inputs, saved Ridge terms and exact tree paths are in
[the case evidence](../reports/model-evidence/hitter-extended-training/cases.json).
Tree path contributions explain a saved fit, not causality or proof that a
single earlier player changed the refitted model.

**Nick Kurtz, 2024:** age 21; 50 A/AA PA, four HR, twelve walks, ten K.
Rank .63 and draft pick are present. Appearance falls 6.06% to 3.87%; active PA
rises 168 to 176, so expected PA falls 10.18 to 6.81 versus 489 actual. Rank
is a positive saved-tree contribution in both fits, but weaker in the extended
classifier. Rate -.063 to .041 remains far below 5.150 actual. Refined active
support stays zero despite broad support 15 to 20. Strict level peers lack
equivalent elite pedigree; their non-arrival cannot justify Kurtz's miss.

**Wyatt Langford, 2023:** age 21; 200 PA including 54 AA/26 AAA, ten HR,
36 walks, 34 K and .95 rank. Every level enters the model, despite dominant
A-plus in the review label. Arrival 59.91% to 51.07% and active PA 359 to 321
reduce expected PA 215 to 164 versus 557. The conditional rank path falls
147 to 128 PA and the zero-current-MLB-work path becomes more negative.
Rate .688 to .823 moves away from .549 actual. Refined active support stays
zero. Earlier Belt has comparable split exposure, not identical draft or talent.

**Pete Alonso, 2018:** age 23; 574 AA/AAA PA, 36 HR, 73 walks and 128 K.
Arrival stays about 80%, but active PA 268 to 263 leaves expected PA 211 versus
693 actual. Zero current MLB exposure remains a large negative conditional
path; rank and AAA power contribute positively. Rate .286 to .221 also moves
away from 3.283 actual. Broad active support rises 48 to 60, refined stays
seven. Thaiss, VanMeter, Mercado and Walsh had 164/260/482/87 PA; their varied
timing does not make Alonso's large underforecast satisfactory.

**Ronald Acuna Jr., 2017:** age 19; 612 A-plus/AA/AAA PA, 21 HR, 43 walks,
144 K and unchanged .99 rank. Appearance rises 48.22% to 71.07%, active PA
211 to 243 and expected PA 102 to 173, closer to 487 actual. Saved paths
redistribute AA exposure, games and age effects; rank was not missing before.
One active teenage-AAA person, Montero 2010, enters the actual fold, compared
with none previously. Only two strict forecast peers exist. Rate .164 to .170
still misses 3.681, so this is a partial readiness gain, not solved star talent.

**Julio Rodriguez, 2021:** age 20; 340 A-plus/AA PA, thirteen HR, 42 walks,
66 K, with the canceled MiLB year explicitly represented. Listing and .98/.96
ranks are present. Expected PA falls 254 to 211 versus 560. The current-rank
conditional lift stays near 96 PA, but the prior-rank lift shrinks and the zero
MLB-work penalty grows. Rate .754 to .766 barely improves against 2.683.
Refined active support stays nine. This is a harm, not an absent-rank bug.

**Jackson Holliday, 2023:** age 19; 581 PA across A through AAA, twelve HR,
99 walks, 118 K and rank one. Appearance 88.68% to 90.90% and active PA
396 to 417 increase expected PA 351 to 379 versus 208. The current-rank
conditional path grows; rate .621 to .600 is marginally closer to -2.838 but
still optimistic. Value rises 1.451 to 1.552 against -.503. Earlier Heyward's
623 PA demonstrate a successful path, not that Holliday must follow it.

**Aaron Judge, 2024:** age 32; 696/458/704 MLB PA with 62/37/58 HR.
Appearance is already over 99%; higher active PA 536 to 570 raises expected PA
531 to 566, closer to 679. Trees use recent workload, quality and PA/game;
Ridge uses pooled and recent batting quality. Rate 4.534 to 4.500 worsens
slightly against 6.287. Value 5.668 to 6.010 still understates 9.393. Broad
MLB support is plentiful, but cannot certify Judge-specific superstar support.

**Hector Martinez, 2016:** age 17; 204 DSL PA, four HR, 33 walks, 49 K after
186 DSL PA. Both immediate arrival chances are around .1%, expected PA .089
to .108, actual zero. Conditional PA rises 59 to 83 with no active DSL profile
support. Rate .347 to .449 mostly reflects age and generic effects; actual
rate is null. Four DSL peers also have zero next-year PA. This is evidence of
immediate rarity, not a validated estimate of lifetime MLB talent.

**Nelson Cruz, 2018, largest value gain:** age 37; 667/645/591 MLB PA with
43/39/37 HR. Appearance 61.83% to 75.24%, with active PA nearly unchanged,
raises expected PA 274 to 336 versus 521. Soft nonlisting is a negative
classifier path; refitting redistributes listing, games, workload and age
effects. A productive unsigned veteran is not known unavailable. Rate 1.683
to 1.808 still misses 4.779; value 1.613 to 2.048 remains far below 6.260.
Complete preseason contract/employment information is not in this branch.

**Jose Bautista, 2016, largest value harm:** age 35; 673/666/517 MLB PA and
35/40/22 HR. Appearance 53.70% to 89.45% raises expected PA 270 to 455,
**closer to 686 actual**. Yet rate 2.277/2.307 is much too high versus -1.223,
so value rises 1.861 to 3.157 against .979. Better workload makes value worse
because estimated hitting yield is wrong. This is not evidence that the PA
direction is bad, or that multiplying a PA-weighted rate estimate by expected
PA inherently assumes independence. Finite models can still combine badly.

**Chris Davis, 2017, largest false high:** 47/38/26 HR and 670/665/524 MLB PA,
with high strikeouts and reduced recent quality. Both fits correctly give high
appearance and roughly 500 PA. Extended expected PA 481 is slightly worse
than 503 against 522. Rate remains +1.08 against -3.68, producing +2.345 value
versus -1.963. Ridge retains positive pooled-quality and workload terms.
The miss is mostly a talent collapse, not arrival; this comparison cannot
establish how predictable the full collapse was beforehand.

**Aaron Judge, 2016, largest false low:** 410 AAA PA with nineteen HR,
47 walks, 98 K, plus 95 MLB PA with four HR/42 K. Appearance is already over
92%, but active PA falls 335 to 317, leaving expected PA 297 versus 678.
Rank stays positive while the low-current-MLB path becomes more negative.
Rate -.040 to .018 still misses the 5.330 breakout. Refined support stays one;
Moreland and Renfroe illustrate possible workloads, not guaranteed breakouts.

**Travis Demeritte, 2018, selected ordinary by value error:** 494 AA PA,
seventeen HR, 56 walks, 140 K after 511 AA and 530 A-plus PA. Appearance
9.42% to 6.28% lowers expected PA 9.14 to 5.65 versus 186. Rate -.325 to
-.397 is also too optimistic versus -2.379. Nonetheless value .0232 to .0137
nearly matches .0157 actual. This is **not a well-predicted player**: low
exposure accidentally offsets overly optimistic hitting. The walkthrough
catches a lucky combined forecast that aggregate value scoring would reward.

**Cody Bellinger, 2016, largest prospect harm:** age 20; 465 AA/twelve AAA PA,
26 combined HR, 58 walks, 94 K after thirty A-plus HR. Rank .88 and all split
counts are present. Arrival 39.90% to 25.71% and active PA 257 to 178 lower
expected PA 103 to 46 versus 548. The zero-current-MLB penalty grows; tiny-AAA
PA/game gets an unfavorable path. Rate .085 to .066 also worsens versus 2.700.
Refined active support stays five. Moustakas 365 and Mesoraco 53 PA demonstrate
different timing, not justification for this substantial deterioration.

Peers are selected without future outcomes, matching origin, age, participation,
dominant/highest level and distance on PA, performance, position and pedigree.
Strict intersections sometimes leave only two peers or peers with weaker
pedigree. They are controls, not proof of equal talent. Outcome-selected gain,
harm and false-high/low cases are diagnostics, not independent confirmation.

## Decision and next work

Do not promote the extended arm or choose a post-result hybrid. Retain the
current opportunity model and the reviewed translated/ranking hitting alternative
as separate anchors. Keep the repaired earlier inputs available for the next
matched construction; this result does not reject historical training data.

The central remaining problem is readiness and workload for advancing hitters,
plus hitting-tail errors—not another missing rank join or a presumed single
2021 anomaly. The next comparison should examine an explicitly separated
prospect/readiness workload construction against the current pooled active-PA
head, using the same complete counts and origin-known pedigree. First reconcile
the earlier direct/class-conditional workload experiments to avoid rerunning the
same architecture under a new name. Lock any genuinely different contrast and
training support before fitting. Keep the cohort/public errors and Demeritte/
Bautista cancellation warnings alongside delivered-value scores.

Execution note: scoring encountered two NumPy/Polars type-interface errors
before saving outputs; these were fixed without refitting any model. It then
saved the complete verified scores but its final console print failed on a
missing import. The import is fixed; the read-only `show` command verifies the
unchanged saved hashes. No score, case or fit was overwritten to hide a result.

No protected 2026 outcomes, frozen forecasts or deployed explorer were changed.
The full practical hitter goal remains active. This experiment does not deliver
complete defense, control-year valuation or a satisfactory final model.

Evidence: [scores](../reports/model-evidence/hitter-extended-training/scores.json),
[intervals](../reports/model-evidence/hitter-extended-training/intervals.json),
[preflight summary](../reports/model-evidence/hitter-extended-training/preflight-summary.json),
[actual model cases](../reports/model-evidence/hitter-extended-training/cases.json),
[reviewed assessments](../reports/model-evidence/hitter-extended-training/reviewed-cases.json),
[verification](../reports/model-evidence/hitter-extended-training/verification.json)
and [final experiment report](../reports/model-evidence/hitter-extended-training/final-report.json).
