# Where the remaining hitter forecast difference comes from

2026-10-05. The saved forecasts were diagnosed without fitting another model,
changing PA, removing players or using 2026 outcomes. The seventeen actual
[player walkthroughs](hitter-restored-error-diagnosis-player-review.md) are complete.
Retain the incumbent. The newer model is a near-tie overall, not a proven failure
of detailed hitting information and not a justified new deployment.

## The comparison and its size

All 30,506 original forecasts, including 25,968 non-arrivals, remain. Origins
2016–2018 and 2021–2024 predict the next calendar year's MLB batting. Thirteen
added players lack an incumbent forecast and remain separate. Hitting is batting
wins above league mean per 600 PA; delivered value adds replacement at forecast
PA. Neither is full WAR, six years of club control or trade value.

| Model | Hitting RMSE | Delivered batting value RMSE | Delivered MAE |
| --- | ---: | ---: | ---: |
| Unchanged incumbent | 1.804813 | 0.435133 | 0.123874 |
| Four MLB quality summaries restored | 1.801956 | 0.436118 | 0.123733 |
| Seven separate MLB event rates also restored | 1.799172 | 0.435373 | 0.123507 |

The seven inputs improve their matched four-summary model. Against the incumbent,
hitting improves about 0.31%, delivered RMSE worsens about 0.055%, and MAE improves.
The existing nominal player-bootstrap intervals include zero for both incumbent
contrasts: hitting MSE change −0.020333, interval −0.052602 to +0.011555; delivered
MSE change +0.000209, interval −0.001457 to +0.001816. These are repeatedly exposed
development data, not independent confirmation. Do not describe this tiny net
loss as a confidently established accuracy difference.

## Established MLB hitters are the main remaining weak group

The following six groups are defined entirely by source history available at the
forecast origin. MLB exposure uses normalized recency weights 1, 0.8 and 0.6.
Foreign means observed recent NPB/KBO history, not nationality. The quantities
are contributions to the same global score; positive means the newer model is
worse. They sum exactly to the headline change, not to subgroup RMSEs.

| Recent MLB exposure and foreign source | Forecasts | Active MLB labels | Delivered MSE contribution | Hitting MSE contribution |
| --- | ---: | ---: | ---: | ---: |
| No MLB, no foreign source | 24,761 | 798 | −0.000249781 | −0.008618292 |
| No MLB, foreign source | 91 | 5 | −0.000035369 | −0.004429473 |
| Positive MLB below 600, no foreign source | 3,502 | 1,895 | −0.000537340 | −0.012409312 |
| Positive MLB below 600, foreign source | 157 | 19 | +0.000079220 | +0.001738922 |
| At least 600 MLB, no foreign source | 1,990 | 1,817 | +0.000974848 | +0.005569745 |
| At least 600 MLB, foreign source | 5 | 4 | −0.000022571 | −0.002184554 |
| All original forecasts | 30,506 | 4,538 | +0.000209006 | −0.020332965 |

The mature domestic group contributes more loss than the net headline because
gains elsewhere offset it. It includes 637 distinct players, 597 with active
labels, rather than just Judge or one foreign entrant. Its global hitting
contribution also worsens. The seven new event inputs recover much of the
four-summary model's loss in this group (matched delivered contribution
−0.000525283), but do not eliminate the difference from incumbent.

All foreign groups together contribute only +0.000021279 to the net delivered
difference. Their handful of active players remain weak evidence for translation.
Thames and Yoshida are genuine concerns, but repairing only these names is not
the main answer. Nor does this check establish a 2021-only explanation: delivered
loss also appears at 2016, 2017 and 2022 origins. No year is erased.

## Playing time can conceal hitting mistakes

For an active player, delivered error equals hitting error at expected PA plus
PA error valued at that player's actual hitting. The unchanged PA error interacts
with a changed hitting estimate. Both terms are retrospective bookkeeping, not
independent causal explanations or information available at forecast time.

| Delivered MSE term | Newer minus incumbent | Newer minus four summaries |
| --- | ---: | ---: |
| Squared hitting error at expected PA | +0.001686029 | −0.000645580 |
| Interaction with unchanged PA error | −0.001766849 | +0.000049027 |
| Non-arrivals | +0.000289826 | −0.000052018 |
| Total | +0.000209006 | −0.000648572 |

Among active players, the newer model's net delivered contribution improves
−0.000080820 versus incumbent, but worsening squared hitting error at expected
PA is hidden by a favorable interaction. Overall hitting RMSE improves because
it uses actual future PA weights, not squared expected PA weights. These are
different questions; there is no contradiction and neither should be renamed
an unqualified talent win.

Non-arrivals contribute the net reversal. They are not simply obscure prospects:
Tatis has substantial prior MLB history but zero target PA. The newer model's
total value on non-arrivals falls from 225.927 to 216.362, yet squared error rises.
A lower sum can coexist with concentrating more value on the wrong absentees.
Zero realized contribution is not an observed zero batting-talent label.

Across all originals, expected PA remains 1,228,732.5 versus 1,270,493 actual.
Expected value is 4,174.414 versus 4,185.434 actual, closer in total than incumbent
4,155.430. That does not certify individuals. For actual MLB participants the
model supplies 1,109,984.5 PA and 3,958.052 value; the non-arrivals receive the
remaining 118,748.0 PA and 216.362 value. Those retrospective splits cannot be
used to select who will actually play next year.

## What the player checks add

Misner's K information helps; his delivered error falls to +0.0271 from +0.0597
incumbent. Judge's established forecast remains both too low in rate and PA.
Kurtz's 10.2 projected PA versus 489 actual dwarf the change to his hitting
estimate. Thames and Yoshida have optimistic hitting and excessive PA together.

Lee illustrates the danger especially clearly. The seven inputs make his hitting
estimate worse versus the matched model, +1.432 versus +1.311 with +0.463 actual,
yet his delivered error improves because optimistic hitting partially offsets
153.6 projected PA versus 617 actual. Conversely, Suzuki's 2023 hitting estimate
improves versus matched but delivered error worsens as that compensation shrinks.
France's almost exact value still consists of roughly +0.149 hitting error and
−0.150 opportunity error. None is a clean whole-model success.

## Decision and one next question

Source integrity, all 105 saved model hashes, independent target labels,
forecast equations, every-row error decomposition, all global partitions and
the seventeen linked actual source/model walks pass their checks. Sparse joint
training profiles remain qualified. The diagnosis is complete; it has not
improved a forecast, established a statistically significant incumbent loss or
approved deployment. The explorer and both frozen packages remain unchanged.

The next bounded question is whether the fixed past-production starting estimate
is constraining the direct-rate learner. The current seven-input model predicts
that fixed baseline plus a learned residual; the incumbent learns batting rate
without that imposed offset. The inputs already contain the same past production,
so a same-matrix comparison can learn its usefulness instead of requiring a
unit-weight starting contribution. This is a hypothesis, not a cause proved by
these error terms. First write the exact source/target/offset contrast and check
its mechanics; then at most one fixed absolute-rate fit with the same inputs,
alpha, weights, routes, people and PA, retaining all anchors and player cases.
No profile-selected hybrid, foreign-only detour, prior search or algorithm sweep.
Do not spend another cycle chasing the tiny delivered headline alone.

Reproduce with `scripts/diagnose_hitter_restored_errors.py`. The public report
links the immutable full source/model walkthroughs and their hashes rather than
duplicating them. All targets end in 2025. The one-time 2026 evaluation was
already completed and is not reopened or used for this development decision.
