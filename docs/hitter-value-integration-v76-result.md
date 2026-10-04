# Next year MLB batting contribution comparison and player review

2026-10-03. Keep the current research candidate. None of the three new ways
of combining hitting and playing time improves the overall forecast. Fifteen
actual player walkthroughs explain why: a few direct-value gains leave workload
wrong, and coherent event counts can still produce an implausible workload or
event mixture. The alternative hitting reference remains research evidence,
not an adopted blend. Protected 2026 outcomes, the frozen forecast and the
deployed explorer are unchanged. The full project goal remains active.

## What this comparison measures

The [contract](hitter-value-integration-v76-contract.md) and
[source review](hitter-value-integration-v76-source-review.md) precede fitting.
There are 30,506 next-calendar-year forecasts, 11,020 distinct people, seven
origins (2016–18 and 2021–24) and 35 chronological whole-player cells. The same
players, including non-arrivals and exits, appear in every comparison. Training
outcomes mature by origin; the entire held-player fold is excluded. Canceled
2020 MiLB exposure is missing, while short-season MLB workload is normalized
once. These exposed historical years provide development evidence, not a fresh
holdout or certification of six years of control value.

Current combines the fresher-ranking opportunity model with the existing
PA-weighted linear batting estimate. Bridge is the previously tested translated
linear hitting alternative for never-debut players, with current opportunity.
Direct predicts signed batting contribution on all eligible rows. Active
predicts contribution conditional on MLB appearances and multiplies by the
current arrival probability. Counts predicts the means of eight disjoint events,
then derives PA and contribution from the same means. The two signed heads
retain current PA only as a diagnostic; they do not independently improve PA.

All new heads share 272 predictors: the current 251 inputs, twelve translated
profile/reliability features, eight known origin league event shares and one
replacement reference. Their contrasts with current change both representation
and target/loss; they do not isolate a feature, covariance effect or library.
This branch does not silently include every previous contact, park, opponent,
injury, defense or catching experiment. Translations are own-origin and
held-player safe, but are not certified park-neutral major-league equivalents.

Contribution is a custom fixed-event batting-plus-replacement measure, not full
WAR. The primary observed label compares future MLB batting with the origin's
MLB event index. The [pre-score environment sensitivity](hitter-value-integration-v76-environment-supplement.md)
instead compares with the actual target-season index. No forecast receives that
future average. Both signed heads were trained on the primary label; the
sensitivity is not a fair tournament of differently trained neutral targets.

## Forecast errors and uncertainty

Lower is better. Errors give each target year equal weight; cohort totals are
raw sums. Prospect-only errors cannot be compared directly with public errors:
most prospects have no next-year MLB appearances. Numbers below remain in the
declared custom contribution units.

| Population and measure | Current | Bridge | Direct | Active | Counts |
| --- | ---: | ---: | ---: | ---: | ---: |
| All contribution RMSE | .453384 | .453223 | .464296 | .461887 | .491055 |
| Never debuted contribution RMSE | .152257 | .151662 | .150796 | .151267 | .162216 |
| Upper minors never debuted contribution RMSE | .312832 | .311491 | .308056 | .310619 | .331429 |
| Lower minors never debuted contribution RMSE | .043039 | .042987 | .045486 | .043266 | .043227 |
| Public matches contribution RMSE | 1.060504 | 1.060504 | 1.088050 | 1.085271 | 1.146830 |
| All PA RMSE | 60.499 | 60.499 | 60.499 | 60.499 | 61.756 |
| All PA MAE | 20.612 | 20.612 | 20.612 | 20.612 | 21.130 |
| Never debuted PA RMSE | 27.252 | 27.252 | 27.252 | 27.252 | 27.711 |
| Never debuted PA MAE | 4.764 | 4.764 | 4.764 | 4.764 | 5.061 |

All-population contribution MAE also worsens: .128788 current, .137261 direct,
.131839 active and .141025 counts. The nominal player-clustered paired 95%
intervals for candidate-minus-current contribution MSE are:

| Population | Direct | Active | Counts |
| --- | --- | --- | --- |
| All | +.010014 [.006440, .013781] | +.007783 [.004321, .011344] | +.035578 [.027909, .044012] |
| Never debuted | -.000443 [-.001408, +.000422] | -.000300 [-.000859, +.000245] | +.003132 [.001446, .005130] |
| Upper minors never debuted | -.002965 [-.007243, +.000959] | -.001380 [-.003851, +.001067] | +.011982 [.004724, .020359] |

Positive means worse. The signed-head prospect improvements are uncertain and
do not justify replacing an overall better model. Lower-minors count PA RMSE
improves 7.966 to 7.763, with nominal paired MSE interval [-6.356, -.272], but
MAE worsens .622 to .689 and their PA total rises further above actual. This
is a real loss tradeoff, not a uniformly improved lower-minors forecast. New
draftee count PA RMSE improves slightly, 24.514 to 24.100, but contribution
RMSE worsens .164208 to .174469. Intervals do not protect against all historical
experimentation or common season-level shocks; no causal claim follows.

On the unchanged 2,627 public matches, current PA RMSE/MAE is 138.330/106.411,
counts 139.396/106.578, and Steamer 135.379/92.083. Current is 2.18% higher on
RMSE but 15.56% higher on MAE, still outside the practical plan's 15% MAE
allowance. Do not waive that target. Steamer converted contribution RMSE is
1.118659; current's lower custom value error does not establish published
WAR or park-neutral talent superiority. Existing archive snapshot-date and
environment-conversion qualifications still apply. ZiPS supplies matched rate
context here, not an invented season PA/value forecast.

The season-relative sensitivity does not reverse the overall result. All
contribution RMSE is .437947 current, .437767 bridge, .449389 direct, .446751
active and .482667 counts. Never-debut RMSE is .148895, .148234, .147393,
.147932 and .159639 respectively. Signed-head prospect intervals still include
harm; count value is worse. A proper season-relative training comparison would
require a new contract, not relabeling these fits after the fact.

## Totals and accounting checks

All 350 new heads and 105 baseline heads were independently replayed. Actual
eight-event counts reproduce each of the 63,282 source PA/value responses.
All fifteen cases' 150 saved new-head paths reconstruct the predictions;
count effects are additive in log means and are exponentiated only after the
complete sum. These are model mechanics, not SHAP or causal feature effects.
All old anchor columns remain bit-identical. These execution checks do not
establish predictive quality or adequate training support.

Across evaluated players, counts improves the PA total from 1,228,733 to
1,253,726 against 1,270,493 actual, while contribution becomes more excessive:
4,541 versus 4,264 common-origin actual and 4,185 season-relative actual.
Current predicts 4,166. Better aggregate PA does not mean better allocation or
better contribution. Aggregate HR is close, 40,329 versus 40,502 actual, while
individual Soto/Judge/Kurtz forecasts miss badly. League-like event totals are
not a substitute for player-level accuracy.

For the 24,199 never-debut forecasts, the unresolved totals are:

| Origin | Actual PA | Current PA | Counts PA | Common actual contribution | Season relative actual contribution | Current contribution | Counts contribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 10,735 | 11,308 | 9,552 | 21.28 | 17.21 | 27.59 | 15.82 |
| 2017 | 11,854 | 9,529 | 9,411 | 23.57 | 31.87 | 21.91 | 8.12 |
| 2018 | 15,836 | 10,032 | 10,222 | 64.28 | 48.92 | 24.57 | 26.17 |
| 2021 | 18,944 | 10,432 | 12,480 | 35.36 | 46.26 | 30.08 | 47.08 |
| 2022 | 14,072 | 13,575 | 14,771 | 31.07 | 18.31 | 34.71 | 58.20 |
| 2023 | 11,697 | 14,725 | 17,029 | 5.12 | 14.32 | 35.18 | 17.78 |
| 2024 | 15,190 | 12,248 | 13,577 | 34.07 | 30.55 | 25.51 | 29.90 |

The 2019 league environment explains 15.36 custom wins of the 2018-origin
label, but not the remaining production or 5,804-PA current shortfall. Counts
reduces the 2021 deficit but remains 6,464 PA short; it worsens the 2023 PA
excess. These are not fixed MLB-wide budgets, complete future team rosters or
forecasts of players who enter professional baseball after the origin.

Counts has zero physical accounting incompatibilities, but four 800-PA caps:
Swanson at origin 2016, Benintendi at 2016/2017 and Langford at 2023. Langford's
raw sum is 1,760.24; the other sums are about 820/951/996. Capping proportions
does not repair an implausible event mixture. Direct has 4,120 incompatibilities
when paired with unchanged current PA, mostly lower-minors non-arrivals; active
has two, Denorfia and Matt Winn at origin 2017. This does not invalidate a
standalone direct expected-value estimand: its PA is not independently fitted.
It does block presenting those pairs as a coherent hitting/workload model.
Do not hide the issue by clipping direct value after seeing results.

Refined full training profiles are unseen for 49 forecasts and sparse below
twenty distinct people for 717. Active profiles are unseen for 8,452 and sparse
for 15,019. These forecasts remain scored. Missing foreign/roster-only histories
and publication-date qualifications remain; a count-source pass does not certify
complete worldwide player coverage. Count means provide no calibrated debut
probability, covariance, injury explanation or season prediction interval.

## Fifteen actual player walkthroughs

Each origin below forecasts the following calendar year. The eight fixed cases
were declared before fitting. Additional cases are each new arm's largest
contribution gain/harm, count PA false high/low and an ordinary active case.
They are outcome-selected diagnostics, not independent confirmation. The
[full cases](../reports/model-evidence/hitter-value-integration-v76/cases.json)
contain every source row, 272 actual inputs, all saved paths, eight predicted
and observed events, support and four origin-selected peers. The
[reviewed summaries](../reports/model-evidence/hitter-value-integration-v76/reviewed-cases.json)
add the explicit baseball judgments below.

Peer matching uses origin/stage/debut status, age, MLB/minor/AA/AAA exposure,
fresh ranking, translated K/walk/HR profile and pooled MLB quality. Future
outcomes cannot affect selection, as checked by mutation. These are measured
controls, not equivalent position, health, scouting detail or roster openings.
In particular, generic inactive peers do not establish suspended-star risk.
Tree path terms depend on correlated inputs and ordering; they are not causal
benefits from changing one stat or transferring a player.

### Elite entrants and retained stars

**Nick Kurtz, 2024.** Age 21, 50 A/AA PA, four HR, twelve walks and ten K.
Actual model rank is .63, not the stale inherited zero display; draft pedigree
is present. Translation reliability is .04. Current .0606 arrival times 168.16
active PA gives 10.18 expected PA. Direct rank/translated-HR paths add .188/.073,
raising contribution .031 to .190; active .655 times .0606 gives .040. Count
paths penalize thin exposure despite pedigree lifts: 7.26 PA and .513 HR versus
489 PA/36 HR, contribution .083 versus 5.838 common or 5.724 relative actual.
Refined full/active support is 1/0. Smith receives 493 PA, Moore 184 and
Quero/Williams zero. None of the constructions fixes this thin-elite entry miss.

**Wyatt Langford, 2023.** Age 21, 200 pro PA, ten HR, 36 walks and 34 K,
including 80 AA/AAA PA; actual fresh rank .95 and translation reliability .143.
Current .5991 times 358.74 = 214.92 PA; contribution .912, bridge 1.181,
direct .499 and active .806. Count log paths add strongly for ranking and
AA/A+ role features across heads. Their sum reaches 1,760.24 raw PA before
the proportional 800 cap. Final 275.89 K, 58.83 singles and 24.37 HR produce
-.904 contribution against actual 557 PA/115 K/16 HR and +1.796 common/+2.234
relative value. Zero refined support in both subsets is material. Teel,
Montgomery and DeLauter receive zero next-year PA, Amador 36. The error is an
unsupported fitted extrapolation, not missing pedigree or inconsistent summing.

**Julio Rodríguez, 2021.** Age 20, 340 A+/AA PA, 13 HR, 42 walks and 66 K;
canceled 2020 MiLB is not a poor season. Fresh and lagged ranks .98/.96/.83
contribute positively to direct paths, lifting value 1.116 to 1.867. Active
1.645 times .805 arrival yields 1.324. Count PA falls 254.11 to 175.40, with
5.88 HR, against 560 PA/28 HR; contribution 1.303 versus 3.937 common/4.259
relative. Support is 10/7. Torkelson 404 PA, Abrams 302, Casas 95 and Davis
zero show different timing and production. Direct contribution helps, but the
opportunity problem is not repaired and not every ranked entrant succeeds.

**Pete Alonso, 2018.** Age 23, 574 AA/AAA PA, 36 HR, 73 walks and 128 K.
Fresh rank .50 and pooled AAA HR .05985 are present; direct power/rank paths
add .246/.158. Direct/active value .987/.994 improves on .765 but misses 6.598
common/5.926 relative actual. Counts raises PA 215.03 to 281.66 but forecasts
10.95 HR against 693 PA/53 HR, reducing value to .647. Support is 6/4.
Lester, Craig and Hayes receive zero next-year PA, Solak 135; they do not
share all his power and AAA exposure. League conditions explain .672 of his
label, not the remaining major workload and production miss.

**Aaron Judge, 2024.** Age 32, three seasons of 696/458/704 MLB PA and
62/37/58 HR. Pooled quality 3.649 is present; refined support 69/69 does not
establish exact superstar support. Direct/active recognize quality but lower
contribution 5.668 to 5.199/5.355. Counts raises PA 530.75 to 562.52 yet
forecasts only 28.60 HR, lowering contribution to 4.230 against 679 PA/53 HR
and 9.393 common/9.236 relative actual. Olson, Schwarber and Ohtani receive
724/724/727 PA, Ozuna 592. This is not a lost source row: the fitted model
compresses the star tail, and extra PA cannot offset its weak predicted mix.

### Low arrival and upper minors controls

**Kevin Maitan, 2017.** Age 17, 176 rookie PA, two HR, ten walks and 49 K.
Actual fresh current rank is .14, versus the stale display's .69; genuine
prior rank .69 remains. Its direct path adds .237, giving .276 contribution
against current .005. Active .268 times .0152 arrival gives .004. Counts
predicts .191 PA and approximately zero value, versus zero observed. Support
is 5/0. Guerrero, Infante, Coronado and Méndez also have zero next-year PA.
Immediate non-arrival is reasonable, but cannot tell us whether this model
correctly values a teenager's eventual MLB ability or long-term option value.

**Bryan Reynolds, 2018.** Age 23, 383 AA PA, seven HR, 40 walks and 73 K
after 541 A+ PA. No fresh global ranking is present; that is not evidence of
no scouting value. Translated event probabilities imply 28.4% K/1.44% HR,
and active paths subtract for no MLB quality and weak translated HR. Current
.1564 times 81.02 = 12.67 PA. Counts gives 16.27 PA/.325 HR against 546 PA/
16 HR. Direct value -.008 is worse than current .030; counts .062 remains
far below 4.696 common/4.166 relative actual. Support is 634/183, so a tiny
coarse training count is not the explanation. Jackson receives four PA,
Nuñez 43, Arenado/Woodrow zero; they do not make the missed readiness or
unmeasured talent disappear.

**Dawel Lugo, 2017.** Age 22, 557 AA PA, 13 HR, 32 walks and 72 K;
translated walk/HR probabilities 3.09%/1.77%. Counts predicts 69.85 PA,
.91 HR, 2.49 walks and 36.17 other outcomes. Value -.022 is closer than
current +.161 to actual -.235, despite PA moving farther from 101. Direct/
active remain too positive .174/.181. Support is 173/68. Reyes receives 219
PA with negative value, Kiner-Falefa 396 with positive value, Espinal/Dubón
zero. This is a hitting-mix gain with a workload loss, not a complete win.

### Largest gains and harms

**Fernando Tatis Jr., 2022.** Age 23, 257 actual short-2020 MLB PA/17 HR,
546 in 2021/42 HR, then zero 2022 MLB PA and fourteen AA PA. Prior MLB
debut/talent survive, but origin on-40-man is zero and stage Upper minors.
Current arrival .134 times 296.16 active PA produces 39.68 PA against 635.
Direct pooled-quality/age paths add 1.642/.386, lifting contribution .209 to
2.459; active 2.729 times .134 yields .366. Counts gives 34.70 PA/1.06 HR
and .063 value against 3.333 common/2.757 relative actual. The finite-suspension
meaning was [documented previously](availability-context-v29b-amendment.md),
not an unforeseeable permanent departure. Support 11/6 and Sisco/Long/Welker
zero, Jones eleven, are poor suspended-star analogues. The largest direct
gain cannot be presented as repaired playing time or a coherent career path.

**Juan Soto, 2023.** Age 24, prior MLB PA 654/664/708, unintentional walks
122/129/121 and HR 29/27/35. Current .9931 times 638.36 = 633.93 PA and
6.126 value; direct/active lower that to 4.534/4.956. Counts improves PA to
670.16 against 713 but predicts 73.43 walks/29.15 HR against 127/41, reducing
value to 2.818 versus 8.201 common/8.762 relative actual. Translated walk
probability .182 was present: the deficient final walk mix is learned, not a
missing stat. Support is 18/18. Guerrero 697, Rutschman 638, Paredes 641 and
Acuña 222 PA show downside variation without making extreme regression of
Soto's demonstrated walks persuasive. This is the largest direct/count harm.

**Josh Donaldson, 2018.** Age 32, 219 recent MLB PA after 496/700, with
8/33/37 HR; minor rehab counts remain separate. Direct/active use pooled
quality 1.631 and prior strong seasons, raising value 2.504 to 3.787/3.673;
active intermediate 4.044 times .908. Actual is 659 PA and 5.976 common/
5.337 relative value. PA remains 430.84; counts 427.74 PA/16.12 HR worsens
value to 2.122. Support 192/165 and Fowler 574, Joyce 238, Cozart 107,
Céspedes zero show recovery and downside. The largest active gain recognizes
retained production, but is not a workload recovery fix for older stars.

**Corey Seager, 2017.** Age 23, prior 687/613 MLB PA and 26/22 HR. Current
.9959 times 635.08 = 632.46 PA and 3.770 contribution. Positive quality,
age and workload paths lift direct/active value to 4.900/5.237. Actual is
115 PA and .368 common/.449 relative. Counts still gives 630.83 PA/29.17 HR
and 4.245 value. Support 82/82 is not absence-specific certainty. Machado,
Bregman, Bell and Correa receive 709/705/583/468 PA. This largest active
harm must remain visible, but a future absence is not proof that a young
regular's origin-known healthy-season forecast should have been near zero.

**Aaron Judge, 2021.** Age 29, 633 current MLB PA/39 HR; actual short-2020
114 PA/nine HR is retained with separate workload normalization. Counts gives
535.88 PA/33.12 HR and lifts contribution 3.443 to 5.572, its largest gain;
direct/active 3.990/3.833. Actual is 696 PA/62 HR and 9.391 common/9.791
relative value. Paths use workload, translated HR and double profile, not a
causal effect of doubles. Support 56/56; Suárez 629, Bryant 181, Story 396
and Soler 306 PA preserve downside. A large gain on this spectacular season
does not overturn the same construction's 2024-origin Judge harm or overall loss.

### False high and ordinary workload control

**David Dahl, 2016.** Age 22, 237 MLB PA/seven HR plus 400 AA/AAA PA/
eighteen HR. Counts uses brief MLB exposure and accumulated games to give
631.78 PA, up from 394.67, against zero actual. Yet value .229 is closer
to zero than current 1.671 because the event mix is weak: 165 K, 28.68
walks, 22.47 HR and 301.74 other outcomes. That is compensating error,
not successful absence prediction. Support 6/6; Sánchez 525, Turner 447,
Hernández 95 and Quinn zero PA preserve differing outcomes. The value gain
must not be called a better playing-time forecast.

**Andrew Knapp, 2017.** Age 25, 204 current MLB PA, three HR, 27 walks and
56 K after 443 AAA PA. Counts gives 215.10 PA against 215 actual, the
ordinary workload control, but predicts 62.23 K/10.32 doubles against
75/six. Value +.538 misses actual -.227 common/-.076 relative; current
+.448 is less wrong. Direct +.370 helps modestly; active +.517 hurts.
Support 24/22; Wolters 216, Marisnick 235, Pinder 333 and Valaika 133 PA
demonstrate plausible part-time usage with different production. Exact PA is
not exact value, and this batting-only measure includes no catcher or position value.

## Decision and next work

Review is complete, not predictive approval. Do not promote direct, active or
counts, retune their settings, blend their attractive cases or retroactively
reject all joint/count models. Keep the coherent current opportunity/rate
construction as the research anchor and the translated linear model as a
tested alternative. PA weighting can already encode workload/performance
dependence; this comparison provides no evidence that decomposition itself
must be replaced.

The useful findings are specific: future league conditions must be separated
from player contribution when interpreting WAR-like targets; event totals and
PA can improve while player contribution worsens; thin elite entry and known
temporary absence remain opportunity gaps; tree paths can compound sparse
profile signals rather than sensibly represent them. Finite-suspension work
exists elsewhere but is not fully integrated into the current opportunity
branch. Its poor test results must be reviewed before borrowing a remedy.

Next, finish the practical plan's candidate integration audit: map the exact
current opportunity, batting and availability branches to their existing
tested evidence, especially source-known temporary absence versus permanent
exit. Determine whether an already supported source/branch repair is being
omitted before designing any new fit. Keep the public MAE miss, cohort totals,
uncertainty and prospect support visible in the eventual model card and
team-filtered explorer. No new library or marginal feature sweep follows this
negative result. Any new model comparison still requires a contract and actual
player review, and any forecast/explorer promotion requires separate approval.

Evidence: [scores](../reports/model-evidence/hitter-value-integration-v76/scores.json),
[paired intervals](../reports/model-evidence/hitter-value-integration-v76/intervals.json),
[season relative sensitivity](../reports/model-evidence/hitter-value-integration-v76/season-relative-sensitivity.json),
[event diagnostics](../reports/model-evidence/hitter-value-integration-v76/event-diagnostics.json),
[public rate context](../reports/model-evidence/hitter-value-integration-v76/public-rate-context.json),
[final review report](../reports/model-evidence/hitter-value-integration-v76/report.json).
