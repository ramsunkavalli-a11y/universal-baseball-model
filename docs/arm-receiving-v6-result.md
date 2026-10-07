# Arm and first base receiving talent baselines

Two more defensive components now have explicit research estimates: an outfield
arm baseline and a first-base receiving baseline. Both use actual opportunities,
recent adjusted results and direct small-sample shrinkage. They do not yet add
runs to the selected hitter forecast or establish minor-league defensive talent.

## What the comparison found

The 2022-origin comparison predicts pooled 2023–2025 MLB skill. Arm error is
0.605 runs per 100 opportunities for neutral defense and 0.573 for history,
about 5.2% lower. Receiving error is 0.370 versus 0.359, about 2.9% lower.
Both paired 95% intervals include no improvement: arm RMSE change -0.0315
[-0.1514, +0.0967], receiving -0.0108 [-0.0952, +0.0646].

These are narrow talent comparisons: 47 of 488 origin-eligible arm players and
18 of 246 receiving players meet the predeclared later-quality requirement.
Exits, short samples and mixed arm positions stay unknown quality, not poor
defense. Each forecast remains in coverage reporting. The arm history point
estimate improves in all six complete origins, but repeated players and
survivor selection limit that evidence. Receiving loses at the earlier 2021
origin, 0.342 versus 0.357. Its short source history supports no mature learned
age model at 2022. None was fitted.

Young arm players are a real failure, not a microscopic veto: among 20 measured
players aged at most 24, error rises from 0.527 to 0.635. The 23-player age
25–29 group improves from 0.615 to 0.496. That does not establish an age curve;
it qualifies a pooled average that would otherwise conceal the young misses.

Using actual later opportunities only as a diagnostic, arm history awards
-0.27 runs against -34.42 observed in the measured cohort. Receiving gives
+19.15 against +44.58. Thus these estimates alone do not settle cohort value
calibration or forecast future opportunity. Full player-value integration remains
unfinished.

## Player checks explain the successes and misses

All figures below are adjusted runs per 100 actual channel opportunities.

| Component and player | Historical estimate | Later measured quality | Meaning |
| --- | ---: | ---: | --- |
| Arm Castellanos | -0.520 | -1.120 | Poor history helps, but understates later weakness |
| Arm Laureano | +0.657 | +1.746 | Positive evidence helps, still shrinks heavily |
| Arm Nootbaar | +0.972 | -0.494 | Strong past result reverses; largest deterioration |
| Arm Kwan | -0.301 | +0.876 | Development or variation defeats the old negative record |
| Arm Happ | -0.148 | +0.279 | Later improvement is missed |
| Receiving Olson | +0.469 | +0.481 | Useful persistent history |
| Receiving Freeman | +0.321 | +0.600 | Direction holds; strong shrinkage understates quality |
| Receiving Walker | -0.062 | +0.440 | Earlier negative record misses later improvement |
| Receiving Alonso | -0.071 | +0.527 | Another reversal, not proof history is useless |
| Receiving Lowe | +0.251 | -0.306 | Largest receiving deterioration |
| Receiving Smith | +0.041 | +0.715 | Only 96.5 weighted prior throws leave little evidence |

Judge's later 582 arm opportunities fall just below the locked 600-opportunity
threshold; Kiermaier has 477. That is a measurement restriction, not a judgment
that their arms are bad. Betts's mixed position record cannot supply an isolated
OF denominator. Varsho's catcher/OF history leaves no qualified isolated arm
input at 2022, while later OF-only quality is positive. These cases remain visible
and demonstrate the limits of position-pure data rather than justify forced zeros.

Twenty focal forecasts and 60 origin-selected peers have dated source records,
recency calculations, exact shrinkage and annual future records in the
[player walkthrough](../reports/model-evidence/arm-receiving-v6/talent/player-walkthrough.json).
No player overrides or post-result prior tuning were used.

## Source corrections retained

The historical capture contains 4,832 player-seasons: arms 2016–2025 and
receiving 2021–2025. All 850 receiving records reconcile to native credit using
actual received throws, six throw categories and expected outs. Sixteen arm
records remain unqualified: native scope gaps, one null adjustment and two
unexplained numerator disagreements. The team-setting probe did not repair
Matt Reynolds or Ryan Vilade; neither was silently forced to match.

Complete official fielding history corrected 100 arm scope flags that native
position splits had made appear exclusively outfield. Old pilot/support artifacts
remain preserved; the corrected `official-scope` records and labels supersede
those flags. Innings establish position scope only, not arm opportunity counts.

## Retained recipe and remaining work

Use three seasons weighted 1, 0.5 and 0.25. Divide 100 times weighted adjusted
runs by weighted opportunities plus 300 arm chances or 600 received throws.
Those prior exposures are explicit conservative assumptions, not optimized
constants. A one-chance hot result is directly reduced by the prior; a separate
reliability flag is not used as a substitute for shrinkage. Unmeasured histories
produce a neutral fallback marked unknown skill, not an observed average grade.

Current research outputs cover 470 arm and 282 receiving players. Of these 752
component rows, 184 have no qualified recent skill evidence and are explicitly
marked unknown with a neutral fallback. They receive no future opportunities or
awarded runs. Fourteen current focal/42 peer checks accompany those outputs.

All 4,666 origin forecasts, quality labels, chronological support counts, scores
and paired intervals independently replay. Thirteen focused source/baseline
checks pass. The research recipe is retained cautiously, with young-arm misses,
small receiving cohorts and position-scope exclusions explicit. No full-WAR,
lower-minors transfer or deployment improvement is claimed.

Next, forecast actual defensive positions and channel opportunities, then test
whether the combined components improve delivered defensive runs and total
player value on a matched historical cohort. Do not repeat a prior sweep or
algorithm tournament. Frozen forecasts, the explorer and the completed 2026
evaluation are unchanged.
