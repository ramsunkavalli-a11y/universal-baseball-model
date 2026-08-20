"""Completeness gate for an alternate-season MLB-centering sensitivity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


REQUIRED_SURFACE_KEYS = (
    "official_positive_pa_membership",
    "projected_pa_with_outside_snapshot_fallback",
    "batting_profile",
    "mlb_batting_run_reference",
    "baserunning_projection",
    "defense_projection",
    "position_and_dh_projection",
)


@dataclass(frozen=True)
class CenteringSensitivityFeasibility:
    complete: bool
    available_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]


def evaluate_centering_sensitivity_feasibility(
    availability: Mapping[str, object],
) -> CenteringSensitivityFeasibility:
    """Require every contract component; a partial alternate season is forbidden."""

    unknown = sorted(set(availability) - set(REQUIRED_SURFACE_KEYS))
    if unknown:
        raise ValueError(f"unknown surface keys: {unknown}")
    absent = [key for key in REQUIRED_SURFACE_KEYS if key not in availability]
    if absent:
        raise ValueError(f"availability map missing required keys: {absent}")
    available = tuple(key for key in REQUIRED_SURFACE_KEYS if availability[key] is True)
    missing = tuple(key for key in REQUIRED_SURFACE_KEYS if availability[key] is not True)
    return CenteringSensitivityFeasibility(
        complete=not missing,
        available_keys=available,
        missing_keys=missing,
    )

