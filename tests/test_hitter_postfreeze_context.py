from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_postfreeze_context import (
    build_postfreeze_prior_pitcher_binary_feature,
)


def _events() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": pl.Series([2024, 2025], dtype=pl.Int64),
            "game_date": [date(2024, 7, 1), date(2025, 7, 1)],
            "game_pk": [1, 2],
            "at_bat_index": [0, 0],
            "league_id": [110, 110],
            "level_group": ["aaa", "aaa"],
            "pitcher_id": [50, 50],
            "batter_side": ["R", "R"],
            "pitcher_hand": ["R", "R"],
            "canonical_outcome": ["K", "OTHER_OUT"],
            "context_label_ready": [True, True],
        }
    )


def test_postfreeze_adapter_preserves_real_seasons() -> None:
    result = build_postfreeze_prior_pitcher_binary_feature(
        _events(), "K", protected_season=2026
    )
    assert result.get_column("season").to_list() == [2024, 2025]
    prior = result.filter(pl.col("season") == 2025).row(0, named=True)
    assert prior["K_prior_pitcher_denominator"] == pytest.approx(2**-0.5)


def test_postfreeze_adapter_rejects_protected_outcomes() -> None:
    events = pl.concat(
        [
            _events(),
            _events()
            .head(1)
            .with_columns(pl.lit(2026, dtype=pl.Int64).alias("season")),
        ]
    )
    with pytest.raises(ValueError, match="protected season 2026"):
        build_postfreeze_prior_pitcher_binary_feature(
            events, "K", protected_season=2026
        )
