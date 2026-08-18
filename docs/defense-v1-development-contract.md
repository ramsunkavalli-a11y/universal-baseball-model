# Defense v1 development contract

Last updated: 2026-08-18

Status: **PRE-REGISTERED UNIVERSAL DEVELOPMENT GATE — 2025 DEFENSIVE TARGETS UNTOUCHED.**

## Objective

Build the smallest defensible one-year **defensive-quality projection** that works for affiliated players even when public tracking is unavailable.

This first gate is deliberately universal and non-tracking. It must establish that the traditional all-level evidence already shown to predict next-year Savant outcomes can beat a neutral position-relative baseline. Tracked OAA/framing evidence is reserved for a later incremental challenger after the universal baseline is selected.

This is a defensive-skill model only. Position/Role, playing time, positional adjustment, team allocation, WAR/value, and final ranking remain separate.

## Development / confirmation boundary

Already-opened development target years:

- 2021 inputs -> 2022 MLB defensive targets;
- 2022 inputs -> 2023 MLB defensive targets;
- 2023 inputs -> 2024 MLB defensive targets.

These three target years were used in the prior feature-screening gate and are therefore all **development evidence**, not untouched validation years.

**Completed-2025 defensive targets are reserved as untouched confirmation and may not be opened during this development gate.**

No claim of an untouched 2022/2023/2024 fold is permitted. Candidate selection uses grouped cross-validation inside the already-opened pre-2025 development surface; 2025 is the only future confirmation period.

## Frozen source inputs

Use only:

1. certified official 2021-2024 fielding captures from run `32148467330`;
2. public Savant target leaderboards for 2022-2024 via pinned `sportsdataverse==0.0.75`;
3. deterministic position/level metadata available in those official fielding rows.

Do not fetch 2025 defensive targets, Statcast tracking, scouting grades, prospect rankings, future level/role, or future playing time.

## Evidence rows

Aggregate all team/league rows by player × completed season × defensive position. Exclude P and DH.

Primary defensive position is the position with the most completed-season fielding outs, tie-broken by numeric position order C, 1B, 2B, 3B, SS, LF, CF, RF.

`current_level_group` is the highest affiliated level at which the player recorded positive fielding outs in the input season, using:

`MLB > AAA > AA > HIGH_A > SINGLE_A > ROOKIE_COMPLEX`.

The level is descriptive current evidence only; future level is prohibited.

## Universal general-range feature set — frozen

Only these four prior-season features may enter the first general-position challenger:

- `fielding_pct` — positive signal;
- `range_factor_per_9` — positive signal;
- `errors_per_9` — negative signal;
- `throwing_errors_per_9` — negative signal.

`double_plays_per_9` is closed after failing the position-adjusted next-year Savant screen and may not be rescued in this gate.

### General exposure eligibility

For a player-season to receive a fitted general-range estimate:

- primary position must be 1B, 2B, 3B, SS, LF, CF, or RF;
- completed-season fielding outs at that primary position >= 300;
- `fielding_pct` requires >= 100 chances.

Rows below the minimum remain explicit `insufficient_evidence`; the production fallback for such rows is not frozen until development completes.

## Universal catcher feature set — frozen

Catcher throwing candidate input:

- `caught_stealing_pct` only;
- require catcher fielding outs >= 300 and steal attempts (`caughtStealing + stolenBases`) >= 10.

Catcher blocking candidate input:

- `passed_balls_per_9` only;
- require catcher fielding outs >= 300.

`catcher_interference_per_9` is excluded because the frozen target screen had no direct Savant outcome. Public pitch-description throwing reconstruction is excluded because its validated coverage is weak.

No universal framing feature is asserted. Untracked framing remains missing evidence rather than fabricated talent.

## Target construction

### General range target

Use next-season Savant OAA leaderboard `diff_success_rate_formatted` only when:

- the player has a Savant target row;
- Savant `primary_pos_formatted` exactly matches the input primary position;
- target is finite.

Within each **target year × position**, standardize target to mean 0 / standard deviation 1. This creates `range_target_z`, a position-relative defensive-quality rate. The target transformation uses target outcomes only at scoring/training time and does not feed future information into predictors.

### Catcher throwing target

Use next-season Savant `cs_aa_per_throw`, requiring target `sb_attempts >= 10` and a finite value. Standardize within target year to `throwing_target_z`.

### Catcher blocking target

Use next-season Savant `blocks_above_average_per_game`, requiring target `pitches >= 500` and a finite value. Standardize within target year to `blocking_target_z`.

A later value layer may calibrate component z-scores to runs. Do not force run conversion inside this development gate.

## Predictor normalization

Normalization is fitted **inside each grouped training fold only**.

For each general feature:

1. calculate the raw prior-season rate from counts;
2. within training data, estimate feature mean and standard deviation by input `primary_position × current_level_group`;
3. if a cell has fewer than 30 eligible player-seasons, fall back to training-year `primary_position` mean/SD;
4. if still degenerate, fall back to the training-fold global mean/SD;
5. apply those training-only moments to the held-out target-year fold.

No held-out target or predictor distribution may set training normalization.

Catcher features are standardized using training-fold catcher input distributions with the same global fallback rule.

## Frozen model families

### B0 — neutral position-relative baseline

Predict `0.0` for every target z-score.

This is the appropriate skill baseline after within-year/position target standardization.

### General U1 — current-season traditional ridge

Linear ridge regression predicting `range_target_z` from the four frozen normalized general features.

Candidate ridge penalties:

`lambda in {0.0, 0.1, 1.0, 10.0}`

Intercept is unpenalized.

No interactions, trees, splines, position-specific coefficients, or feature selection are allowed in U1.

### General U2 — two-season recency/exposure traditional ridge

Same model and lambda grid as U1, but each frozen feature is replaced by a deterministic two-season standardized history:

`history_feature = (current_outs * current_z + 0.5 * prior_outs * prior_z) / (current_outs + 0.5 * prior_outs)`

when eligible same-feature prior-season evidence exists. If not, use `current_z` alone.

Prior-season `z` is standardized using only the corresponding training-fold source-year normalization. No future information enters the history feature.

The 0.5 prior-season recency multiplier is frozen and is **not** tuned.

### Catcher C1 — current-season single-feature linear model

Fit separate unpenalized one-feature linear regressions:

- `caught_stealing_pct_z -> throwing_target_z`;
- `passed_balls_per_9_z -> blocking_target_z`.

### Catcher C2 — two-season recency/exposure single-feature model

Use the same frozen 0.5 prior-season recency rule as U2, with exposure equal to steal attempts for CS% and fielding outs for passed-ball rate.

No multicomponent catcher model is authorized in this gate.

## Grouped development scoring

Use leave-one-target-year-out grouped cross-validation across 2022, 2023, and 2024:

- train on two target years;
- score the held-out target year;
- repeat for all three years.

This is internal development CV only because all three years were already opened during feature screening.

For each candidate report by fold and pooled out-of-fold:

- player count;
- mean squared error (primary);
- mean absolute error;
- Pearson correlation;
- Spearman correlation;
- calibration slope/intercept from `target ~ prediction` when estimable.

## Frozen selection rules

### General model promotion

A U1/U2 + lambda candidate is eligible to beat B0 only if all are true:

1. MSE is lower than B0 in at least 2 of 3 target-year folds;
2. pooled OOF MSE improves on B0 by at least **2.0%**;
3. no target-year fold MSE is more than **5.0% worse** than B0;
4. pooled OOF Spearman is at least **0.10**;
5. all predictions and metrics are finite.

Among eligible candidates, select the lowest pooled OOF MSE. Ties within `1e-6` choose the simpler model in this order:

`U1 before U2`, then smaller lambda.

If none pass, freeze general Defense-v1 universal range at B0 rather than rescue tuning.

### Catcher component promotion

C1/C2 for each catcher component is eligible only if:

1. at least 30 scored catchers exist in each target-year fold;
2. MSE is lower than B0 in at least 2 of 3 folds;
3. pooled OOF MSE improves by at least **2.0%**;
4. no fold is more than **7.5% worse** than B0;
5. pooled Spearman is at least **0.10**;
6. all metrics are finite.

Choose lower pooled OOF MSE; ties choose C1.

Failing a catcher gate leaves that component at explicit neutral/insufficient-evidence baseline pending later evidence; do not tune thresholds after failure.

## What is deliberately deferred

The following are **not candidates in this first universal gate**:

- age / age curve;
- tracked OAA or framing;
- Statcast launch/trajectory features directly;
- scouting/prospect information;
- position-specific regression coefficients;
- team defensive context;
- future position/role or playing time;
- run conversion / WAR.

If the universal baseline survives, age and tracked evidence may be tested only in a separately frozen incremental challenger contract before any 2025 defensive target is opened.

## Post-development rule

If any universal component passes:

1. persist the exact selected form and development evidence;
2. define the finite tracked/age incremental challenger, if worthwhile, without opening 2025;
3. after all pre-2025 development is closed, refit the retained Defense-v1 component(s) on all authorized 2022-2024 development responses;
4. freeze parameters, normalization moments, package versions, fallback behavior, and scoring code;
5. materialize completed-2025 defensive targets in a separate source-only workflow;
6. perform one-shot confirmation with no refit, reselection, threshold change, or rescue tuning.

If all components fail, Defense v1 remains neutral position-relative defensive skill with explicit uncertainty; positional value still belongs to the later value layer.

## Binding boundaries

- 2025 defensive targets remain untouched.
- No production Defense v1 parameters are frozen by this contract alone.
- No tracked evidence is used in this first gate.
- No age effect is tested in this first gate.
- No missing defense is silently encoded as observed average talent.
- No WAR/value calculation is authorized.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.
