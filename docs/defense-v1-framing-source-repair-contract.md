# Defense v1 framing source-repair contract

## Purpose

Repair one invalid historical source dependency in the already-predeclared Defense v1 catcher-framing challenger. This is a source-semantics correction only; it is not a new model-development round.

## Defect being repaired

The frozen tracked challenger built the 2022-2024 catcher-framing target by calling SportsDataverse 0.0.75 `mlb_statcast_leaderboard_catcher_framing(year=YEAR)` and then locally applying the frozen target construction.

SportsDataverse 0.0.75 sends that argument to Baseball Savant as the generic query parameter `year=YEAR`. Baseball Savant's catcher-framing leaderboard uses the framing-specific season parameters `seasonStart` and `seasonEnd`. Therefore the prior fold labels cannot be treated as certified year-specific historical framing targets.

The old framing result remains immutable audit history. Its rejection is superseded only with respect to target-source validity; it is not deleted or rewritten.

## Authorized repair

Only the historical Savant framing target source may be corrected.

For target seasons 2022, 2023, and 2024, query the Baseball Savant `/leaderboard/catcher-framing` CSV endpoint directly with:

- `type=catcher`
- `seasonStart=YEAR`
- `seasonEnd=YEAR`
- `team=`
- a deliberately permissive source-side `min=1`
- `sortColumn=rv_tot`
- `sortDirection=desc`
- `csv=true`

The permissive source-side minimum is transport-only. The model target eligibility remains exactly the original local rule below.

## Frozen target construction

For each requested target season:

1. require a valid MLBAM catcher id;
2. require finite `rv_tot` and `pitches`;
3. require `pitches >= 1000` exactly as in the original challenger;
4. define `target_raw = 1000 * rv_tot / pitches`;
5. standardize `target_raw` globally within that target season using population standard deviation (`ddof=0`) to obtain `target_z`.

No other eligibility, scaling, or target transformation may change.

## Frozen F0/F1 evaluation

After the corrected 2022-2024 source is independently materialized and certified, rerun the original framing comparison without modification:

- F0: neutral zero predictor on the season-standardized framing target.
- F1: the already-certified tracked-framing predictor only.
- predictor eligibility, standardization, input seasons, catcher fielding-outs threshold, fitting method, folds, and MiLB-transfer logic remain exactly as previously declared.
- minimum 20 catchers in every MLB validation fold;
- F1 MSE better than F0 in at least 2 of 3 folds;
- pooled F1 MSE improvement versus F0 at least 2%;
- worst-fold F1 MSE degradation versus F0 no more than 5%;
- pooled F1 Spearman at least 0.10;
- all fitted coefficients and predictions finite.

The original Tier B transfer gate remains unchanged and is attempted only if the repaired Tier A gate passes.

## Fail-closed source certification

The repair source materializer must:

- access only 2022-2024;
- persist the exact requested parameters and resolved response URL for every season;
- persist raw CSV and parsed parquet for every season;
- persist a canonical target parquet for every season;
- reject missing required fields, invalid ids, duplicate canonical player-season keys, nonfinite target values, or degenerate target variance;
- reject suspiciously identical raw payloads across requested seasons;
- record file hashes and row counts;
- perform no model fitting or scoring.

If the source cannot be certified as year-specific, framing remains closed and the repair stops.

## Explicitly closed paths

This exception does **not** authorize:

- any change to general range U1/T1;
- any change to repaired catcher throwing or blocking;
- any new framing feature, interaction, regularization choice, threshold, or calibration;
- any change to the tracked-framing predictor construction;
- any 2025 target access during repaired development;
- any rescue or alternate challenger if repaired F1 fails;
- any run-value conversion, positional adjustment, WAR, or player-value work.

A repaired F1 failure closes framing. A repaired F1 pass authorizes only a separate parameter-freeze and untouched-2025 confirmation step under a separately persisted boundary.