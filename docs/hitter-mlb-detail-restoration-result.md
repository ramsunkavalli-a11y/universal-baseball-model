# Restoring separate MLB batting history partly recovers lost accuracy

2026-10-05. The fixed comparison and seventeen player walkthroughs are complete.
Adding back three annual MLB batting summaries and their pooled summary improves
the compressed direct-rate model, but does not beat the incumbent on delivered
batting value. Retain the incumbent and the existing explorer. This is a useful
representation finding, not an approved replacement or a rejection of MLB history.

## What changed and what stayed fixed

The [prospective contract](hitter-mlb-detail-restoration-contract.md) added exactly
four inputs to the same residual Ridge learner. The [source review](hitter-mlb-detail-restoration-source-review.md)
reconstructs them from actual past MLB counts and each source season's observed
league mean. Annual evidence is shrunk by actual PA/(PA+1200); pooled evidence
uses recency weights 1/.8/.6 with that prior applied once. Neither defense nor
replacement credit enters these inputs. A certified MLB absence supplies no
batting evidence, not a measured average hitter. Shortened 2020 counts are not
annualized into fictitious observations.

The common past-production profile, other features, alpha=100, weights, player
folds, chronology, three existing routes, expected PA and all evaluation identities
stay fixed. All 105 candidate heads replay across 35 cells after 105 preflight
checks. The original 30,506 forecasts and thirteen separately scored additions
remain. All original forecast columns match the preceding direct-rate output
exactly; actual labels and eight headline equations reconstruct independently.
No 2026 outcomes, frozen forecasts or explorer were changed. The previously
authorized one-time 2026 evaluation remains final.

The target is next calendar year's MLB batting contribution. Conditional hitting
is batting wins above the future MLB mean per 600 PA, observed only for those
who play. Delivered value adds the unchanged replacement contribution and uses
expected PA; non-arrivals have actual zero contribution but no observed hitting
ability. These are not full WAR, lifetime talent, club-control years or trade value.

## Matched results

Lower error is better. Conditional hitting uses actual future PA weights within
each origin and equal weights across origins. Delivered errors average all
eligible rows within each origin and then origins equally. The test origins are
2016, 2017, 2018 and 2021–2024; outcomes end in 2025.

| Model on the original population | Hitting RMSE per 600 PA | Delivered value RMSE | Delivered value MAE | Predicted total value |
| --- | ---: | ---: | ---: | ---: |
| Incumbent | 1.804813 | 0.435133 | 0.123874 | 4155.43 |
| Past-only count model | 1.813472 | 0.438111 | 0.123708 | 4117.78 |
| Same-input direct-rate model | 1.804223 | 0.436950 | 0.124228 | 4187.11 |
| Direct rate plus four MLB summaries | 1.801956 | 0.436118 | 0.123733 | 4176.98 |

There are 4,538 active forecasts and 25,968 non-arrivals. Actual total value is
4,185.43. All arms predict exactly 1,228,732.51 PA against 1,270,493 actual PA.
Near-correct value totals do not establish correct allocation to players.

Paired player-clustered nominal 95% development intervals below measure candidate
minus anchor **MSE**, not RMSE. Negative favors the candidate. The 2,000 bootstrap
draws preserve the original origin/PA weights. These repeatedly exposed years
are development evidence, not a fresh independent holdout or multiplicity correction.

| Anchor | Hitting MSE change and interval | Delivered MSE change and interval |
| --- | --- | --- |
| Incumbent | −0.010306 [−0.041878, +0.022301] | +0.000858 [−0.000797, +0.002467] |
| Same-input direct rate | −0.008176 [−0.023165, +0.005141] | −0.000727 [−0.001716, +0.000238] |
| Count model | −0.041636 [−0.068154, −0.015390] | −0.001743 [−0.003720, +0.000168] |

The incumbent comparison does not meet the declared requirement to improve both
primary errors. The four-summary change recovers some of the previous loss, but
the recovery versus the direct-rate anchor remains statistically uncertain.

## Cohorts and origins still show important gaps

The same people remain in each comparison. Cohort hitting is conditional on
playing; delivered value includes everyone in that cohort.

| Cohort and forecast count | Active count | Incumbent hitting | Restored hitting | Incumbent delivered | Restored delivered |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current MLB, 4541 | 3596 | 1.705463 | 1.706529 | 1.067759 | 1.071455 |
| At least 600 weighted recent MLB PA, 1995 | 1821 | 1.537229 | 1.543040 | 1.332732 | 1.341435 |
| Upper minors never debuted, 5454 | 730 | 2.563248 | 2.542197 | 0.301695 | 0.299459 |
| Lower minors never debuted, 17852 | 54 | 3.179084 | 3.090793 | 0.045813 | 0.045600 |
| Foreign history, 253 | 28 | 1.880241 | 1.802103 | 0.493093 | 0.496359 |
| Non-arrivals, 25968 | 0 | Unobserved | Unobserved | 0.069388 | 0.072223 |

Upper-minors predicted value falls from 177.49 incumbent to 160.35 restored,
against 196.73 actual. Better individual errors do not imply better cohort totals.
Only 54 lower-minors forecasts reach MLB next year; their conditional score cannot
validate every lower-level hitter's talent or long-term upside. Foreign-history
rate improves while delivered value worsens. None of the predeclared >5% cohort
worsening checks trigger, but that is not a pass on predictive usefulness.

Against the incumbent, hitting improves in four of seven origins and delivered
value in only two, 2018 and 2024. Against the compressed direct-rate anchor,
hitting improves in five and delivered value in six. The distinction matters:
recovering a failed alternative is not the same as beating our best existing model.

The thirteen source additions have six active cases and no invented incumbent.
Restored hitting RMSE is 3.38838 versus direct 3.43398 and count 3.20812. Delivered
RMSE is 1.43483 versus direct 1.43357 and count 1.43564. Predicted restored value
is 5.11 against 8.34 actual. Sparse entry profiles remain unsupported or weakly
supported; this addition test does not solve their reliability or playing time.

## Player checks explain why the partial recovery is insufficient

The [seventeen complete walks](hitter-mlb-detail-restoration-player-review.md)
retain every fixed case, largest gain/harm, false high/low and an ordinary case.
Each has raw source counts, cutoff, actual route/fold, common baseline, full
coefficient trace, unchanged expected PA, reality, support and origin-selected
peers. Sensitivity probes use unchanged fitted parameters; they are artificial
mechanics, not validated substitute forecasts or causal effects.

Judge's 2023 forecast recovers some power: direct +3.511 becomes +3.774 batting
wins per 600, versus +7.558 actual and +3.899 incumbent. His 2016 forecast moves
the wrong way: −0.095 becomes −0.254, versus +5.330 actual. His poor 95-PA MLB
debut is genuine evidence, heavily shrunk, not a source error to erase after his
breakout. Keeping useful information does not make every use of it sensible.

Perdomo's improved latest season is visible. Yet pooled and older negative MLB
history outweigh it, moving −0.637 to −0.693 before his actual +2.728 season.
The representation can show a trend; this fit has not shown that it reads the
trend well. Mature MLB errors are still worse than the incumbent.

Suzuki 2022 remains the largest delivered gain versus the incumbent, but the
restoration lowers an overly optimistic hitting forecast from +2.719 to +2.599
and makes delivered value slightly worse versus direct, because underestimated
PA previously offset excessive talent. Thames and Yoshida remain too optimistic;
restoring their positive MLB summaries does not fix foreign-to-MLB adaptation.
Their joint profile support is zero and three active people respectively.

Ty France is the new ordinary case. His delivered forecast 0.26438 almost equals
0.26399 actual, but projected 87 PA versus 201 actual and −0.025 hitting versus
−1.060 actual largely cancel. This is not a demonstration of near-perfect talent
or opportunity prediction. Tatis has a plausible high conditional hitting estimate
but no next-year MLB PA; boosting that talent worsens his delivered-value miss.

The added terms cannot be read as the entire effect. Adding correlated annual
and pooled summaries relearns other coefficients too. For Judge 2023, new terms
add +0.660 while other coefficient changes subtract −0.397. For Suzuki 2022,
new terms add +0.104 but other changes subtract −0.225, producing a net decrease.
Those are exact fitted arithmetic, not independently estimated causal contributions.

## Public anchors and claim limits

The unchanged matched public cohort has 2,627 forecasts, 2,088 active. Against
future-relative hitting labels, incumbent RMSE is 1.66475 and restored 1.67092.
Under the separate origin-centered public convention, incumbent is 1.72848,
restored 1.71779, Steamer 1.77459 and ZiPS 1.75336. The ranking changes with the
environment convention. Vintage, park and environment differences remain; ZiPS
workload is not certified. Do not claim this proves superiority to public systems.

Integrity is checked, but sufficient training support is not universally established.
Joint full/active counts and restored-feature empirical range checks accompany
each fold. No physical rate-envelope violations occur. An in-range coordinate
or numerous broad peers does not cure a sparse joint profile. Existing contact,
Statcast, foreign and equivalency qualifications remain; raw MLB summaries are
not park-neutral talent. The fixed prior and Ridge scaling are not newly optimized.

## Decision and next work

Do not adopt, blend or deploy this candidate. Keep the incumbent and preserve
all sealed results. The next bounded task is a source-only audit of the seven
original pooled MLB event-rate inputs that the compressed alternatives also
removed: strikeouts, walks, hit by pitch, homers, BABIP, doubles and triples.
If they reconstruct and are correctly interpreted, specify one same-learner
restoration before fitting. That addresses the remaining loss of separate MLB
component information without switching algorithms or tuning to these players.
No automatic fit approval, favorable-cohort hybrid, closed opportunity rerun or
2026 reopening follows. The broader hitter goal remains active.

Machine evidence: `reports/model-evidence/hitter-mlb-detail-restoration/report.json`.
Private complete matrices, model files, range/support checks and receipt hashes
remain under `reports/generated/hitter-mlb-detail-restoration`.
