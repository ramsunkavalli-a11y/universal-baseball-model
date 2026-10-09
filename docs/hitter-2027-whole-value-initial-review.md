# Historical whole-WAR review: useful result, two reporting repairs

2026-10-09. Review the first fixed assembly before correcting its reference.
This is historical development evidence, not an independent win over public
projections. All 12,432 identities and their PA match the batting/role archives.
Published full-WAR labels cover every participating player; only one PA differs
from official counts (ID 686527, 2025, 269 versus 268). WAR is not manufactured
from that PA discrepancy. Nonparticipants remain in scoring.

The initial combined RMSE is .4823 versus .4953 for the simple full-WAR history
baseline and .5187 for batting plus replacement alone. Most rows are minor
leaguers who do not play MLB, so this is not the headline for major leaguers.
On 1,985 origin-MLB/public matches the errors are 1.1528 WAR RMSE and .7612 MAE,
versus Steamer 1.1642 and .7719. The overall player-clustered interval against
Steamer crosses zero. The right description is approximately comparable on
these archives, with original snapshot-date qualifications—not better than
Steamer. Plain ZiPS workload is a different scenario, not depth-chart opportunity.

## Named source-to-forecast checks

**Judge, 2024: largest harm versus simple history and false low.** The model sees
633/696/458 MLB PA and 39/62/37 HR in 2021–23. It forecasts 536 PA and +3.360
batting wins/600: 30.02 batting runs, 16.64 replacement, −6.67 position, −1.01
running, +.66 fielding, plus the common league reference. That gives 3.943 WAR
versus simple 4.677, Steamer 6.136 and actual 11.213 in 704 PA. Both workload
and elite batting are too conservative. Adding appropriate positional costs
can worsen an already-low batting forecast; omitting those costs is not a fix.
The source-selected peers Carpenter, Brennan and Walker produce 2.354, .421
and −.657 actual WAR, illustrating that ordinary 450-PA outfielders are poor
substitutes for Judge's extreme talent. The model's arithmetic is coherent but
its upper tail is limited. Judge 2023 is a contrary case: 4.212 versus 4.745
actual, while Steamer 6.947 was too high after his exceptional 2022.

**Witt, 2024: largest improvement versus simple history, still a big miss.**
His 632/694 MLB PA, 20/30 HR and 30/49 SB follow strong 2021 AA/AAA production.
642 projected PA award +9.52 batting, +19.94 replacement, +5.08 position,
+5.30 running and +2.68 range runs. Combined 4.228 beats simple 3.607 toward
actual 10.464, but Steamer 4.883 is also far short. Turner, Lindor and Bogaerts
are the origin-selected peers, with actual 3.767, 7.583 and 2.034 WAR. Useful
components do not make a 10-WAR breakout predictable or justify outcome-driven
upward overrides.

**Acuña, 2024: largest false high.** After 735 PA, 41 HR and 73 SB, expected PA
is 588 and batting +3.414 wins/600. +33.47 batting, +18.27 replacement, −6.00
position, +4.30 running and nearly offsetting range/arm give 4.985 WAR against
.955 in 222 PA. Steamer is higher, 7.493. The realized loss of workload is
not evidence the original talent was zero. His peers Betts/Springer/Thomas
also span different outcomes (4.279/1.021/1.270). No future injury override.

**Bailey, 2024: catching makes a meaningful difference.** The source has 353
MLB PA in 2023 plus 120 AA/AAA PA. Batting forecasts −.870 wins/600 and 284 PA.
The batting-plus-replacement forecast is only .468. +4.60 position, +7.00
framing, +1.19 throwing and −1.02 blocking runs bring full WAR to 1.614. Actual
is 4.351 in 448 PA; Steamer is 2.639. Catching is recognized, but workload and
skill regression leave a miss. Catcher peers Vázquez/Sabol/Rogers actually
produce .738/.223/2.130, not the same catching premium for everyone.

**Ohtani, 2024: retain the DH debit.** Recent seasons have 639/666/599 PA and
46/34/44 HR. Forecast 570 PA, +3.044 batting wins/600, +28.91 batting runs,
+17.69 replacement and −13.95 position yield 3.386 hitter WAR. Actual 8.927
in 731 PA is far higher; Steamer 4.030 also misses. His tiny retained old OF
exposure is under one projected out. There is no pitching credit. Ozuna is
another underpredicted DH peer; Soler and Turner have much smaller actual WAR.
Do not erase DH cost to compensate for conservative batting/workload.

**Tatis, 2023: known unresolved baseline failure, not a new discovery.** The
saved anchor still predicts 39.68 PA after 546 MLB PA/42 HR in 2021, no 2022
MLB PA and 14 AA rehabilitation PA. Combined .268 WAR versus 4.033 actual is
driven by that workload failure, not missing range credit. His old MLB role is
retained, but inappropriate prospect-like peers Javier/Guzmán/Hernandez all
fail to arrive. They do not validate the comparison for a suspended established
star. Prior finite-return work already reconstructed 520–605 PA scenarios but
failed its medical/reference-model checks. Do not claim that adding fielding
repairs this or secretly substitute the exposed 605-PA result. Current 2027
Tatis has normal recent MLB evidence; finite-return profiles remain a separate
release limitation requiring explicit scenario/review status.

**Vaughn, 2025: ordinary well-predicted full value.** From 555/615/619 PA and
17/21/19 HR, the model gives 524 PA and modest positive batting (+5.00 runs).
−9.99 positional, −3.19 range and −2.53 running runs bring the old 2.135
batting-plus-replacement forecast to .602 full WAR, versus .601 actual.
Simple history is .622 and Steamer 1.296. This is why full accounting matters
for a bat-first first baseman. Peers Díaz/Schanuel/Harper realize 3.040/1.550/
3.358; the model does not assign the same value to all first basemen.

Eldridge before 2025 is .114 versus negative actual WAR in his brief debut,
while Concepcion has no following-year MLB opportunity. These are near-term
contribution checks, not tests of eventual prospect ceiling. Lovich has no
eligible historical row in this test. Keep that absence explicit.

## What must be repaired before accepting the check

The historical reference accidentally admitted seven zero-origin-PA appearances,
unlike the declared positive-PA reference used in 2027. Kingery/Spangenberg,
Rodríguez/Solak/Kolozsvary, and Hudson/Smith are affected reference identities.
Fix only that cohort definition and recompute the common centering constant.
Do not refit or change any player rate, workload, role, target or eligibility.
Retain these first results and the correction's per-player deltas.

The score helper's `expected_PA` field reports UBM PA even for public arms.
The WAR errors are unaffected. Correct that report metadata to each system's
own PA. In the captured website schema `Pos` is not the CSV positional-runs
field; do not treat it as runs. Only verified WAR and PA are used as labels.
Keep other unverified dashboard fields out of financial/model inputs.

Total UBM WAR by year is 539/562/552 versus 568/570/570 matched actual. Upper
minors are 94.26 versus 64.94 total WAR (45% high); lower minors 6.54 versus
1.62 on very little delivered exposure. Their totals need component/error
inspection, even though the entire league looks reasonable. The active-MLB
aggregate cannot certify rare arrivals or six-year paths.

Player walkthrough complete for the first assembly; reference/report correction
required, release not approved. Continue with the mechanical correction and
its checked cohort totals, not a new parameter search. Exact source rows,
intermediates and outcome-blind peers remain in the compressed player walks.
