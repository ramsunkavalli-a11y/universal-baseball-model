from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_foundation import (
    build_prospect_foundation_payload,
    write_prospect_foundation_explorer,
)


def test_foundation_withholds_fv_and_preserves_raw_level_performance() -> None:
    peak_hitters = pl.DataFrame({
        "player_id": [7], "player_name": ["Test Catcher"],
        "player_type": ["hitter"], "age_years": [24.0],
        "effective_evidence": [104.0], "reliability": [0.08],
        "evidence_band": ["moderate_100_199"], "ranking_status": ["ranked"],
        "current_primary_position": ["C"], "present_runs_rate": [-2.5],
        "peak_runs_rate": [-2.5], "prospect_peak_rate_rank": [None],
        "recent_component_direction_runs": [-1.8],
        "pitch_process_applied": [False], "pitch_process_runs_change": [0.0],
    })
    peak_pitchers = pl.DataFrame(schema={
        "player_id": pl.Int64, "player_type": pl.String,
    })
    future_hitters = pl.DataFrame({
        "player_id": [7, 7], "player_type": ["hitter", "hitter"],
        "horizon_years": [1, 2], "projected_runs_rate": [-26.7, -25.2],
    })
    future_pitchers = pl.DataFrame(schema={
        "player_id": pl.Int64, "player_type": pl.String,
        "horizon_years": pl.Int64, "projected_runs_rate": pl.Float64,
    })
    hitter_arrival = pl.DataFrame({
        "player_id": [7], "level_tier": ["AAA"],
        "primary_level_tier": ["A_OR_BELOW"],
        "primary_level_workload_share": [0.9], "level_progression": [0.0],
        "development_history_seasons": [2.0],
    })
    pitcher_arrival = pl.DataFrame(schema={
        "player_id": pl.Int64, "level_tier": pl.String,
        "primary_level_tier": pl.String,
        "primary_level_workload_share": pl.Float64,
        "level_progression": pl.Float64,
        "development_history_seasons": pl.Float64,
    })
    names = pl.DataFrame({
        "player_id": [7], "player_name": ["Test Catcher"],
        "organization_id": [137],
    })
    raw_hitting = pl.DataFrame({
        "season": [2026], "player_id": [7], "level_group": ["SINGLE_A"],
        "plate_appearances": [40], "at_bats": [40], "hits": [10],
        "doubles": [2], "triples": [0], "home_runs": [0],
        "base_on_balls": [0], "intentional_walks": [0], "hit_by_pitch": [0],
        "strike_outs": [8], "sac_flies": [0],
    })
    raw_pitching = pl.DataFrame(schema={
        "season": pl.Int64, "player_id": pl.Int64, "level_group": pl.String,
        "batters_faced": pl.Int64, "strike_outs": pl.Int64,
        "base_on_balls": pl.Int64, "intentional_walks": pl.Int64,
        "hit_batters": pl.Int64, "home_runs": pl.Int64,
    })

    payload = build_prospect_foundation_payload(
        peak_hitters, peak_pitchers, future_hitters, future_pitchers,
        hitter_arrival, pitcher_arrival, names, raw_hitting, raw_pitching,
        pl.DataFrame({
            "player_id": [7], "historical_comparable_players": [150],
            "historical_arrivals_4y": [10],
            "historical_conditional_rate_supported": [True],
            "historical_arrival_rate_4y": [0.04],
            "historical_conditional_component_war_per_600": [0.08],
            "historical_conditional_component_war_4y": [0.05],
            "historical_component_war_4y": [0.002],
            "historical_positive_component_war_4y": [0.005],
            "historical_impact_rate_4y": [0.0],
        }),
        season=2026,
    )
    player = payload["players"][0]

    assert payload["meta"]["status"] == "foundation_only_fv_withdrawn"
    assert player["fv"] is None
    assert player["expected_war"] is None
    assert player["value"] is None
    assert player["peak_runs_rate"] is None
    assert player["foundation_status"] == "peak_outside_supported_age"
    assert player["one_year_runs_rate"] == -26.7
    assert player["raw_levels"][0]["slg"] == 0.3
    assert player["historical_comparable_players"] == 150
    assert player["historical_component_war_4y"] == 0.002
    assert player["historical_impact_rate_4y"] == 0.0
    assert player["current_raw_workload"] == 40
    assert player["history_raw_workload"] == 40
    assert player["outcome_status"] == "historical_outcome_available"
    assert player["historical_conditional_rate_validated"] is True


def test_explorer_serialization_replaces_nonfinite_values(tmp_path: Path) -> None:
    template = tmp_path / "template.html"
    output = tmp_path / "output.html"
    template.write_text("<script>__EXPLORER_DATA__</script>", encoding="utf-8")

    write_prospect_foundation_explorer(
        {"players": [{"value": float("nan"), "nested": [float("inf")]}]},
        template,
        output,
    )

    embedded = output.read_text(encoding="utf-8").removeprefix("<script>").removesuffix(
        "</script>"
    )
    assert json.loads(embedded) == {"players": [{"value": None, "nested": [None]}]}
