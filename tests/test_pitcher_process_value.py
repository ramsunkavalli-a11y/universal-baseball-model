from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.pitcher_process_value import (
    add_neutral_process_features,
    build_pitcher_process_features,
)


def _source() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024],
            "player_id": [1, 2, 3],
            "level_group": ["AAA", "AAA", "AAA"],
            "bf": [100.0, 100.0, 20.0],
            "pitches": [400.0, 400.0, 80.0],
            "swings": [200.0, 200.0, 40.0],
            "whiffs": [60.0, 40.0, 20.0],
            "strikes": [260.0, 240.0, 50.0],
            "balls": [140.0, 160.0, 30.0],
        }
    )


def test_process_features_shrink_and_exclude_tiny_samples() -> None:
    result = build_pitcher_process_features(_source())
    assert set(result["player_id"]) == {1, 2}
    first = result.filter(pl.col("player_id") == 1).row(0, named=True)
    second = result.filter(pl.col("player_id") == 2).row(0, named=True)
    assert first["process_whiff"] > 0
    assert second["process_whiff"] < 0
    assert first["process_available"] == 1


def test_missing_process_is_joined_as_neutral() -> None:
    stats = pl.DataFrame(
        {"season": [2024, 2024], "player_id": [1, 9], "feature": [1.0, 2.0]}
    )
    joined = add_neutral_process_features(stats, build_pitcher_process_features(_source()))
    missing = joined.filter(pl.col("player_id") == 9).row(0, named=True)
    assert missing["process_available"] == 0
    assert missing["process_whiff"] == pytest.approx(0.0)


def test_bad_process_accounting_fails() -> None:
    source = _source().with_columns(
        pl.when(pl.col("player_id") == 1)
        .then(pl.lit(300.0))
        .otherwise(pl.col("whiffs"))
        .alias("whiffs")
    )
    with pytest.raises(ValueError, match="accounting"):
        build_pitcher_process_features(source)
