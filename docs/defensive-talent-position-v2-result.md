# Infield talent milestone: better evidence, no new production predictor

2026-10-06. The 2016–2025 MLB range history now separates actual positions, and
the unchanged minor cohort has repaired identity/age and dated fielding context.
The one fixed comparison is finished, including player and unsuccessful-peer
reviews. **The existing adjusted ground-ball play-share feature did not improve
the ordinary-year result. Do not deploy it or retune this version.** This does
not establish that minor defense is uninformative or finish the defense model.

## What changed, and what did not

The full 31,563 position-origins/4,529 people remain. Public biography fills
6,202 missing age rows and 6,226 name rows; original metadata is preserved.
Current and weighted fielding-level shares now come from actual dated exposure,
not a possibly missing batting snapshot. Tovar's 2019 INACTIVE/missing-age row
is correctly represented as a 17-year-old with short-season fielding evidence.

Position splits recover mixed-position seasons without apportioning aggregate
runs. Quality coverage rises from 28 to 119 distinct no-prior-MLB-fielding people
for fixed three-year windows (108 under exact exposure equality). The
[source review](defensive-talent-position-v2-source-review.md) and
[pre-fit exposure amendment](defensive-talent-position-v2-exposure-amendment.md)
explain tiny exposure disagreements, omitted positions and missing range.
These are data/measurement improvements, **not demonstrated forecast gains**.

Selected batting/value forecasts, completed 2026 evaluation and the 8810 explorer
are unchanged. No new 2026 outcome is collected or used. This work neither
changes current defense contributions nor claims improved full WAR.

## The actual comparison

End-of-2022 evidence predicts pooled same-position MLB range in 2023–2025,
measured in runs per 500 innings. Both arms receive repaired age, position,
fielding-level shares, exposure/current participation and prior MLB range.
The candidate alone adds the frozen minor play-share signal. A crude unadjusted
credit-share arm and a zero-range anchor provide additional checks. All use one
fixed conservative ridge fit; no parameter search or second model tournament.
Training people are separate and training labels have finished by the origin.

| Forecast origin | Scored people / position rows | Context baseline error | Add raw credit share | Add adjusted play share | Zero-range anchor |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022, primary ordinary origin | 89 / 102 | 2.627 | 2.614 | 2.642 | 2.756 |
| 2021, separate COVID stress | 99 / 113 | 2.738 | 2.733 | 2.773 | 2.761 |

Error is player-weighted RMSE in runs/500 innings; each person's measured position
rows total one within an origin. The 2022 candidate-minus-baseline difference is
+0.015, with a player-cluster 95% interval of −0.026 to +0.057. Compared with raw
share it is +0.028 (−0.001 to +0.056). Small and uncertain does not mean a win.
The 2021 difference is +0.035 (−0.041 to +0.113); it is not pooled into a claim
about ordinary seasons. Unweighted scores give the same ordering.

For 2022, the candidate is slightly worse in all three positions, and among both
no-prior-fielding players (32 people: 2.620 → 2.639) and prior-fielding players
(57: 2.630 → 2.644). Small subgroups cannot certify absence of an effect. In 2021
it helps prior-fielding players but worsens no-prior-fielding players, so that
mixed result is particularly unsuitable for a general prospect claim.

The 2022 selected cohort's mean observed rate is +0.006; baseline/candidate means
are −0.078/−0.065. There is no large mean-calibration error hiding the result.
These conditional quality averages are not league-wide defensive-run or WAR
totals: unmeasured/non-arriving players cannot be entered as zero defenders.

## Player walkthrough: inputs → mechanism → MLB reality

All figures below are same-position runs/500 innings, not WAR. Cases combine
pre-fit fixed players with deterministic primary-year largest gain/loss,
false-high/low and median-error selections. Outcome-selected cases explain the
result, not independently validate it. Full source rows, coefficients, input
contributions, annual paths and three origin-blind peers per focal case are saved
in `reports/generated/defensive-talent-position-v2/qualified/comparison/player-walkthrough.json`.
Twenty-five focal cases and their peer traces were reviewed, including unscored
older origins and three input-selected DSL cases.

| Player and origin / position | Baseline | Candidate | Observed fixed-window quality | What the trace shows |
| --- | ---: | ---: | ---: | --- |
| Witt 2021 / SS | +0.28 | −0.29 | +2.03 | Negative minor signal worsens the estimate; MLB changes from negative 2022 to strong positive 2023/24. |
| Tovar 2021 / SS | −1.06 | −0.65 | +3.86 | Positive minor signal helps, but the young lower-level baseline remains far too low; zero exact-profile training peers. |
| Volpe 2022 / SS | −0.19 | −0.32 | +0.77 | Small negative minor residual worsens an already modest estimate. Annual MLB range is positive, strongly positive, then negative. |
| Mateo 2021 / SS | −0.06 | +0.40 | +1.67 | Positive older AAA evidence helps despite weak small-sample prior MLB range; mixed-position seasons now count correctly. |
| Clement 2022 / SS | −0.19 | +0.24 | +4.69 | Largest primary-year improvement, but still a substantial underprediction from only 103.5 weighted minor balls. |
| Edwards 2022 / SS | −0.34 | +0.08 | −6.84 | Largest deterioration/false high: 192 minor balls with above-expected credited plays do not identify poor later MLB SS range. |
| Otto Lopez 2022 / 2B | −0.17 | −0.24 | +7.33 | Largest false low: near-average minor credit share and 12 prior MLB outs fail to reveal excellent later range. |
| Ibáñez 2022 / 2B | +0.71 | +0.89 | +2.42 | Median-error case: positive prior MLB range and small positive minor residual move in a sensible direction, with remaining error. |

**Witt:** dated 2021 AA/AAA exposure is 490/522 team ground balls, with 94/93
credited successful first-handled plays versus 100.88/106.02 expected. Add one-
quarter of 2019 rookie exposure: 1,091.25 weighted balls, 205 credits, 222.93
expected. The 600-ball shrinkage gives −0.010603. In his saved candidate fit that
feature directly contributes −0.562 runs/500 innings. Setting only this input
to zero in the fixed fit gives +0.272, close to baseline +0.282. This really is
the signal hurting him, not a join bug. His later SS path is −6.88, +9.76, +11.36
range runs. At the 2022 origin both negative rookie MLB range and stale minor
evidence pull him down: −0.54 → −0.87 against later +4.89. Development is missed;
his later breakout was not available to the origin model.

**Tovar:** the 2021 pool contains 660 short-season balls from 2019 (quarter
weight), plus 643 A and 310 A+ balls in 2021. Weighted credits/expectation are
241.25/222.37 across 1,118 balls. Positive signal directly adds +0.404 to the
fixed candidate; the negative age/level/context baseline remains the bigger
problem. The label uses 234, 3,981 and 4,127 SS outs in 2022–2024, not his best
season. In 2022 his signal falls to +0.000876 as newer AA evidence arrives; a
234-out negative MLB cameo also enters the regressed prior. Predictions remain
around −0.40 versus later +3.53. This identifies a development/support limitation,
not permission to make Tovar-specific overrides.

**Volpe:** the model preserves current AA 1,013 versus AAA 205 balls and half-
weighted 2021 A/A+ evidence. AA accounts for 62.1% of the weighted pool, AAA
12.6%; calling it all AAA would lose context. The residual is just −4.586 credited
plays before shrinkage. It directly subtracts 0.070 in the candidate; the rest
of the arm difference is refitting other coefficients. His +0.94/+10.53/−5.19
annual MLB runs explain the moderate pooled target. Eight exact-profile training
people do not support a precise star-quality estimate.

**Mateo:** his 2021 origin has no current minor SS record, not inactivity: 2019
AAA 1,211 balls enter at quarter weight, producing 302.75 weighted balls and
+0.008386 signal. His 360 prior MLB SS outs carry −1.31 runs, heavily shrunk.
The signal adds +0.444 in the fixed fit. Later +7.58/−0.83/+0.39 SS runs over
2022–2024 give +1.67 pooled quality. His separate 2018 origin still lacks enough
MLB exposure inside its fixed window; the review does not extend it to his peak.

**Clement versus Edwards:** both have modest minor SS samples, yet strongly
positive adjusted residuals. Clement has 32 weighted credits versus 23.69
expected on 103.5 balls; Edwards 49 versus 40.28 on 192. Direct signal additions
are +0.400 and +0.472. Clement's later +1.04/+3.25/+1.20 runs on 1,753 total SS
outs support a positive measured rate, though precision is limited. Edwards's
2024/2025 SS runs are −7.79/−5.20 on 2,849 outs; 2023 has no SS exposure. The
same plausible direction of minor signal helps one and hurts the other. His
positive 2025 second-base range is a different target, not a rescue of the SS test.

**Lopez versus Ibáñez:** Lopez's weighted 2B credits/expected are 128/131.07
on 685 balls, a slightly negative residual. Twelve prior MLB outs provide almost
no information. Later range is +12.10 in 2024 and +4.25 in 2025, with no 2023
2B exposure; +7.33 is a measured two-season rate, not an assumed permanent talent.
Ibáñez has 72 weighted minor balls, 16/13.47 credits/expected and a +1.44
regressed prior MLB rate from 408.5 weighted outs. The candidate's positive
movement follows actual prior evidence; his target pools three seasons rather
than selecting the best.

**Origin-known peers and unknowns:** Volpe's nearest same-profile peers are Dale,
Rocchio and Tena. Dale has no recorded MLB fielding in 2023–2025; Rocchio has
measured SS quality +0.22; Tena has MLB fielding but too little SS exposure for
quality. Tovar's 2021 peers Marte/Luciano/Winn have limited SS, limited SS, and
measured −0.08 respectively, so not every promising 19-year-old becomes Tovar.
Clement's peers Díaz/Guthrie/Barreto have limited other-position MLB exposure,
limited other-position exposure, and none. Edwards's peers Izturis/Young/Barger
have none, none, and MLB exposure elsewhere. None is given zero defensive talent.
Turang and Giménez are especially important counterexamples: their lack of
sufficient later SS measurements is **not** failure to become good MLB defenders.
Same-position selection cannot certify position-converted talent. DSL cases and
their origin-blind peers stay in the ledger, but have no qualified three-year
quality observations or chronological long-window predictions.

## What this says about the approach

The regression consistently gives positive weight to the adjusted signal: this
is not a mysterious sign reversal. But the signal counts successful first-
handled grounders relative to **team** ground balls while a player fields that
position. Those are not individually reachable chances. Park, handedness and
league backgrounds are adjusted coarsely; exact ball direction, difficulty,
starting position, teammates and development are not separated. More credits
can reflect more balls hit toward that fielder, not more range. This is a
plausible measurement limitation, not a proven explanation for each miss.

The contextual model is also only a conservative linear reference. Age/level
associations in a selected mixed sample of prospects and returning MLB players
are not biological aging/development curves. It underpredicts several young
standouts; that does not establish every young SS should be upgraded. The
fixed three-year label combines development and observed later range, and only
scores players who remain at that position long enough. Quality uncertainty,
position conversion and exposure selection remain outside this comparison.

Support is still thin: 70/102 primary scored rows have fewer than 20 exact-profile
training people; one rookie-origin person and zero predominantly DSL-origin
people have measured three-year quality across the entire ledger. Five/seven-
year chronological fits remain impossible with these minor inputs. Never claim
this loss proves that lower-level defensive statistics cannot identify talent.

## Disposition and coherent next work

Integrity: pass for the stated component experiment, with bounded source-count
discrepancies disclosed. Support: adequate only for a small selected-population
comparison, not broad prospect validation. Prediction: no demonstrated gain
from the adjusted feature. Baseball review: completed, with substantial star
misses and position-selection limitations. Deployment: **not approved**.

Keep the repaired position/identity/context source and close this particular
play-share addition. Do not rerun it with new weights or algorithms to seek a win.
The next infield checkpoint is a source-feasibility review of actual defensive
opportunity and position-retention evidence from existing PBP and traditional
fielding records, following the literature already reviewed. First establish
which ball-location/error/assist/role information is genuinely comparable across
levels; then predeclare a materially different talent test if usable. No new
college collection, no team-record experiment, no assumption that AAA Statcast
coverage automatically exists for minor fielding. Catcher, outfield, baserunning
and position development still require their own talent targets/support review.

All 31,563 origin inputs and 94,689 labels reconstruct; all 7,333 player-position
forecasts replay for each of three fitted arms (21,999 checks), and all 30 ridge
fits also reproduce via independent normal equations. Player-cluster intervals
and scores replay. Twenty-one focused tests pass. These checks establish execution,
not a predictive win. The infield source-and-comparison milestone is complete;
the full nonbatting talent and player-value goals remain unfinished.
