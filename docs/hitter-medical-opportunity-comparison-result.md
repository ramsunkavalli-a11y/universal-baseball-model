# Repaired injury histories did not improve this playing-time model

2026-10-05. Walkthrough status: complete.

Do not replace the stronger forecast with this candidate. Playing-time error
increased from 148.79 to 150.99 PA on the same 2,641 eligible forecasts. Batting
value and participation predictions also worsened. The repaired source remains
useful: an old injury no longer continues through documented MLB play. That is
not, by itself, an improvement in player projections.

The comparison also exposed a specific baseball failure: Victor Martínez's inputs
marked him as released, not retired. Do not call that an unpredictable injury
outcome. Nor does a better PA estimate automatically improve player value:
Franco's 2022 PA forecast improved while his delivered batting-value error grew.

## What was tested, and what was not

The [fixed contract](hitter-medical-opportunity-comparison-contract.md) compares
two otherwise matched refits against the stronger saved historical forecast:

- **Existing forecast:** the stronger `observation` anchor, unchanged.
- **Old-input refit (A):** 293 existing playing-time predictors, including six
  old injury/capture inputs, refitted on medically eligible, source-covered rows.
- **Repaired-input refit (B):** the same 287 nonmedical predictors plus nine
  reconstructed medical-observation states/counts, on exactly the same rows,
  settings and year-balanced weights as A. No injury-day or clinical-recovery
  probability is manufactured from an administrative record.

Eligibility requires a past MLB debut, at least 300 normalized MLB PA in one
of the preceding three seasons, and two covered transaction-source years.
Known suspensions and other nonmedical exclusions retain the anchor. So do
unsupported histories. Twenty distinct training people in each relevant joint
profile is a sparse-data screen, not proof of equivalent medical prognosis.
Unsigned/released players and future exits remain in scoring.

The population stays at 30,519 historical forecasts: origins 2016–2018 and
2021–2024, predicting 2017–2019 and 2022–2025. Five held-player folds per origin
use only matured training outcomes. Of 2,641 eligible forecasts, 1,719 receive
either refit; the rest retain exact anchor probability, conditional PA, expected
PA and value. Origin 2016 has no fully covered medical training history, so no
new head is fitted there. Thirty populated cells yield 120 fitted heads.

Cutoff clarification: the sealed contract's blanket reference to January cutoffs
is imprecise. The actual unchanged source dates are January 24–28 except the
origin-2021 cohort, which uses **March 18, 2022**. The same dates apply to all
three arms and were checked against the source; this is not a claim that every
historical forecast was available on January 1. The contract is preserved.

The experiment predicts **next-calendar-year MLB participation and PA**, then
multiplies by the unchanged batting-rate plus origin replacement contribution.
The value units are WAR-like batting-plus-replacement units, **not full WAR**:
no defense, running or positional value is added here. It does not estimate
clinical recovery, six-year control value or minor-league health. No protected
2026 results, selected forecasts or explorer files were changed or reopened.

## Matched results

Error scores weight each forecast origin equally; smaller is better. Counts and
totals below are sums of the identical rows, not reconciled league budgets.

| Eligible forecasts: 2,641 | Existing forecast | A: old-input refit | B: repaired-input refit |
|---|---:|---:|---:|
| PA RMSE | 148.79 | 150.86 | 150.99 |
| PA mean absolute error | 116.36 | 117.56 | 117.78 |
| Participation Brier | 0.05475 | 0.05792 | 0.05809 |
| Participation log loss | 0.18820 | 0.19814 | 0.19810 |
| Batting-plus-replacement RMSE | 1.2400 | 1.2447 | 1.2456 |
| Conditional PA RMSE among actual MLB participants | 148.79 | 150.93 | 150.93 |
| Predicted PA; actual = 916,858 | 898,644 | 905,361 | 904,638 |
| Predicted batting value; actual = 3,471.80 | 3,451.89 | 3,452.22 | 3,448.63 |

The player-cluster bootstrap, 1,000 draws preserving origins, gives B minus
existing PA mean-squared error **+661.09**, with 95% interval **+210.32 to
+1,132.75**. The deterioration is not an uncertain improvement. But B minus A
is only **+40.19**, interval **−62.34 to +142.62**. That small, uncertain
representation difference does **not** establish that fixing injury histories
hurts projections, or that injury information is useless. Most deterioration
is shared by both restricted refits.

| Origin → predicted season | Existing PA RMSE | A | B |
|---|---:|---:|---:|
| 2016 → 2017 | 149.14 | 149.14 | 149.14 |
| 2017 → 2018 | 147.67 | 154.40 | 154.24 |
| 2018 → 2019 | 159.75 | 164.56 | 165.81 |
| 2021 → 2022 | 140.89 | 138.92 | 139.14 |
| 2022 → 2023 | 150.25 | 154.47 | 154.54 |
| 2023 → 2024 | 149.58 | 150.63 | 150.31 |
| 2024 → 2025 | 143.51 | 142.47 | 142.21 |

This is not a failure confined to the COVID-disrupted 2021 origin: that cohort
improves. Origins 2017, 2018 and 2022 worsen by more than the predeclared 2%.
Predicted total PA moves closer to reality while individual errors and batting
value worsen. Better cohort totals alone do not justify the change.

Other checks agree. On the 1,719 applied rows, PA RMSE is 150.37 → 154.74.
On all 2,281 eligible rows with fitted heads, using raw unsupported predictions
as diagnostics, it is 148.73 → 154.16: fallback is not hiding a winner. Among
373 eligible next-year exits, predicted PA rises 30,801 → 32,536 despite zero
actual PA, and RMSE rises 131.66 → 139.78. Full-population error is only
60.33 → 60.77 because many minor leaguers have unchanged near-zero next-year
MLB predictions; that diluted score is not evidence of satisfactory MLB accuracy.

## Follow the players through the calculation

Eight player-origins were fixed before fitting. The largest improvement,
deterioration, false high and false low, an ordinary applied case, and an
outcome-blind lower-minor control were then selected by the fixed rules.
These are diagnostics, not fourteen independent confirmations. Full inputs,
source episodes, dated stats, actual fold support, three outcome-blind peers per
case and fixed-model probes are in the
[player traces](../reports/model-evidence/hitter-medical-opportunity-comparison/player-walks.json).

Expected PA = chance of any MLB PA × PA conditional on playing. Applied scores
use the unchanged batting rate and replacement conversion. Here is that actual
calculation, rounded; A is included so changes shared by both refits are visible.

| Player → predicted season | Existing probability × conditional PA | Existing expected PA | A PA | B probability × conditional PA | B PA | Actual PA |
|---|---:|---:|---:|---:|---:|---:|
| Travis → 2017 | 98.24% × 539 | 530 | 530 | unchanged | 530 | 197 |
| Tatis → 2023 | 15.35% × 400 | 61 | 61 | unchanged | 61 | 635 |
| Hoskins → 2024 | 92.14% × 399 | 367 | 367 | unchanged | 367 | 517 |
| Ellsbury → 2019 | 77.77% × 335 | 261 | 261 | unchanged | 261 | 0 |
| Alvarez → 2023 | 98.99% × 510 | 504 | 504 | unchanged | 504 | 496 |
| Franco → 2018 | 95.22% × 533 | 507 | 507 | unchanged | 507 | 465 |
| Judge → 2025 | 99.46% × 536 | 533 | 533 | unchanged | 533 | 679 |
| Canha → 2017 | 85.64% × 163 | 139 | 139 | unchanged | 139 | 187 |
| Franco → 2022 | 62.78% × 293 | 184 | 318 | 81.42% × 393 | 320 | 388 |
| Martínez → 2019 | 32.49% × 206 | 67 | 237 | 89.82% × 259 | 232 | 0 |
| McLain → 2024 | 98.61% × 606 | 598 | 598 | unchanged | 598 | 0 |
| Drury → 2022 | 45.75% × 170 | 78 | 36 | 20.97% × 192 | 40 | 568 |
| Smoak → 2019 | 99.29% × 493 | 489 | 494 | 99.15% × 505 | 500 | 500 |
| Ravelo → 2025 | 1.94% × 112 | 2.18 | 2.18 | unchanged | 2.18 | 0 |

### Source repairs and unsupported returns

**Devon Travis:** 239 MLB PA/8 HR in 2015, then 432/11 in 2016. Actual play
ends the stale March 2016 observation by May 25; three recent captured episodes
remain separate. There are zero fully covered training people in either 2016
head. The 530 PA forecast stays wrong versus 197, with batting value 1.724
versus 0.419. Zunino, Cron and Dietrich subsequently record 435/373/464 PA.
Neither source cleanup nor those broad role peers certify his clinical prognosis.

**Fernando Tatis Jr.:** 546 MLB PA/42 HR in 2021, no MLB PA and 14 AA rehab PA
in 2022. His medical follow-up stops being observable at the suspension, not at
recovery. The known finite nonmedical restriction makes him ineligible for this
medical refit; the 61 PA miss remains visible. White, Lopes and Long all have
zero subsequent MLB PA and do not represent a returning star. The previously
reported-ready role construction of 550 PA is a separate conditional reference,
not a repair of this 61 PA unconditional forecast or a validated health forecast.

**Rhys Hoskins:** 672 MLB PA/30 HR in 2022, then no MLB PA in 2023. Free agency
censors medical follow-up. His exact joint profile has only one training person
in each head, despite 562/514 total people. Raw B gives about 455 PA versus A's
431, but the applied forecast stays 367 versus 517. Giving B a peer's medical
inputs leaves its probability and conditional PA unchanged; the apparent raw
improvement is not evidence of learned ACL recovery. Solak/Iglesias/Severino
have 0/291/0 subsequent PA and are not equivalent past power-hitting regulars.

**Jacoby Ellsbury:** 626 MLB PA in 2016 and 409 in 2017, none in 2018. November
activation is an administrative return, not observed play or medical clearance.
His profile has zero training people in both heads. Raw B would worsen the
overestimate to about 398 PA; fallback keeps 261 versus zero. Tulowitzki/Vogt/
García have 13/280/0 PA. A roster activation cannot promise normal MLB workload.

**Yordan Alvarez:** 598 MLB PA/33 HR in 2021 and 561/37 in 2022. Observed July
21 play ends the old 2022 entry rather than carrying it to year-end. Joint
support is only nine/eight people, so 504 PA stays unchanged versus 496. Fixed
batting value is 4.127 versus 5.462: near-correct workload does not close talent
error. Riley/Soto/Lowe receive 715/708/724 PA; those totals do not imply Alvarez
should have been forced to the same exposure.

**Maikel Franco, origin 2017:** MLB PA 335 → 630 → 623 in 2015–2017, with
14/25/24 HR. His documented return prevents the old 2015 injury from spanning
later seasons. Joint support is fourteen/thirteen people. Raw B would give
599 PA, farther from 465 than the unchanged 507. Anderson/Polanco/Russell
receive 606/535/465 PA. Reject the claim that stale-span correction alone
necessarily lowers, or improves, the playing-time estimate.

**Aaron Judge:** 696/62, 458/37 and 704/58 MLB PA/HR in 2022–2024. Although
27 people occupy the broad profile in each head, his last-season quality 2.794
exceeds the participation training maximum 2.215. This is an empirical range
warning, not physically impossible talent. Raw B would give 579 PA; applied
533 stays below 679. Ohtani/Ozuna/Soto receive 727/592/715. Medical-input swapping
does not change either raw head. This does not repair the established-star
workload shortfall.

**Mark Canha:** 485 MLB PA/16 HR in 2015, 44/3 in 2016; the May injury entry
lacks qualifying return evidence before the January 2017 cutoff. Prior regular
work qualifies him, but the 2016 training set is unavailable, so 139 PA remains
versus 187. Lagares/Souza/Gonzalez subsequently receive 272/617/515. No recovery
probability was fitted or inferred from those three peers.

### Actual changes, gains and failures

**Franco, origin 2021, largest PA improvement:** 428 MLB PA/17 HR in 2019,
243/8 in the short 2020 season, and 403/11 in 2021. The original exposure
normalization stays fixed; a captured injury followed by MLB use and a minor
agreement are visible at the March 18, 2022 information date. Joint support is
198/187 people. Both A and B raise participation and conditional workload;
Franco reaches 388 PA. But fixed positive batting value 0.364 → 0.634 moves
farther from actual −0.309. Fletcher/DeJong/Ruiz receive 228/237/0 PA. Swapping
the closest peer's medical inputs changes neither B head (the inputs match).
This is mainly a shared refit change, not a demonstrated medical-information win.

**Victor Martínez, largest deterioration:** age 39, MLB PA/HR 610/27 → 435/10
→ 508/9 in 2016–2018. The source contains two observed-return episodes and a
release, but `status_retired=0`; joint support is 39/30 people. Participation
jumps 32% → 90%, causing 67 → 232 expected PA despite zero actual PA. Batting
value rises 0.080 → 0.280 against zero. Martínez's retirement was public before
the January 2019 cutoff. [MLB's dated report](https://www.mlb.com/news/victor-martinez-to-play-final-game-saturday-c295503108).
This is a missing cutoff-known source fact, not inevitable forecasting noise.
The scores are not rewritten to remove him. Closest peers Utley/Pujols/Davis
have 0/545/26 PA; age alone does not distinguish retirement from continued play.
The peer medical swap leaves both heads unchanged. A retires no more players
than B and similarly overpredicts him at 237 PA.

**Matt McLain, largest false high:** 452 AA PA/17 HR in 2022, then 403 MLB
PA/16 HR plus 180 AAA PA/12 HR in 2023. Captured activation is not clinical
clearance. Joint support 16/14 blocks the refit; 598 PA remains versus zero.
McLain's shoulder injury occurred March 18, 2024, after this January forecast.
[MLB's dated report](https://www.mlb.com/news/matt-mclain-shoulder-surgery).
That later event cannot be inserted into the January inputs. Injury uncertainty
still needs population-level modeling; the miss remains in unconditional scores.
Julien/Diaz/Casas receive 301/619/243 PA. B's raw diagnostic remains about
590 PA; borrowing Julien's medical inputs barely changes its probability and
moves conditional PA 595 → 590, not to zero.

**Brandon Drury, largest false low:** 447 MLB PA/15 HR in 2019, 49/0 in 2020,
88/4 plus 236 AAA PA/9 HR in 2021. Prior regular exposure is retained rather
than calling him a never-debuted prospect. Joint support is 214/206. The B
participation estimate falls 46% → 21% even though conditional PA rises
170 → 192; expected PA falls 78 → 40 versus 568. Batting value falls
0.146 → 0.076 versus 3.657. A similarly misses at 36 PA. The closest peer's
medical inputs are identical and produce no change. DeShields/Sánchez/Haase
receive 0/471/351 PA. The reduced-training refit is a poor replacement here;
this comparison does not establish a clinical cause or predict every breakout.

**Justin Smoak, ordinary applied case:** 341/14, 637/38 and 594/25 MLB PA/HR
in 2016–2018. No captured medical entry is not certified health. Joint support
56/55 permits the refit. Expected PA 489 → 500 nearly matches the 500 actual,
but batting value 2.531 → 2.588 is worse against 1.705 because the fixed hitting
rate is too optimistic. Medical inputs match the closest peer's, so the swap
does nothing. McCutchen/Upton/Brantley receive 262/256/637 PA: an apparently
ordinary history can still have a wide range of next-year workloads.

**Rangel Ravelo, original lower-minor control:** age 32, 258 AAA PA/8 HR in
2023 and 11 rookie PA in 2024. The stage label reflects latest low-level play,
not a teenage DSL prospect. Without recent MLB regular exposure he is ineligible;
1.94% × 112 conditional PA gives 2.18 expected PA against zero, unchanged.
Toles/Stamets/Miller also have zero outcomes. This control cannot validate health
modeling for young prospects, so a genuine DSL fallback check was appended.

## Minor-league scope check, not a new experiment

The [append-only DSL selection and review](../reports/model-evidence/hitter-medical-opportunity-comparison/minor-fallback-review.json)
does not replace Ravelo or change any fit or score. Selection projected only
origin-known fields: smallest row ID among origin-2024 DSL hitters who had not
debuted, plus three nearest age/DSL-PA peers, before reading their predictions
or outcomes.

Geury Estevez, age 22 in the stored source, has 112/180/193 DSL PA and 0/2/3 HR
in 2022–2024. Annual transaction coverage is present and no injury entry is
captured, but this is not proof of MiLB medical coverage or health. He is
ineligible for the MLB-history refit. His unchanged 0.239% MLB participation
chance × 84.50 conditional PA gives 0.202 expected MLB PA in 2025; actual is
zero. Rainer Reyes, Isaias Dipre and German Guilarte similarly remain unchanged
at 0.208/0.156/0.137 expected MLB PA with zero actual. None is evidence about
six-year MLB upside. All **24,207 no-debut forecasts** retain exact anchor
probability, conditional PA, PA and value in both arms. This medical candidate
neither improves nor damages their projections.

## Decision and one coherent next step

Reject **this restricted refit as a replacement**, not medical information.
Retain the repaired source and the stronger forecast. Integrity checks pass;
predictive and baseball checks do not. Preserve the failed candidate rather
than retuning thresholds or deleting awkward cases. Reproducing all 120 heads,
independently recalculating scores, checking exact fallbacks and tracing the
players establishes what ran; it does not certify a useful model.

The next modeling design, if pursued, must preserve the stronger performance
training backbone instead of throwing away older/uncovered histories to fit a
standalone medical subset. Missing medical coverage must be explicit, not
fabricated healthy data. That design is not yet tested and may still fail.
Before another fit, reconcile cutoff-known retirement reports against captured
transaction states, starting with Martínez and checking similarly classified
peers. A released player like Belt is not thereby retired. Require dated
affirmative evidence, reversible by a later documented return; do not infer
retirement from next-year zero PA or use an age penalty as a substitute.

Tatis's unconditional health-adjusted forecast remains open. This comparison
does not close it, promote a forecast, add clinical probabilities, reopen 2026,
or establish that the whole hitter model is satisfactory.

Evidence: [scores and uncertainty](../reports/model-evidence/hitter-medical-opportunity-comparison/report.json),
[fixed case selection](../reports/model-evidence/hitter-medical-opportunity-comparison/case-selection.json),
[player traces](../reports/model-evidence/hitter-medical-opportunity-comparison/player-walks.json),
and [completion receipt](../reports/model-evidence/hitter-medical-opportunity-comparison/completion.json).
