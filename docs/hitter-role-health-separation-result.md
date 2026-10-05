# Injury records were distorting the experimental role estimate

2026-10-05. Walkthrough status: complete. Research repair, not deployment.

The experimental reference no longer rewards injury records with hundreds of
extra plate appearances. Travis moves from 800 to 417 PA. Tatis's reported-ready
2023 construction moves from 605 to 550 after the remaining suspension. These
are more defensible calculations, not proof that the whole model is better.
The stronger existing observation forecast still wins the broad playing-time
comparison, so it remains the benchmark. The live explorer is unchanged.

## What was wrong, and what changed

The previous role reference combined age, hitting, workload and job evidence
with six medical/capture inputs. Those inputs mixed reported injury with source
coverage and incomplete roster bookkeeping. In Travis's actual training fold,
only one person had observation-scope interruption and three had recorded
surgery. Standardization made rare flags large extrapolations. The four medical
effects contributed 434 PA to his raw 851-PA conditional prediction, clipped to
800. This was a model/design failure, not a plausible high-end projection.

There was a source problem too. His recorded March 25–September 1, 2016 spell
overlapped 74 actual MLB games and 313 PA. The official log starts May 25 and
sums to the independently recorded 432 annual PA. The captured May roster-status
change has an inconsistent later effective date and does not explicitly say IL
activation. We did not rewrite that transaction or call May 25 clinical recovery.
Instead, a new audit records the contradiction and leaves certified medical
absence days unknown. Existing broad appearance windows crossed the spell's
endpoint, so they alone could not establish this contradiction; the daily log
was needed. This additional source check happened after fitting and changed no
model inputs or choices.

Source: [official 2016 game log](https://statsapi.mlb.com/api/v1/people/581527/stats?stats=gameLog&group=hitting&season=2016&sportIds=1&gameType=R).
The saved [source audit](../reports/model-evidence/hitter-role-health-separation/travis-source-audit.json)
has SHA-256 `b3c9afe3aa602422694f882166cee8981bb9375f47f1b8b3d458f349c729660d` and
binds the raw capture. Historical publication versions are not independently
verified; dates are game dates, not a newly certified medical history.

The new reference removes those six inputs from both role heads. It does NOT
replace unknown health with a healthy flag. Prior PA, age and actual training
outcomes still carry ordinary durability risk. This is ordinary delivered
workload, not a healthy-season maximum; an individual clinical prognosis remains
outside this reference. All twenty other inputs, folds, training subsets,
weights and settings are unchanged. There was one fixed comparison, no tuning.

## Same-player results

The contrast covers the same 1,988 original unrestricted established-hitter
forecasts, seven origins and held-player chronological folds. All 116 future
zero-PA exits remain. The main units are next-year MLB PA, not six-year value or
full WAR. These historical outcomes were already exposed development evidence.

| Measurement | Stronger existing benchmark | Failed medical reference | Separated role reference |
| --- | ---: | ---: | ---: |
| PA RMSE, equal weight per origin | 154.06 | 159.04 | 155.43 |
| PA absolute error, equal weight per origin | 123.31 | 125.35 | 123.81 |
| Participation Brier | 0.03215 | 0.03767 | 0.03550 |
| Participation log loss | 0.12276 | 0.15117 | 0.13435 |
| Total expected PA | 809,086 | 841,997 | 826,632 |
| Actual PA | 821,446 | 821,446 | 821,446 |
| Batting-plus-replacement contribution RMSE | 1.35789 | 1.36130 | 1.35574 |

Removing the unsafe inputs improves PA error against the failed reference:
paired player-cluster interval for MSE change −1,748 to −556. Against the stronger
benchmark, the difference is +425 with interval −244 to +1,083; no improvement
is established. The small contribution advantage is not separately certified,
and better contribution error can conceal offsetting workload/rate errors.

The new reference improves PA error against the stronger benchmark in two
origins (2016 and 2022) and worsens it in five. It fails the predeclared primary,
participation and per-origin guards; only the aggregate-total guard passes.
Exit PA RMSE is 221 versus 211 in the stronger benchmark. A closer total is not
better individual allocation. Do not replace the broad benchmark or conclude
that medical information cannot help: this tests removal of an unsafe encoding.

## Tatis: the arithmetic now has a supported role interpretation

At the January 2023 cutoff, the inputs preserve his 2021 546 PA/42 HR and the
normalized 2020 record (257 actual PA/17 HR in the short season), age 23, MLB
link and 14 AA rehab PA. There is no 2022 MLB batting record. Those are not
equivalent to an unsigned veteran's zero or a prospect's non-arrival.

Under the dated reported-ready assumption, the new conditional role is 627.78
PA before suspension. Applying the known remaining 20 games once gives
627.78 × 142/162 = 550.28 conditional PA. The role participation head is 99.93%,
giving 549.91 expected PA in this conditional construction. Actual was 635.
Retaining the missed-year gap gives a 465.61-PA sensitivity after the same budget.
These two numbers are NOT a confidence interval or a recovery distribution.

The ready construction removes an explained-year gap penalty of about 94 PA;
it does not receive any positive surgery/days/spells increments. The actual
interrupted profile has one training person. Removing the medical variables
improves ordinary role support but does not create evidence about surgery
recovery. The 99.93% figure is not chance of being healthy all season. His
overlapping medical and suspension absence is not charged twice.

Only this conditional research row changes from the observation benchmark.
All other 30,518 observation forecasts are preserved; all original hitting rates
and old artifacts remain intact. The batting rate still projects too high:
the new contribution is 2.925 versus 2.757 actual despite too few PA. That near
contribution result therefore does not certify the hitting estimate. The matched
public cohort excludes the zero-origin MLB-PA row, so this does not close the
Steamer/ZiPS accuracy gap.

## Eighteen retained and mechanically selected player walkthroughs

Unless stated otherwise, numbers below are stronger benchmark → new role
reference → actual MLB PA. These are comparisons, NOT replacements for the
listed players. The fixed player list was retained; the additional largest
gain/harm, false high/low and ordinary cases were selected from errors with
row-ID tie breaks, not to illustrate only wins. These outcome-selected cases
are diagnostics, not independent confirmation.

All actual three-season/level stats, twenty supplied inputs, six omitted-input
range/support checks, both heads' exact contributions, cutoff context and peers
are in the [machine-readable walks](../reports/model-evidence/hitter-role-health-separation/player-walks.json).
Peer selection uses the same origin, eligibility, MLB link and gap category,
then distance in age, prior workload and quality; it never uses future outcomes.
The clinical-span audit intentionally does not infer exact recovery from period
totals. The separate Travis daily audit supplies his missing contradiction check.

- **Tatis, target 2023:** 61 → 550 conditional reconstruction → 635. The ungated
  ordinary-gap role estimate is 531 before suspension; the ready construction
  is described above. No exact interrupted peer exists at this origin. This
  repairs role/calendar logic; individualized health risk is still unresolved.
- **Tatis, target 2024:** known 635 PA/25 HR in 2023, age 24, no new gap.
  Participation 99.67%, conditional 583, expected 581 versus benchmark 603 and
  actual 438. Guerrero, Suwinski and Torkelson compare at 653/697, 489/277 and
  556/381 forecast/actual. No old suspension is deducted again. This miss
  remains; the finite-return change is not applied to it.
- **Hoskins, target 2024:** known 672 PA/30 HR in 2022 after 443/27 in 2021,
  followed by a missed year; age 30, reported MLB link. Probability 99.42%,
  conditional 468 gives 465 versus 367 benchmark and 517 actual. Actual-gap
  support is three people. Lux 371/487 and Stassi 205/0 show why retaining prior
  role matters and why a return is not guaranteed. No validated clinical
  recovery probability is supplied by this contrast.
- **Ellsbury, target 2019:** last MLB 409 PA/7 HR in 2017, previously 626/9,
  age 34, missed year. Probability 90.85%, conditional 320 gives 291 versus
  261 benchmark and zero actual; failed reference was 344. There are two
  matching training people and no exact same-origin peer. A dated spring-return
  expectation did not ensure return. The later February setback is beyond the
  January cutoff and cannot be used to make that forecast zero retroactively.
- **Kang, target 2018:** last MLB 370 PA/21 HR, age 30, year gap. The unrestricted
  role calculation is 98.68% × 281 = 277 versus benchmark 64 and six actual.
  Duffy is the only same-origin peer (303/560). This is NOT an admissible
  replacement: unresolved nonmedical restrictions fail the finite-return gate.
  A strong prior bat does not imply legal clearance.
- **Franco, target 2024:** known 491 PA/17 HR, age 22. The unrestricted role
  calculation is 99.39% × 533 = 530 versus benchmark 545 and zero actual.
  Harris, Greene and Gorman compare at 539/470, 461/584 and 463/402. Ordinary
  talent-profile support of 146 people does not resolve his pending channel.
  This row is outside the unrestricted broad scoring set and is not repaired.
- **Marcano, target 2025:** last MLB 220 PA/3 HR, age 24. He is below the
  reference's 300-PA role threshold and has a hard exclusion. Its numerical
  extrapolation of 13.5 PA is not a valid forecast. Benchmark, retained repair
  and actual are all zero. Castro, Diaz and Araúz are lower-role controls, not
  evidence for overriding the exclusion. No health/role fit can reopen it.
- **Duran, target 2025:** known 735 PA/21 HR after 362/8, age 27. Probability
  99.84%, conditional 583 gives 582 versus benchmark 585 and actual 696.
  Contreras, Devers and Adames compare at 607/659, 591/729 and 610/686. The
  cleared restriction is not charged again; underallocation is a workload
  problem, not a residual suspension budget.
- **Belt, target 2024:** known 404 PA/19 HR after 298/8, age 35, no current MLB
  link in this representation. Probability 57.83% × 270 gives 156 versus
  benchmark 195, failed reference 198 and zero actual. Martinez, Solano and
  Duvall compare at 247/495, 149/309 and 147/330. A lower forecast happened to
  help Belt; these returning peers prevent treating an unsigned good hitter as
  automatically finished. His zero was a surprise, not a mandatory exact call.
- **Judge, target 2025:** known 704 PA/58 HR after 458/37, age 32. Probability
  99.95%, conditional 736 gives 735 versus benchmark 533 and actual 679.
  Ohtani, Ozuna and Rooker compare at 699/727, 615/592 and 531/699. Removing
  medical inputs hardly changes this forecast. Extreme hitting quality still
  raises a linear workload head too far; this is not fixed by clinical cleanup.
- **McLain, target 2024; largest apparent gain:** known 403 MLB PA/16 HR plus
  180 AAA PA/12 HR, age 23. Probability 99.56%, conditional 485 gives 483 versus
  benchmark 598 and zero actual. Casas, Julien and Diaz compare at 478/243,
  435/301 and 370/619. The new head gives less workload to a short established
  record. It did not predict an injury; the smaller error must not be credited
  as validated health prediction.
- **Travis, target 2017:** known 432 PA/11 HR after 239/8, age 25. Probability
  99.54%, conditional 419 gives 417 versus benchmark 530, failed reference
  800 and actual 197. The new conditional calculation is intercept 453, age
  about +32, most recent workload −24, active-history mean −29 and career
  exposure −19, with small remaining role/job terms; no medical increments.
  Realmuto, Cron and Stanton compare at 465/579, 398/373 and 520/692. Ordinary
  role support is 176 people, not clinical-profile support. The absurd boost is
  gone; his specific future durability is not fully explained.
- **Tatis, target 2022; largest false high:** known 546 PA/42 HR, age 22.
  Probability 99.94%, conditional 635 gives 634 versus benchmark 556 and zero
  actual. Soto, Acuña and Riley compare at 697/664, 533/533 and 595/693. The
  later injury/suspension cannot be moved into the January cutoff. This large
  miss must stay scored; the target-2023 budget must not be applied here.
- **Moustakas, target 2018:** known 598 PA/38 HR after 113/7 and 614/22, age 28,
  no current MLB link. Probability rises from the failed reference's 28.8%
  to 90.8%; conditional 391 gives 355 versus benchmark 443 and actual 635.
  The old medical-days input alone subtracted 3.92 log-odds despite a strong
  full return season. Removing medical inputs eliminates that direct penalty;
  all coefficients are refitted, so this is not a causal surgery effect.
  The new conditional MLB-link term is still −89 PA. Morrison, Núñez and
  Gonzalez compare at 378/359, 272/502 and 522/552. Support is 15; unsigned-role
  handling remains deficient rather than solved by this improvement.
- **Sánchez, target 2019:** known 374 PA/18 HR after 525/33, age 25, catcher.
  Probability 99.51%, conditional 404 gives 402 versus benchmark 516,
  failed reference 446 and actual 446. Alfaro, Hedges and Hanson compare at
  327/465, 329/347 and 292/48. Removing the unsafe inputs makes this ordinary
  case worse than the failed reference. That is a real tradeoff, not an excuse
  to restore selected medical coefficients for him.
- **Acuña, target 2024; largest deterioration:** known 735 PA/41 HR after
  533/15 and 360/24, age 25. Probability 99.96%, conditional 717 gives 716
  versus benchmark 589 and actual 222. Recent workload contributes +77 PA,
  recent quality +78 and pooled quality +51. Soto, Ohtani and Alvarez compare
  at 717/713, 605/731 and 585/635. A full-season regular forecast is plausible,
  but the linear high-quality uplift is aggressive and prior interruptions
  matter. This contrast supplies no individualized health model to resolve it.
- **Reynolds, target 2017; largest false low:** known 441 PA/14 HR after
  432/13 and 433/22, age 32, no current MLB link. Probability 60.47%,
  conditional 316 gives 191 versus benchmark 245 and actual 593. MLB-link
  contrast subtracts 83 conditional PA. Moss, Napoli and Pagán compare at
  145/401, 259/485 and 228/0. This is systematic uncertainty in unsigned
  opportunity, not loss of his actual previous statistics; it remains open.
- **Margot, target 2019; mechanically selected ordinary case:** known 519
  PA/8 HR after 529/13, age 23. Probability 99.22%, conditional 445 gives
  441 versus benchmark 442 and actual 441. Lower hitting-quality terms reduce
  workload moderately, not to non-arrival. Swanson, Rosario and Russell compare
  at 450/545, 479/655 and 476/241. This is a sensible role estimate, but its
  error-selected near-exact result is not independent validation.

## Decision and remaining work

Retain the separated reference as a cleaner research role calculation; retire
the failed medical reference from future use, preserving all historical evidence.
Do not deploy either as the broad playing-time model. This is one verified
representation repair, not a win from an algorithm tournament.

Tatis's role/calendar construction is now defensible without an injury bonus.
His unconditional individualized medical availability is still open. The next
work must reconcile dated medical spans with actual appearances before fitting
a separate clinical adjustment. Scope exits and unknown source coverage cannot
be injury-day labels. Do not repeat this feature-removal test, fit an arbitrary
penalty, or proceed to another component while pretending the clinical issue is
solved. Unsigned opportunity and extreme-quality workload saturation are retained
failures for later case repair, not new experiments launched in this checkpoint.

Seventy training checks preceded the seventy fits. Final completion independently
replays both actual-gap and ready calculations from each saved head and rebuilds
the main loss equations. These are integrity checks, not predictive approval.
Forty focused tests passed. The frozen forecasts, completed 2026 evaluation and
explorer are unchanged; the broad project goal remains unfinished.
