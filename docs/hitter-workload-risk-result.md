# Playing time uncertainty improves some forecasts but leaves readiness gaps

2026-10-03. The fixed uncertainty test and fourteen actual player walkthroughs
are complete. Retain the new distribution as qualified workload-risk research,
not a validated whole-population component or deployable player ranges. It
improves proper scores overall and for upper-minors prospects, but does not
repair playing-time means, missing readiness or return probabilities. The
current candidate, explorers and frozen 2026 forecast are unchanged.

## The question and comparison

The [prefit contract](hitter-workload-risk-contract.md) asks whether a learned
spread around current conditional workload produces useful next-calendar-year
MLB PA risks. Every current appearance probability, active PA mean, expected
PA, hitting estimate and expected offense is held exactly fixed. There are
30,506 forecasts for 11,020 people, with targets 2017–19 and 2022–25. Exits and
non-arrivals remain. The canceled 2020 minor season is not poor performance;
2020 MLB targets are excluded as in the current experiment, with historical
short-season MLB source information preserved where used.

The distribution puts exactly 1-p probability at zero PA. Given appearance,
PA follows 1 plus a beta-binomial count on 799 trials. Its mean is the current
conditional PA forecast; a single earlier-outcome concentration estimate per
outer cell sets spread. No widths, group parameters or means were selected
after scores. Support to 800 PA is an engineering bound, not a physical claim;
the maximum observed source target was 753.

The mean-matched binomial reference is deliberately narrow and weak, not a
public projection system's risk model. The stronger older paired forest uses
different features, participation probabilities and means. Its comparison
therefore cannot identify the new spread's isolated effect. Public point
forecasts provide no comparable uncertainty ranges; the public rows below
refer to the matched population, not Steamer or ZiPS quantile forecasts.

## Proper scores and uncertainty

Primary loss averages the PA quantile losses at P10, P50 and P90, then weights
represented target years equally. Lower is better. This is not RMSE or mean
absolute PA error. Parentheses show the nominal player-clustered 95% interval
for new loss minus forest loss; a negative difference favors the new method.

| Population | Rows | New | Narrow | Older forest | Difference and interval |
| --- | ---: | ---: | ---: | ---: | --- |
| All forecasts | 30,506 | 6.0963 | 8.0639 | 6.2290 | -.1327 [-.2045, -.0676] |
| Public matched players | 2,627 | 31.1812 | 43.6428 | 31.4770 | -.2958 [-.7203, +.1718] |
| Current MLB | 4,541 | 31.8753 | 44.2400 | 32.3470 | -.4717 [-.8555, -.0715] |
| Upper minors never debuted | 5,454 | 5.7954 | 6.3520 | 6.1940 | -.3985 [-.6156, -.1871] |
| Lower minors never debuted | 17,852 | .1472 | .1486 | .1483 | -.0011 [-.0105, +.0095] |
| Previously debuted but absent | 1,766 | 3.5781 | 3.8752 | 3.4074 | +.1707 [-.0624, +.4278] |
| Thin newly drafted players | 1,429 | .5844 | .5680 | .5386 | Not a predeclared interval |

The overall reduction versus forest is about 2.13%, and upper-minors reduction
about 6.43%, in this particular quantile score. Six of seven origins improve;
2023 origin worsens slightly. All historical outcomes have been repeatedly
exposed during development. The nominal intervals do not account for this
selection history, shared season shocks or uncertainty in refitted parameters.
They are not a new holdout confirmation.

The 80% interval score also improves overall, 90.970 forest to 89.068 new,
and upper minors, 102.896 to 95.536. Public matched scores are nearly tied,
434.656 to 432.348. Full-distribution CRPS improves against the mean-matched
binomial, 16.803 to 13.577 overall; no comparable full forest PMF is available
for this CRPS contrast. At least 400 PA Brier/log loss are slightly better
overall than forest, but the expected number reaching 400 falls short.

Inclusive P10–P90 coverage is 96.39% overall, 87.21% in public matches,
93.02% in upper minors and 99.75% in lower minors. These are not evidence of
nominal 80% calibration: discrete mass at zero and the many non-arrivals dominate
coverage. Active-outcome coverage is 77.07%, a descriptive survivor slice, not
a population selected for fitting or a forecast conditioned on actual activity.
The loss and width penalties, not coverage alone, govern the comparison.

## Player checks and reference attribution

The [fourteen complete player walks](hitter-workload-risk-player-walkthrough.md)
trace dated counts, every actual input, saved point paths, calibration evidence,
complete probability mass and outcome-blind peers. They explain the limitations:

- Langford's P90 rises to 523 PA from narrow 372 and forest 238, closer to
  557 actual. Alonso's rises to 459, but actual 693 is still far higher.
- Kurtz's p remains only 6.06%; P10/P50/P90 are all zero before 489 actual.
  That is correct mixture arithmetic, not an acceptable readiness forecast.
- Hoskins's p is 10.07%. His P90 maps to the bottom 0.65% of the positive
  distribution; widening that distribution lowers P90 from 228 to sixteen
  before 517 actual. This is the largest harm against both references, not
  a scoring bug or a reason to tune his interval individually.
- Judge after 2024 has actual 679 within the new 315–720 range, but the forest
  has better quantile loss and a closer median. Franco's wider positive range
  cannot repair 99.05% appearance odds before zero PA. Belt's zero is given
  meaningful probability without wrongly treating his unsigned status as retirement.

Ortiz supplies the largest forest gain because the current candidate already
has a retirement rule. The [explicit post-result attribution check](hitter-workload-risk-attribution-check.md)
keeps the original headline and applies the same origin-known zero policy
to fifteen forest reference rows. Those rules account for 9.68% of the net
advantage. The remaining all-row difference is -.1199 [-.1920, -.0557]. This
check is descriptive, not a new selected model; other context and mean
differences remain. The new spread receives no credit for introducing retirement.

## Means and cohort problems remain unchanged

Expected total PA is still 1,228,733 versus 1,270,493 actual, with 4,392 expected
appearances versus 4,538. Fixed-event offense totals remain 4,165.85 versus
4,264.19 in custom batting-plus-replacement units, not full WAR. The public
PA errors remain 138.33 RMSE and 106.41 MAE versus Steamer 135.38 and 92.08:
MAE is 15.56% worse, outside the plan's 15% working allowance.

Across all forecasts, the new distribution expects 1,319 instances of at least
400 PA versus 1,473 actual; the forest expects 1,428. Upper-minors entrants
expect 32.5 such seasons versus 59, with expected total PA 74,239 versus 92,891.
Lower-minors entrants instead expect 7,055 PA versus 5,194. Thin newly drafted
players expect 746 versus 1,647 PA, although 7.39 expected appearances is close
to seven actual. Correct aggregate debut counts can hide incorrect identities
and workloads. These are totals over the fixed cohort, not an MLB-wide budget.

## Execution support and decision

The [prefit support receipt](hitter-workload-risk-readiness.md) prepared 95
nested contexts excluding both outer and inner held-player groups. Fifty
unique heads were reused only after exact membership checks, independently
replayed, and all 35 concentration fits recomputed. All current forecast columns
remain bit-identical. Concentrations range 4.2436–5.8214, with one explicitly
floored calibration label retained. Fourteen cases include 28 point-head replays
and 42 independent scalar quantile checks. These are execution evidence, not
predictive validation by themselves.

An initial scorer call failed on constructing reference columns, before any
scores or selection were saved. The argument-unpacking error was corrected;
no fitted recipe, forecast, cohort, target or comparison changed. The successful
rerun and its source hash are retained. Original fit and verification receipts
still truthfully say review was pending then; a separate final report records
the completed review.

Each outer cell has 153–217 distinct earlier active calibration people. However,
8,420 forecasts lack an earlier active refined-profile analogue, and 12,820
have fewer than twenty. Global calibration counts do not establish supported
risks for every DSL player, new elite draftee or absent MLB regular. Peers also
do not control fully for talent, medical history or eligibility.

Retain this as limited research evidence for active-workload spread. Do not
promote it as calibrated uncertainty across all levels: public gain is uncertain,
absence/thin-entry scores are worse against forest, and material readiness
problems remain. No new explorer ranges, mean replacement, frozen-forecast
change or protected 2026 outcome use occurred. Earlier incidental web exposure
disclosed in project status still qualifies any future wholly-unseen claim.

The next practical milestone must address readiness and workload means rather
than merely widening their risks. Before choosing a repair, reconcile earlier
talent-to-workload evidence with this candidate: the September 23 test held
participation fixed and used a different population, so it cannot settle whether
talent helps arrival here. Retain its negative conditional-workload result and
required review qualification; do not repeat it unchanged or start another
library/status-feature sweep. Use the current whole population, supported
cutoffs, public benchmark and consequential player traces to define one
substantive comparison. Joint batting-performance uncertainty and delivered
player value remain unfinished; the full active goal is not complete.

Evidence: [scores](../reports/model-evidence/hitter-workload-risk/scores.json),
[paired intervals](../reports/model-evidence/hitter-workload-risk/intervals.json),
[concentrations](../reports/model-evidence/hitter-workload-risk/concentrations.json),
[attribution](../reports/model-evidence/hitter-workload-risk/attribution.json),
[execution verification](../reports/model-evidence/hitter-workload-risk/verification.json),
[completed review](../reports/model-evidence/hitter-workload-risk/final-report.json).
