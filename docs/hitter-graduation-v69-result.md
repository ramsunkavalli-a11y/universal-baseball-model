# Graduation context helps a little but does not solve hitter opportunity

2026-10-03. All 140 saved heads replayed and twelve actual player reviews are
complete. Three graduation/history inputs are added to the fresher-list model;
hitting, evaluation identities, training folds and model settings stay fixed.
No protected 2026 outcomes, frozen forecast or deployed explorer changes.

## What changed in the forecasts

| Same population | Original PA RMSE | Fresh-list PA RMSE | Graduation PA RMSE |
| --- | ---: | ---: | ---: |
| All 30,506 forecasts | 60.686 | 60.499 | 60.476 |
| 2,627 public matches | 138.488 | 138.330 | 138.196 |
| 274 previously ranked AB graduates | 177.598 | 178.907 | 177.953 |
| Never-debuted upper minors | 56.242 | 55.127 | 55.084 |
| Never-debuted lower minors | 7.828 | 7.966 | 7.973 |

Graduate PA squared-error improves versus the fresher-list model, nominal
whole-player 95% interval -667.61 to -25.39 PA-squared. But the graduate group
still trails the original model. Graduate offense improvement is uncertain;
its interval spans zero. Overall and public PA/offense intervals also span
zero. This is repeatedly exposed development evidence, not final validation.

Public PA MAE falls 106.411 to 106.321, versus original 106.871 and Steamer
92.083. It remains 15.46% worse than Steamer, outside our unchanged 15% working
target. PA RMSE is 2.08% worse than Steamer. Converted offense RMSE is 1.060208
versus original 1.061315 and Steamer 1.118659; the public snapshot/environment
qualifications prevent a batting-talent-superiority claim. These are custom
batting-plus-replacement units, not full WAR or trade value.

Graduates receive 104,409 expected PA versus 114,989 actual, up from 103,654
in the fresh-list model but below original 105,895. Overall appearances stay
near 4,393 versus 4,538 actual. The 2021-origin stress cohort predicts 582
appearances versus 686 and 165,006 PA versus 181,583. Lower-minor opportunity
remains high, upper-minor opportunity low. No totals are rescaled to reality.
Appearance Brier slightly worsens versus V68 while log loss barely improves.

## The player checks

Meadows is not repaired. The raw source correctly identifies 178 MLB AB and
graduation; recent rank history is retained. But neither saved head uses the
added information on his path. Conditional workload is exactly unchanged and
expected PA falls 248 to 247 versus 591. His original 327 was less wrong;
fixed hitting also misses his breakout. A sensible new feature does not prove
the fitted learner made use of it.

Soto after his MLB debut improves 596 to 615 PA versus 659, but the original
already predicted 614. His own graduation/history probe explains only part
of the refit difference. This does not identify Soto before his debut. Fowler
still gets 213 versus zero; being an AB graduate never guarantees a job.

Carroll worsens 462 to 443 versus 645 despite remaining ranked and having no
graduation signal. That change comes from refitting shared trees, not a direct
penalty for his own status. Judge's debut, Kurtz and Langford retain substantial
readiness/talent misses. Sparse precisely matched recent-entry support is not
erased by hundreds of loosely similar training players.

Bader's offense forecast is almost exact, but only because low PA and optimistic
hitting cancel. He gets 142 PA versus 437; the year-end roster zero reduces
both appearance and conditional workload in the saved paths. This warrants a
broader roster/employment-semantics audit, not flipping his source zero to one.
Rortvedt shows the same cancellation. Davis is different: his PA is reasonable,
but extreme hitting decline remains missed. Keep these failure types separate.

## Decision and next work

Retain the source distinction and qualified research result, not a new deployed
model. This particular representation has not solved graduation or the broad
playing-time gap. Keep the original V53/V63 candidate and both extensions
separate; do not stitch subgroup winners together after viewing outcomes.

Close the ranking/graduation batch. Audit whether December roster absence is
being confused with lack of future MLB employment, including unsigned established
hitters, failed peers and defensive-role context. Inspect existing source and
prior tests before one matched correction; no invented roster status, new
college collection or library tournament. Then choose a coherent candidate and
finish the comparative research handoff. The long-range goal stays active.

The [contract](hitter-graduation-v69-contract.md), twelve source-to-fit-to-reality
reviews, all actual inputs, unsuccessful peers, origin totals and nominal
intervals are saved in `reports/model-evidence/hitter-graduation-v69/`.
