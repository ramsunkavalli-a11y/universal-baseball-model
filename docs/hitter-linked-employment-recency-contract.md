# Test employment record age separately from an MLB link

2026-10-05 before fitting. One opportunity representation comparison under the
basics reset. No new source, hitting model, library, tuning, named-player rule
or 2026 reuse. Existing employment and unused observation tests stay closed.

## Question and mechanism

Does treating old employment evidence as a staleness signal only for players
WITHOUT a reported MLB organization link improve next year's MLB opportunity?
The existing saved path gives Tatis before 2023 a −.725 log-odds contribution
from 1.449 years since employment evidence, despite a positive MLB-link field.
This is a correlated tree-path attribution, not a causal effect or proof the
field alone caused his miss. Hoskins's broader employment representation already
improves his forecast; it must not be advertised as a new gain from this test.

The completed historical inputs identify 54 original absent former-regular rows
(zero current MLB PA and at least 400 season-normalized MLB PA in either of the
two preceding seasons). Twelve report an MLB link; eight subsequently appear.
The employment reference predicts 2,634 PA for them versus 2,899 actual, while
the selected incumbent gives 1,137. Thus this is not proof of universal return
underprediction in the stronger job arm. Unlinked players include real returns
and exits. The rare-group evidence is development evidence, not confirmation.

Replace ONE ordered model input, `employment_evidence_age_years`, with:

`unlinked_employment_age_years = employment_evidence_age_years × (1 − status_major_link)`.

Preserve the raw date, raw age and unknown/coverage/conflict fields. A zero for
a linked player means that this particular staleness signal is inapplicable;
it does NOT mean a new signing occurred, contract duration is known, health is
restored or an MLB job is guaranteed. Reported linkage can itself be incomplete
or stale. The arm retains all other context, regular history, restrictions,
retirement/permanent-ban overrides and both workload heads.

This is a deliberately constrained interaction/representation hypothesis, not a
data correction or an isolated causal test of employment. Retraining can change
predictions even when a person's replacement value equals the old input. No
post-result gate, legal-status exemption, penalty search or subgroup hybrid.

## Fixed comparison and inputs

Benchmark: completed nonmedical-observation opportunity arm, identical to the
fully corrected employment arm in predictions. Also retain selected incumbent
opportunity. Same 293 ordered opportunity fields except the single replacement,
same shallow histogram settings, weights and full/active training identities.
Thirty-five chronological whole-player cells, seventy new heads. Preflight full
and active subsets before fitting, replay the seventy benchmark heads first.

Keep all 30,506 original forecasts and thirteen explicitly separate additions.
No substitute zero incumbent for additions. Origins 2016–18 and 2021–24,
next-calendar-year outcomes through 2025; target 2020 excluded. Actual shortened
2020 MLB workload is normalized as in the reference; no MiLB 2020 is invented.
Preserve existing individual preseason cutoffs, including March 18, 2022 where
declared. No current foreign tables or later transactions are imported.

Targets: MLB participation, PA conditional on participating, expected PA and
delivered batting-plus-replacement contribution. Rate is exactly the selected
incumbent rate for original rows and the unchanged research fallback for additions.
Contribution uses the same compatible future-relative labels and replacement
reference. Not full WAR, six-year control value, recovery prognosis or future job
certainty. Keep non-arrivals in PA/value scoring, not conditional workload fitting.

Training support counts DISTINCT people, not repeated rows. In each full/active
cell count age band, prior MLB regular evidence, current MLB presence, reported
link and unresolved observation intersections. Sparse/zero cases remain scored;
they block claims of universally supported comeback forecasts, not execution.
Check chronology, unchanged identities/targets, scalar transform validity and
future-label invariance. Existing generic support warnings remain alongside these.

## Evaluation and stop conditions

Primary paired contrast: expected PA squared error against the completed employment
reference, equal origin weight. Report mean absolute PA error, participation Brier
and log loss, compatible contribution error, participant/nonparticipant allocations,
every origin and stage, current regulars, absent former regulars (linked/unlinked),
upper/lower never-debut and the unchanged 2,627 public matches. Public dates/park
qualifications persist; ordinary ZiPS PA is not unconditional workload.

Use 2,000 whole-player bootstrap repetitions, seed 84, for primary PA and value
contrasts against both anchors. These nominal intervals do not correct for the
many exposed historical experiments. Keep all rows and show subgroup counts.

No adoption unless PA error improves against employment reference, contribution
does not worsen against either reference, public PA MAE does not worsen, and no
populated major stage/current-regular group worsens PA squared error over 2%.
A convincing claim needs a nominal paired primary interval favoring improvement
and consistent baseball walks, not just a fractional pooled win. Rare comeback
behavior cannot be certified from twelve evaluated linked former regulars.
Failure closes this EXACT interaction; no automatic variants. Correct source
facts remain correct regardless of scores. Deployment requires separate approval.

## Mandatory player checkpoint

Fixed diagnostic cases: Tatis 2022, Hoskins 2023, Kang 2017, Ellsbury 2018, Lux
2023, Belt 2023, Kwan 2021 and Judge 2024. Add whole-original-cohort largest
contribution gain/harm, false high/low and an ordinary positive-PA case. Preserve
all fixed cases, distinct players where possible, and genuine exits.

Walk actual dated three-year stats, link/date source, raw/transformed inputs,
saved benchmark/candidate paths, participation × conditional PA, fixed hitting,
contribution and actual future counts. For each case select three peers without
outcomes using same origin/current-MLB-presence/link/prior-regular category,
then age and three-year MLB exposure/quality distance. State when exact peer
categories have fewer than three people; do not fill with minor fringe players
or imply every known regular will return. Complete player walks before disposition.

Preserve both frozen packages, completed one-time 2026 receipt and explorer. This
experiment changes a research opportunity representation, not the evaluated
forecast. The broader hitter goal remains unfinished.
