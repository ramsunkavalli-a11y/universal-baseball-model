import polars as pl

from universal_baseball.current_baserunning import (
    build_advancement_history,
    build_current_baserunning_rates,
    build_steal_history,
)
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference


def _components() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2025, 2025],
            "player_id": [1, 2, 1, 2],
            "player_name": ["One", "Two", "One", "Two"],
            "sport_id": [1, 1, 1, 1],
            "level_group": ["MLB", "MLB", "MLB", "MLB"],
            "plate_appearances": [100, 100, 100, 100],
            "hits": [30, 25, 30, 25],
            "doubles": [5, 4, 5, 4],
            "triples": [1, 1, 1, 1],
            "home_runs": [4, 4, 4, 4],
            "base_on_balls": [10, 10, 10, 10],
            "intentional_walks": [0, 0, 0, 0],
            "hit_by_pitch": [2, 2, 2, 2],
            "stolen_bases": [8, 2, 10, 2],
            "caught_stealing": [2, 2, 2, 2],
        }
    )


def test_current_baserunning_uses_history_then_reverts_to_neutral() -> None:
    steals, _ = build_steal_history(_components())
    advancement = build_advancement_history(
        {
            2025: [
                {
                    "player_id": "1",
                    "runner_runs_xb": "2.0",
                    "n_runner_moved_xb": "20",
                }
            ]
        }
    )
    reference = build_baserunning_reference(
        season=2025,
        plate_appearances=200,
        runs=25,
        outs=140,
        steal_opportunity_proxy=60,
        steal_attempts=16,
        stolen_bases=12,
        advancement_opportunities=30,
    )
    result = build_current_baserunning_rates(
        pl.DataFrame({"player_id": [1, 3]}),
        steals,
        advancement,
        forecast_seasons=(2026, 2029),
        reference=reference,
    )
    assert result.height == 4
    player_one = result.filter(pl.col("player_id") == 1)
    assert player_one.filter(pl.col("season") == 2026).item(
        0, "baserunning_evidence_tier"
    ) == "steal_and_advancement"
    assert player_one.filter(pl.col("season") == 2029).item(
        0, "baserunning_evidence_tier"
    ) == "population_neutral"
    assert abs(
        player_one.filter(pl.col("season") == 2029).item(
            0, "baserunning_runs_per_600"
        )
    ) < 1e-10
    assert result.filter(pl.col("player_id") == 3).get_column(
        "baserunning_runs_per_600"
    ).abs().max() < 1e-10
