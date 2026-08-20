# Player Value v1 — defensive exposure contract

Last updated: 2026-08-19

Status: **V1 DEFENSIVE EXPOSURE FULLY SELECTED / FROZEN.**

This contract fixes the observed and forward exposure interfaces used by Player Value v1. General defensive outs and catcher native opportunities are now frozen. It prevents batting playing time, batting-role shares, or generic fielding outs from being silently substituted for component-native defensive opportunities.

## 1. Canonical observed general defensive exposure

The canonical observed general exposure is **official fielding outs** from the certified Position/Role historical source:

- source workflow run: `32148467330`;
- artifact: `position-role-historical-source-2021-2024`;
- digest: `sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3`;
- source builder: `scripts/certify_position_role_historical_source.py`;
- deterministic projection: `src/universal_baseball/position_role_source.py`.

Source grain is `season x league_id x team_id x player_id x position_code`. Calculations use exact integer `fielding_outs`; displayed defensive innings may be the deterministic transform `fielding_outs / 3`.

General position-player defensive exposure uses:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

DH receives zero defensive-skill exposure. Pitcher defense is outside this interface.

## 2. Role share and defensive share remain distinct

Historical defensive position share is:

`defensive_probability = position fielding_outs / player total_defensive_outs`.

The frozen Position/Role model forecasts a nine-position batting-role vector over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

Its `role_probability` is constructed from games started, with games played as fallback. It is not the same quantity as `defensive_probability`.

The allocation gate explicitly tested a deterministic defensive normalization of frozen Position/Role and rejected it. Therefore **do not relabel frozen Position/Role probability as projected defensive-out share**.

## 3. Playing Time semantics remain distinct

Frozen Playing Time v1 forecasts batting opportunity / plate appearances. Projected PA is not defensive outs.

The shortcut

`projected defensive outs = projected PA x projected role share`

is not the selected general defensive-outs bridge. A projected-PA total-outs challenger was tested and rejected.

Frozen projected PA is used only where a separately predeclared component-native opportunity gate selected a PA-ratio hybrid; it does not reopen or replace the general defensive-outs bridge.

Do not refit Playing Time or Position/Role inside Player Value.

## 4. Total defensive-outs bridge — FROZEN

Contract: `docs/player-value-v1-defensive-exposure-diagnostic-contract.md`.

Binding result: `docs/player-value-v1-defensive-exposure-diagnostic-result.json`.

Workflow run: `32261447127`.

Development folds: 2022 inputs -> 2023 and 2023 inputs -> 2024. 2025 was not accessed.

Binding selection: **`B0_raw_persistence`**.

Thus:

`projected_total_defensive_outs = prior_season_mlb_defensive_outs`.

Rejected projected-PA and fixed-hybrid challengers must not be retuned after result access.

## 5. Defensive position allocation — FROZEN

Contract: `docs/player-value-v1-defensive-position-allocation-contract.md`.

Binding result: `docs/player-value-v1-defensive-position-allocation-result.json`.

Workflow run: `32266007594`.

Binding selection: **`S0_prior_defensive_share_persistence`**.

For a player with positive prior-season MLB defensive outs:

`projected_position_share[p] = prior_position_outs[p] / prior_total_defensive_outs`

and

`projected_position_outs[p] = projected_total_defensive_outs x projected_position_share[p]`.

Because both selected forms are prior-year persistence, v1 projected position outs reduce algebraically to prior-year position outs for the eight eligible positions. The explicit two-stage representation remains because total exposure and allocation are conceptually separate interfaces.

Projected position outs must reconcile to projected total defensive outs within deterministic numerical tolerance.

## 6. Catcher native opportunities — FROZEN

Contract: `docs/player-value-v1-catcher-native-opportunity-selection-contract.md`.

Binding result: `docs/player-value-v1-catcher-native-opportunity-selection-result.json`.

Workflow run: `32269076231`.

Artifact digest: `sha256:edc6c4fef7f0d17e063917f3defca48243ae60466a0e665c200c7989bfb42486`.

Development folds: 2022 inputs -> 2023 and 2023 inputs -> 2024. 2025 was not accessed.

### Catcher throwing

Native opportunity: Savant `sb_attempts`.

Selected form: **`H1_fixed_50_50_hybrid`**.

`projected_sb_attempts = 0.5 * prior_sb_attempts + 0.5 * (prior_sb_attempts * projected_expected_mlb_pa / source_year_mlb_pa)`.

If source-year MLB PA is nonpositive, the PA-ratio term falls safely back to prior `sb_attempts`, so H1 collapses to persistence for that player.

### Catcher blocking

Native opportunity: Savant blocking `pitches`.

Selected form: **`H1_fixed_50_50_hybrid`**.

`projected_blocking_pitches = 0.5 * prior_blocking_pitches + 0.5 * (prior_blocking_pitches * projected_expected_mlb_pa / source_year_mlb_pa)`.

If source-year MLB PA is nonpositive, H1 falls safely back to persistence.

Do **not** use `n_pbwp` as the blocking opportunity denominator. The native-semantics/run-rate work showed that Savant blocking `pitches` is the appropriate v1 opportunity interface.

### Catcher framing

Native opportunity: Savant framing `pitches`.

Selected form: **`B0_raw_persistence`**.

`projected_framing_pitches = prior_framing_pitches`.

The fixed 50/50 PA-ratio hybrid improved aggregate MAE/RMSE but failed the preregistered continuing-catcher MAE guardrail in the 2022->2023 fold, so raw persistence remains binding.

Do not retune the 2% guardrail or the 50/50 blend weight.

## 7. Complete v1 exposure interface

Player Value v1 defensive exposure is now fully specified:

- general total defensive outs: prior-year MLB defensive-outs persistence;
- general by-position allocation: prior-year defensive-out-share persistence;
- throwing opportunity: selected H1 projected `sb_attempts`;
- blocking opportunity: selected H1 projected Savant blocking `pitches`;
- framing opportunity: prior-year Savant framing-pitch persistence.

These are component-specific interfaces. Do not replace them with one generic defensive-exposure variable.

## 8. Required production exposure output

A production projection surface must persist at least:

- player identifier;
- projection season;
- level/scope;
- projected total defensive outs;
- projected defensive outs by eligible position;
- projected defensive position shares;
- projected throwing `sb_attempts`;
- projected blocking pitches;
- projected framing pitches;
- total-outs model/provenance = `B0_raw_persistence`;
- position-allocation model/provenance = `S0_prior_defensive_share_persistence`;
- catcher opportunity model/provenance by component;
- PA-ratio fallback flags;
- source provenance.

## Binding boundaries

- Official `fielding_outs` is the canonical observed general defensive-exposure unit.
- Total defensive outs are frozen at `B0_raw_persistence`.
- Defensive position allocation is frozen at `S0_prior_defensive_share_persistence`.
- Catcher native-opportunity forecasts are frozen at throwing H1, blocking H1, framing B0.
- `role_probability` and `defensive_probability` remain distinct.
- Do not use PA x role share as the v1 production general defensive-outs bridge.
- Do not refit Playing Time or Position/Role.
- Do not retune rejected exposure challengers after result access.
- Do not use 2025 as an allegedly untouched exposure holdout.
- Defense run conversion is governed separately by `docs/player-value-v1-defense-native-run-conversion-parameters.json` and is frozen.
- Positional adjustment remains separate.
- Replacement level, runs per win, WAR/value, and final ranking remain closed.
