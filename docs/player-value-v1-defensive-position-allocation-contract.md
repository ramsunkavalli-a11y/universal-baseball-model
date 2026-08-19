# Player Value v1 — defensive position allocation diagnostic contract

Last updated: 2026-08-19

Status: **PREDECLARED BINDING V1 POSITION-ALLOCATION SELECTION; PRE-2025 DEVELOPMENT EVIDENCE ONLY.**

This contract resolves how the already-retained total defensive-outs forecast is distributed across
`C, 1B, 2B, 3B, SS, LF, CF, RF`. It does not reopen total exposure, Playing Time, Position/Role,
or Defense skill. It does not perform Defense run conversion, positional adjustment, replacement
level, runs-per-win, WAR, or final Player Value aggregation.

## 1. Frozen upstream decisions

The diagnostic consumes without refitting:

- total defensive-outs form: `B0_raw_persistence` from
  `docs/player-value-v1-defensive-exposure-diagnostic-result.json`;
- frozen Position/Role v1 form: `primary_share_thresholded_transition_mean_v1` with threshold
  `0.65` from `docs/position-role-selective-transition-result.json` and the binding 2025
  confirmation record;
- certified official historical fielding usage from run `32148467330`, artifact
  `position-role-historical-source-2021-2024`, digest
  `sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3`;
- chronology-safe Position/Role development predictions from run `32152125644`, artifact
  `position-role-transition-challenger-development`, digest
  `sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5`.

The Position/Role development artifact contains the source-year role vector and the frozen
transition-smoothed candidate vector for the 2022->2023 and 2023->2024 folds. The final frozen
selective forecast is reconstructed exactly: use the transition-smoothed vector when
`current_primary_share >= 0.65`; otherwise carry the current role vector forward unchanged.

No upstream coefficient, transition mean, threshold, total-outs form, or evidence population may
be refit inside this diagnostic.

## 2. Development folds and target

Development folds:

1. 2022 inputs -> 2023 observed MLB defensive allocation;
2. 2023 inputs -> 2024 observed MLB defensive allocation.

No 2025 fielding outcome may be opened by this workflow. Because 2025 Position/Role outcomes have
already been accessed upstream, this gate is explicitly a development selection and is not
presented as an untouched confirmation.

Observed defensive exposure is official MLB `fielding_outs` over:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

For a player-season with positive defensive outs, observed defensive share is position outs divided
by total defensive outs.

## 3. Scoring population

The allocation-scoring population is the exact frozen Position/Role development-prediction
population for each fold, restricted to **continuing defenders**:

- source-year MLB defensive outs > 0; and
- target-year MLB defensive outs > 0.

This restriction is deliberate. A defensive-position share is undefined when observed total
defensive exposure is zero. Entrant and exit volume error was already addressed by the separate
total-outs gate and must not be smuggled back into a share-allocation selection.

The workflow must still report the full fold population, continuing-defender count, source-only
positive count, target-only positive count, and zero/zero count for coverage diagnostics.

## 4. Fixed total exposure

For every candidate and every player:

`projected_total_defensive_outs = prior_season_mlb_defensive_outs`

This is the retained `B0_raw_persistence` total-outs baseline. Position allocation candidates may
change only the share vector. For every scored continuing defender, projected per-position outs
must sum back to this same projected total within `1e-9`.

## 5. Candidate position-share forms

### S0 — prior defensive-out-share persistence

For each defensive position:

`S0_position_share = prior_position_outs / prior_total_defensive_outs`

This is the required simple allocation baseline.

### R1 — frozen Position/Role defensive normalization

1. Reconstruct the frozen selective nine-position Position/Role forecast exactly.
2. Drop `DH` from that vector.
3. Let `defensive_role_mass` be the remaining eight-position sum.
4. If `defensive_role_mass > 1e-12`, normalize the eight defensive probabilities to sum to one.
5. If `defensive_role_mass <= 1e-12` for a player with positive prior defensive outs, fail safely to
   S0 for that player and report the fallback.

No learned calibration, position-specific scale, cap, threshold, or refit is allowed.

### H1 — fixed 50/50 share hybrid

`H1_position_share = 0.5 * S0_position_share + 0.5 * R1_position_share`

The 0.5 weight is fixed before results are opened and may not be changed afterward.

## 6. Metrics

For each fold and candidate, on continuing defenders report:

- mean total-variation distance between predicted and observed eight-position share vectors;
- mean summed-squared error of the share vector;
- primary defensive-position match rate;
- per-position-out cell MAE after multiplying the candidate share by the fixed projected total;
- per-position-out cell RMSE;
- mean per-player L1 error across the eight projected position-out totals;
- predicted and observed mean total defensive outs as a reconciliation diagnostic;
- per-position MAE diagnostics.

Also report equal-fold means for:

- share TV;
- share SSE;
- position-out cell MAE;
- position-out cell RMSE;
- primary-position match rate.

## 7. Binding selection rule

S0 is retained unless R1 or H1 satisfies **all** of the following:

1. fold-specific position-out cell MAE is no more than 2% worse than S0 in both folds;
2. equal-fold mean position-out cell MAE is strictly lower than S0;
3. equal-fold mean position-out cell RMSE is strictly lower than S0;
4. fold-specific mean share TV is no worse than S0 in both folds;
5. equal-fold mean share TV is strictly lower than S0; and
6. primary defensive-position match rate is not more than 0.01 absolute below S0 in either fold.

If both challengers pass, select the one with lower equal-fold mean position-out cell MAE. If tied
within `1e-9`, select the one with lower equal-fold mean share TV. If that is also tied within
`1e-9`, prefer R1 because it is the simpler direct mapping from the already-frozen Position/Role
forecast.

The selected form is the **binding Player Value v1 defensive position-allocation form** on the
available development evidence. No 2025 confirmation claim is made. The frozen total-outs form
remains B0 regardless of which share form is selected.

## 8. Required output and boundaries

Persist a binding result containing:

- contract SHA-256;
- exact upstream run IDs, artifact names, and digests;
- fold population and fallback diagnostics;
- candidate fold metrics and equal-fold means;
- gate-by-gate selection-rule outcomes;
- selected position-share form;
- explicit boundary flags.

Boundary flags must confirm:

- 2025 fielding outcomes accessed = false;
- total-outs form changed = false;
- Playing Time refit = false;
- Position/Role refit = false;
- Defense refit = false;
- run conversion performed = false;
- positional adjustment calculated = false;
- WAR/value calculated = false.

## Binding boundaries

- Total defensive exposure remains `B0_raw_persistence` and is not reopened.
- Position allocation changes shares only; projected position outs must reconcile to fixed total
  projected outs.
- The frozen Position/Role forecast is an input only and is not relabeled as defensive share without
  the R1 normalization tested here.
- Do not tune the 0.65 Position/Role threshold, the 50/50 hybrid weight, or any selection guardrail
  after results are opened.
- Do not use 2025 as an allegedly untouched allocation confirmation.
- Component-native opportunity mappings and Defense run conversion remain separate future gates.
- Positional adjustment remains separate from Defense skill and exposure.
- Replacement level, runs per win, WAR/value, and final ranking remain closed.
