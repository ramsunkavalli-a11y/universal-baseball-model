"""Player Value v1 position-player replacement-level calculation."""

from __future__ import annotations

import math
from dataclasses import dataclass


REPLACEMENT_LEVEL_CONVENTION_ID = "fangraphs_570_war_pool_projected_pa_v1"
FULL_MLB_SEASON_GAMES = 2430.0
POSITION_PLAYER_WAR_ALLOCATION = 570.0
BREF_POSITION_PLAYER_WAR_ALLOCATION_SENSITIVITY = 590.0
LEGACY_REPLACEMENT_RUNS_PER_600_PA = 20.5


@dataclass(frozen=True)
class ReplacementLevelReference:
    reference_season: int
    mlb_regular_season_games: float
    mlb_plate_appearances: float
    runs_per_win: float
    position_player_war_allocation: float
    replacement_war_pool: float
    replacement_runs_per_pa: float
    replacement_runs_per_600_pa: float
    convention_id: str = REPLACEMENT_LEVEL_CONVENTION_ID


@dataclass(frozen=True)
class ReplacementLevelResult:
    replacement_runs: float
    projected_expected_mlb_pa: float
    replacement_runs_per_pa: float
    replacement_runs_per_600_pa: float
    reference_season: int
    position_player_war_allocation: float
    convention_id: str = REPLACEMENT_LEVEL_CONVENTION_ID


def _finite(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    return numeric


def _positive_finite(value: object, label: str) -> float:
    numeric = _finite(value, label)
    if numeric <= 0:
        raise ValueError(f"{label} must be positive")
    return numeric


def _nonnegative_finite(value: object, label: str) -> float:
    numeric = _finite(value, label)
    if numeric < 0:
        raise ValueError(f"{label} must be nonnegative")
    return numeric


def build_replacement_reference(
    mlb_regular_season_games: object,
    mlb_plate_appearances: object,
    runs_per_win: object,
    *,
    reference_season: int,
    position_player_war_allocation: object = POSITION_PLAYER_WAR_ALLOCATION,
    convention_id: str = REPLACEMENT_LEVEL_CONVENTION_ID,
) -> ReplacementLevelReference:
    """Derive a season-specific replacement run rate from a league WAR pool."""

    games = _positive_finite(mlb_regular_season_games, "mlb_regular_season_games")
    pa = _positive_finite(mlb_plate_appearances, "mlb_plate_appearances")
    rpw = _positive_finite(runs_per_win, "runs_per_win")
    allocation = _positive_finite(position_player_war_allocation, "position_player_war_allocation")
    if games > FULL_MLB_SEASON_GAMES:
        raise ValueError(
            f"mlb_regular_season_games cannot exceed {FULL_MLB_SEASON_GAMES:g} for v1"
        )
    try:
        season = int(reference_season)
    except (TypeError, ValueError) as exc:
        raise ValueError("reference_season must be a positive integer") from exc
    if season <= 0:
        raise ValueError("reference_season must be a positive integer")
    if not str(convention_id).strip():
        raise ValueError("convention_id must be nonempty")

    war_pool = allocation * (games / FULL_MLB_SEASON_GAMES)
    runs_per_pa = war_pool * rpw / pa
    runs_per_600 = runs_per_pa * 600.0
    return ReplacementLevelReference(
        reference_season=season,
        mlb_regular_season_games=games,
        mlb_plate_appearances=pa,
        runs_per_win=rpw,
        position_player_war_allocation=allocation,
        replacement_war_pool=war_pool,
        replacement_runs_per_pa=runs_per_pa,
        replacement_runs_per_600_pa=runs_per_600,
        convention_id=str(convention_id),
    )


def build_v1_replacement_reference(
    mlb_regular_season_games: object,
    mlb_plate_appearances: object,
    runs_per_win: object,
    *,
    reference_season: int,
) -> ReplacementLevelReference:
    """Build the binding FanGraphs 570-WAR position-player replacement reference."""

    return build_replacement_reference(
        mlb_regular_season_games,
        mlb_plate_appearances,
        runs_per_win,
        reference_season=reference_season,
        position_player_war_allocation=POSITION_PLAYER_WAR_ALLOCATION,
        convention_id=REPLACEMENT_LEVEL_CONVENTION_ID,
    )


def calculate_v1_replacement_level(
    projected_expected_mlb_pa: object,
    reference: ReplacementLevelReference,
) -> ReplacementLevelResult:
    """Return replacement runs from projected MLB PA and a frozen MLB reference."""

    pa = _nonnegative_finite(projected_expected_mlb_pa, "projected_expected_mlb_pa")
    if reference.convention_id != REPLACEMENT_LEVEL_CONVENTION_ID:
        raise ValueError("binding v1 replacement calculation requires the frozen convention id")
    return ReplacementLevelResult(
        replacement_runs=pa * reference.replacement_runs_per_pa,
        projected_expected_mlb_pa=pa,
        replacement_runs_per_pa=reference.replacement_runs_per_pa,
        replacement_runs_per_600_pa=reference.replacement_runs_per_600_pa,
        reference_season=reference.reference_season,
        position_player_war_allocation=reference.position_player_war_allocation,
    )
