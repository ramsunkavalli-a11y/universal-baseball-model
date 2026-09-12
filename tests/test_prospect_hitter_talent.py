from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_batting_runs import MlbBattingReference
from universal_baseball.prospect_hitter_talent import (
    RANKING_MINIMUM_EFFECTIVE_EVENTS,
    build_present_hitter_talent,
    evidence_band,
)


def _reference() -> MlbBattingReference:
    probabilities = {core_bin: 1 / len(ALL_CORE_BINS) for core_bin in ALL_CORE_BINS}
    values = {core_bin: 0.0 for core_bin in ALL_CORE_BINS}
    values["K"] = -0.3
    values["BB_HBP"] = 0.3
    return MlbBattingReference(
        season=2024,
        core_event_rate_per_pa=0.9,
        reference_probabilities=probabilities,
        bin_run_values=values,
        reference_run_value_per_core_event=0.0,
        reference_run_value_per_pa=0.0,
    )


def _profile(player_id: int, effective: float, *, better: bool) -> list[dict[str, object]]:
    probabilities = {core_bin: 1 / len(ALL_CORE_BINS) for core_bin in ALL_CORE_BINS}
    if better:
        probabilities["K"] -= 0.02
        probabilities["BB_HBP"] += 0.02
    return [
        {
            "player_id": player_id,
            "core_bin": core_bin,
            "baseline2_latent_probability": probability,
            "baseline2_effective_core_events": effective,
        }
        for core_bin, probability in probabilities.items()
    ]


@pytest.mark.parametrize(
    ("events", "expected"),
    [(0, "unresolved_lt_25"), (25, "thin_25_49"), (50, "limited_50_99"),
     (100, "moderate_100_199"), (200, "strong_200_plus")],
)
def test_evidence_band_boundaries(events: float, expected: str) -> None:
    assert evidence_band(events) == expected


def test_thin_player_is_not_ranked_even_with_better_rate() -> None:
    profile = pl.DataFrame(
        _profile(1, RANKING_MINIMUM_EFFECTIVE_EVENTS - 1, better=True)
        + _profile(2, RANKING_MINIMUM_EFFECTIVE_EVENTS, better=False)
    )
    context = pl.DataFrame({"player_id": [1, 2], "as_of_level_group": ["AA", "AAA"]})
    result = build_present_hitter_talent(profile, context, _reference())
    thin = result.filter(pl.col("player_id") == 1).row(0, named=True)
    supported = result.filter(pl.col("player_id") == 2).row(0, named=True)

    assert thin["present_batting_runs_per_600_pa"] > supported["present_batting_runs_per_600_pa"]
    assert thin["ranking_status"] == "unresolved"
    assert thin["present_batting_talent_rank"] is None
    assert supported["present_batting_talent_rank"] == 1
    assert thin["strongest_positive_component"] in {"fewer strikeouts", "more walks/HBP"}
