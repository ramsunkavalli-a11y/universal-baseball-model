# Overseas hitter integration results and decision

2026-10-04. The complete comparison is reviewed, including its player walks.
Neither new candidate should replace the current model. Participation forecasts
improve, but the playing-time improvement is small and uncertain, hitting
accuracy deteriorates, and important player forecasts have implausible mechanics.
This rejects these fitted integrations, not the usefulness of overseas history.
The broad practical hitter goal remains unfinished.

## What was compared

The [contract](hitter-overseas-integration-contract.md) preserves 30,506 existing
next-calendar-year forecasts for 11,020 people across origins 2016–2018 and
2021–2024. It adds 32 qualified source origins, of which 13 enter evaluation.
There are 63,314 source origins. Newcomers, exits and non-arrivals stay in the
population. Missing old forecasts for additions remain missing, not zero.

The domestic candidate adds the reviewed dated employment and scoped availability
inputs to the existing 251 workload definitions. The overseas candidate also adds
NPB/KBO exposure, component contrasts and the already reviewed translation.
Both fit fixed histogram boosting participation and conditional-PA heads and a
standardized ridge hitting head. The old current model is a separate fixed anchor,
not the domestic arm: changing its talent architecture as well as context limits
causal attribution. Overseas versus domestic is the matched foreign-input contrast.

Each actual fit uses earlier mature targets and excludes the entire test-player
fold. The translated features also exclude the training player's own fold.
There is no translation retuning. Canceled US minor-league 2020 evidence is
missing; real Japanese/Korean 2020 production remains. Target 2020 is excluded.

The hitting label is next year's MLB batting wins above that season's league
average per 600 PA. Delivered value adds a consistent origin replacement reference
and multiplies by expected PA. It is batting contribution, not full WAR, six years
of control, or trade value. No-arrival players have zero delivered contribution;
their unobserved batting rate is not scored as zero ability.

## Matched scores

Lower is better. Overall scores give each origin equal weight, not each PA.

| Metric on the original population | Current model | Domestic candidate | Overseas candidate |
| --- | ---: | ---: | ---: |
| PA RMSE | 60.499 | 60.311 | 60.298 |
| PA mean absolute error | 20.612 | 20.541 | 20.540 |
| Delivered batting value RMSE | 0.43513 | 0.44491 | 0.44978 |
| Participation Brier score | 0.03354 | 0.03252 | 0.03252 |
| Participation log loss | 0.11474 | 0.11152 | 0.11153 |
| Active hitting rate RMSE weighted by actual PA | 1.80481 | 1.86461 | 1.89842 |

Delivered-value RMSE worsens by 2.25% and 3.37%. A 2,000-draw whole-player bootstrap
retains the original origin weights. Overseas minus current value MSE is +0.01296,
with nominal 95% interval [+0.00728, +0.01914]; domestic minus current is +0.00861
[+0.00482, +0.01240]. Overseas minus domestic is +0.00435 [+0.00067, +0.00916].
These are exposed-development intervals, not protection from repeated model choice.

Overseas minus current PA mean absolute error changes by −0.0725 PA, with interval
[−0.1766, +0.0252]. The Brier gain is clearer: −0.001016
[−0.001347, −0.000708]. Better participation probabilities have not established
a useful improvement in delivered player value.

The unweighted conditional-rate RMSE slightly improves for the domestic arm,
3.8723 to 3.8612. That apparent win reverses when weighting by actual PA, and
does not survive delivered-value scoring. Tiny future samples cannot certify
that this new talent head is better.

## Public comparison

On the fixed 2,627 public-matched forecasts, PA RMSE is 138.330 current, 137.943
domestic, 137.901 overseas and 135.379 Steamer. PA mean absolute error is 106.411,
105.632, 105.675 and 92.083 respectively. The new arms narrowly reach the practical
15% MAE tolerance but improve by less than one PA, with paired intervals still
including zero. Crossing an engineering threshold is not model certification.

Delivered-value RMSE is 1.02398 current, 1.05053 domestic and 1.05813 overseas.
Steamer's raw conversion is 1.09011, but different forecast environments, park
adjustments and snapshot dates prevent interpreting that as talent superiority.
On the 2,088 active public cases, PA-weighted common-reference hitting RMSE is
1.72848 current, 1.77828 domestic, 1.80071 overseas, 1.77459 Steamer and 1.75336
ZiPS. Public forecasts were not recentered using future-season averages. ZiPS
archives here are not certified workload forecasts, so their nominal PA is not
scored as expected playing time.

## Cohorts and totals

The original population produced 1,270,493 PA, 4,538 arrivals and 4,185.43 batting
wins across the seven target years. Current forecasts sum to 1,228,733 PA and
4,155.43 wins; domestic to 1,238,854 PA and 3,891.43 wins; overseas to 1,238,539 PA
and 3,879.09 wins. These are matched-population totals, not the entire MLB roster.
Getting closer in total PA does not compensate for losing roughly 300 value wins.

The overseas candidate loses to current delivered-value RMSE in all seven origins,
including 2016–2018. This is not just a 2021/COVID anomaly. Current-MLB value RMSE
goes from 1.06776 to 1.10699. Lower-minors never-debut value RMSE goes from 0.04581
to 0.04639; their actual value total is 9.48 versus 16.2 current and 21.3 overseas.
No claim of improved lower-minors discovery is supported.

For the 253 original origins with foreign history, value RMSE goes from 0.49309
current to 0.51337 domestic and 0.88708 overseas. The 13 additions produce 1,625 PA
and six arrivals; the overseas candidate forecasts only 176.5 PA and 1.40 arrivals.
Their small value RMSE improvement versus domestic, 1.61632 to 1.61210, is uncertain
and accompanies substantially worse conditional hitting. Admission is not a solution
to newcomer forecasts.

The predeclared head substitutions help locate the harm without refitting.
New PA times current talent gives overall value RMSE 0.43542 domestic and 0.43536
overseas, both slightly worse than current 0.43513. Current PA times new talent
gives 0.44481 and 0.44920. Most integrated deterioration comes from the new talent
head; this diagnostic does not approve a post-result blend.

## What the player review established

The [38 player walks](hitter-overseas-integration-player-review.md) preserve fixed,
score-selected and ordinary cases. Lee's 2024-origin older KBO contact feature
contributes +14.17 batting wins per 600 PA to an additive rate forecast of +9.44,
despite 158 newer MLB PA. Ohtani's 2018-origin forecast falls to −6.53 despite a
367-PA, 22-HR MLB debut. Yoshida retains 1,001 recent MLB PA but old NPB features
add +5.12 to his rate accounting. These are integration failures, not evidence
that the underlying Japanese/Korean production is worthless.

The same rare-feature problem occurs domestically: Yordan's largest apparent
gain is driven by +6.01 from 57 older DSL PA; Benintendi's strong old short-season
walk rate contributes −1.26 after a 658-PA MLB season. Marginal shrinkage alone
does not enforce sensible cross-level precision or fading.

Thames, Suzuki, Yoshida and debut Ohtani still receive very low opportunity
forecasts despite professional histories. Suzuki's broad OF role becomes UNKNOWN;
Tatis's known finite suspension still resembles career exit to the fitted heads.
Hoskins improves from 26 to 225 expected PA against 517 actual, a genuine useful
direction with sparse support. Belt's unexpected non-signing and McLain's later
injury are not justifications for invented cutoff-known retirement or injury rules.

## Execution and remaining limits

All 210 actual fit/subset preflights preceded fitting, all 210 saved heads replay,
and original outcome labels reconstruct from complete MLB counts through 2025.
An accounting mismatch and two failed preparations occurred before any fitting;
the [reference correction](hitter-overseas-reference-check.md) preserves the record.
The legacy source reference remains unchanged; the integration uses the benchmark's
completed-schedule replacement reference.

The additional end-to-end future-mutation check for newly materialized additions
finished after fitting started. Earlier admission mutation checks and all actual
preflights preceded fits. Its 2,720 independent input checks and mutation checks
for twelve represented origins pass; no fits, features or choices changed afterward.
This ordering qualification is retained, not described as fully pre-fit evidence.

The participation support table has 59 unsupported and 512 under-20-person rows;
active PA and rate subsets have 1,240 unsupported and 10,992 under-20 rows each.
Twenty people is only a warning threshold. Coarse populated groups do not establish
support for a rare overseas job or fast-track college prospect. Foreign mover
selection, park exposure, partial identities and other missing eligible players
remain unresolved. The raw-history ridge does not contain every contact/Statcast
winner and cannot disprove those approaches.

## Decision and next repair

The review is complete; predictive and baseball checks fail. Keep the current
candidate anchor and these completed research results. Do not deploy either new
arm or overwrite the frozen 2026 forecast or explorer. Seven focused tests and
the 31-file protected-forecast verification support execution, not suitability.

The next repair belongs to the same practical talent/integration milestone:
represent level-translated talent as evidence with explicit sample precision and
recency, rather than unrestricted parallel additive rate columns. New MLB evidence
must demonstrably reduce older foreign and lower-level influence. Preserve useful
current talent branches; do not discard them just to make integration convenient.
For opportunity, distinguish established foreign professional experience and known
finite absence from missing US history or uncertain employment. Broad OF must not
mean unknown hitter. These are coherent representation requirements, not permission
for another tuning sweep, new college collection, or reopening team-record tests.

Public bounded evidence is in `reports/model-evidence/hitter-overseas-integration`.
Detailed source histories and fitted artifacts remain private. No strong full-model,
long-horizon or deployment claim is made.
