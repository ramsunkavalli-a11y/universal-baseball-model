# Old restrictions are contaminating current availability evidence

2026-10-05. The read-only inventory found a source-design defect before another
model fit: historical restrictions remain marked active after subsequent MLB
appearances. Existing availability experiments already contain the main proposed
status and timing features. Repeating those additions would not resolve the
defect. No source rows, fitted parameters, predictions, explorers or completed
2026 evaluation changed in this audit.

## What was already tried

The reviewed history includes the
[offseason injury-count test](hitter-offseason-injury-feature-result.md),
[two-year workload shortfall test](hitter-availability-gap-v1-result.md),
[scoped context comparison](availability-context-v29-result.md),
[dated status comparison](practical-hitter-opportunity-status-v59-result.md),
[continuing-absence observation repair](hitter-observed-return-v60-result.md),
[scoped status source review](hitter-status-evidence-result.md),
[complete evidence comparison](hitter-evidence-representation-result.md), and
the now-closed [employment correction](hitter-employment-comparison-v2-result.md).

Broad injury counts had uncertain small workload gains with worse other scores.
The shortfall test targeted Year 2, not next-year health or minor-league players;
it cannot reject those other questions. The context experiment had a genuine
development probability/PA improvement but worsened aggregate PA underallocation
and failed its minor-contract guard. Rare medical/unresolved contexts were
unsupported, not clean negative tests of those mechanisms. The later status
comparison exposed stale medical observations; the observation adapter repaired
those sources without certifying recovery. Its ten-feature sweep was explicitly
closed, not an invitation to rerun it with another penalty.

The latest opportunity branch already receives finite/unresolved/permanent
status, original game duration, known calendar end and tentative return-report
timing. These are not missing feature names. Their source meaning and actual
training examples require scrutiny before another learner or calibration rule.
Earlier evidence is not globally recertified by this inventory, and unrelated
minor-league health and foreign-role coverage remain unresolved.

## The conservative warning

Across the unchanged 63,314 source rows, 83 origins for 27 people have positive
origin-year MLB PA while the latest retained active nonmedical channel predates
January 1 of that year. In the unchanged 30,519-row historical evaluation this
is 54 origins for 23 people. Warnings use only information available at the
forecast origin, not next-year participation. Same-year PA is insufficient to
establish a return after a late restriction. Permanent ineligibility/death are
excluded and cannot be cleared by generic participation.

This disproves a representation of uninterrupted absence; it does not certify
the exact legal reinstatement date, continuing health or a current starting job.
The 83 are a conservative lower bound on inconsistencies, not a complete count
of all stale status. The audit preserves every difficult row, including genuine
unresolved cases. Missing capture events remain unknown, not proof that the
restriction persisted.

The saved state can be reproduced exactly from the captured inputs. That is
why another parser replay is not enough. For Tatis the captured records used
by the status builder lack the 2023 nonmedical return event. The preseason
transaction requests cover October through January, not the whole intervening
season. The separate annual transaction payloads span full calendar years but
do not contain his return; calendar span alone is not complete event coverage.
His later injury-list activation correctly does not silently clear another
legal channel. We must repair missing return coverage or represent subsequent
observed activity separately, rather than simply broadening that clearing rule.

## Nine source and saved forecast walks

All nine cases replay their original scoped source state and eighteen saved
opportunity heads; nothing is refitted. Each private trace retains eligible raw
records, normalized status events, three-season counts, actual inputs,
participation, conditional PA, unchanged talent/contribution and actual next-year
outcomes. These are source contrasts, not a newly fitted gain/harm experiment.

| Player and origin | Prior MLB PA | Stored status | Saved expected PA | Following-year actual PA | Finding |
|---|---:|---|---:|---:|---|
| Tatis 2022 | 0 | Finite suspension | 61 | 635 | Genuine interrupted season and tentative return are known |
| Tatis 2023 | 635 | Finite suspension | 603 | 438 | Old suspension persists after MLB return |
| Tatis 2024 | 438 | Finite suspension | 563 | 691 | The same stale restriction persists again |
| Grandal 2016 | 457 | Unresolved restriction | 404 | 482 | November 2012 restriction survives years of MLB play |
| Reyes 2017 | 561 | Unresolved restriction | 459 | 251 | February 2016 restriction survives later MLB play |
| Franco 2023 | 491 | Unresolved channels | 545 | 0 | Same-year PA cannot clear August leave |
| Duran 2024 | 735 | Explicit return | 585 | 696 | August 14 activation correctly clears suspension |
| Marcano 2024 | 0 | Permanent ineligible | 0 | 0 | Factual hard zero remains separate |
| Ruiz 2017 | 145 | Unresolved restriction | 25 | 0 | Stale restriction and eventual exit are different facts |

Tatis's 546 PA/42 HR in 2021 precede the missed MLB season. At the January
2023 cutoff the model knows the eighty-game suspension and an April 20 tentative
return report, yet gives 15.35% participation times 400.38 conditional PA = 61.48.
This is a real readiness/availability miss, not proof of lost talent. At January
2024 it already knows 635 MLB PA/25 HR after suspension, yet still receives the
finite flag and a return-report date in the past. Its 99.02% times 608.99 gives
603.04 PA. At January 2025 the same flag accompanies 438 recent PA/21 HR;
98.70% times 570.16 gives 562.73. Recent play dominates the forecast despite the
stale restriction. That coexistence contaminates what a learner can infer from
the finite flag; the audit does not claim to quantify its causal score effect.

Grandal's 443/426/457 MLB PA and latest 27 HR coexist with a 2012 restricted
channel. His 99.20% times 406.79 gives 403.54 PA. Reyes's 279 MLB PA in 2016
and 561/15 HR in 2017 coexist with a 2016 channel; 97.03% times 473.01 gives
458.95. These are not useful current-restriction training examples merely because
the transactions are real. Ruiz's 320/233/145 recent PA and later zero outcome
show why correcting historical state must not imply a universal return boost:
28.87% times 84.91 gives 24.51 PA despite his unrelated employment/age risks.

Franco's 491 PA all precede or overlap the same-year August restrictions in this
annual representation. Both restricted and administrative channels remain;
99.06% participation is still implausibly high as an availability forecast, but
neither future legal outcomes nor earlier appearances can be used to erase or
convert those channels into a permanent ban. Duran's explicit restriction return
and later explicit suspension activation are captured and correctly scoped.
Marcano's June permanent ineligibility keeps participation zero independently
of the raw conditional model's 189 PA. These controls prevent an indiscriminate
rule that every old record or activation restores eligibility.

## Decision and next source repair

Inventory and player review are complete; predictive improvement is untested.
The employment correction remains a completed bounded contrast, not a full
availability certification. Its two arms held the same flawed restriction inputs
fixed, so the small score changes do not reject employment or health information.

Do not run another status, comeback, suspension or injury-feature fit yet.
First recover systematic cutoff-safe nonmedical return coverage and separate
restriction history, later observed MLB activity and current legal uncertainty.
Preserve literal events, scoped parallel channels, permanent bans, same-year
late restrictions and missing dates. Audit all impacted profiles, not just
Tatis; retain ordinary exits such as Ruiz. Only after that source review can a
bounded future-MLB opportunity comparison be justified. No team-record testing,
named-player override or 2026 retuning follows from this finding.

The audit initially stopped before creating any artifacts because capture
selection included metadata files. Excluding metadata completed the specified
24-payload audit; no source content, cohort, settings or saved model changed.
Five focused warning tests pass. The inventory is preserved separately under
`reports/generated/hitter-availability-inventory` with hashes and nine traces.
