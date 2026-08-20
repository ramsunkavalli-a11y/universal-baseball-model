# Player Value v1 — DH positional-exposure selection contract

Last updated: 2026-08-19

Status: **PREDECLARED BINDING V1 DH POSITIONAL-EXPOSURE SELECTION; PRE-2025 DEVELOPMENT ONLY.**

## Purpose

Freeze the one positional-adjustment exposure quantity not already supplied by the frozen defensive-out bridge: projected DH role-equivalent games.

All non-DH positional exposure remains the already-frozen projected fielding outs by position. This gate must not reopen general defensive-out volume or allocation.

## Evidence and folds

Use exactly:

1. 2022 inputs -> 2023 observed DH role events;
2. 2023 inputs -> 2024 observed DH role events.

No 2025 outcome may be queried or opened.

Reuse exactly:

- Position/Role development run `32152125644`, artifact `position-role-transition-challenger-development`, digest `sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5`;
- Playing Time selection run `32141616127`, artifact `playing-time-v1-candidate-selection`, digest `sha256:a8719576ef7ed7377a6376556d34e1fd377d5e27ca88535543a43c615f4cb5d8`;
- Playing Time 2023 validation run `32141934868`, artifact `playing-time-v1-validation-2023`, digest `sha256:738c631f5b4fbaa7875219ee452996e487799c4a323b0cafa57a7500583c5b39`;
- Playing Time 2024 validation run `32142089669`, artifact `playing-time-v1-validation-2024`, digest `sha256:979386377b5c2fa7f8f411bcd3284c6f4e68d532a5585e002b493f3cfffe0366`;
- certified fielding/role source run `32148467330`, artifact `position-role-historical-source-2021-2024`, digest `sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3`.

## Frozen Position/Role reconstruction

Reconstruct the binding Position/Role forecast exactly:

- when `current_primary_share >= 0.65`, use the transition-smoothed candidate role vector;
- otherwise carry the current role vector forward unchanged.

Do not refit transition means or the 0.65 threshold.

## DH role-event semantics

Use the same role-event semantics frozen by `build_batting_role_profiles`:

- if a player-season has positive total games started across `C, 1B, 2B, 3B, SS, LF, CF, RF, DH`, role events equal games started by position;
- otherwise role events equal games played by position.

Thus:

`observed_dh_role_events = DH games_started` when the player has any starts, otherwise `DH games_played`.

This quantity is a role-equivalent game count for positional-adjustment exposure. It is not defensive innings and must not be relabeled as such.

## Scoring population

Use the exact Position/Role development-prediction fold population. Join frozen Playing Time predictions where available and report any missing coverage.

Target-year missing DH role events are zero. This keeps non-DH players and players exiting DH exposure in the score.

## Candidate forms

### B0 — raw DH role-event persistence

`B0 = prior_dh_role_events`.

### R1 — frozen role-share redistribution at persistent total role volume

`R1 = frozen_projected_DH_role_probability * prior_total_role_events`.

This tests the frozen Position/Role share forecast without introducing a new total playing-time forecast.

### P1 — frozen role share with frozen Playing Time ratio

If source-year MLB PA > 0 and a frozen projected expected MLB PA is available:

`P1 = frozen_projected_DH_role_probability * prior_total_role_events * projected_expected_mlb_pa / source_year_mlb_pa`.

Otherwise fail safely to R1 and report the fallback.

No cap, floor, exponent, or fitted coefficient is allowed.

### H1 — fixed 50/50 B0/P1 hybrid

`H1 = 0.5 * B0 + 0.5 * P1`.

The 0.5 weight is fixed before results are opened and may not be changed afterward.

## Metrics

For each fold and candidate report:

- overall MAE and RMSE;
- observed and predicted mean DH role events;
- target-positive MAE/RMSE;
- incumbent-DH MAE/RMSE (`prior_dh_role_events > 0`);
- entrant-DH MAE/RMSE (`prior_dh_role_events = 0` and target > 0`);
- exit-DH MAE/RMSE (`prior > 0` and target = 0`);
- P1 fallback count.

Report equal-fold mean overall MAE and RMSE.

## Binding selection rule

B0 is retained unless R1, P1, or H1 satisfies all of:

1. fold-specific overall MAE is no more than 2% worse than B0 in both folds;
2. equal-fold mean overall MAE is strictly lower than B0;
3. equal-fold mean overall RMSE is strictly lower than B0;
4. target-positive MAE is no more than 2% worse than B0 in both folds; and
5. entrant-DH MAE is strictly lower than B0 in each fold containing at least one entrant.

If multiple challengers pass, select the one with the lowest equal-fold mean overall MAE. If tied within `1e-9`, prefer in order R1, P1, H1 because that order adds increasing dependence on a second upstream projection / fixed blend.

## Required output

Persist:

- selected DH positional-exposure form and formula;
- exact upstream provenance;
- fold population and Playing Time fallback diagnostics;
- all candidate metrics and gate outcomes;
- explicit boundary flags.

## Boundaries

- No 2025 outcome access.
- No Current Talent, Projection, Playing Time, Position/Role, or Defense refit.
- No change to frozen general defensive outs or defensive position allocation.
- No positional run schedule is selected in this gate.
- No positional-adjustment runs are calculated in this gate.
- No replacement level, runs per win, WAR/value, or final ranking.
