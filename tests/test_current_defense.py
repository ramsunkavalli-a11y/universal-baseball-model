import polars as pl

from universal_baseball.current_defense import build_current_general_defense_rates


def _general_parameters() -> dict[str, object]:
    moments = [
        {
            "feature": feature,
            "position": "SS",
            "level_group": "MLB",
            "mean": 0.0,
            "sd": 1.0,
        }
        for feature in (
            "fielding_pct",
            "range_factor_per_9",
            "errors_per_9",
            "throwing_errors_per_9",
        )
    ]
    return {
        "normalization": {"cell": moments, "position": [], "global": []},
        "universal": {"coefficients": [0.0, 1.0, 0.0, 0.0, 0.0]},
    }


def test_current_defense_uses_mlb_outs_only_and_one_validated_horizon() -> None:
    profiles = pl.DataFrame(
        {
            "season": [2026, 2026],
            "player_id": [1, 2],
            "position": ["SS", "SS"],
            "fielding_outs": [600, 600],
            "mlb_fielding_outs": [300, 300],
            "chances": [200, 200],
            "current_level_group": ["MLB", "MLB"],
            "fielding_pct": [1.0, -1.0],
            "range_factor_per_9": [1.0, 1.0],
            "errors_per_9": [1.0, 1.0],
            "throwing_errors_per_9": [1.0, 1.0],
        }
    )
    opportunity = pl.DataFrame(
        {
            "player_id": [1, 1, 2, 2],
            "season": [2027, 2028, 2027, 2028],
            "mlb_active_probability": [1.0, 1.0, 1.0, 1.0],
            "conditional_mlb_pa": [600.0, 500.0, 600.0, 500.0],
        }
    )
    result = build_current_general_defense_rates(
        pl.DataFrame({"player_id": [1, 2]}),
        profiles,
        opportunity,
        current_season=2026,
        forecast_seasons=(2027, 2028),
        general_parameters=_general_parameters(),
        conversion_parameters={
            "parameters_by_position": {
                position: {"run_rate_per_z_opportunity": 0.01}
                for position in ("1B", "2B", "3B", "SS", "LF", "CF", "RF")
            }
        },
    )
    adjacent = result.filter(pl.col("season") == 2027)
    later = result.filter(pl.col("season") == 2028)
    assert adjacent.item(0, "conditional_defense_runs") == 3.0
    assert adjacent.item(0, "defense_runs_per_600") == 3.0
    assert later.item(0, "conditional_defense_runs") == 0.0
    assert later.item(0, "defense_evidence_tier") == (
        "neutral_beyond_validated_adjacent_year"
    )
    assert result.filter(pl.col("season") == 2027).get_column(
        "conditional_defense_runs"
    ).sum() == 0.0
