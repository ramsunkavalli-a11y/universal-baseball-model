# Defense v1 tracked-evidence challenger contract

Last updated: 2026-08-18

Status: **FINAL PRE-2025 INCREMENTAL DEVELOPMENT GATE — 2025 DEFENSIVE TARGETS UNTOUCHED.**

## Question

Does portable public tracking evidence add meaningful next-season defensive-skill signal beyond the selected universal Defense-v1 components, and is the same representation usable for tracked MiLB players without silently assuming proprietary MiLB truth?

This is the final planned pre-2025 challenger. Age failed its frozen gate and is closed.

Frozen universal incumbents:

- general range: `U1`, lambda `0.0`;
- catcher blocking: `C2`;
- catcher throwing: `C1`.

No incumbent feature/model may be reselected in this gate.

## Source materialization — frozen

Pinned package: `sportsdataverse==0.0.75`.

Materialize the portable SportsDataverse tracking implementations once for:

### MLB input seasons

- 2021 regular season: `2021-04-01` through `2021-10-03`;
- 2022: `2022-04-07` through `2022-10-05`;
- 2023: `2023-03-30` through `2023-10-01`.

Use `mlb_statcast_search(..., season=YEAR, game_type="R")` with bounded date chunks.

### MiLB transfer season

- 2023: `2023-03-31` through `2023-09-30`;
- use `mlb_statcast_search_minors(..., season=2023, game_type="R", minors="true")`;
- do not rely on server-side `hfLevel`;
- classify AAA client-side from official 2023 Triple-A team abbreviations;
- retain remaining tracked rows separately as `TRACKED_NON_AAA`.

No 2024 tracking source is needed for predictors in this gate and **no 2025 tracking/target source may be accessed**.

## Portable tracked range feature

For each source season × tracked level, run the pinned SportsDataverse `mlb_fielding_oaa` implementation on balls in play.

For each player × defensive position:

`tracked_oaa_per_100 = 100 * oaa / opportunities`

Require:

- position in 1B, 2B, 3B, SS, LF, CF, RF;
- at least 100 OAA opportunities.

Within each source season × tracked level × position, standardize eligible `tracked_oaa_per_100` to mean 0 / SD 1. Require at least 20 eligible players in the cell; otherwise the tracked range feature is unavailable for that cell rather than pooled across a different position/level.

This creates `tracked_range_z`. The same representation is used in MLB and MiLB; no MiLB-specific coefficient or outcome tuning is allowed.

## General tracked challenger T1

T1 uses the exact selected U1 general pipeline and adds only `tracked_range_z`.

- lambda remains `0.0`;
- no age;
- no interactions;
- no change to U1 traditional-feature normalization;
- no extra tracking feature.

### MLB development comparison

Repeat grouped leave-one-target-year-out scoring for 2022, 2023, 2024.

For each fold, fit both U1 and T1 on the **same training rows with eligible tracked range evidence** and score them on the **same held rows with eligible tracked evidence**.

T1 passes the Tier-A tracked gate only if:

1. at least 75 held players exist in each target-year fold;
2. T1 MSE is lower than U1 in at least 2 of 3 folds;
3. pooled OOF MSE improves on U1 by at least **1.0%**;
4. no fold MSE is more than **3.0% worse** than U1;
5. pooled Spearman is no more than **0.005 lower** than U1;
6. all coefficients/predictions/metrics are finite.

If this fails, tracked range is closed for Defense v1 without rescue.

## Tracked MiLB transfer diagnostic — general range

Only if T1 passes the MLB gate, score a frozen 2023-MiLB -> 2024-MLB transfer diagnostic using the **2024 held-fold T1 coefficients trained only on 2022/2023 target years**.

Eligibility:

- 2023 U1 general evidence is eligible;
- player's `current_level_group` in 2023 is not MLB;
- eligible 2023 AAA or `TRACKED_NON_AAA` `tracked_range_z` exists at the same input primary position;
- 2024 Savant target exists at that exact position.

Tier-B tracked range is authorized only if:

1. at least 30 transfer players exist;
2. T1 transfer MSE is no more than **5.0% worse** than U1 on the identical transfer population;
3. T1 transfer Spearman is no more than **0.02 lower** than U1;
4. all metrics are finite.

If fewer than 30 exist, record `insufficient_transfer_evidence`; do not call the transfer a pass. Tier B then remains on the universal U1 range model for Defense v1.

## Portable catcher framing feature

For each source season × tracked level, run pinned `mlb_catcher_framing`.

For each catcher:

`tracked_framing_per_1000_takes = 1000 * framing_runs / takes`

Require at least 500 takes.

Within each source season × tracked level, standardize eligible rates to mean 0 / SD 1. Require at least 15 eligible catchers; otherwise framing evidence is unavailable for that level-season.

## Framing target

For target years 2022, 2023, 2024 use the public Savant catcher-framing leaderboard:

`target_framing_per_1000 = 1000 * rv_tot / pitches`

Require target `pitches >= 1000`, finite values, then standardize within target year to `framing_target_z`.

## Framing challenger F1

Baseline F0 predicts zero framing z.

F1 is an unpenalized one-feature linear model:

`tracked_framing_z -> framing_target_z`

Grouped leave-one-target-year-out gate:

1. at least 20 held catchers in each fold;
2. F1 MSE lower than F0 in at least 2 of 3 folds;
3. pooled OOF MSE improves at least **2.0%**;
4. no fold more than **5.0% worse**;
5. pooled Spearman >= **0.10**;
6. finite metrics.

Failing closes tracked framing for Defense v1 without rescue.

## Tracked MiLB transfer diagnostic — framing

Only if F1 passes MLB development, use the 2024 held-fold F1 fit trained on 2022/2023 targets to score 2023 tracked MiLB catchers who reach the 2024 Savant framing target.

Require:

- 2023 `current_level_group != MLB`;
- eligible tracked framing evidence;
- 2024 Savant framing target.

Tier-B framing is authorized only if:

1. at least 10 transfer catchers exist;
2. F1 transfer MSE is no more than **10.0% worse** than F0;
3. transfer Spearman is >= `0.0`;
4. finite metrics.

If fewer than 10 exist, record insufficient transfer evidence and do not use tracked framing for Tier B Defense v1.

## Source / model separation

Historical tracked source materialization must be persisted as a reusable artifact before scoring the challenger. Scoring may not re-query or alter tracked source filters based on model results.

The source artifact must record:

- package version;
- exact date ranges/filters;
- pitch/BIP/take counts;
- derived player-position opportunity counts;
- output file hashes;
- MiLB level-classification rule.

## End of pre-2025 development

After this gate there are **no additional planned Defense-v1 development challengers**.

- Age is closed.
- Failed traditional features are closed.
- Any tracked component that fails is closed.

The retained component set must then be refit/frozen on all authorized 2022-2024 development responses before any completed-2025 defensive target is opened.

## Binding boundaries

- no 2025 defensive target/source access;
- no new feature search;
- no age rescue;
- no position-specific tracked coefficients;
- no proprietary MiLB validation claim;
- no run conversion / WAR/value;
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
