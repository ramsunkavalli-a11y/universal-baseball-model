# What minor fielding counts tell us about later MLB range

The new count recipe is not ready to use in player valuations. Its small overall
loss hides two different issues: the tuning often weakens the existing position
expectation, and the count reliability can be unstable in tiny samples. Neither
issue supports a blanket conclusion that minor fielding statistics are useless.
The existing MLB-history range baseline remains the stronger research building
block for players with major-league defensive experience. No frozen forecast or
explorer changed.

## The question actually tested

At the end of 2021 or 2022, use minor-league fielding evidence to estimate range
at the same position during the next three calendar years in MLB. Players with
prior or current MLB fielding are excluded. The baseline uses age, position,
principal minor level and defensive innings. The candidate adds error avoidance,
throwing-error avoidance, infield assists and outfield putouts relative to dated
level/age expectations, with estimated sample-size regression.

This recipe uses the player's current season, not his whole defensive history.
Assists and putouts are opportunity proxies, not adjusted chances to make plays.
It does not include batted-ball location, pitcher mix, park context, other-position
talent, arm value, double-play skill, receiving or catcher defense. Error avoidance
need not explain all of a tracking-based range target.

The label requires two measured MLB seasons and at least 500 defensive innings
over the window, with valid annual measurement wherever official exposure is
positive. Unknown quality stays unknown. This is a conditional talent comparison
among measured arrivals, not a test of every minor leaguer's eventual ability,
next-year delivered defense, full WAR or trade value.

## What the fixed comparison found

All 13,133 origin-position forecasts remain in the evidence. The primary 2022
cohort has 6,547 forecasts but only 71 measured positions from 62 distinct people.
The 2021 stress cohort has 6,586 forecasts and 94 measured positions from 83 people.
Each measured person has equal total weight, split across his positions.

| Forecast origin | Neutral range error | Age position level baseline error | Selected count recipe error |
| --- | ---: | ---: | ---: |
| 2022 primary | 3.047 | 2.732 | 2.753 |
| 2021 stress | 3.136 | 3.012 | 3.110 |

Errors are RMSE in native range runs per 500 defensive innings. The selected
count recipe is 0.78% worse in 2022 and 3.28% worse in 2021. In 2022 its average
absolute error improves from 2.211 to 2.169, but the paired intervals include no
change: RMSE difference −0.149 to +0.197; absolute-error difference −0.191 to
+0.099. In 2021 absolute error worsens from 2.362 to 2.481. These are development
results, not protected confirmation or overall player-value gains.

Center field is the clearest group harm: 14 measured people, RMSE 3.581 to 3.922,
9.5% worse. Shortstop improves from 3.155 to 3.012 and second base from 2.539 to
2.492. Those groups are small; do not choose separate recipes after seeing them.
The candidate fails the predeclared improvement screen and is not promoted.

## Most center field downgrades come from tuning rather than counts

Both arms tune their regression penalty on earlier completed, held-player
cohorts. The penalty pulls fitted effects toward average. In 2022 every baseline
selects penalty 10; four of five count folds select the stronger penalty 100.
That stronger penalty also weakens age, position and level effects, not just the
new count effects. Earlier tuning has only 52–63 measured people per outer fold,
despite thousands of retained unknown-quality forecast rows.

For Jacob Young the selected estimate drops 2.272 to 0.663. Of that −1.609 change,
−1.566 comes from changing the baseline penalty and only −0.043 from the count
recipe at a matched penalty. The same distinction explains most of Rafaela's,
Meadows's and Wiemer's center-field downgrades. This is not a numerical execution
bug: it is a modeling tradeoff that makes the headline unsuitable for attributing
the loss solely to the added baseball information.

The saved, already fitted arms allow a diagnostic at equal penalties. With
penalty 10, 2022 RMSE improves 2.732 to 2.666 and absolute error 2.211 to 2.112.
With penalty 100, RMSE improves 2.895 to 2.872. Both equal-penalty comparisons
worsen in 2021. These exposed diagnostics explain the recipe; they are not a
new winning candidate, a retuning decision or proof that a repair will work.

## Actual players show what works and what is missing

The [full walkthrough](../reports/model-evidence/defense-minor-range-v19/player-walkthrough.md)
contains 11 focal selections and 33 origin-selected peer comparisons, covering
41 distinct player-origins and all 106 of their modeled positions. Every selected
reference mean, variance and sample weight is recomputed from raw counts, not
accepted from the feature generator. Annual MLB paths are independently replayed.
Bryce Eldridge has no eligible 2021/2022 origin and is not forced into this test.

- **Volpe:** 13 errors, eight throwing, in 449 AA/AAA shortstop chances in 2022.
  Baseline −0.615 becomes +0.071; later pooled range is +0.772. At a matched
  penalty, the count recipe accounts for +0.272 of the +0.686 change. His AA
  nonthrowing-error avoidance is favorable. AAA variation estimates erase its
  count signal. Peers Mauricio and Tena do not have qualifying later SS exposure;
  Rocchio does, at +0.222. An improved Volpe forecast does not certify the others.
- **Neto, largest gain:** 11 errors, five throwing, in 137 AA/High-A chances.
  +0.288 becomes −1.383 versus later −1.438. The penalties are the same here.
  Unfavorable error signals contribute to the downgrade, but the fitted assist
  coefficient is negative and penalizes his above-reference assists too. That
  sign can reflect missing context rather than a baseball rule. Peer Rafaela's
  shortstop grade moves the wrong way; Rodríguez and Ozoria lack measured SS
  quality. Neto's gain is not permission to label every high-assist player worse.
- **Jacob Young, largest deterioration and false low:** zero errors in 116
  Single-A CF chances. All three count signals receive zero reliability because
  estimated reference variation after count noise is nonpositive. The selected
  model nevertheless drops +2.272 to +0.663, almost entirely due to the penalty.
  His later annual range rates are +4.85, +7.31 and +7.11; pooled quality +6.952.
  Only five earlier training people share level/position and one shares the full
  profile. His nearest peers Flores, Cerny and Allen never supply MLB CF quality.
- **Rafaela:** two errors in 211 AA/High-A CF chances; all CF count signals are
  erased by zero-reliability estimates. +1.259 becomes +0.447 against +6.657.
  His SS grade is separately +0.552 against −4.317 and has an out-of-range assist
  input. His CF success cannot validate that SS forecast. Barrosa has only 360
  future CF outs; Mears and Doston have none. They remain unknown, not average.
- **Witt:** eight errors in 322 AA/AAA SS chances in 2021. −0.200 becomes −0.060
  against +2.033. His native annual rate changes from −4.17 in his first MLB year
  to +3.81 and +4.07. A near-average expectation misses that development. Arias
  has a positive qualifying label; Downs has just 78 future SS outs; Perez has
  none. The model has only two earlier AAA/SS people in Witt's held fold.
- **Peña:** four nonthrowing errors in 116 AAA/complex SS chances. +0.437 becomes
  +0.148 against +0.533. The AAA count signal is zero and most of the downgrade
  is the penalty. His annual rates decline from +1.99 to +0.58 to −0.73. Estevez
  and Davis never supply same-position MLB quality; Fox's 156 outs are too few.
- **Abrams:** four errors, two throwing, in 126 AA SS chances. +0.128 becomes
  +0.254 against −4.299, with negative range in all three MLB seasons. Rocchio
  develops a positive pooled label; Barreto has no MLB fielding and Groshans
  moves to 3B. Similar age/level plus a few errors do not distinguish all talent.
- **Edwards, largest false high at SS:** just 71 AAA SS chances; +0.122 becomes
  +0.134 against −6.840. There are only three earlier AAA/SS training people and
  zero exact-profile matches. His primary-origin 2B label is unknown because 27
  positive 2024 outs lack native measurement. Later 2B evidence does not fix SS.
  Turang moves mostly to 2B; Wyatt Young and Hernandez have no later MLB SS label.
- **Canzone, ordinary median-error selection:** +0.039 becomes +0.198 against
  −1.584 at RF. The review also catches an unstable input: six error-free complex
  chances receive 94.5% reliability. Two reference people each have one error in
  one chance, inflating the between-record variation. This weight is not 94.5%
  confidence in his MLB talent. Fletcher has 1,479 future RF outs, just below the
  unchanged quality cutoff; Leon has a cameo and Cedrola none.
- **Pabst, sparse unsupported-level case:** 28 error-free complex 1B chances,
  96 outs. With no earlier supervised level-position example, both arms use the
  same +0.465 baseline. It is an uncertain borrowed prior, not proven 1B ability
  or receiving talent. Goldfarb, Schreiber and Melo likewise lack later quality.

## A good score can miss a bad extrapolation

The supplemental all-forecast check finds **Patrick Frick at −13.308** range
runs per 500 innings from 16 AA third-base chances: six errors, five nonthrowing.
The nonthrowing-error input lies outside supervised training bounds and is about
26 training standard deviations below its mean. Its fitted contribution alone is
−13.545. Only one exact-profile training person exists. His origin-selected
peers Sanchez, Rodriguez and Reyes receive +2.107, −4.520 and +0.661; none supplies
later MLB fielding. These grades are unvalidated extrapolations, not confirmed
talent assessments. A warning flag is not a practical repair.

There are 2,930 out-of-range forecasts in 2022 but only four out-of-range measured
positions. Also 3,098 forecasts have no supervised level-position example and
receive matched baseline fallbacks. Conditional-quality scoring cannot detect
most extreme errors among non-arrivals. Sparse lower-level talent needs a
defensible prior and uncertainty, not an apparently precise unsupported grade.

## What is verified and what remains open

Independent checks replay all 13,133 forecast identities, exact outer/inner
memberships, chronology, held-person exclusion, source-trace arithmetic, support
and input-range flags, 184 fitted parameter sets, tuning choices, scores and
paired intervals. Seventy unique cells have 90 logged uses because identical
2018 internal cells are shared across the two outer origins. They are not double
counted within a tuning comparison. Twenty-eight focused unit tests pass.
Selected walks replay 488 raw reference calculations; the supplemental extremes
are checked too. Execution integrity passes; predictive/reasonability approval
does not follow from it.

The earlier count-audit prose said 63 distinct measurable 2022 prospects. The
correct global count is 62. Its per-level counts sum to 63 because Davis Schneider
supplies positions with AA and High-A principal levels. This is an additive prose
correction; the sealed source rows, support cells and fitted populations are
unchanged.

The disk-full run and two recovery wrappers remain documented. Completed JSON
evidence is losslessly compressed; canonical receipt hashes refer to decompressed
bytes. The independent walk initially misread a certified one-out annual rounding
difference as missing exposure, then shadowed a local variable; both review-code
issues were corrected before any walkthrough artifact was saved. No statistical
recipe, target or completed fit was changed to repair them.

## Decision and next step

Do not promote this count recipe or discard the underlying count information.
Keep the useful MLB-history range baseline and mark sparse prospect estimates
as uncertain. Do not replace a missed development curve with zero talent.

Next repair the count-reliability calculation and its extrapolation behavior
before any new future-MLB fit. Then test an incremental count correction that
cannot silently change the existing age/position baseline's regression penalty.
Its contract must preserve chronology, unknown outcomes, same players, all-level
coverage and player walkthroughs. No selecting penalty 10 because it happened to
look better here. The [repair sequence](defense-minor-range-repair-sequence.md)
keeps this specific work tied to later MLB ability and eventual value integration.
Catcher training history, position transfers, longer-path lower-minor ability
and delivered-value integration remain unfinished; the full goal stays active.
