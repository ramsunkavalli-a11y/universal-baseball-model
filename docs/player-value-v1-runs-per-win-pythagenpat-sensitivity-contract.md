# Player Value v1 PythagenPat runs-to-wins sensitivity contract

Last updated: 2026-08-20

## Status

**PRE-OUTCOME SENSITIVITY METHOD FROZEN.**

This is the required practical Baseball-Reference player-aware/PythagenPat
runs-to-wins comparison. It is diagnostic only. The binding Player Value v1
conversion remains the common FanGraphs/Tango divisor frozen in
`docs/player-value-v1-runs-per-win-contract.md`.

## Public-method sources

- Baseball-Reference, "WAR Explained, Converting Runs to Wins":
  <https://www.baseball-reference.com/about/war_explained_runs_to_wins.shtml>
- Baseball-Reference, "Position Player WAR Calculations and Details":
  <https://www.baseball-reference.com/about/war_explained_position.shtml>

The public method uses

`PythagenPat(RS, RA) = RS^x / (RS^x + RA^x)`

with

`x = (RS + RA)^0.285`.

For a position player, offensive runs are added to the average team's runs
scored and fielding runs are subtracted from its runs allowed. The public page
also defines the position-player innings estimate as the greatest of `2.1 * PA`
and available fielding innings (or an `8 * G` fallback when fielding innings are
not available).

## Frozen 2024 adaptation

The comparison must consume the exact 651-player numerical-centering component
artifact from Actions run `32379246845`, artifact `9410315587`. No component is
refit or replayed.

For every positive-projected-PA player:

- `estimated_innings = max(2.1 * projected_expected_mlb_pa, projected_defensive_outs / 3)`;
- `estimated_games = estimated_innings / 9`;
- `offensive_runs = Rbat + Rbr + Rpos + Rlg`;
- `fielding_runs = Rdef`;
- `RS_player = league_team_runs_per_game + offensive_runs / estimated_games`;
- `RA_player = league_team_runs_per_game - fielding_runs / estimated_games`;
- `player_WAA = estimated_games * (PythagenPat(RS_player, RA_player) - 0.5)`.

`Rlg` is the already-frozen MLB centering term. No separate GIDP term has been
frozen for v1, so this sensitivity does not invent one. The park term remains
zero under the completed park-neutrality audit.

Replacement is evaluated as a second PythagenPat comparison rather than being
silently divided by the binding common RPW:

- `Rrep = frozen_replacement_runs_per_pa * projected_expected_mlb_pa`;
- `RS_replacement = league_team_runs_per_game - Rrep / estimated_games`;
- `replacement_wins = estimated_games * (0.5 - PythagenPat(RS_replacement, league_team_runs_per_game))`;
- `PythagenPat_WAR = player_WAA + replacement_wins`.

The binding comparison is `(Rbat + Rbr + Rdef + Rpos + Rlg + Rrep) / RPW`.

The league environment is the frozen 2024 materialization in
`docs/player-value-v1-mlb-run-environment-2024.json`. Team runs per game is MLB
runs divided by twice completed games; the binding RPW value is consumed exactly
as stored. Replacement uses the binding rate in
`docs/player-value-v1-replacement-level-2024.json`.

The frozen defensive-position allocation from run `32266007594`, artifact
`9370211679`, supplies projected defensive outs solely for the public innings
estimate. It does not change any component value.

## Zero-exposure and validity rules

The six mandated zero-exposure MLB members remain explicit rows with zero wins
under both conversions. For positive exposure, estimated games, `RS_player`,
`RA_player`, and `RS_replacement` must all be finite and positive. Duplicate or
missing player rows fail closed.

## Required output

Freeze `docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json` and
upload the complete 651-player comparison table. Report aggregate and player
difference distributions, but do not select, tune, or replace the binding RPW
from those outcomes.

