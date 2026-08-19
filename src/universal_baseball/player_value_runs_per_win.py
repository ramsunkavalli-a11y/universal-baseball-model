"""Frozen Player Value v1 position-player runs-per-win calculation."""

from __future__ import annotations

import math
from dataclasses import dataclass


RUNS_PER_WIN_CONVENTION_ID = "fangraphs_tango_league_rpw_v1"


@dataclass(frozen=True)
class RunsPerWinResult:
    mlb_runs_scored: float
    mlb_innings_pitched: float
    mlb_runs_per_9_innings: float
    runs_per_win: float
    reference_season: int | None
    convention_id: str = RUNS_PER_WIN_CONVENTION_ID


def _finite(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    return numeric


def calculate_v1_runs_per_win(
    mlb_runs_scored: object,
    mlb_innings_pitched: object,
    *,
    reference_season: int | None = None,
) -> RunsPerWinResult:
    """Calculate the frozen FanGraphs/Tango league-wide hitter RPW."""

    runs = _finite(mlb_runs_scored, "mlb_runs_scored")
    innings = _finite(mlb_innings_pitched, "mlb_innings_pitched")
    if runs < 0:
        raise ValueError("mlb_runs_scored must be nonnegative")
    if innings <= 0:
        raise ValueError("mlb_innings_pitched must be positive")

    runs_per_9 = 9.0 * runs / innings
    runs_per_win = 1.5 * runs_per_9 + 3.0
    if not math.isfinite(runs_per_win) or runs_per_win <= 0:
        raise ValueError("calculated runs_per_win must be finite and positive")

    if reference_season is not None:
        try:
            season = int(reference_season)
        except (TypeError, ValueError) as exc:
            raise ValueError("reference_season must be integer-like") from exc
        if season <= 0:
            raise ValueError("reference_season must be positive")
    else:
        season = None

    return RunsPerWinResult(
        mlb_runs_scored=runs,
        mlb_innings_pitched=innings,
        mlb_runs_per_9_innings=runs_per_9,
        runs_per_win=runs_per_win,
        reference_season=season,
    )
