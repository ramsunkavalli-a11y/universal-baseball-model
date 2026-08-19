"""Frozen Player Value v1 position-player replacement-level calculation."""

from __future__ import annotations

import math
from dataclasses import dataclass


REPLACEMENT_LEVEL_CONVENTION_ID = "baseball_reference_20_5_runs_per_600_pa_v1"
REPLACEMENT_RUNS_PER_600_PA = 20.5
REPLACEMENT_RUNS_PER_PA = REPLACEMENT_RUNS_PER_600_PA / 600.0


@dataclass(frozen=True)
class ReplacementLevelResult:
    replacement_runs: float
    projected_expected_mlb_pa: float
    replacement_runs_per_600_pa: float = REPLACEMENT_RUNS_PER_600_PA
    convention_id: str = REPLACEMENT_LEVEL_CONVENTION_ID


def _nonnegative_finite(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite nonnegative number") from exc
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return numeric


def calculate_v1_replacement_level(projected_expected_mlb_pa: object) -> ReplacementLevelResult:
    """Return replacement runs from frozen expected MLB plate appearances only."""

    pa = _nonnegative_finite(projected_expected_mlb_pa, "projected_expected_mlb_pa")
    return ReplacementLevelResult(
        replacement_runs=pa * REPLACEMENT_RUNS_PER_PA,
        projected_expected_mlb_pa=pa,
    )
