# Hitting uncertainty improves offense ranges but the small sample distribution needs repair

2026-10-04. The fixed comparison and seventeen player walkthroughs are complete.
Allowing realized hitting to vary produces substantially better historical
offense ranges than treating a player's hitting rate as certain. Allowing that
variation to shrink as MLB PA grows beats giving every sample the same spread.
However, the Normal approximation permits impossible outcomes at tiny PA and
still misses important readiness and superstar paths. Retain this as development
evidence, not a deployable full-population distribution. No average forecast,
frozen 2026 file or deployed explorer changed.

## What was tested

The [prefit contract](hitter-offense-risk-contract.md) keeps 30,506 forecasts,
all exits and non-arrivals, targets 2017–19 and 2022–25, and the current hitting,
arrival and playing-time means. Every arm uses the previously tested workload
distribution. Workload only fixes hitting rate; constant spread adds the same
Normal rate variance at every future PA; sample dependent spread estimates a
persistent error plus a term inversely proportional to PA. Rate errors are
centered on the existing hitting estimate without post-result recentering.

This targets delivered fixed-event batting plus replacement in common-origin
custom win units, not full WAR or pure batting talent. The labels were independently
reconstructed from eight actual events and the corrected replacement reference.
Future run environments are used only to construct labels. Every distribution's
expected offense is exactly the current point forecast, so these improvements
are not improvements in average WAR predictions or public-system point accuracy.

All 130 actual inner/outer source, chronology and player checks preceded fitting.
Fifty genuinely nested Ridge heads exclude both outer and inner player groups;
35 existing outer hitting heads reproduce the current rate. All nested heads,
35 variance fits and all 30,506 distribution rows were independently replayed.
The calibration uses 153–217 distinct earlier active people per cell, but
19,800 forecasts have no identical refined calibration profile and 30,322 have
fewer than twenty. Global borrowing is an assumption, not specific DSL or
elite-draftee calibration. Sparse cases remain in every headline score.

## Exact matched results

Lower quantile loss is better. This averages P10, median and P90 pinball loss,
with represented target years equally weighted. It rewards useful ranges and
penalizes both misses and unnecessary spread; it is not RMSE. The public row is
the matched player population, not a comparison with Steamer uncertainty ranges,
which are unavailable in the saved point exports.

| Population | Forecasts | Workload only | Constant hitting spread | Sample dependent spread |
| --- | ---: | ---: | ---: | ---: |
| All | 30,506 | .047190 | .048708 | .041233 |
| Public matched | 2,627 | .258569 | .272266 | .221910 |
| Current MLB | 4,541 | .273102 | .283286 | .234540 |
| Upper minors never debuted | 5,454 | .029151 | .028818 | .028082 |
| Lower minors never debuted | 17,852 | .000561 | .000571 | .000559 |
| Previously debuted but absent | 1,766 | .016858 | .017048 | .016376 |
| Thin new draftees | 1,429 | .002925 | .002967 | .002959 |

The sample dependent construction improves all-population quantile loss about
12.6 percent versus workload only and 15.3 percent versus constant spread.
All seven origins improve against both references. Its nominal paired
player-clustered all-population loss difference versus workload only is
-.005957, with 95 percent interval [-.006502, -.005374]; versus constant it is
-.007475 [-.008201, -.006751]. Public matched difference versus workload only
is -.036658 [-.040399, -.032563]. These are repeatedly exposed historical
development results, not a new holdout or selection-adjusted confidence claim.

The proper 80 percent interval score improves .799943 to .632573 overall,
and 4.279376 to 3.267495 on public matches. Public inclusive coverage rises
46.3 to 78.6 percent; constant spread reaches 93.5 percent but has a worse
interval score because it is too wide. Overall sample dependent coverage is
94.4 percent, dominated by the zero atom and non-arrivals; it is not nominal
80 percent calibration. Active-outcome coverage is only 62.3 percent, a survivor
diagnostic rather than a forecast population selected for fitting.

Negative-offense and two-win event scores improve overall. Nevertheless,
the model expects 1,104 negative-offense seasons versus 1,610 observed, and
823 two-win seasons versus 928. Upper-minors forecasts expect nineteen two-win
seasons versus 36, and thin new draftees worsen slightly in quantile loss.
A better average risk score does not settle tails, debut readiness or every cohort.

## Physical and conditional mean limits

There are 1,424 forecasts with more than one percent impossible joint
PA/offense probability, including 875 current-MLB forecasts. Terrance Gore's
is 8.62 percent and Ben Rortvedt's 3.23 percent. These failures arise because a
Normal hitting average at one or a few PA can fall outside the minimum/maximum
event values. The displayed marginal offense interval can look sensible while
the underlying conditional distribution is invalid. No clipping or selective
high-PA deployment was used to conceal this.

Average impossible probability is .52 percent for current MLB players, but
averaging does not erase consequential individual failures. For conditional PA
means of at least 300, maximum mass is below .036 percent; that descriptive
finding is not a predeclared subgroup model or permission to promote one.
The physical-distribution gate therefore fails at low PA despite positive scores.

The [descriptive limits receipt](../reports/model-evidence/hitter-offense-risk/limits.json)
also shows remaining mean dependence on realized workload. For example, one
2024 calibration cell has mean rate residual -4.58 for 1–49 actual future PA,
-1.52 for 50–299, and -.21 for at least 300. Actual PA bands are diagnostics,
not origin-known features or an allowed routing rule. The PA-weighted point
rate need not be an unbiased rate for every realized workload. A zero-centered
error distribution with constant conditional center cannot fully describe this.
Neither fitted variance parameter is a uniquely identified talent variance.

## What the player checks establish

The [seventeen full walkthroughs](hitter-offense-risk-walkthrough.md) retain
actual statistics, input contributions, opportunity paths, calibration, saved
probability mass, independent inverse CDFs and unsuccessful origin-selected peers.

- Soto's offense range becomes 3.62–8.59 and contains 8.20 actual; the constant
  range 0.32–12.29 is unnecessarily diffuse. This is a useful risk example.
- Judge after 2024 improves P90 7.69–8.45 but still misses 9.39 actual. Judge
  after 2016 and Acuña after 2022 retain major star-tail misses.
- Kurtz remains at zero for P10, median and P90 because arrival stays 6.06 percent.
  Reynolds's P90 falls to zero as negative batting mass crosses the zero atom.
  Neither result is a numerical error, and neither is an acceptable readiness fix.
- Langford's actual offense was already in the old interval; widening risk
  worsens his score. Dozier similarly pays a real sharpness cost. These harms
  remain in the review, not excluded because the pooled score improves.
- Rortvedt's almost exact offense mean hides 82 expected versus 328 actual PA
  and overly optimistic hitting. His impossible tails block a clean success claim.
- Belt retains a meaningful chance of no MLB work without a new retirement
  penalty. Franco's missed availability is not repaired by batting variance.
  Chris Davis's hitting collapse also remains badly underweighted.

Peers are selected from origin-known broad stage, age, position, exposure,
MLB quality and prospect rank. They do not fully match exact level exposure,
minor hitting, medical history or elite talent. Kurtz's closest peers are not
equivalent top college picks; their zero outcomes cannot explain away his miss.

## What changes next

Retain the evidence that sample size must affect hitting uncertainty. Do not
promote this Normal law as the final risk model. The next substantive comparison
should use a coherent event-count construction and examine the remaining
workload-related rate bias, with the same point anchors and player checks.
This is not another width sweep or a claim that uncertainty fixes readiness.

Expected PA remains 1,228,733 versus 1,270,493 actual; expected custom offense
4,165.85 versus 4,264.19. Public PA RMSE/MAE remains 138.33/106.41 versus
Steamer 135.38/92.08; MAE is 15.56 percent worse, beyond the plan's 15 percent
working allowance. These known gaps and full player value remain unfinished.
All 31 frozen files verify unchanged, twelve focused tests pass, and the full
goal remains active. No protected outcome or deployed forecast change occurred.

Execution notes are preserved: the first scorer failed on boolean negation
before saving scores; only its event-score arithmetic was repaired. The first
physical-review call failed on a string-versus-Path argument before saving
outputs. The initial finalizer assumed nine scalar checks for the added physical
case although it had then replayed only three; the separate
[review verification](../reports/model-evidence/hitter-offense-risk/review-verification.json)
actually recomputes all nine for every case, proving 153 checks. Original receipts
remain preserved; none of these repairs changes fits, predictions or comparisons.

Evidence: [scores](../reports/model-evidence/hitter-offense-risk/scores.json),
[paired intervals](../reports/model-evidence/hitter-offense-risk/intervals.json),
[execution replay](../reports/model-evidence/hitter-offense-risk/verification.json),
[completed review](../reports/model-evidence/hitter-offense-risk/final-report.json).
Scoring follows [Gneiting and Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf);
the variance model and its baseball interpretation are this project's assumptions.
