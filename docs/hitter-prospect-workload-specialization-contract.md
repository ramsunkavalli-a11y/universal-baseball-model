# Testing separate first arrival workload training

2026-10-04. Test whether the active-workload model benefits from learning only
from players who had not debuted at the forecast cutoff. This is a conditional
training-population comparison, not a prospect bonus or another learner sweep.
No new fits have been run when this contract is saved.

## Why this comparison is different

Current saved trees use active established MLB hitters and active first-time
entrants together. Several major prospect misses have very low conditional PA,
even when debut probability is substantial. A separate model may represent
first-year timing and role better, but it also sacrifices training support and
could overfit a small selected sample. Neither outcome is assumed.

Earlier smooth prospect-only readiness models already tested this general idea
with different representations and both probability and workload changing. Do
not call prospect specialization entirely untested. The September detailed
conditional-workload result used a different panel, 892 inputs, identity weights
and LightGBM. Inspection of its actual training helper shows no explicit player
exclusion and no pre-debut training restriction. Its prospect-only label refers
to forecast routing, not necessarily training. Audit the actual memberships and
qualify that older evidence before using it to steer this comparison. Do not
rewrite or rerun the sealed older result.

## Fixed population and comparisons

Keep all 30,506 current forecasts at origins 2016–18 and 2021–24, including all
24,199 never-debut records and certified zero next-year MLB outcomes. Target is
MLB PA in the next calendar year, not minor-league performance, lifetime talent,
full WAR, club control or trade value. Positive MLB PA is an appropriate
conditional-head training condition; it is not an evaluation eligibility rule.

Use the previously sealed 76,639-row compatible source and exactly its existing
restricted and extended training memberships. Restricted contains current
2011+ origins; extended adds all 13,357 repaired 2008–10 origins. Both exclude
the entire held-player fold, require target year no later than cutoff and exclude
2020 targets. Canceled 2020 minor data remain missing, not poor production.
Older roster/rank/history limitations remain visible.

Four workload arms form a matched comparison:

- Pooled restricted is the unchanged current conditional head.
- Pooled extended is the saved earlier-training conditional head.
- Prospect restricted is a new head trained only on restricted active rows
  whose origin-known prior_debut is zero.
- Prospect extended is the same restriction applied to extended active rows.

Use identical 253 inputs and existing histogram-tree settings: 250 iterations,
depth three, minimum leaf 30, learning rate .05, L2 10, seed 31, no early stopping.
Keep inverse-origin-frequency weights, computed within each actual active
training subset. Save subset-specific distinct-player/profile support before
all fits. No tuning, target-selected training rows or mandatory regular-role PA.

Every arm uses the unchanged current probability of any MLB PA, including the
existing explicit unavailability/retirement rules. Only never-debut conditional
workloads change; established forecasts remain bit-identical. Clip conditional
PA to [1,800] and report clipping. Expected PA remains probability times
conditional mean. This isolates workload training from arrival calibration.

Primary value ledger uses the unchanged current hitting yield and origin
replacement rate. A predeclared secondary ledger uses the previously reviewed
translated/ranking Ridge hitting rate, with the same expected PA; it is not a
new fit or a post-result rescue. Preserve both current and translated anchors.
Value remains custom fixed-event batting plus replacement, not published WAR.

## Preflight and evidence

Before fitting, verify prior completed player-review receipts, all input hashes,
row pairing, exact source features, actual full and active training memberships,
held-player exclusion, label maturity and physical labels. Run the required
forecast preflight for each pooled and specialized conditional subset. Count
distinct people for broad and refined age, level, rank, thin-history and draft
profiles; retain unsupported forecasts. Save all 140 checks before the 70 new
fits. Replay both saved pooled controls before new fits and all new heads after.

The legacy audit records actual overlap between historical training and query
identities for every old origin/horizon, plus the mix of prior-debut and
never-debut active training. This limits the older result's transferability; it
does not establish whether repeated-player forecasting itself is undesirable
for every other application.

## Scoring and baseball review

Report equal-target-year PA RMSE, MAE, raw PA/value totals and player-clustered
nominal paired 95% MSE intervals. Compare specialization within each source
history and each new arm against unchanged current and translated value
anchors. Report all players, never-debut, upper/lower minors, thin professional
history, new draftees, teenage DSL, every origin and the matched 2,627 public
players. Public and all established forecasts are unchanged by definition;
this test cannot repair their benchmark gap. Arrival scores are also unchanged.
Evaluate conditional PA error and calibration among actual debutants as a
diagnostic, without dropping non-arrivals from primary expected-PA/value scores.

Fixed cases are Kurtz 2024, Langford 2023, Alonso 2018, Acuna 2017, Julio 2021
and Holliday 2023. Add the first eligible teenage DSL row and the largest value
gain, harm, false high, false low and an ordinary active case for each new arm.
Persist the union. Trace dated stats, actual inputs, fixed arrival and hitting,
saved pooled and specialized tree paths, conditional and expected PA, delivered
value and reality. Select up to four same-origin/profile peers using only
origin-known age, exposure, position, pedigree and production. Do not explain
away an elite miss using noncomparable zero-outcome peers. A near-exact value
with wrong PA and hitting is not a successful component forecast.

Do not adopt merely because RMSE falls. We need a coherent material benefit,
no consequential cohort deterioration, plausible player tradeoffs and stronger
value evidence. Exposed history is development evidence, not a fresh holdout;
uncertain effects remain uncertain. If specialization is worse or unsupported,
retain the best existing construction and explain why this bounded recipe did
not help, without rejecting all first-arrival models.

No protected 2026 outcome access, frozen forecast modification or explorer
promotion. Full goal stays active unless all remaining practical model and
deliverable requirements actually pass.
