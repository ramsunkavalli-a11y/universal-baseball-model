from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.park_gradient_features import (
    attach_prior_park_features,
    build_park_factor_vintage,
)


COMPONENTS = ("single", "double", "triple", "hr", "out")


def _factors() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "venue_id": venue,
                "component": component,
                "training_precision": precision,
                "training_seasons": seasons,
                "park_clr_effect": effect,
            }
            for venue, precision, seasons, effect in (
                (10, 5000.0, 2, 0.1),
                (20, 1000.0, 1, -0.05),
            )
            for component in COMPONENTS
        ]
    )


def test_vintage_exposes_effect_support_and_shrinkage_reliability() -> None:
    vintage = build_park_factor_vintage(
        _factors(),
        through_season=2023,
        components=COMPONENTS,
        prior_exposure=5000.0,
    )
    known = vintage.filter(pl.col("venue_id") == 10).row(0, named=True)
    assert known["park_factor_through_season"] == 2023
    assert known["park_effect_hr"] == pytest.approx(0.1)
    assert known["park_factor_reliability"] == pytest.approx(0.5)


def test_attach_uses_neutral_unknown_park_and_preserves_known_effect() -> None:
    vintage = build_park_factor_vintage(
        _factors(),
        through_season=2023,
        components=COMPONENTS,
        prior_exposure=5000.0,
    )
    rows = pl.DataFrame({"season": [2024, 2024], "venue_id": [10, 999]})
    result = attach_prior_park_features(rows, vintage, components=COMPONENTS)
    known, unknown = result.rows(named=True)
    assert known["park_factor_known"] is True
    assert known["park_effect_single"] == pytest.approx(0.1)
    assert unknown["park_factor_known"] is False
    assert unknown["park_factor_reliability"] == 0.0
    assert all(unknown[f"park_effect_{value}"] == 0.0 for value in COMPONENTS)


def test_attach_rejects_same_season_or_future_information() -> None:
    vintage = build_park_factor_vintage(
        _factors(),
        through_season=2024,
        components=COMPONENTS,
        prior_exposure=5000.0,
    )
    with pytest.raises(ValueError, match="strictly before"):
        attach_prior_park_features(
            pl.DataFrame({"season": [2024], "venue_id": [10]}),
            vintage,
            components=COMPONENTS,
        )
