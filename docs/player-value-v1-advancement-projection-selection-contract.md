# Player Value v1 non-steal advancement projection selection contract

Status: **PREDECLARED BEFORE MODEL FITTING — BASERUNNING NOT YET FROZEN — WAR CLOSED**

This contract fixes the first MLB non-steal advancement current-talent / projection diagnostic before candidate results are inspected. It uses the already-certified public Baseball Savant runner-level advancement run-value surface and does not reopen the portable steal gate.

## 1. Scope

Select a deliberately simple method for carrying forward **non-steal baserunning advancement skill** from MLB Statcast history.

This gate does not:

- refit Statcast's underlying advancement model;
- use stolen-base run value as an advancement predictor;
- invent MiLB advancement values;
- select GIDP residual value;
- choose final baserunning aggregation or WAR.

The purpose is to determine whether a player's prior Statcast extra-base advancement run value contains enough out-of-sample persistence to justify player-specific carry-forward rather than a neutral fallback.

## 2. Frozen source evidence

Use the public Baseball Savant runner-level regular-season baserunning-run-value CSV certified by `docs/player-value-v1-baserunning-source-audit-contract.md` and materialized in `docs/player-value-v1-baserunning-source-audit-result.json`.

Required row fields:

- `player_id`;
- `runner_runs_xb` — source-defined non-steal extra-base advancement run value;
- `n_runner_moved_xb` — source-defined non-steal advancement opportunity count.

`runner_runs_tot` and `runner_runs_sbx` remain source-validation fields and are not predictors in this gate.

Source seasons are exactly **2019–2024**. Do not use 2025 evidence.

## 3. Observed player-season quantity

For each MLB player-season with positive `n_runner_moved_xb`:

`advancement_rate = runner_runs_xb / n_runner_moved_xb`

This is a source-model run-value rate, not a newly estimated event model. The gate tests only whether the player-specific rate persists.

No missing run value or opportunity count may be filled with zero. A player with no eligible prior MLB advancement evidence receives the neutral player-specific rate for the candidate being evaluated.

## 4. Candidate family

Keep the search compact and shrink directly toward a neutral player-specific advancement rate of zero.

### A0 — neutral

`projected_advancement_rate = 0`

No player-specific carry-forward.

### A1 — prior-season shrunk rate

Use only the immediately preceding eligible season.

### A2 — three-season recency shrunk rate

Use up to the prior three eligible seasons with fixed annual weights:

- one year back: `1.00`
- two years back: `0.50`
- three years back: `0.25`

For A1 and A2 evaluate exactly three prior strengths measured in non-steal advancement opportunities:

- `25`
- `75`
- `225`

No additional prior strengths or recency weights may be introduced after results are visible.

Candidate IDs are:

- `A0_neutral`
- `A1_k25`, `A1_k75`, `A1_k225`
- `A2_k25`, `A2_k75`, `A2_k225`

## 5. Estimation

For target player `i` and target season `t`, collect only eligible history before `t` allowed by the candidate family.

Let:

- `R_hist = sum(w_s * runner_runs_xb[i,s])`
- `N_hist = sum(w_s * n_runner_moved_xb[i,s])`
- `K` = candidate prior strength.

Then:

`projected_advancement_rate = R_hist / (K + N_hist)`

The prior contributes `K` opportunities at run-value rate zero. If `N_hist = 0`, the projected rate is zero.

For retrospective scoring only:

`predicted_target_runs = projected_advancement_rate * target_n_runner_moved_xb`

Target-season realized opportunities are an evaluation exposure only and may not be used in production Player Value.

## 6. Chronological firewall

### Development targets

Use completed **2022 and 2023** player seasons. Predictor evidence must precede each target season.

The 2019–2021 source history allows A2 to use its complete three-prior-season window for a 2022 target.

### Confirmation target

Completed **2024** is held out from candidate selection.

Select one candidate on 2022–2023 only. Then inspect exactly:

1. `A0_neutral` on 2024;
2. the preselected development winner on 2024.

Do not inspect alternative 2024 candidates and reselect after confirmation.

2025 remains closed for this gate.

## 7. Eligibility and coverage

A target player-season is scoreable only when:

- `player_id` is a positive MLBAM ID;
- `runner_runs_xb` is finite and observed;
- `n_runner_moved_xb` is an observed positive integer;
- the audited Savant season passed the source gate.

Candidate coverage must be identical for every candidate within a target year. Missing prior history changes the prediction to neutral; it does not remove the target from scoring.

## 8. Primary scoring

Primary score is opportunity-weighted squared error of the observed player-season advancement rate:

`loss_i = n_i * (observed_rate_i - predicted_rate_i)^2`

For each target year report:

`score_year = sum(loss_i) / sum(n_i)`

The development objective is the **equal-year mean** of the 2022 and 2023 scores so one season cannot dominate solely by opportunity volume.

Secondary diagnostics:

- opportunity-weighted absolute error of advancement rate;
- player-season RMSE of advancement rate;
- observed-vs-predicted correlation when defined;
- scored player count and opportunity exposure by year.

Do not create a composite objective after inspecting results.

## 9. Selection and stability rule

1. Compare all A1/A2/K candidates with A0 on 2022–2023 only.
2. Select the lowest equal-year mean primary score.
3. A player-specific winner is ineligible if its primary score is at least **10% worse than A0 in either development target year**.
4. Compare scores at **8 decimal places** for tie handling only.
5. If tied at that precision, prefer A1 over A2; within the same family prefer stronger shrinkage in the order `225`, `75`, `25`.
6. Promote a player-specific winner only if its unrounded equal-year mean primary score is lower than A0.

## 10. Held-out confirmation / freeze rule

The preselected player-specific winner freezes only if, on 2024:

- its primary score is lower than A0;
- it does not produce non-finite predictions or require clipping/repair;
- source coverage remains complete under the frozen audit.

If it fails, freeze `A0_neutral` for Player Value v1. Do not choose a different 2024 winner without opening a new predeclared gate before inspecting that alternative.

## 11. Production opportunity scaling boundary

Retrospective scoring uses realized target `n_runner_moved_xb` only to test skill persistence.

Production Player Value must not let projected batting quality create a second advancement advantage. If a player-specific advancement rate is frozen, use one common MLB reference non-steal advancement-opportunity rate per MLB PA from the certified reference environment:

`reference_xb_opportunity_rate_per_pa = total_MLB_n_runner_moved_xb / total_MLB_PA`

For player `i`:

`projected_xb_opportunities_i = projected_expected_mlb_pa_i * reference_xb_opportunity_rate_per_pa`

`Radvance_i = frozen_player_advancement_rate_i * projected_xb_opportunities_i`

A player with no eligible prior MLB advancement history receives the frozen neutral player-specific rate. MiLB-only history does not receive an invented Statcast-equivalent advancement score.

This production transform is not authorized until the selection result is frozen and the exact reference-season materialization is verified.

## 12. Relationship to other baserunning channels

- Portable steal attempt propensity and success skill are already selected separately and remain untouched.
- `runner_runs_sbx` is not added to that portable steal component in this gate.
- Raw GIDP run value remains non-additive because the frozen batting RE24/bin values already contain the baseline double-play cost.
- A possible opportunity-adjusted GIDP residual remains a separate unresolved source/model question.

Final `Rbr` aggregation remains closed until advancement is confirmed/frozen and GIDP handling is resolved.
