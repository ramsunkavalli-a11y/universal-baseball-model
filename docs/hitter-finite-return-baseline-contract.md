# Preserve an established role through a known finite interruption

2026-10-05, before fitting. Tatis before 2023 is the focal repair. This is not
another employment-date interaction or a blanket increase for absent players.

## The forecast and the assumption

Estimate next-calendar-year MLB participation and conditional PA from a recent
demonstrated MLB role, current age, batting quality, employment and medical
history. Keep the existing hitting forecast. A temporary suspension must not
erase the role; its remaining games reduce eligible work separately.

Use a simple standardized logistic participation model and standardized Ridge
conditional-PA model, fixed C=1 and alpha=100, with equal origin weights. Fit on
previously debuted players with at least 300 season-normalized PA in their last
observed MLB season within the existing three-season window. Include future
exits and injured players. Exclude pending legal restrictions from reference
training: their realized workload would contaminate an independent suspension
baseline. Fit conditional workload only for actual MLB participants.

The reference inputs are current age and its square, log observed career PA,
last active MLB workload/quality, mean workload over observed active seasons,
pooled MLB quality, elapsed years since MLB work, position, current reported
employment flags and record-age/unknown/conflict flags, clinical evidence,
medical coverage, prior injury days/spells and surgery. Do not use current
snapshot level or treat a zero-PA season as an observed zero batting rate.

For an explicitly reported finite return, suppress the interruption gap ONLY
when a separate cutoff-known medical report expects readiness before the season.
Retain actual age, past role and injury history, including reported surgery.
This is a conditional transport assumption: expected preseason recovery makes
the known finite absence inapplicable to the ordinary unexplained-gap penalty.
It is NOT medical clearance or a probability of successful recovery learned from
that report. The ordinary historical injury/recurrence risk remains in the fitted
baseline. Also retain a delayed-recovery scenario using the unremoved gap.
Do not present these two scenarios as a calibrated probability distribution.

The dated supplement records only actual source facts, no PA, probability or
desired outcome. Tatis's October report anticipated spring readiness after
operations; [MLB report](https://www.mlb.com/padres/news/fernando-tatis-jr-return-date-from-suspension-in-2023).
The comparison report for Ellsbury also expected spring readiness at the January
cutoff; [MLB report](https://www.mlb.com/news/jacoby-ellsbury-has-hip-surgery-c289262798).
His February setback is later information and cannot justify a January zero.
Neither report establishes that those players were healthy at the cutoff.

## Fixed implementation and validation

Same 35 chronological whole-player cells and 30,519 identities as completed
nonmedical opportunity, including all 30,506 original rows and 13 additions.
Targets end in 2025. Exclude target 2020; retain original normalized 2020 MLB
history and unknown cancelled MiLB history. Do not read 2026 outcomes, retune,
replace the explorer or change either frozen forecast.

Validate all full/active subsets before fitting, both generic preflight and
distinct-person counts for last-role exposure, age, link, actual gap and medical
coverage. Mark absent/sparse profiles; a gap-zero transport is not evidence of
observed medically cleared returning players. Preserve paired labels and all
non-arrivals. Supplement selection requires matching player, target season,
information cutoff and dated source, without using future outcomes.

Candidate replacement is limited to reported finite budgets with no parallel
restriction, recent established role, positive reported MLB link, no employment
conflict and a separately reported anticipated medical readiness before opening.
Other cases retain the stronger employment/observation benchmark EXACTLY.
This is a generic evidence gate, not a named-player PA override. Missing budgets,
unresolved restrictions, permanent exclusions and unsigned veterans cannot pass.

For the candidate, apply eligible-games/162 to conditional PA once; do not
multiply participation by the same factor. The baseline includes ordinary
medical risk but no separate dated medical deduction, so no overlapping calendar
period is subtracted twice. Longer recovery is represented separately, not added
as a second scalar penalty. The source report does not prove a starting job.

Score the original cohort against both corrected employment and selected anchors:
PA MSE/RMSE, MAE, Brier, log loss, batting-plus-replacement error and totals,
all origins/stages and public matched PA MAE. Also evaluate the reference model
on all eligible nonrestricted regulars as a diagnostic, not a chosen second arm.
No broad accuracy claim from correcting one already-exposed named case. No
deployment without separate review. If only Tatis changes, pooled improvement is
an arithmetic case repair, not independent confirmation of a general return model.

Walk Tatis 2022, Tatis 2023, Hoskins 2023, Ellsbury 2018, Kang 2017, Franco 2023,
Marcano 2024, Duran 2024, Belt 2023 and Judge 2024. Keep cases where the gate does
not apply; add largest reference gain/harm, false high/low and an ordinary case.
Show actual prior stats, dated context, model inputs, coefficient contributions,
participation/conditional PA, suspension, fixed hitting, contribution and actuals.
Select three comparison players per case using only origin features and no later
outcome. Reference failure closes that reference construction, not the source
correction or the need to preserve career evidence. Do not fit follow-up variants.
