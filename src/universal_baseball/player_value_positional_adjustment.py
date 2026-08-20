"""Deterministic Player Value v1 positional-adjustment calculation.

The v1 method uses the fixed FanGraphs full-season positional schedule, frozen
projected defensive outs by non-DH position, and frozen projected DH role events.
It does not perform league centering, replacement level, runs-per-win conversion,
or WAR aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

DEFENSIVE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF")
POSITIONAL_RUNS_PER_162 = MappingProxyType(
    {
        "C": 12.5,
        "1B": -12.5,
        "2B": 2.5,
        "3B": 2.5,
        "SS": 7.5,
        "LF": -7.5,
        "CF": 2.5,
        "RF": -7.5,
        "DH": -17.5,
    }
)
FULL_SEASON_DEFENSIVE_OUTS = 1458.0 * 3.0
FULL_SEASON_DH_ROLE_EVENTS = 162.0
SCHEDULE_ID = "fangraphs_fixed_162_game_v1"
BREF_POSITIONAL_RUNS_PER_150 = MappingProxyType(
    {
        "C": 9.0,
        "1B": -9.5,
        "2B": 3.0,
        "3B": 2.0,
        "SS": 7.0,
        "LF": -7.0,
        "CF": 2.5,
        "RF": -7.0,
        "DH": -15.0,
    }
)
BREF_FULL_SEASON_DEFENSIVE_OUTS = 1350.0 * 3.0
BREF_FULL_SEASON_DH_ROLE_EVENTS = 150.0
BREF_SENSITIVITY_SCHEDULE_ID = "baseball_reference_current_raw_150_game_sensitivity_v1"


@dataclass(frozen=True, slots=True)
class PositionalAdjustmentResult:
    """Transparent component decomposition for one projected player-season."""

    schedule_id: str
    runs_by_position: Mapping[str, float]
    total_runs: float
    projected_defensive_outs_by_position: Mapping[str, float]
    projected_dh_role_events: float


def _nonnegative_float(value: object, *, field: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric; got {value!r}") from exc
    if numeric < 0.0:
        raise ValueError(f"{field} must be nonnegative; got {numeric}")
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite; got {numeric}")
    return numeric


def _calculate_positional_adjustment(
    projected_defensive_outs_by_position: Mapping[str, object],
    *,
    projected_dh_role_events: object,
    schedule: Mapping[str, float],
    full_season_defensive_outs: float,
    full_season_dh_role_events: float,
    schedule_id: str,
) -> PositionalAdjustmentResult:
    unknown = sorted(set(projected_defensive_outs_by_position) - set(DEFENSIVE_POSITIONS))
    if unknown:
        raise ValueError(f"unsupported defensive position keys: {unknown}")

    outs: dict[str, float] = {
        position: _nonnegative_float(
            projected_defensive_outs_by_position.get(position, 0.0),
            field=f"projected_defensive_outs_by_position[{position}]",
        )
        for position in DEFENSIVE_POSITIONS
    }
    dh_events = _nonnegative_float(
        projected_dh_role_events,
        field="projected_dh_role_events",
    )

    runs: dict[str, float] = {
        position: (
            schedule[position]
            * outs[position]
            / full_season_defensive_outs
        )
        for position in DEFENSIVE_POSITIONS
    }
    runs["DH"] = (
        schedule["DH"]
        * dh_events
        / full_season_dh_role_events
    )

    return PositionalAdjustmentResult(
        schedule_id=schedule_id,
        runs_by_position=MappingProxyType(runs),
        total_runs=float(sum(runs.values())),
        projected_defensive_outs_by_position=MappingProxyType(outs),
        projected_dh_role_events=dh_events,
    )


def calculate_v1_positional_adjustment(
    projected_defensive_outs_by_position: Mapping[str, object],
    *,
    projected_dh_role_events: object,
) -> PositionalAdjustmentResult:
    """Calculate the binding FanGraphs-schedule positional adjustment."""

    return _calculate_positional_adjustment(
        projected_defensive_outs_by_position,
        projected_dh_role_events=projected_dh_role_events,
        schedule=POSITIONAL_RUNS_PER_162,
        full_season_defensive_outs=FULL_SEASON_DEFENSIVE_OUTS,
        full_season_dh_role_events=FULL_SEASON_DH_ROLE_EVENTS,
        schedule_id=SCHEDULE_ID,
    )


def calculate_bref_positional_sensitivity(
    projected_defensive_outs_by_position: Mapping[str, object],
    *,
    projected_dh_role_events: object,
) -> PositionalAdjustmentResult:
    """Calculate the required non-binding Baseball-Reference raw sensitivity."""

    return _calculate_positional_adjustment(
        projected_defensive_outs_by_position,
        projected_dh_role_events=projected_dh_role_events,
        schedule=BREF_POSITIONAL_RUNS_PER_150,
        full_season_defensive_outs=BREF_FULL_SEASON_DEFENSIVE_OUTS,
        full_season_dh_role_events=BREF_FULL_SEASON_DH_ROLE_EVENTS,
        schedule_id=BREF_SENSITIVITY_SCHEDULE_ID,
    )
