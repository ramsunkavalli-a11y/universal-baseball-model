"""Final additive Player Value v1 runs-above-replacement and WAR arithmetic."""

from __future__ import annotations

import math
from dataclasses import dataclass


FINAL_AGGREGATION_ID = "player_value_v1_additive_war_2024"


def _finite(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    return numeric


@dataclass(frozen=True)
class FinalPlayerValue:
    runs_above_replacement: float
    runs_per_win: float
    war: float
    aggregation_id: str = FINAL_AGGREGATION_ID


def calculate_final_player_value(
    *,
    batting_runs: object,
    baserunning_runs: object,
    defense_runs: object,
    positional_runs: object,
    centering_runs: object,
    park_runs: object,
    replacement_runs: object,
    runs_per_win: object,
) -> FinalPlayerValue:
    """Apply the frozen, fully explicit Player Value v1 additive formula."""

    components = (
        _finite(batting_runs, "batting_runs"),
        _finite(baserunning_runs, "baserunning_runs"),
        _finite(defense_runs, "defense_runs"),
        _finite(positional_runs, "positional_runs"),
        _finite(centering_runs, "centering_runs"),
        _finite(park_runs, "park_runs"),
        _finite(replacement_runs, "replacement_runs"),
    )
    rpw = _finite(runs_per_win, "runs_per_win")
    if rpw <= 0:
        raise ValueError("runs_per_win must be positive")
    rar = math.fsum(components)
    war = rar / rpw
    if not math.isfinite(war):
        raise ValueError("calculated WAR must be finite")
    return FinalPlayerValue(runs_above_replacement=rar, runs_per_win=rpw, war=war)

