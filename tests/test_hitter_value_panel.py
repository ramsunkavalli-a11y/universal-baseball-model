from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.hitter_value_panel import (
    build_hitter_contact_features,
    build_hitter_forecast_panel,
    build_hitter_stat_features,
    build_hitter_value_panel,
    build_neutral_mlb_value_targets,
)


def _stat_rows() -> pl.DataFrame:
    rows = []
    for season in (2015, 2016, 2017):
        rows.append(
            {
                "season": season,
                "player_id": 1,
                "level_group": "AA" if season < 2017 else "AAA",
                "reported_age": 20.0 + season - 2015,
                "plate_appearances": 100,
                "at_bats": 90,
                "hits": 30,
                "doubles": 5,
                "triples": 1,
                "home_runs": 4,
                "base_on_balls": 8,
                "intentional_walks": 1,
                "hit_by_pitch": 1,
                "strike_outs": 20,
                "sac_bunts": 0,
                "sac_flies": 1,
                "stolen_bases": 3,
                "caught_stealing": 1,
                "ground_into_double_play": 2,
            }
        )
    return pl.DataFrame(rows)


def _events() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "season": season,
                "player_id": 1,
                "source_level": "aa",
                "core_bin": contact_bin,
                "canonical_outcome": outcome,
            }
            for season in (2015, 2016, 2017)
            for contact_bin, outcome in (("PULL_GB", "1B"), ("CENTER_LD", "OTHER_OUT"))
        ]
    )


def _mlb() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2017],
            "player_id": [1],
            "batting_plate_appearances": [100],
            "batting_hits": [30],
            "batting_doubles": [5],
            "batting_triples": [1],
            "batting_home_runs": [4],
            "batting_base_on_balls": [8],
            "batting_intentional_walks": [1],
            "batting_hit_by_pitch": [1],
        }
    )


def test_builds_joint_cells_and_stat_rates() -> None:
    stats = build_hitter_stat_features(_stat_rows())
    contacts = build_hitter_contact_features(_events())

    assert stats.item(0, "single_rate") == pytest.approx(0.20)
    assert stats.item(0, "pa_level__AA") == 100
    assert contacts.item(0, "contact_events") == 2
    assert contacts.item(0, "contact_cell_rate__PULL_GB___1B") > contacts.item(
        0, "contact_cell_rate__PULL_GB___HR"
    )
    targets = build_neutral_mlb_value_targets(_mlb())
    assert targets["component_war"].is_finite().all()


def test_panel_keeps_zero_outcomes_and_exact_calendar_lags() -> None:
    stats = build_hitter_stat_features(_stat_rows())
    contacts = build_hitter_contact_features(_events())
    ages = pl.DataFrame(
        {
            "season": [2015, 2016, 2017],
            "player_id": [1, 1, 1],
            "age": [20.0, 21.0, 22.0],
            "relative_age": [-2.0, -1.0, 0.0],
        }
    )
    targets = build_neutral_mlb_value_targets(_mlb())
    panel = build_hitter_value_panel(
        stats,
        contacts,
        ages,
        targets,
        origins=(2015, 2016),
    )

    origin_2015 = panel.filter(pl.col("origin_year") == 2015).row(0, named=True)
    origin_2016 = panel.filter(pl.col("origin_year") == 2016).row(0, named=True)
    assert origin_2015["target_mlb_active"] == 0
    assert origin_2015["target_component_war"] == 0.0
    assert origin_2016["target_mlb_active"] == 1
    assert origin_2016["lag1__contact_events"] == 2


def test_rejects_2020_transition_and_2026_target() -> None:
    stats = build_hitter_stat_features(_stat_rows())
    contacts = build_hitter_contact_features(_events())
    ages = pl.DataFrame(
        {"season": [2015, 2016, 2017], "player_id": [1, 1, 1], "age": [20.0] * 3}
    )
    targets = build_neutral_mlb_value_targets(_mlb())

    with pytest.raises(ValueError, match="2019/2020"):
        build_hitter_value_panel(stats, contacts, ages, targets, origins=(2019,))
    with pytest.raises(ValueError, match="2026"):
        build_hitter_value_panel(stats, contacts, ages, targets, origins=(2025,))


def test_panel_keeps_stat_rows_when_contact_feed_is_unavailable() -> None:
    raw = _stat_rows().vstack(
        _stat_rows()
        .filter(pl.col("season") == 2016)
        .with_columns(pl.lit(2).cast(pl.Int64).alias("player_id"))
    )
    stats = build_hitter_stat_features(raw)
    contacts = build_hitter_contact_features(_events())
    ages = pl.DataFrame(
        {
            "season": [2015, 2016, 2017, 2016],
            "player_id": [1, 1, 1, 2],
            "age": [20.0, 21.0, 22.0, 23.0],
        }
    )
    panel = build_hitter_value_panel(
        stats,
        contacts,
        ages,
        build_neutral_mlb_value_targets(_mlb()),
        origins=(2016,),
    )
    no_contact = panel.filter(pl.col("player_id") == 2).row(0, named=True)
    assert no_contact["lag0__plate_appearances"] == 100
    assert no_contact["lag0__contact_events"] == 0
    assert no_contact["lag0__contact_feature_available"] == 0
    assert no_contact["lag0__missing"] == 0
    assert no_contact["lag0__contact_cell_rate__PULL_GB___1B"] is None


def test_forecast_panel_matches_development_features_without_targets() -> None:
    stats = build_hitter_stat_features(_stat_rows())
    contacts = build_hitter_contact_features(_events())
    ages = pl.DataFrame(
        {
            "season": [2015, 2016, 2017],
            "player_id": [1, 1, 1],
            "age": [20.0, 21.0, 22.0],
            "relative_age": [-2.0, -1.0, 0.0],
        }
    )
    development = build_hitter_value_panel(
        stats,
        contacts,
        ages,
        build_neutral_mlb_value_targets(_mlb()),
        origins=(2016,),
    )
    forecast = build_hitter_forecast_panel(
        stats,
        contacts,
        ages,
        origin=2016,
    )

    target_columns = {
        column
        for column in development.columns
        if column.startswith("target_") and column != "target_season"
    }
    assert not any(column in forecast.columns for column in target_columns)
    assert forecast.equals(development.drop(target_columns))
