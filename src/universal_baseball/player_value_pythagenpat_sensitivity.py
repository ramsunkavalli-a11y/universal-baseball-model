"""Player-aware PythagenPat sensitivity for Player Value v1 position players."""

from __future__ import annotations

import math
from dataclasses import dataclass


PYTHAGENPAT_EXPONENT_POWER = 0.285
PYTHAGENPAT_SENSITIVITY_ID = "baseball_reference_player_aware_pythagenpat_v1"


def _finite(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    return numeric


def pythagenpat_win_percentage(runs_scored: object, runs_allowed: object) -> float:
    """Return PythagenPat win percentage for positive per-game run rates."""

    rs = _finite(runs_scored, "runs_scored")
    ra = _finite(runs_allowed, "runs_allowed")
    if rs <= 0 or ra <= 0:
        raise ValueError("runs_scored and runs_allowed must be positive")
    exponent = (rs + ra) ** PYTHAGENPAT_EXPONENT_POWER
    win_percentage = rs**exponent / (rs**exponent + ra**exponent)
    if not math.isfinite(win_percentage) or not 0 < win_percentage < 1:
        raise ValueError("calculated win percentage must be finite and between zero and one")
    return win_percentage


@dataclass(frozen=True)
class PythagenPatSensitivityResult:
    estimated_innings: float
    estimated_games: float
    offensive_runs: float
    fielding_runs: float
    replacement_runs: float
    player_runs_scored_per_game: float
    player_runs_allowed_per_game: float
    replacement_runs_scored_per_game: float
    player_win_percentage: float
    replacement_win_percentage: float
    wins_above_average: float
    replacement_wins: float
    war: float
    sensitivity_id: str = PYTHAGENPAT_SENSITIVITY_ID


def calculate_position_player_pythagenpat_sensitivity(
    *,
    projected_pa: object,
    projected_defensive_outs: object,
    batting_runs: object,
    baserunning_runs: object,
    defense_runs: object,
    positional_runs: object,
    centering_runs: object,
    replacement_runs_per_pa: object,
    league_team_runs_per_game: object,
) -> PythagenPatSensitivityResult:
    """Apply the frozen practical Baseball-Reference position-player comparison."""

    pa = _finite(projected_pa, "projected_pa")
    defensive_outs = _finite(projected_defensive_outs, "projected_defensive_outs")
    components = {
        "batting_runs": _finite(batting_runs, "batting_runs"),
        "baserunning_runs": _finite(baserunning_runs, "baserunning_runs"),
        "defense_runs": _finite(defense_runs, "defense_runs"),
        "positional_runs": _finite(positional_runs, "positional_runs"),
        "centering_runs": _finite(centering_runs, "centering_runs"),
    }
    replacement_rate = _finite(replacement_runs_per_pa, "replacement_runs_per_pa")
    league_rpg = _finite(league_team_runs_per_game, "league_team_runs_per_game")
    if pa < 0 or defensive_outs < 0 or replacement_rate < 0 or league_rpg <= 0:
        raise ValueError("exposures and replacement rate must be nonnegative; league rate positive")

    offensive_runs = (
        components["batting_runs"]
        + components["baserunning_runs"]
        + components["positional_runs"]
        + components["centering_runs"]
    )
    fielding_runs = components["defense_runs"]
    replacement_runs = replacement_rate * pa
    if pa == 0:
        if defensive_outs != 0 or any(value != 0 for value in components.values()):
            raise ValueError("zero-PA rows must have zero exposure and component runs")
        return PythagenPatSensitivityResult(
            estimated_innings=0.0,
            estimated_games=0.0,
            offensive_runs=0.0,
            fielding_runs=0.0,
            replacement_runs=0.0,
            player_runs_scored_per_game=league_rpg,
            player_runs_allowed_per_game=league_rpg,
            replacement_runs_scored_per_game=league_rpg,
            player_win_percentage=0.5,
            replacement_win_percentage=0.5,
            wins_above_average=0.0,
            replacement_wins=0.0,
            war=0.0,
        )

    estimated_innings = max(2.1 * pa, defensive_outs / 3.0)
    estimated_games = estimated_innings / 9.0
    player_rs = league_rpg + offensive_runs / estimated_games
    player_ra = league_rpg - fielding_runs / estimated_games
    replacement_rs = league_rpg - replacement_runs / estimated_games
    player_wp = pythagenpat_win_percentage(player_rs, player_ra)
    replacement_wp = pythagenpat_win_percentage(replacement_rs, league_rpg)
    waa = estimated_games * (player_wp - 0.5)
    replacement_wins = estimated_games * (0.5 - replacement_wp)
    return PythagenPatSensitivityResult(
        estimated_innings=estimated_innings,
        estimated_games=estimated_games,
        offensive_runs=offensive_runs,
        fielding_runs=fielding_runs,
        replacement_runs=replacement_runs,
        player_runs_scored_per_game=player_rs,
        player_runs_allowed_per_game=player_ra,
        replacement_runs_scored_per_game=replacement_rs,
        player_win_percentage=player_wp,
        replacement_win_percentage=replacement_wp,
        wins_above_average=waa,
        replacement_wins=replacement_wins,
        war=waa + replacement_wins,
    )

