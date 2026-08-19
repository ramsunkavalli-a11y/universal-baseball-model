# Player Value v1 — defensive exposure contract

Last updated: 2026-08-19

Status: **OBSERVED SOURCE FROZEN; V1 GENERAL DEFENSIVE-OUT VOLUME AND POSITION ALLOCATION SELECTED / FROZEN; COMPONENT-NATIVE OPPORTUNITIES STILL OPEN.**

This contract fixes what counts as observed defensive exposure and records the selected Player Value v1 forward bridge for general defensive outs. It prevents batting playing time or start-share probabilities from being silently substituted for defensive opportunities. Catcher-component native opportunities remain separate because throwing, blocking, and framing do not share the same denominator as general fielding outs.

## 1. Canonical observed defensive exposure

The canonical observed exposure is **official fielding outs** from the certified Position/Role historical source:

- source workflow run: `32148467330`;
- artifact: `position-role-historical-source-2021-2024`;
- digest: `sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3`;
- source builder: `scripts/certify_position_role_historical_source.py`;
- deterministic projection: `src/universal_baseball/position_role_source.py`.

Source grain is `season x league_id x team_id x player_id x position_code`. Calculations use exact integer `fielding_outs`; displayed defensive innings may be the deterministic transform `fielding_outs / 3`.

Player Value v1 position-player defensive exposure uses:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

DH receives zero defensive-skill exposure. Pitcher defense is outside this interface.

## 2. Role share and defensive share remain distinct

Historical defensive position share is:

`defensive_probability = position fielding_outs / player total_defensive_outs`.

The frozen Position/Role model instead forecasts a nine-position batting-role vector over:

`C, 1B, 2B, 3B, SS, LF, CF, RF, DH`.

Its `role_probability` is constructed from games started, with games played as fallback. It is not the same quantity as `defensive_probability`.

The allocation gate explicitly tested a deterministic defensive normalization of frozen Position/Role and rejected it under the preregistered rule. Therefore **do not relabel frozen Position/Role probability as projected defensive-out share** in Player Value v1.

## 3. Playing Time semantics remain distinct

Frozen Playing Time v1 forecasts batting opportunity / plate appearances. Projected PA is not defensive outs.

The shortcut

`projected defensive outs = projected PA x projected role share`

is not the selected v1 bridge. A projected-PA total-outs challenger was tested and rejected under the frozen development rule.

Do not refit Playing Time or Position/Role inside Player Value.

## 4. Total defensive-outs bridge — FROZEN

Contract: `docs/player-value-v1-defensive-exposure-diagnostic-contract.md`.

Binding result: `docs/player-value-v1-defensive-exposure-diagnostic-result.json`.

Workflow run: `32261447127`.

Development folds: 2022 inputs -> 2023 and 2023 inputs -> 2024. 2025 was not accessed.

Candidates:

- `B0_raw_persistence`: prior-season MLB defensive outs;
- `P1_projected_pa_global_scale`: frozen projected MLB PA x one contemporaneous outs/PA scale;
- `H1_fixed_50_50_hybrid`: fixed 50/50 B0/P1 blend.

Binding selection: **`B0_raw_persistence`**.

Equal-fold means:

- B0: MAE `151.8143`, RMSE `473.4592`;
- P1: MAE `180.2195`, RMSE `427.4569`;
- H1: MAE `152.5628`, RMSE `430.7028`.

P1 and H1 improved RMSE and entrant error but failed the preregistered overall-MAE requirements. H1's 2022->2023 MAE was about 2.20% worse than B0 against an allowed 2%. Do not retune the threshold or blend weight.

Thus:

`projected_total_defensive_outs = prior_season_mlb_defensive_outs`.

## 5. Defensive position allocation — FROZEN

Contract: `docs/player-value-v1-defensive-position-allocation-contract.md`.

Binding result: `docs/player-value-v1-defensive-position-allocation-result.json`.

Workflow run: `32266007594`.

The allocation gate kept total projected defensive outs fixed at B0 and compared:

- `S0_prior_defensive_share_persistence`: prior defensive-out shares;
- `R1_frozen_role_defensive_normalization`: exact frozen Position/Role forecast, DH removed and defensive mass renormalized;
- `H1_fixed_50_50_share_hybrid`: fixed 50/50 S0/R1 share blend.

Scoring used continuing defenders on the 2022->2023 and 2023->2024 development folds because a position share is undefined when total defensive exposure is zero. Entrant/exit volume error had already been addressed in the separate total-outs gate.

Binding selection: **`S0_prior_defensive_share_persistence`**.

Equal-fold means:

- S0: position-out cell MAE `164.8437`, RMSE `472.8779`, share TV `0.275841`, primary-position match `0.66025`;
- R1: MAE `167.4807`, RMSE `466.5794`, share TV `0.280707`, primary match `0.65041`;
- H1: MAE `165.4973`, RMSE `468.6990`, share TV `0.272824`, primary match `0.66121`.

H1 improved RMSE/share TV but failed the required equal-fold position-out MAE improvement. R1 failed additional share-TV/primary-position guardrails. Do not retune the 0.65 upstream Position/Role threshold, 50/50 blend weight, or selection guardrails.

Thus, for a player with positive prior-season MLB defensive outs:

`projected_position_share[p] = prior_position_outs[p] / prior_total_defensive_outs`

and

`projected_position_outs[p] = projected_total_defensive_outs x projected_position_share[p]`.

Because both selected forms are prior-year persistence, this reduces deterministically to prior-year position outs for the eight eligible positions. The explicit two-stage representation is retained because total exposure and position allocation remain conceptually separate interfaces.

Projected position outs must reconcile to projected total defensive outs within deterministic numerical tolerance.

## 6. General v1 defensive-out bridge — CLOSED

The forward general defensive-out bridge is now selected:

1. total defensive outs: `B0_raw_persistence`;
2. defensive position shares: `S0_prior_defensive_share_persistence`;
3. position outs: fixed total x fixed share.

The 2025 fielding period was not used to tune either selection, and no untouched-confirmation claim is made for the allocation question because upstream 2025 Position/Role outcomes had already been accessed.

Do not reopen these exposure selections absent a concrete implementation failure.

## 7. Component-native opportunities remain separate

`fielding_outs` is the canonical general seasonal defensive-exposure source, but it is **not** automatically the denominator for every Defense component.

Run conversion must preserve each component's actual native target/opportunity unit:

- **general range:** determine the principled exposure/run mapping for Savant Success Rate Added;
- **catcher throwing:** native target is `cs_aa_per_throw`; projected throw opportunities must be handled explicitly;
- **catcher blocking:** repaired native target is `blocks_above_average_per_game` with source pitch eligibility; preserve the target's actual denominator rather than multiplying by fielding outs by default;
- **framing:** raw target is run value per 1,000 pitches before standardization; projected catcher pitch exposure is the natural native interface to validate.

Historical fielding outs may be used as an input to a separately validated component-opportunity bridge, but no component receives an arbitrary universal `runs per out` or `runs per z` constant.

## 8. Required production exposure output

A production projection surface using the frozen bridge must persist at least:

- player identifier;
- projection season;
- level/scope;
- projected total defensive outs;
- projected defensive outs by eligible position;
- projected defensive position shares;
- total-outs model/provenance = `B0_raw_persistence`;
- position-allocation model/provenance = `S0_prior_defensive_share_persistence`;
- fallback/coverage flags;
- component-specific projected opportunity counts once separately frozen;
- source provenance.

## Binding boundaries

- Official `fielding_outs` is the canonical observed general defensive-exposure unit.
- Total defensive outs are frozen at `B0_raw_persistence`.
- Defensive position allocation is frozen at `S0_prior_defensive_share_persistence`.
- `role_probability` and `defensive_probability` remain distinct.
- Do not use PA x role share as the v1 production defensive-outs bridge.
- Do not refit Playing Time or Position/Role.
- Do not retune rejected exposure challengers after result access.
- Do not use 2025 as an allegedly untouched exposure holdout.
- Component-native catcher opportunity mappings remain open.
- Do not convert Defense skill to seasonal runs until each needed native conversion/opportunity interface is frozen.
- Positional adjustment remains separate.
- Replacement level, runs per win, WAR/value, and final ranking remain closed.
