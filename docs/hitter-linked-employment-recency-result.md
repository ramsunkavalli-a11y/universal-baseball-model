# Old employment records are not a sufficient return signal

2026-10-05. Completed historical development test under the
[fixed contract](hitter-linked-employment-recency-contract.md), with
[twelve player walks](hitter-linked-employment-recency-player-review.md).

Do not replace the forecast with this encoding. It slightly improves ordinary
absolute error, but does not improve the declared primary playing-time error and
worsens the inactive/unknown group. The main baseball lesson is that a historical
MLB connection cannot substitute for evidence that a player can actually return.
This closes the exact interaction, not the broader career-continuity problem.

## What changed

The reference already has corrected employment sources, career workload and
quality, current roster/link evidence, medical summaries and two opportunity
models. Those sources and models were not missing. We replaced one ordered
input: years since employment evidence became that age multiplied by one minus
the reported MLB-link flag. Linked players therefore do not receive this
particular staleness signal. The raw date remains unchanged. Zero is not a new
signing, recovery date, known contract duration or guaranteed job.

Same 293 fields except that replacement, same shallow boosting settings,
same training/test people, same targets and origin weights. Seventy candidate
heads were fitted; 140 benchmark/candidate heads replay exactly. Hitting is
exactly unchanged. Thirty thousand five hundred six original forecasts remain,
plus thirteen separately reported additions without an invented incumbent.
Origins 2016–18 and 2021–24 predict the following calendar season through 2025.
No 2026 outcome was used or rescored. Canceled MiLB 2020 remains missing, and
shortened MLB workload keeps the reference's normalization.

The main benchmark is the completed nonmedical-observation model, which has
the same predictions as corrected employment V2. The selected forecast remains
an additional stronger batting-contribution reference. Improvements previously
made by employment parsing do NOT belong to this new interaction.

## Matched results

Errors below are lower-is-better. The whole population includes non-arrivals;
its smaller PA error should not be confused with the MLB-heavy public cohort.

| Same population and hitting | Selected | Corrected employment | New encoding |
| --- | ---: | ---: | ---: |
| All 30,506: PA RMSE | 60.4991 | 60.2698 | 60.2758 |
| All 30,506: PA mean absolute error | 20.6124 | 20.5180 | 20.4342 |
| All 30,506: batting-plus-replacement RMSE | .435133 | .435456 | .435078 |
| Public 2,627: PA RMSE | 138.3298 | 137.7704 | 137.6755 |
| Public 2,627: PA mean absolute error | 106.4108 | 105.2844 | 105.0025 |

Steamer's public-cohort PA mean absolute error remains 92.0828. The new encoding
is still about 14% worse on this statistic, versus the selected forecast's 15.6%.
Archive-date and depth-chart qualifications persist; this is not a full-WAR
or clean same-information-date comparison. The marginal new change improves
public absolute error only .282 PA against corrected employment, not 1.408 PA
of wholly new progress against selected.

Primary PA squared error changes by +.7271, with nominal player-bootstrap 95%
interval −12.0745 to +12.3745. It is not a convincing gain. Compatible
contribution squared error improves .0003294 against employment, but only
.0000483 against selected, whose interval spans −.0010979 to +.0010106.
Do not sell this as a proven player-value improvement. These intervals are
exposed development evidence, not fresh confirmation after many experiments.

PA squared error improves in three origins and worsens in four, including
2021. Current MLB changes +.021%, upper minors −.415%, lower minors +.432%,
and inactive/unknown +8.801%. The last group violates the predeclared 2%
stage guardrail. Current regulars improve only .056% against employment and
remain worse than selected. Both the primary-improvement and stage gates fail;
the nominal primary interval also fails the convincing-gain requirement.
No subgroup hybrid, Kang exemption or penalty variant follows this result.

## Totals and who receives the PA

| Group | Corrected employment PA | New PA | Actual PA |
| --- | ---: | ---: | ---: |
| All original rows | 1,236,263 | 1,234,213 | 1,270,493 |
| 54 absent former regulars | 3,461 | 3,561 | 3,892 |
| 12 absent former regulars with MLB link | 2,634 | 2,799 | 2,899 |
| 42 absent former regulars without link | 827 | 762 | 993 |
| Upper-minor never-debuted players | 74,213 | 72,781 | 92,891 |
| Lower-minor never-debuted players | 8,108 | 7,738 | 5,194 |

The linked-return total gets closer while individual PA error gets worse:
linked-group squared error rises 2.14%. Raising Tatis also raises Kang and
Ellsbury. A closer group total does not mean better allocation. All-row PA sent
to actual nonparticipants falls 115,103 to 112,283, but the forecast also loses
1,432 PA from already underallocated upper-minor debut candidates. There were
730 upper-minor debuts versus about 588 predicted; lower-minor debuts were 54
versus about 87 predicted. A blanket prospect or comeback boost is not justified.
Totals sum evaluated origin cohorts, not complete league rosters or future team
depth charts; error metrics equally weight origins, whereas totals sum rows.

## What the player checks say

Tatis improves 61 to 112 PA before 635 actual, but still has only a 27% chance
of appearing. Kang rises 64 to 143 before six actual. Ellsbury rises 261 to
272 before zero. Hoskins's stronger reference already predicts 367 rather
than selected's 26; the new interaction worsens him to 354. Kwan stays around
110 before 638. Judge's 2017 breakout remains the largest false low. Slater's
nearly exact contribution combines too many PA with too little hitting: a useful
warning against celebrating the combined score alone.

All twelve cases retain raw dated stats, actual inputs, exact fitted-path
accounting, participation × active workload, fixed batting, outcomes and
origin-only peers. Tatis has only one matching full/active training person;
Kang has none; Ellsbury has three. The experiment can execute without those
profiles being adequately supported. Employment peers are not good minor-hitting
comparisons when minor exposure/translated quality are omitted from their distance.
That limitation is disclosed, not repaired by selecting happier peers afterward.

## Decision and next work

Reject this exact encoding; preserve corrected facts and the unchanged selected
forecast. Do not rerun it with alternate dates, thresholds, penalties or renamed
flags. The return distinction remains unresolved, not disproven. The fitted
paths now demonstrate why a broad removal of staleness is insufficient.

The next mechanism checkpoint is a **joint distinction between eligibility,
availability and a plausible MLB role**, using completed transaction/absence
evidence and career quality. It must distinguish a finite restriction from an
unresolved absence, and a 40-man assignment from being ready to play. Before
another fit, demonstrate which existing origin-known fields can distinguish
these cases and whether they are actually used; if they cannot, state the source
limit instead of fitting another equivalent flag. No new general source sweep.
Prospect workload and brief-debut talent handoff remain in the same ordered
reset queue, not an excuse to start a new unrelated tournament.

The [machine-readable completion](../reports/model-evidence/hitter-linked-employment-recency/report.json)
contains unchanged raw-score receipt hashes, all origins/stages, intervals,
gate decisions and reviewed cases. Completion is separate from predictive
success and deployment. Both frozen packages, the completed once-only 2026
evaluation and the explorer remain unchanged. The broad hitter goal is unfinished.
