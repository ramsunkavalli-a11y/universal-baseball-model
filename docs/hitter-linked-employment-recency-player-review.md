# Twelve source-to-forecast checks: employment recency

2026-10-05. Walkthrough complete for this historical development comparison;
the [result](hitter-linked-employment-recency-result.md) rejects the exact
encoding. This is not a new 2026 forecast or full-WAR evaluation.

Eight cases were fixed before fitting. Tatis also supplies the largest gain;
four additional rows supply largest harm, false low/high and an ordinary
near-correct contribution. Extremes are outcome-selected diagnostics, not
confirmation. Origins below mean stats through that season, next-year target.
Cutoffs are saved individual preseason dates, not universally December 31.

Reference means the completed corrected employment model, not the weaker
selected opportunity model. Rate is the same in both arms. Values are
batting-plus-replacement equivalents, not defense-inclusive WAR. Absent players
have unobserved batting rates, not zero talent. Raw three-year PA/HR/K/BB and
all actual inputs/path receipts are preserved privately; compact numerical
summaries, support and peers are in the completed machine-readable report.

| Player / target | Reference chance × conditional PA | New chance × conditional PA | Expected PA, old → new | Actual PA |
| --- | --- | --- | ---: | ---: |
| Tatis / 2023 | 15.4% × 400 | 27.0% × 417 | 61 → 112 | 635 |
| Hoskins / 2024 | 92.1% × 399 | 90.5% × 392 | 367 → 354 | 517 |
| Kang / 2018 | 19.0% × 336 | 42.6% × 336 | 64 → 143 | 6 |
| Ellsbury / 2019 | 77.8% × 335 | 79.1% × 344 | 261 → 272 | 0 |
| Lux / 2024 | 94.8% × 344 | 94.6% × 347 | 326 → 329 | 487 |
| Belt / 2024 | 60.1% × 325 | 64.3% × 323 | 195 → 208 | 0 |
| Kwan / 2022 | 72.1% × 158 | 71.1% × 155 | 114 → 110 | 638 |
| Judge / 2025 | 99.5% × 536 | 99.5% × 547 | 533 → 544 | 679 |
| Albies / 2022 | 90.3% × 618 | 95.6% × 614 | 558 → 587 | 269 |
| Judge / 2017 | 90.2% × 348 | 91.2% × 354 | 314 → 323 | 678 |
| Acuña / 2024 | 99.3% × 593 | 99.4% × 596 | 589 → 592 | 222 |
| Slater / 2023 | 97.8% × 305 | 97.9% × 307 | 298 → 301 | 207 |

Exact paths account for the output of the saved fits. The effects described
below are correlated split accounting, not causal player effects, SHAP values
or isolated changes with parameters fixed. Retraining can alter a prediction
even when that player's replacement input equals the old input.

## Return cases and genuine exits

**Tatis, age 23, cutoff January 26, 2023.** The data have 257 MLB PA/17 HR in
2020, 546/42 in 2021, and only 14 AA PA in 2022. The old employment record is
an August 15, 2021 activation, 1.449 years old, with MLB link but `on_40man=0`.
The data contain finite-absence/career summaries; they do not supply a guaranteed
return date to this tested head. The old classifier's employment-age path is
−.725 log-odds; the new zero-input path is +.583. Other paths change too.
Conditional PA changes 400 to 417; the participation change drives most of the
51-PA gain. Batting stays +1.313 above-average equivalents per 600, contribution
.327 → .598 versus 2.757 actual. This is better, but still implausibly near exit
for a proven young regular. Training support is one matching distinct person
for each head. The only same-origin/category peer is Evan White, who gets
110 → 113 PA and later zero. His shortened 2020 MLB season normalizes above
400 PA, but he has only 104 MLB PA in 2021 and inferior production. The coarse
regular category is not proof of comparable talent, health or restriction.

**Hoskins, age 30, cutoff January 26, 2024.** Known MLB PA/HR are 443/27 in
2021 and 672/30 in 2022, with no 2023 PA. The January 26 agreement record has
age zero; current roster evidence is 40-man/linked. No input scalar changes for
him, yet retraining lowers PA 367 to 354. The old positive 40-man path is 3.504
log-odds; the new 4.007 is offset by other paths. Signed first-team history adds
about 83/86 PA to the conditional head. Fixed batting is +.037 per 600;
contribution 1.160 → 1.119 versus 1.715 actual. The old selected 26-PA forecast
had already been improved by employment evidence: do not claim this as a new
26-to-354 gain. Support is five full/four active people. Lux is the sole exact
origin/category peer. Both return, but two successful cases do not establish
universal recovery.

**Kang, age 30, cutoff January 27, 2018.** Known 2015/16 MLB PA/HR are 467/15
and 370/21, with zero 2017 MLB PA. A September 5, 2016 activation remains the
reported link. Old age 1.395 becomes zero despite unresolved nonmedical evidence
and `on_40man=0`. Participation goes 19% to 43% while conditional PA stays 336;
the old age path −.822 disappears and the new path contributes +.447. Fixed
batting +.262 and contribution .224 → .502 substantially overstate his later
six PA/.0098 contribution. There are zero matching full or active training
people. Peers are Duffy (340 → 346 PA; 560 actual) and Gose (134 → 141; zero).
The historical link encodes neither clearance nor certainty. This opposite-risk
failure prevents describing the Tatis change as a general solution. No
post-result legal exemption is allowed.

**Ellsbury, age 34, cutoff January 27, 2019.** The history is 626 MLB PA/9 HR
in 2016, 409/7 in 2017, none in 2018. A November 1, 2018 activation and 40-man
record give age .238 and link one; the new encoding is zero. The 40-man path
already dominates participation (4.259 → 4.356 log-odds); reducing staleness
cannot establish recovery. Expected PA rises 261 to 272 before zero actual.
Fixed batting −.983 per 600 produces .376 → .393 contribution before zero.
Support is three people in each head. The only category peer is Tulowitzki,
177 → 177 PA before thirteen actual. Both failures are retained: official
roster membership alone is not usable health prognosis.

**Lux, age 26, cutoff January 26, 2024.** Known MLB PA/HR are 381/7 and 471/6
in 2021/22, no 2023 PA. A November 6, 2023 activation plus 40-man evidence gives
age .222, changed to zero. Participation stays about 95%, conditional PA rises
344 to 347. Signed first-team history contributes 95/97 PA; zero current pro
work contributes about −52 in both fits. Fixed batting −.184 gives .909 → .917
contribution versus 1.576 actual. Support is five full/four active people;
Hoskins is the sole exact peer. This small change does not solve recovery
workload even when return probability is already high.

**Belt, age 35, cutoff January 26, 2024.** History is 381/29, 298/8, 404/19
MLB PA/HR in 2021–23. A November 2 release has no current link. Age .233 stays
.233, but the refit raises participation 60% to 64% and expected PA 195 to 208.
Signed first-team work is zero, with conditional-path contributions about
−68 PA; good current quality contributes +42. Fixed batting +.547 produces
.782 → .833 contribution versus zero actual. The rule does not know his later
failure to find a job; some return probability remains baseball-plausible.
Do not force all productive unsigned veterans to zero because of this one case.
Support is 68 full/17 active people. Origin peers Solano, Grandal and Longoria
later get 309, 243 and zero PA, respectively; the group contains returns and exits.

## Prospects, established stars, and an ordinary case

**Kwan, age 23, cutoff March 18, 2022.** History has 542 A+ PA in 2019,
no invented MiLB 2020, and 221 AA plus 120 AAA PA in 2021. In those upper-minor
341 PA he has twelve HR, 31 K and 36 unintentional walks. November 19 roster
activation supplies current linkage, age .326 → zero. Participation slightly
falls; conditional PA stays near 155. The signed first-team-work path is about
−67 PA in both fits because he has no previous MLB workload. That is fitted
history accounting, not a recommendation that debutants deserve a penalty.
His fixed batting −.253 versus actual +1.618 and PA 110 versus 638 are both
misses; contribution .308 → .298 versus 3.720. Support is 357 full/263 active
people. Predeclared peers Hernández, Castillo and Figuera later have zero,
283 and zero PA. The distance ignores minor quality/exposure, so these cannot
certify whether the model handles his exceptional contact profile.

**Judge before 2025, age 32, cutoff January 24.** The known MLB PA/HR are
696/62, 458/37 and 704/58 in 2022–24. The latest activation is July 28, 2023,
age 1.496 → zero, with 40-man evidence. Participation remains almost one;
conditional PA increases eleven. Positive signed first-team and current-work
paths remain. Fixed batting +4.935 survives; contribution 6.046 → 6.175 versus
9.236 actual. Support is 255 full/251 active people. Ohtani, Altuve and Freeman
are origin-selected peers with 727, 654 and 627 later PA. A good known star
should retain large expected work, but this small improvement is not a solved
upper-tail or durability model.

**Albies before 2022, age 24, cutoff March 18.** Selected as largest
contribution deterioration, not a favorite example. Known MLB PA/HR are 702/24
in 2019, 124/6 in shortened 2020, and 686/30 in 2021. MLB link exists while the
captured 40-man field is zero; that zero is not proof of no job. September 9,
2020 activation age 1.521 → zero removes the old −.896 age path. Participation
rises 90% to 96%, conditional PA falls four, net PA increases 29. Fixed batting
+1.437 yields 3.087 → 3.248 contribution versus .753 actual. Forecasting high
work for this profile can be reasonable despite the low later result; no
cutoff-known evidence here proves that later interruption was predictable.
Support is 91 full/90 active people. Rosario, Torres and Meadows later have
670, 572 and 147 PA. Their mixed outcomes caution against outcome-based overrides.

**Judge before 2017, age 24, cutoff January 28.** Largest false low. Known
AAA history is 260 PA/8 HR in 2015 and 410/19 in 2016; his 95-PA debut has four
HR and 42 K. October 3 activation age .321 → zero, current 40-man present.
Both fits already put appearance near 90%; dated scouting paths add about
81/51 and 83/54 conditional PA. Expected PA 314 → 323 is well below 678, while
fixed batting +.264 misses actual +5.330. Contribution 1.107 → 1.139 versus
8.115 remains a joint hitting/workload miss, not an employment-age solution.
Support is 275 full/245 active people. Narváez, Gamel and Kemp later get 295,
550 and 39 PA; their same current MLB category does not match prospect power.
Neither a perfect foreknowledge of this breakout nor a near-exit estimate is
required to conclude the present mechanism remains limited.

**Acuña before 2024, age 25, cutoff January 26.** Largest false high. Known
MLB PA/HR are 360/24, 533/15, 735/41 in 2021–23. April 28, 2022 activation
age 1.748 → zero and 40-man evidence leave participation almost certain and
conditional PA about 595. Signed first-team and current professional-work
paths are large in both fits. Fixed batting +3.826 gives 5.582 → 5.613
contribution before .955 actual in 222 PA. Almost the whole miss existed before
the change; later events cannot become a low preseason prediction by fiat.
Support is 356 full/347 active people. Tucker, Robert and Arraez later get
339, 425 and 672 PA; even promising established peers have variable workloads.

**Slater before 2023, age 29, cutoff January 26.** Ordinary case selected
for closest contribution among actual 200–399 PA rows, NOT closest PA. Known
MLB PA/HR are 104/5 in shortened 2020, 306/12 and 325/7. September 19, 2022
activation age .353 → zero, 40-man present. Both probability estimates are
about 98%; signed first-team history contributes 76 conditional PA. Expected
PA 298 → 301 overstates actual 207. Fixed batting −.116 understates actual
+.681. Contribution .87660 → .88322 nearly matches .88319 through cancellation.
This is why the combined score alone is a poor smell test. Support is 579
full/535 active people; Vogelbach, Trevino and Caratini later get 319, 168 and
226 PA. These varied part-time outcomes are plausible, not an exact workload
promise.

## What these cases establish

The new field is exercised, unlike the earlier unused-observation trial. It
does remove staleness effects in the suspected paths, yet a broad removal also
overrides useful uncertainty in old or unresolved connections. Sparse comeback
training support and incomplete current status remain explicit limitations.
No data bug was discovered that invalidates this exact test; its scope is a
restricted representation comparison, not proof that historical job evidence
cannot be improved. The new encoding fails its primary and stage guardrails.
Correct facts and useful hitting stay; the candidate is not deployed.
