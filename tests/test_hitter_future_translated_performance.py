import polars as pl
import pytest

from universal_baseball.hitter_future_translated_performance import (
    HITTER_COMPONENTS,
    build_future_translated_targets,
    build_hitter_component_counts,
)


def _line(
    season: int,
    player_id: int,
    level: str,
    pa: int,
    *,
    hits: int,
    doubles: int,
    triples: int,
    home_runs: int,
    walks: int,
    intentional_walks: int,
    hbp: int,
) -> dict[str, object]:
    return {
        "season": season,
        "player_id": player_id,
        "level_group": level,
        "plate_appearances": pa,
        "hits": hits,
        "doubles": doubles,
        "triples": triples,
        "home_runs": home_runs,
        "base_on_balls": walks,
        "intentional_walks": intentional_walks,
        "hit_by_pitch": hbp,
    }


def test_component_counts_reconcile_to_plate_appearances() -> None:
    stats = pl.DataFrame(
        [
            _line(
                2022,
                1,
                "AAA",
                100,
                hits=30,
                doubles=8,
                triples=2,
                home_runs=5,
                walks=12,
                intentional_walks=2,
                hbp=3,
            )
        ]
    )

    result = build_hitter_component_counts(stats)

    assert result.item(0, "ubb") == 10
    assert result.item(0, "single") == 15
    assert sum(result.item(0, component) for component in HITTER_COMPONENTS) == 100


def test_future_target_translates_every_destination_level_to_one_scale() -> None:
    stats = pl.DataFrame(
        [
            _line(
                2022,
                1,
                "AAA",
                100,
                hits=30,
                doubles=8,
                triples=2,
                home_runs=5,
                walks=12,
                intentional_walks=2,
                hbp=3,
            ),
            _line(
                2022,
                1,
                "MLB",
                100,
                hits=25,
                doubles=6,
                triples=1,
                home_runs=4,
                walks=10,
                intentional_walks=1,
                hbp=2,
            ),
            _line(
                2023,
                2,
                "AAA",
                120,
                hits=36,
                doubles=9,
                triples=2,
                home_runs=6,
                walks=14,
                intentional_walks=1,
                hbp=3,
            ),
            _line(
                2023,
                3,
                "MLB",
                150,
                hits=40,
                doubles=10,
                triples=1,
                home_runs=7,
                walks=15,
                intentional_walks=1,
                hbp=4,
            ),
        ]
    )
    components = build_hitter_component_counts(stats)

    result = build_future_translated_targets(components, origins=(2022,))

    assert result.targets.height == 2
    assert set(result.targets["target_primary_level_rank"].to_list()) == {4, 5}
    assert result.targets["target_translated_woba"].is_finite().all()
    rates = result.targets.select(
        pl.sum_horizontal(
            *(f"target_translated_rate__{component}" for component in HITTER_COMPONENTS)
        ).alias("total")
    )
    assert rates["total"].to_list() == pytest.approx([1.0, 1.0])
    assert result.fold_metrics[0]["translation"]["completed_seasons"] == [2022]
