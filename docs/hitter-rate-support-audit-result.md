# What the cross level hitting model actually knows

2026-10-03. The source audit confirms an important limit: many positive hitting
estimates for young lower-level players have no directly comparable next-year
MLB participant in their actual training fold. They must not be sold as measured
MLB ability. This is not a new loss result, a claim that the prospects lack
talent, or permission to erase them from the model. The earlier translated
performance alternative has useful development evidence and remains available.

No new model was fitted. All 30,506 current forecasts and their scores remain
unchanged. Thirty-five current hitting heads were replayed; sixteen cases
were reassessed with exact age/level accounting, linked to their full
[stats and model walkthroughs](hitter-talent-opportunity-player-walkthrough.md).
The three existing alternative heads were also replayed for each case.

## Coverage in actual training folds

Dominant level means the bucket with most origin-season PA, not the highest
level reached or a replacement model stage. Langford therefore has dominant
A+ exposure despite having meaningful AA/AAA history, and Kurtz A despite
15 AA PA. The age/level/debut groups are descriptive, not exact talent peers.
Training counts are distinct people within each actual fold, not repeated
seasons or league totals. All labels are mature next-year MLB performance;
no later 2026 information is used.

| Scope | Forecasts | No active age and level analogue | Fewer than 20 analogues | Positive rate estimates | Actual next year participants |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entire population | 30,506 | 11,457 | 18,684 | 8,359 | 4,538 |
| Never debuted with dominant A+ or lower exposure | 18,812 | 10,334 | 16,578 | 6,704 | 125 |
| Same exposure below age 21 | 10,344 | 8,131 | 10,177 | 5,591 | 41 |
| Positive rates in that under 21 group | 5,591 | 4,852 | 5,573 | 5,591 | 14 |

The A+ or lower definition includes separate recorded rookie buckets and DSL,
not MEX or absent current exposure. It is not identical to the existing
explorer's lower-minors stage. Counts are forecast rows; people repeat across
origins. Twenty is only a warning cutoff, not a sufficiency guarantee. A rare
actual next-year arrival cannot validate hypothetical ability for thousands
of others, nor does immediate non-arrival mean poor eventual talent.

In that positive under-21 group, the median combined linear/quadratic age term
is +1.085 batting wins/600. The median net named-level term is +.002. These
are exact signed linear sums, not causal importance, variance explained or
percentages of the forecast. Positive and negative terms can cancel. The
remaining terms include pooled MLB quality, legacy work/quality, draft, position
and other metadata: for established hitters, much of the real performance
signal is there rather than in the named-level sum. Do not conclude that the
model ignores production from this column classification.

## Sixteen actual player checks

All units below are custom batting wins above an average MLB hitter per 600 PA.
The rate equals intercept plus the three displayed sums. The linked original
walks provide actual dated level counts, inputs, outcomes and four peers each;
these additional rows explain the new support and age findings rather than
replace those walks with an error leaderboard.

| Case and source row | Dominant level | Distinct active analogues | Rate | Age sum | Named level sum | Remaining sum |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Aaron Judge 2016 23934 | AAA | 236 | -.040 | +.309 | +.345 | +.050 |
| Greg Garcia 2017 28478 | MLB | 294 | -.157 | .000 | -.086 | +.556 |
| Pete Alonso 2018 33263 | AAA | 48 | +.286 | +.445 | +.331 | +.178 |
| Jeremy Peña 2021 43288 | AAA | 59 | -.064 | +.493 | +.247 | +.100 |
| Juan Soto 2021 43306 | MLB | 146 | +4.069 | +.537 | -.107 | +4.402 |
| Fernando Tatis Jr. 2022 47261 | AA | 59 | +1.289 | +.426 | +.082 | +1.556 |
| Oneil Cruz 2022 47281 | MLB | 152 | -.086 | +.426 | -.087 | +.349 |
| Brandon Belt 2023 50571 | MLB | 96 | +.686 | -.729 | -.093 | +2.419 |
| Wander Franco 2023 51820 | MLB | 168 | +1.035 | +.572 | -.149 | +1.571 |
| Matt McLain 2023 51984 | MLB | 168 | +.915 | +.449 | +.233 | +1.192 |
| Christian Encarnacion-Strand 2023 52609 | AAA | 190 | +1.006 | +.493 | +.411 | +1.005 |
| Wyatt Langford 2023 53164 | A+ | 97 | +.688 | +.773 | +.569 | +.249 |
| Aaron Judge 2024 54849 | MLB | 584 | +4.534 | -.486 | -.118 | +6.060 |
| Matt McLain 2024 55824 | Absent | 30 | +.251 | +.329 | +.157 | +.750 |
| Nick Kurtz 2024 57052 | A | 15 | -.063 | +.697 | +.133 | +.092 |
| Juneiker Caceres 2024 58477 | DSL | 0 | +.499 | +1.486 | +.032 | -.110 |

**Caceres is the clearest unsupported extrapolation.** His 167 DSL PA with
18 K and 17 walks are real, but his +.499 number equals intercept -.910
plus age +1.486, level +.032 and other -.110. No age-at-most-17 DSL never-debut
person in that fold supplies a future-active label. Zero next-year PA is
reasonable; it cannot judge eventual ability. Peers Amoroso, Baker, De La Cruz
and Castillo also do not arrive, without establishing the validity of the rate.

**Kurtz has sparse, not nonexistent coarse support.** Fifteen earlier age-21–23
players with dominant A exposure supply 912 target MLB PA. But the finer
draft/rank/thin-history intersection has zero active people. His estimate is
-.985 + .697 + .133 + .092 = -.063. This distinction prevents claiming that
the general level curve proves adequate elite-college-entry support. The
comparison peers have much weaker pedigree, and the 489-PA arrival is not
repaired by a broader group count.

**Langford, Alonso and Peña are not explained away by lack of data alone.**
Their coarse age/level groups have 97, 48 and 59 active people. Langford's
actual 80 upper-minors PA contributes within a +.569 total level sum, while
the new-draftee rank intersection still lacks close active examples. Alonso's
574 AA/AAA PA and Peña's short 133-PA AAA power sample remain actual predictors.
Their +.331 and +.247 level sums do not turn into enough expected workload:
215/47 current PA before 693/558 actual. Some support exists, but representation,
conditional opportunity and player-specific context still matter.

**Judge, Soto and Belt demonstrate retained production rather than a universal
youth bonus.** Judge 2024 receives a negative age sum but a +6.060 remaining
sum containing strong observed MLB performance, yielding +4.534. Soto +4.069
also has extensive MLB evidence. Belt's older age sum is -.729 while productive
history remains favorable. None justifies identifying the level-sum column as
all hitting information, or declaring Belt's later non-employment predictable.
Judge's earlier AAA-dominant 2016 case has 236 coarse analogues but very few
matching ranked/debut examples; the broad count does not solve his breakout.

**McLain, Tatis and Franco separate talent from availability.** McLain's 2024
absent-exposure group has thirty earlier active people; rate +.251 still
retains earlier performance. Tatis's fourteen-AA-PA return year puts him in
dominant AA but +1.289 retains his established hitting. Franco's +1.035
describes performance rather than administrative eligibility. Their existing
workload misses cannot be repaired by claiming this rate is unaware of talent.
The source listing/status qualifications and unmatched medical/legal peers remain.

**Cruz, Encarnacion-Strand and Garcia retain the tradeoffs.** Cruz's largest
realized PA gain is not knowledge of his later absence. Encarnacion-Strand's
dominant AAA exposure still includes 241 MLB PA, and better forecast hitting
increased workload incorrectly for the realized season. Garcia's net level term
is negative but legacy workload/quality lives in the remaining +.556; his
near-exact PA forecast still missed batting production. These are not reasons
to select a model per player or erase inconvenient outcomes.

## Earlier evidence worth preserving

The [translated and ranking comparison](hitter-talent-bridge-v74-result.md)
has the same identities and a compatible future-MLB rate target after its
explicit score-unit correction. Its translated linear arm improves debutant
rate RMSE 2.6144 to 2.5831, about 1.2%, with a favorable nominal development
interval. Fixed-opportunity delivered-value improvement remains uncertain.
Keep it as an evaluated alternative, not a discarded component or full-value
winner. Established-player primary forecasts remain exactly the anchor.

Selected saved-head replays confirm Kurtz -.063 to +1.024, Alonso +.286 to
+.592, Langford +.688 to +1.439 and Peña -.064 to -.300. These are not all
gains: Langford overshot his observed first-season hitting; Peña's rate falls.
Caceres +.499 becomes -.142 in the translated linear arm, and -1.217 in
the tree arm. The apparent age extrapolation is tempered, but no direct
active age/DSL support has appeared. A connected level graph and a less
optimistic number do not establish low-level true talent. The supplementary
receipt retains age/ranking/translated contributions of the linear alternatives,
actual supported fractions, and all raw versus primary predictions.

The [direct future-MLB contact comparison](practical-hitter-contact-v41-result.md)
already reviewed actual players and retained the full population. Its added
shape ridge was slightly worse overall and uncertain; the tree was worse.
It used older count/scale and workload sources, had exact fallbacks in all
2016 forecasts and did not test park-neutral shape-by-result. Its result cannot
reject every contact/context design, but does not supply a drop-in winner.
The earlier positive minor-target gradient test is a different estimand and
cannot answer future MLB hitting or delivered player value.

## What must change before another fit

Do not launch another library sweep or clip age to force favorable player
rankings. Specify and test a supported cross-level talent representation,
retaining the current full-history anchor and translated alternative. The
contract must distinguish current next-year MLB contribution from talent at
eventual arrival; short-term non-arrival cannot measure a DSL player's latent
MLB batting rate. Progression/development evidence can help bridge levels, but
requires origin-safe labels and mature follow-up, not a universal youth bonus.

The audit completes the source/reasonability checkpoint, not the full hitter
goal. Public workload error, readiness, medical/administrative and rights
coverage, conditional performance risk and complete player value remain
unresolved. No current forecasts, frozen 2026, research/deployed explorers or
models are changed. The next fit remains unperformed and needs its own locked
target/support contract. Evidence:
[audit receipt](../reports/model-evidence/hitter-rate-support-audit/report.json),
[alternative replays](../reports/model-evidence/hitter-rate-support-audit/alternative-replays.json),
[completed review](../reports/model-evidence/hitter-rate-support-audit/final-report.json).
