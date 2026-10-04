# Team record and prospect playing time: completed comparison

2026-10-03. Do not add this feature to the current candidate. The preceding
season's MLB organization record produces a tiny, uncertain average gain, with
mixed player effects and important readiness errors unchanged. This does not
reject the idea that a team's circumstances affect prospect opportunity.

## What was tested

The [locked contract](hitter-team-record-v75-contract.md),
[dated-source repairs](hitter-team-record-v75-source-amendment.md) and
[source review](hitter-team-record-v75-source-review.md) distinguish last
batting club from year-end organization. Historical affiliations and captured
rights transactions are used; unknown rights remain unknown. Context is known
for 23,174 of 24,199 never-debut forecasts. Transaction coverage is imperfect,
particularly before 2015 and in lower levels. This is not certified complete
ownership history.

Three comparisons keep the same hitting estimate, rows and opportunity recipe:

- Current: existing fresher-ranking opportunity model.
- Coverage: add an indicator that the organization record is known.
- Record: additionally add previous-season winning percentage, centered at .500.

The indicator prevents missing affiliations from being mistaken for a .500
record. Record versus coverage is the primary contrast; record versus current
checks whether the complete addition is useful. Primary forecasts change only
never-debut players. Previously debuted players are bit-identical to current.
The separately declared all-player sensitivity is not the primary candidate.

There are 30,506 forecasts at seven origins (2016–18, 2021–24), including 24,199
never-debut forecasts and all non-arrivals. Training outcomes must be available
at origin, the entire tested player's fold is excluded, and 2020 MLB targets are
excluded. The canceled 2020 MiLB season is not treated as poor production.
The repaired 2020 roster and short MLB schedule are handled in the source.
This is exposed historical development evidence, not an untouched holdout.

All 140 full/active chronology and support checks preceded fitting. Seventy
current saved heads were replayed first, and all 140 new heads were replayed
independently after fitting. Hitting, established-player primary forecasts and
PA/value arithmetic were checked. These integrity checks do not establish
predictive merit. Refined participation profiles are absent for 112 forecasts;
active profiles for 9,644. Broad and refined support are separately saved.
Some 2016 strong-team records also exceed the training winning-percentage range.
These forecasts remain included and qualified, not removed to improve scores.
Intermediate fit/verification files retain their original pending-review state;
the final report separately records completion of all sixteen player reviews.

## Scores and uncertainty

Lower is better. Metrics give each target year equal weight; totals are raw sums.
Value is a fixed-event batting-plus-replacement proxy in custom win units,
not full WAR, six-year control value or published FanGraphs WAR. Hitting yield
is unchanged. No new batting-rate accuracy claim is made here.

| Never-debut players | PA RMSE | PA MAE | Delivered-value RMSE | Expected PA total |
| --- | ---: | ---: | ---: | ---: |
| Current | 27.2521 | 4.7639 | 0.152257 | 81,849 |
| Coverage | 27.2325 | 4.7691 | 0.152157 | 82,040 |
| Record | 27.1748 | 4.7855 | 0.152069 | 82,762 |
| Actual | — | — | — | 98,328 |

Record improves PA RMSE about 0.28% relative to current, but worsens absolute
error. The large number of zero-PA players explains why this pooled prospect
RMSE is much smaller than the public-MLB-player RMSE; they are different samples.
Upper-minors RMSE moves 55.1267 → 54.9734, but MAE 18.7321 → 18.7955 worsens.
Lower-minors RMSE moves 7.9664 → 7.9762 and MAE .6217 → .6331, both worse.
New-draftee RMSE moves 24.5140 → 24.5913, also worse.

Appearance Brier/log loss also worsen: current .019800/.070921,
coverage .019794/.070860, record .019830/.071020. Expected debutants rise
677 → 681 against 787 observed; the undercount remains. More expected debuts
is not itself better probability accuracy.

The nominal player-clustered paired 95% interval for record-minus-coverage PA
MSE is -3.136, with interval [-8.383, +1.605]. The
[shared-organization uncertainty sensitivity](hitter-team-record-v75-uncertainty-supplement.md)
widens that to [-12.347, +4.897]. Corresponding delivered-value MSE difference
is -.0000267, with crossed interval [-.0001760, +.0000979]. Record versus
current also has intervals including harm. Neither contrast establishes a
reliable gain. These are nominal development intervals, not protection against
all the project's repeated historical experimentation.

Four of seven origin PA contrasts against coverage worsen: 2016, 2017, 2018
and 2023. About 78% of the net equal-year PA MSE gain comes from origin 2024;
Miami 2024 and Chicago White Sox 2024 alone supply about 60% of the net gain.
The benefit is not solely the COVID year, but it is concentrated. The record
arm still expects 10,201 PA against 15,836 actual for the 2018 debut cohort and
10,758 against 18,944 for 2021. For origin 2023 it expects 14,745 against 11,697,
and custom value 35.10 against 5.12. This feature does not repair cohort totals.

The primary 2,627-player public comparison is unchanged by design:
138.33 PA RMSE / 106.41 MAE versus Steamer 135.38 / 92.08. The all-player record
sensitivity reaches 138.08 / 106.22, but MAE is still about 15.35% above Steamer,
outside the practical plan's 15% allowance. Public coverage/date/value-unit
qualifications from the existing benchmark continue to apply. No benchmark
threshold is waived because the point estimate improves slightly.

Conditional PA is clipped to the existing [1,800] interval. Four record-head
negative outputs occur for Junior Soto, Isaias Quiroz, Eduardo Navas and Gionti
Turner; all subsequently have zero MLB PA. They remain scored, with expected
PA .001–.011 after clipping. Coverage has two clips. This is a qualified learner
artifact, not an inferred medical explanation or a post-result exclusion.

## Sixteen actual player walkthroughs

Each following forecast is made at the end of the stated origin year and
compared with the following calendar year's MLB outcome. Full raw histories,
all model inputs, saved-tree paths, actual outputs, training support and four
origin-selected peers per case are in the evidence linked below. Probabilities
mean any MLB PA, not a successful career. Conditional PA means PA if active;
expected PA multiplies those two numbers. Hitting yield remains fixed.

The .400/.500/.600 probes change only the saved model's record input. They
illustrate mechanics, sometimes outside supported profile combinations; they
are not causal estimates of transferring a player to a different organization.
A feature's within-fit path contribution is not the total between-fit change:
refitting can change splits on many other inputs.

### Elite entrants and earlier stars

**Nick Kurtz, 2024.** Age 21, 50 A/AA PA, four HR, 12 walks and ten strikeouts;
Oakland 69–93. Current 6.06% × 168.16 conditional PA gives 10.18 expected PA.
Record gives 5.90% × 174.03 = 10.26, against 489 actual. The fixed rate is
-.063 custom wins/600; predicted value .031 against 5.838 observed. His refined
training intersection has zero participation and zero active people. Probes
give 10.26/10.26/10.45. Cam Smith received 493 PA; Quero, DeLauter and Emmanuel
Rodríguez zero. Record does essentially nothing for the elite-thin-history miss.

**Wyatt Langford, 2023.** Age 21, 200 professional PA, ten HR, 36 walks and
34 strikeouts, including 80 AA/AAA PA; Texas 90–72. Current 59.91% × 358.74
= 214.92 PA; coverage 211.00; record 58.42% × 350.93 = 205.02, versus 557
actual. Value falls .912 → .870 against 1.796 actual. Refined support is 0/0.
The direct record logit path contribution is positive even though the refitted
probability falls. Crews received 132 PA; Montgomery, DeLauter and Mayer zero.
Contender context does not resolve this readiness/conditional-workload miss.

**Julio Rodríguez, 2021.** Age 20, 340 A+/AA PA, 13 HR, 42 walks and 66 K;
Seattle 90–72. Current 80.51% × 315.63 = 254.11; record 82.32% × 317.17 =
261.09, versus 560 actual. Value rises 1.116 → 1.146 versus 3.937 actual.
Refined support is 10/8. Probes 261.03/259.81/252.50 show interaction rather
than a single record coefficient. Casas 95, Baty 42, Abrams 302 and Davis zero
show varied timing. A modest gain on a winning club leaves the major miss intact.

**Pete Alonso, 2018.** Age 23, 574 AA/AAA PA, 36 HR, 73 walks and 128 K;
Mets 77–85, with Las Vegas correctly mapped historically. Current 80.36% ×
267.58 = 215.03; record 83.41% × 268.04 = 223.59, versus 693 actual. Value
.765 → .795 versus 6.598 actual. Refined support is 4/3. Riley and Hiura
received 297/348 PA; Hayes and Yusniel Díaz zero. Slightly higher debut chance
does not solve the too-low active workload for this productive upper-minors bat.

**Cody Bellinger, 2016.** Age 20, 477 AA/AAA PA, 26 HR, 58 walks and 94 K,
following 30 A+ HR; Dodgers 91–71. Current 39.90% × 257.04 = 102.57; record
40.47% × 246.13 = 99.61, versus 548 actual. Value .331 → .321 versus 4.365.
Refined support 6/3. Probes rise 85.90/99.31/99.61 with a better record,
contradicting a universal weak-team bonus. Rosario 170, Frazier 142, Crawford
87 and Adames zero retain unsuccessful timing cases. This change hurts.

**Jackson Holliday, 2023.** Age 19, 581 A-through-AAA PA, 12 HR, 99 walks,
118 K; Baltimore 101–61. Current 88.68% × 396.01 = 351.19; record 87.61% ×
379.29 = 332.31, versus 208 actual. Refined support 14/11. Record's conditional
path contribution is -8.43 PA; probes fall 371.68/341.56/332.31. This workload
reduction is plausible and helps. But value remains +1.373 versus -.503
observed: the unchanged hitting estimate did not foresee poor production.
Chourio 573, Wood 336, Merrill 593 and Anthony zero show real timing variation.

### Low-arrival and established controls

**Kevin Maitan, 2017.** Age 17, 176 rookie PA, two HR, ten walks and 49 K.
Dated signing rights map to the Angels, 80–82, not Atlanta. Current 1.52% ×
130.37 = 1.99 PA; record 1.57% × 129.31 = 2.03, versus zero actual. Refined
support 2/0. Infante, Cruz, Caraballo and Verbel also had zero MLB PA. A very
low immediate arrival chance is reasonable; next-year non-arrival says little
about whether a model properly prices a teenager's long-term talent.

**Aaron Judge, 2024.** Age 32, 696/458/704 MLB PA and 62/37/58 HR over the
three seasons; Yankees 94–68. Primary current, coverage and record are exactly
the same: 99.07% × 535.74 = 530.75 PA versus 679 actual; custom value 5.668
versus 9.393. The latter is not published full WAR. The all-player sensitivity
gives 530.91 PA. Refined support 657/512 does not establish superstar-specific
support. Flores, Vargas, Suárez and Enrique Hernández are broad controls,
not comparable hitting talent; they cannot explain away Judge's miss.

### Selected gains, harms, false highs/lows and ordinary cases

**Brendan Rodgers, 2017.** Age 20, 400 A+/AA PA, 18 HR, 14 walks and 71 K;
Colorado 87–75. Current 64.57% × 343.25 = 221.63 PA. Coverage reduces it to
198.05, the largest coverage gain; record raises it to 71.06% × 328.98 =
233.77 against zero actual, reversing that benefit. Value rises .655 → .691
against zero. Refined support 6/4. Peers Eloy zero, Tucker 72, Urías 53 and
Torres 484 show mixed timing. Keep this false-high harm in the decision.

**Bobby Witt Jr., 2021.** Age 21, 564 AA/AAA PA, 33 HR, 50 walks and 131 K;
Kansas City 74–88. Current 77.90% × 357.90 = 278.80; coverage 268.61, its
largest harm; record 75.48% × 362.57 = 273.68 versus 632 actual. Value
1.011 → .992 versus 1.675 actual. Refined support 11/7. Direct record-path
effects are tiny, so larger between-fit changes are not a standalone record
effect. Torkelson 404, Greene 418, Thomas 411 and Davis zero show uncertainty.
The existing workload underestimate remains much larger than this adjustment.

**J.P. Crawford, 2016.** Age 21, 551 AA/AAA PA, seven HR, 72 walks and 80 K;
Philadelphia 71–91. Current 85.33% × 448.93 = 383.05; record 85.11% × 442.35
= 376.50 versus 87 actual. Value .870 → .855 versus .191 actual. Refined
support 5/4. Rosario 170, Frazier 142, Happ 413 and Adames zero are timing
controls. Record slightly reduces a false high but leaves approximately 290
excess PA. A weak organization does not guarantee a full MLB season.

**Bryan Reynolds, 2018.** Age 23, 383 AA PA, seven HR, 40 walks and 73 K,
following 541 A+ PA; Pittsburgh 82–79. Current 15.64% × 81.02 = 12.67 PA;
record 18.77% × 74.36 = 13.96 versus 546 actual. Value .030 → .033 versus
4.696 actual. Refined support 778/101 is substantial for the coarse intersection,
yet both heads severely miss. Boykin, Pinto, Navarreto and Gore had zero future
PA, but are not matched on performance or AA exposure. Their outcomes do not
explain away Reynolds. This remains a substantive talent/readiness miss.

**Drew Waters, 2021.** Age 22, 459 AAA PA, 11 HR, 47 walks and 142 K;
Atlanta 88–73. Current 65.89% × 165.56 = 109.08; record 65.63% × 161.51 =
106.01 versus 109 actual. Value .429 → .417 versus .593. Refined support
279/62. Probes decrease with stronger records, but the realized prediction is
slightly less accurate than current. Morel 425, Suwinski 372, Wilson zero and
Amaya zero retain ordinary variation. Current already handles this case well.

**Agustín Ramírez, 2024.** Age 22, 548 AA/AAA PA, 25 HR, 60 walks and 102 K;
dated trade rights place him in Miami, 62–100. Current 84.88% × 133.02 =
112.91; coverage 110.05; record 83.18% × 171.52 = 142.68 versus 585 actual.
Value .206 → .261 versus 1.437 actual. Refined support 237/47. Record's
conditional path adds 21.57 PA; probes give 134.70/118.33/119.51, supporting
a modest weak-team workload lift. Still 442 PA short. Anderson, Simpson,
Sanabria and Workinger are broad peers with zero future PA, not equivalent
upper-minors readiness. A helpful example is not a repaired forecast.

**Nick Senzel, 2018.** Age 23, 193 AAA PA, six HR, 18 walks and 39 K after
507 A+/AA PA; Cincinnati 67–95. Current 75.11% × 389.01 = 292.18; record
62.74% × 381.53 = 239.39 versus 414 actual: the largest incremental record
harm. Value .811 → .664 versus 1.457 actual. Refined support 0/0. Direct
record logit contribution -.442 and probes 239.39/283.52/287.60 reduce arrival
on a weaker club. Murphy 60, Eloy 504, Yordan 369 and Rodgers 81 show varied
timing. Do not invent a Cincinnati decision to rationalize an unsupported harm.

**Dawel Lugo, 2017.** Age 22, 557 AA PA, 13 HR, 32 walks and 72 K;
Detroit 64–98. Current 69.31% × 118.16 = 81.90; record 68.20% × 144.91 =
98.83 versus 101 actual. Refined support 114/27. Record's conditional path
adds 28.03 PA and probes 98.83/80.55/79.03 fit a weak-team workload lift.
But value rises .161 → .194 versus -.235 actual: a better PA forecast makes
value worse because fixed batting yield is too optimistic. Guillorme 74 and
Erceg/Lund/Dubón zero preserve non-arrivals. PA improvement alone is not a
whole-model value improvement.

## Review limits, decision and next work

Peers were selected without future outcomes, within origin/stage/debut status,
using age, minor PA and rank. This avoids cherry-picking only successful players,
but does not establish comparable performance, exact level exposure, position
or star talent. Keep these controls visible, and do not use their zero outcomes
as explanations for Reynolds or Ramírez. Subsequent player reviews should show
those omitted dimensions explicitly when claiming close comparability.

The model can learn different record interactions rather than being forced to
give every weak-team prospect a boost. Nevertheless, mixed directions, sparse
intersections and concentrated uncertain gains do not justify adopting this
particular addition. This experiment tests previous-season record, not current
season standings, deadline decisions or actual roster openings. Those concepts
are not disproved. No extra record tuning or context-feature sweep is authorized
by this small result.

Keep V68 opportunity and V53/V63 hitting/value as the research candidate. Resume
the practical plan's bounded delivered-value integration comparison, with
explicit rate/count units, unchanged anchors and all non-arrivals. PA-weighted
rate estimation can already encode workload/performance dependence; do not
assume multiplying its output by expected PA is intrinsically invalid. Compare
alternative constructions because finite fits and actual misses may differ,
not because decomposition alone proves independence.

The whole goal remains active. Protected 2026 outcomes, frozen forecast and
deployment are unchanged. No source or execution pass waives the outstanding
benchmark, cohort and baseball-reasonability gaps.

Evidence: [scores](../reports/model-evidence/hitter-team-record-v75/scores.json),
[paired intervals](../reports/model-evidence/hitter-team-record-v75/intervals.json),
[shared-context intervals](../reports/model-evidence/hitter-team-record-v75/crossed-intervals.json),
[organization-year losses](../reports/model-evidence/hitter-team-record-v75/organization-year-losses.json),
[complete stats/input/model traces](../reports/model-evidence/hitter-team-record-v75/cases.json),
[reviewed cases](../reports/model-evidence/hitter-team-record-v75/reviewed-cases.json),
[verification](../reports/model-evidence/hitter-team-record-v75/verification.json),
[final report](../reports/model-evidence/hitter-team-record-v75/report.json).
