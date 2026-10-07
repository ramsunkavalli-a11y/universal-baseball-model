# Minor fielding samples now receive more sensible weight

The replacement count calculation passes its historical input-calibration
check. It fixes the two reviewed examples where tiny fielding samples received
implausibly large influence, and improves prediction of later counts in each
tested season. It is a research input recipe, not a new MLB defensive grade,
full-WAR improvement or deployment approval. The frozen forecast is unchanged.

## What changed

The old shortcut estimated variation between players from their observed rates,
then subtracted an approximation of count noise. A player making one error in
one chance could inflate that variation enough to make another player's six
chances look highly reliable. The replacement estimates the probability of the
actual counts, retaining each denominator. At a fixed group mean, one chance
cannot identify how much players' underlying rates vary.

Both recipes use identical dated reference membership and held-player exclusion.
The replacement pools a reference person's counts across the available three
calendar years; the old calculation averages that person's record-level moments.
That pooling change is part of the tested recipe. The gain cannot be attributed
only to choosing a different optimizer. All reference parameters are estimated
before looking at the following season's counts.

Errors use a beta-binomial calculation, while assists and outfield putouts use
a gamma-Poisson calculation. Current counts update the selected reference prior
directly. Sample weight is therefore part of the prediction, not a separate
feature that a regression can ignore. When the source likelihood cannot justify
an individual-rate distribution beyond the point reference, no personal
adjustment is made. That is not proof that the players have identical talent.

## Historical result and coverage

The target is the following minor season at the same position and level,
conditional on its recorded number of chances or outs. The target exposure is
used only for scoring the count distribution. Moving up, changing position,
exiting or lacking a record is unknown quality, not a predicted zero.

| Origin | Eligible people | People with scored counts | Old count loss | Revised count loss | Paired change and 95 percent interval |
| --- | ---: | ---: | ---: | ---: | --- |
| 2018 | 2,989 | 1,362 | 1.74648 | 1.69228 | −0.05420 [−0.06542, −0.04387] |
| 2021 stress | 2,801 | 1,373 | 1.60476 | 1.55707 | −0.04769 [−0.05790, −0.03723] |
| 2022 primary | 2,741 | 1,367 | 1.63389 | 1.57229 | −0.06159 [−0.07360, −0.05013] |

Count loss is average negative log probability: lower means assigning better
probabilities to the actual counts. People receive equal total weight across
their scored position, level and channel records. Intervals resample distinct
people 2,000 times, not individual repeated rows. These cohorts are development
evidence; 2026 results were not used.

In the primary season, each of the four count channels and each of the six
observed source levels improves average count loss. Neither recipe makes an
impossible scored prediction. The revised 90 percent count intervals have
person-balanced coverage of 95.81 percent, compared with 94.56 percent before; central
intervals for discrete small counts can conservatively exceed 90 percent. No
channel or level with at least 100 scored people fails the contracted loss or
coverage checks. This does not establish exact probability calibration in every
age, position or tiny sample group.

The full ledger retains 73,069 channel records. In 2022, 8,354 have positive
matching target exposure, 15,913 have no recorded same-level/position target,
and 136 have recorded zero exposure. The latter two groups are not scored as
zero skill. Across 5,352 reference distributions, 4,130 select finite count
variation, 1,208 select a point reference, one is an all-zero point reference,
and 13 optimization failures visibly use the old matched calculation. No
selected finite prior hits the numerical parameter bounds. Those fallbacks
remain a limitation; the result does not certify every individual weight.

## Player checks and misses

Nine focal cases and three origin-selected peers per case cover 36 distinct
player origins. Peers match origin, position, source level and channel, then
age distance, current log-denominator distance and player ID. Every modeled
position and level is retained, along with dated source records, priors,
individual weights, count distributions and following-season paths. Outcome-
selected gains and misses are diagnostics, not independent confirmation.

**Dominic Canzone:** his 2022 complex right-field stint has six chances and no
errors. Its 45-person reference contains Jorge Ona and Anthony Walters making
one nonthrowing error in one chance, alongside other one-chance records. The
old calculation gives Canzone 94.49 percent personal weight. The new source
likelihood selects a point reference and gives the stint no personal adjustment.
His AA/AAA, left-field and first-base evidence stays separate. Gary Mattis,
Ruben Cardenas and Ben Norman also stop receiving large personal weights from
four or five error-free complex chances. None has a matching complex RF target
the next season; Canzone reaches MLB. This fixes a source-weighting failure,
not evidence that their later MLB defensive quality is known.

**Patrick Frick:** his 2022 AA third-base stint has six errors in sixteen
chances, five nonthrowing, over 171 outs. The old nonthrowing-error weight is
62.78 percent; the replacement is 4.90 percent using 177 reference people.
The predicted error rate falls from 21.09 to 4.56 percent. In 2023 he has zero
errors in five AA third-base chances; count loss improves from 1.09176 to
0.23194. He spends substantially more time at second base and never supplies
an MLB quality label here. Greg Cullen's one error in sixteen chances also
receives much less influence; Devin Mann and Coco Montes have no matching
AA third-base target, and Montes reaches MLB at other positions. Five future
chances cannot certify Frick's talent. The earlier minus-13-run MLB grade has
not been recalculated in this source test.

**Jacob Young:** 113 Single-A CF putouts over 1,224 outs previously supplied
no individual signal. The replacement gives this evidence 35.72 percent weight
and a predicted rate of 0.08263 putouts per out. Young advances through High-A,
AA and AAA to MLB CF; none of those is a matching Single-A target. Peers
Wilfredo Flores, Logan Cerny and Brady Allen also gain moderate source weights
but do not reach MLB in the following season. Putout traffic depends on the
pitchers and play difficulty; the weight is not a probability of MLB skill.

**Anthony Volpe:** four nonthrowing errors in 384 AA chances receive 38.71
percent weight rather than 95.07 percent; AAA evidence remains separate.
His 2023 workload is MLB SS, so the same-level target is unknown. Ronny
Mauricio also leaves AA. José Tena and José Rodríguez have matching AA SS
counts, and both improve count loss. Their MLB position appearances do not
establish equivalent long-term defensive quality.

**Jacob Buchberger, largest person-balanced gain:** a 78-out AA third-base
cameo with seven assists gets only 4.90 percent personal weight. His next AA
season produces 184 assists in 2,395 outs. Count loss improves from 9.56804 to
5.47886, mainly because the revised distribution allows more persistent
variation than the old point reference. The observed count still exceeds the
revised 90 percent interval's upper bound of 182. Rafael Lantigua and James
Nelson leave this scope; Oliver Dunn's matching small sample slightly worsens.
This is better uncertainty handling, not a perfect mean or an MLB talent win.

**Luis Ogando, largest person-balanced harm:** five throwing errors in 49 DSL
third-base chances receive 18.19 percent weight instead of 83.09 percent. The
new rate is 6.41 percent; the following season has six throwing errors in just
21 chances. Both underestimate that count; revised loss worsens from 4.00835
to 6.14211 and its count interval is narrower. His position use also shifts
toward first base. Peer Yohenny Mata instead makes no throwing errors in six
later third-base chances; Wesley Zapata and Frederick Marte lack matching
targets. The revised recipe can shrink persistently poor small-sample fielders
too strongly. No player override or future-selected sample floor was added.

**Luis Colon and Angel Basabe, largest raw-rate errors:** Colon supplies three
DSL SS assists in 78 outs, then none in a five-inning SS cameo. Basabe has zero
High-A RF errors in four chances, then one error in his only following-year
chance. A one-chance outcome has an observed rate of 100 percent; that is not
a credible underlying talent estimate. Their origin-selected peers include
returning and unmeasured players. These deliberately retained rate tails show
why count probabilities and opportunities matter more than fitting a tiny
observed percentage. Error-per-chance and play-per-out rates are different
units, so their pooled raw-rate ranking is only a diagnostic selection rule.

**Tucker Bradley, median absolute raw-rate error:** zero errors in thirteen
AA RF chances predict a 1.24 percent error rate, followed by zero in sixteen
chances. Count loss slightly worsens, 0.16428 to 0.19473. Fabricio Macias and
Matt Gorski instead make later errors and improve; Hunter Markwardt lacks a
matching target. The average improvement is not a universal player improvement.

## Verification and remaining limits

The separate verifier reconstructs all source aggregates, exact reference and
evaluation membership, held-person exclusions, old moments, saved likelihood
objectives, selected priors, posteriors, predictive probabilities and intervals.
It replays every forecast and the origin/group scores and 2,000-person
bootstraps. Forty-seven source/count regression tests pass, including one-trial
concentration invariance, proper probability mass, impossible observations,
zero exposure and changing future counts without changing source eligibility.

Fits are stored in a lossless archive rather than thousands of repository
files. All 5,352 archived compressed entries reproduce their original hashes;
local originals remain. The executed initial verification and player-review
sources are preserved. A sibling player replay separates archive access into
a fully hashed helper and reproduces the original selected cases and traces
without any model refit. Use `scripts/minor_count_archive_access_v20.py --restore`
to restore missing fit files before running the original verifier.

The source likelihood assumes a shared short-window rate within each reference
scope. It does not model parks, weather, pitcher batted-ball traffic or the
difficulty of opportunities. Reference people can include MLB returners in the
minors. Reference-parameter uncertainty is not propagated; a fitted point prior
must not be sold as certainty about latent talent. Only same-level returners
provide these scored counts. Unknown later quality stays unknown, especially
among lower-level prospects and position changes.

## Decision and next component work

Retain this frozen count-reliability recipe for the separately contracted
future-MLB-quality correction. Do not change the existing age/position/level
baseline's penalty while adding counts. Unsupported correction profiles must
fall back to that baseline through a real mechanism, not only a warning flag.
The next test must check whether the repaired count evidence identifies later
MLB ability; these source scores cannot answer that question.

The active defense goal remains open: supported MLB-history range, throwing,
receiving, double plays, catcher skill, position movement, lower-minor talent
paths and delivered-value integration still need a coherent combined layer.
Frozen forecasts, explorer, Lovich batting repair and 2026 selection are unchanged.
