# Player Value v1 — park-neutrality audit contract

Status: **PREDECLARED / ACTIVE**

## Purpose

Determine whether the frozen October 15, 2023 B2 batting projection retains a materially important imprint of a player's prior MLB home environment. The audit distinguishes retained projection context from the ordinary fact that realized batting outcomes vary by venue. An explicit Player Value park term is authorized only if the primary retention test below passes every predeclared gate.

This is an audit of the frozen batting projection, not a model-development gate. No Current Talent probability, translation offset, bin value, playing-time estimate, component run total, centering constant, replacement value, or runs-per-win value may be refit or reselected.

## Immutable inputs

1. Frozen B2 snapshots: Actions run `32099733186`, artifact `9311172007`, `projection_2023_to_2024/frozen_b2_profile.parquet`.
2. Certified 2023 MLB game evidence: Actions run `31989561396`, artifact `9274868338`, digest `sha256:4fde9a0a8774135bcea775bb369a3c4d484d53938a818c4c2bce803878e03d54`.
3. Certified 2024 MLB game evidence: Actions run `32096473700`, artifact `9310382371`, digest `sha256:bdca35299b7a82130eae197987aa1d1bb0448c8ef9dc9ee6c6ba3d39e79f2efe`.
4. Frozen pooled 2024 MLB bin values and batting reference: Actions run `31955392482`, artifact `9265954750`.
5. Frozen numerical centering result: `docs/player-value-v1-mlb-centering-2024.json`, verified Actions run `32379246845`.

The certified MLB game-evidence artifacts contain both the already-materialized player-game core profiles and the exact quarantined Savant CSV snapshots from which batting team, home team, and home/away status can be deterministically recovered. No live Savant fetch is authorized.

## Common-value residual

For every eligible player-game, value the observed core-bin counts with the frozen pooled 2024 MLB bin values. Value the B2 projection in the identical pooled environment:

`projected_raw_runs = game_PA * pooled_core_events_per_PA * sum(B2_bin_probability * pooled_bin_run_value)`

`observed_raw_runs = sum(observed_bin_count * pooled_bin_run_value)`

`residual_runs = observed_raw_runs - projected_raw_runs`

Rates are reported as runs per 600 PA. Before any grouped diagnostic, remove only the PA-weighted global residual rate on that diagnostic's eligible cohort. Do not fit player, team, venue, or park coefficients and feed them back into B2.

## Primary test — retained prior-home context

The primary test uses 2023 only to measure a player's prior home/away context and uses 2024 away games as the out-of-time target. Away-only target performance prevents the player's 2024 home venue from mechanically creating the alleged retained effect.

Eligibility is frozen as follows:

- player has a complete 12-bin B2 profile;
- player maps to exactly one batting team in certified 2023 evidence and exactly the same single batting team in certified 2024 evidence;
- at least 30 PA at home and 30 PA away in 2023;
- at least 60 away PA in 2024;
- every included player-game maps uniquely to batting team and home/away status;
- each reported team has at least five eligible players and at least 300 aggregate 2024 away PA.

For each eligible player:

- `prior_home_signal` is the player's 2023 observed home rate minus 2023 observed away rate;
- `retention_residual` is the player's B2 projected rate minus 2024 observed away rate.

Aggregate both quantities to batting team. Weight the player-level prior-home signal by the harmonic mean of 2023 home and away PA, and weight the retention residual by 2024 away PA. Fit one descriptive weighted least-squares line across eligible teams:

`team_retention_residual = intercept + retention_slope * team_prior_home_signal`

The permutation null shuffles team retention residuals against the fixed prior-home signals for exactly 10,000 iterations with seed `20240820`. The p-value is one-sided for a positive slope and uses the plus-one correction.

An explicit park correction is authorized only if **all** conditions hold:

1. at least 20 teams pass the fixed exposure rules;
2. full-season `retention_slope >= 0.25`;
3. one-sided permutation `p <= 0.05`;
4. the weighted standard deviation of fitted retained context is at least `1.0` run per 600 PA;
5. the slope is positive when the 2024 away target is scored separately before and after `2024-07-15`.

The slope threshold requires at least one quarter of the prior home/away signal to survive into the next-season away residual. The fitted-spread threshold requires that retained signal to be large enough to matter at roughly one-tenth of a win per full season before a new Player Value component is justified.

## Secondary diagnostics — not selection rules

Report, but do not use alone to authorize a correction:

- globally centered 2024 observed-minus-projected residuals by actual venue for venues with at least 2,500 eligible PA;
- 2024 home-minus-away observed residual by batting team;
- exposure-weighted dispersion and the five largest absolute group residual rates;
- included/excluded player, team, game, PA, and core-event counts.

These diagnostics establish whether ordinary realized venue context is visible. They cannot by themselves prove that the frozen projection retains prior park context.

## Decision boundary

- If every primary gate passes, freeze the demonstrated retained fraction and open a separate predeclared park-correction design gate. Do not estimate or apply the final correction inside this audit.
- If any primary gate fails, freeze `Rpark = 0` for Player Value v1. A nonzero realized 2024 venue diagnostic does not override a failed retention test.
- Realized 2024 data are audit targets only and may not enter projected B2 probabilities or numerical centering.
- The six zero-exposure centering members are unaffected; this audit does not change the 651-player centering cohort.
- No 2025 data, final WAR, or final ranking may be accessed or calculated here.

## Required frozen output

Persist `docs/player-value-v1-park-neutrality-audit-result.json` with input artifact identities, exact cohort counts, all primary metrics and gate booleans, secondary diagnostics, boundary assertions, the decision (`park_correction_design_authorized` or `Rpark_frozen_zero`), source commit, and Actions run ID. Upload the player/team/venue diagnostic tables as a workflow artifact.
