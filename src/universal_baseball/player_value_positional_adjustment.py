"""Deterministic Player Value v1 positional-adjustment calculation.

The v1 method uses the fixed FanGraphs full-season positional schedule, frozen
projected defensive outs by non-DH position, and frozen projected DH role events.
It does not perform league centering, replacement level, runs-per-win conversion,
or WAR aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    if numeric != numeric or numeric in {float("inf"), float("-inf")}:
        raise ValueError(f"{field} must be finite; got {numeric}")
    return numeric


def calculate_v1_positional_adjustment(
    projected_defensive_outs_by_position: Mapping[str, object],
    *,
    projected_dh_role_events: object,
) -> PositionalAdjustmentResult:
    """Calculate frozen v1 raw positional-adjustment runs.

    Parameters
    ----------
    projected_defensive_outs_by_position:
        Mapping containing projected MLB defensive outs for C, 1B, 2B, 3B, SS,
        LF, CF, and RF. Missing eligible positions are treated as zero. Any
        unknown position key is rejected so pitcher/DH exposure cannot leak into
        the defensive-out interface.
    projected_dh_role_events:
        Frozen projected DH role-equivalent games. For v1 this is raw prior-year
        DH role-event persistence from the binding DH exposure gate.
    """

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
            POSITIONAL_RUNS_PER_162[position]
            * outs[position]
            / FULL_SEASON_DEFENSIVE_OUTS
        )
        for position in DEFENSIVE_POSITIONS
    }
    runs["DH"] = (
        POSITIONAL_RUNS_PER_162["DH"]
        * dh_events
        / FULL_SEASON_DH_ROLE_EVENTS
    )

    return PositionalAdjustmentResult(
        schedule_id=SCHEDULE_ID,
        runs_by_position=MappingProxyType(runs),
        total_runs=float(sum(runs.values())),
        projected_defensive_outs_by_position=MappingProxyType(outs),
        projected_dh_role_events=dh_events,
    )
