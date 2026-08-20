"""Fixed-reference MLB centering for Player Value v1.

This module contains only the league-average balancing calculation. It deliberately
has no replacement, park, runs-per-win, or WAR interface.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

CENTERING_ID = "fixed_2024_mlb_projected_component_reference_v1"
CENTERING_TOLERANCE_RUNS = 1e-10
REFERENCE_SEASON = 2024


@dataclass(frozen=True, slots=True)
class ReferencePlayerComponents:
    """Frozen projected above-average components for one reference MLB player."""

    player_id: int
    projected_expected_mlb_pa: float
    batting_runs: float
    baserunning_runs: float
    defense_runs: float
    positional_runs: float


@dataclass(frozen=True, slots=True)
class MLBCenteringReference:
    """Aggregate fixed-reference centering result."""

    centering_id: str
    reference_season: int
    reference_player_count: int
    aggregate_projected_mlb_pa: float
    aggregate_batting_runs: float
    aggregate_baserunning_runs: float
    aggregate_defense_runs: float
    aggregate_positional_runs: float
    aggregate_raw_above_average_runs: float
    centering_runs_per_pa: float
    aggregate_centering_runs: float
    post_centering_residual_runs: float
    tolerance_runs: float


def _finite(value: object, *, field: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric; got {value!r}") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite; got {numeric}")
    return numeric


def _finite_nonnegative(value: object, *, field: str) -> float:
    numeric = _finite(value, field=field)
    if numeric < 0.0:
        raise ValueError(f"{field} must be nonnegative; got {numeric}")
    return numeric


def _positive_player_id(value: object) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"player_id must be a positive integer; got {value!r}") from exc
    if numeric <= 0 or str(numeric) != str(value).strip():
        raise ValueError(f"player_id must be a positive integer; got {value!r}")
    return numeric


def build_fixed_mlb_centering_reference(
    rows: Iterable[ReferencePlayerComponents],
    *,
    reference_season: int = REFERENCE_SEASON,
    centering_id: str = CENTERING_ID,
    tolerance_runs: float = CENTERING_TOLERANCE_RUNS,
) -> MLBCenteringReference:
    """Aggregate the predeclared fixed MLB reference population.

    The input rows must already be the fixed MLB reference cohort assembled from
    frozen Player Value components. Membership reconciliation belongs to the
    materializer because it depends on source artifacts; this pure calculation
    still enforces one unique positive player id per row.
    """

    if int(reference_season) <= 0:
        raise ValueError("reference_season must be positive")
    if not centering_id:
        raise ValueError("centering_id must be nonempty")
    tolerance = _finite_nonnegative(tolerance_runs, field="tolerance_runs")

    player_ids: set[int] = set()
    pa_values: list[float] = []
    batting_values: list[float] = []
    baserunning_values: list[float] = []
    defense_values: list[float] = []
    positional_values: list[float] = []

    for index, row in enumerate(rows):
        player_id = _positive_player_id(row.player_id)
        if player_id in player_ids:
            raise ValueError(f"duplicate reference player_id: {player_id}")
        player_ids.add(player_id)

        pa_values.append(
            _finite_nonnegative(
                row.projected_expected_mlb_pa,
                field=f"rows[{index}].projected_expected_mlb_pa",
            )
        )
        batting_values.append(
            _finite(row.batting_runs, field=f"rows[{index}].batting_runs")
        )
        baserunning_values.append(
            _finite(row.baserunning_runs, field=f"rows[{index}].baserunning_runs")
        )
        defense_values.append(
            _finite(row.defense_runs, field=f"rows[{index}].defense_runs")
        )
        positional_values.append(
            _finite(row.positional_runs, field=f"rows[{index}].positional_runs")
        )

    if not player_ids:
        raise ValueError("fixed MLB reference population must not be empty")

    aggregate_pa = math.fsum(pa_values)
    if aggregate_pa <= 0.0:
        raise ValueError("aggregate projected MLB PA must be positive")

    aggregate_batting = math.fsum(batting_values)
    aggregate_baserunning = math.fsum(baserunning_values)
    aggregate_defense = math.fsum(defense_values)
    aggregate_positional = math.fsum(positional_values)
    aggregate_raw = math.fsum(
        (
            aggregate_batting,
            aggregate_baserunning,
            aggregate_defense,
            aggregate_positional,
        )
    )
    centering_runs_per_pa = -aggregate_raw / aggregate_pa
    aggregate_centering = aggregate_pa * centering_runs_per_pa
    residual = math.fsum((aggregate_raw, aggregate_centering))

    if abs(residual) > tolerance:
        raise ValueError(
            "fixed MLB centering residual exceeds tolerance: "
            f"{residual} runs > {tolerance}"
        )

    return MLBCenteringReference(
        centering_id=centering_id,
        reference_season=int(reference_season),
        reference_player_count=len(player_ids),
        aggregate_projected_mlb_pa=aggregate_pa,
        aggregate_batting_runs=aggregate_batting,
        aggregate_baserunning_runs=aggregate_baserunning,
        aggregate_defense_runs=aggregate_defense,
        aggregate_positional_runs=aggregate_positional,
        aggregate_raw_above_average_runs=aggregate_raw,
        centering_runs_per_pa=centering_runs_per_pa,
        aggregate_centering_runs=aggregate_centering,
        post_centering_residual_runs=residual,
        tolerance_runs=tolerance,
    )


def calculate_mlb_centering_runs(
    projected_expected_mlb_pa: object,
    *,
    centering_runs_per_pa: object,
) -> float:
    """Apply the frozen reference rate to one production player's projected PA."""

    pa = _finite_nonnegative(
        projected_expected_mlb_pa,
        field="projected_expected_mlb_pa",
    )
    rate = _finite(centering_runs_per_pa, field="centering_runs_per_pa")
    return pa * rate
