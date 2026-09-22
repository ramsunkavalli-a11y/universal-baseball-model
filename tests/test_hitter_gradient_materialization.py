from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_gradient_materialization import (
    CONTACT_BINS,
    CONTACT_OUTCOMES,
    PARK_COMPONENTS,
    PITCHER_CONTEXT_COLUMNS,
    PITCHER_SUPPORT_COLUMNS,
    attach_as_of_park_features,
    build_contact_cell_features,
    build_fold_manifest,
    join_contact_context_events,
    make_park_vintage,
)


def _contacts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2023, 2023],
            "league_id": [1, 1],
            "source_level": ["aa", "aa"],
            "game_pk": [10, 10],
            "at_bat_index": [1, 2],
            "player_id": [100, 100],
            "source_pitcher_id": [200, 201],
            "batter_side": ["L", "L"],
            "core_bin": ["PULL_GB", "PULL_GB"],
            "canonical_outcome": ["1B", "OTHER_OUT"],
        }
    )


def _context() -> pl.DataFrame:
    values: dict[str, list[object]] = {
        "season": [2023],
        "game_pk": [10],
        "at_bat_index": [1],
        "player_id": [100],
        "pitcher_id": [200],
        "batter_side": ["L"],
        "pitcher_hand": ["R"],
        "canonical_outcome": ["1B"],
        "context_label_ready": [True],
    }
    values.update({column: [0.25] for column in PITCHER_CONTEXT_COLUMNS})
    values.update({column: [20.0] for column in PITCHER_SUPPORT_COLUMNS})
    return pl.DataFrame(values)


def _games() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2023],
            "game_pk": [10],
            "game_date": [date(2023, 7, 1)],
            "sport_id": [12],
            "venue_id": [50],
            "home_team_id": [1],
            "away_team_id": [2],
        }
    )


def test_event_join_keeps_fallback_rows_and_neutralizes_context() -> None:
    result = join_contact_context_events(_contacts(), _context(), _games())
    assert result.height == 2
    assert result["opponent_context_known"].to_list() == [True, False]
    assert result["K_prior_pitcher_log_odds_residual"].to_list() == [0.25, 0.0]
    assert result["venue_known"].all()


def test_contact_cell_features_are_complete_and_sum_to_one() -> None:
    result = build_contact_cell_features(_contacts(), player_prior=10.0)
    probability_columns = [
        f"contact_result__{contact_bin}__{outcome}"
        for contact_bin in CONTACT_BINS
        for outcome in CONTACT_OUTCOMES
    ]
    assert set(probability_columns) <= set(result.columns)
    assert result.select(probability_columns).null_count().sum_horizontal().item() == 0
    for contact_bin in CONTACT_BINS:
        total = result.select(
            pl.sum_horizontal(
                *(f"contact_result__{contact_bin}__{outcome}" for outcome in CONTACT_OUTCOMES)
            )
        ).item()
        assert total == pytest.approx(1.0)


def test_park_vintage_has_neutral_unknown_venue_fallback() -> None:
    factors = pl.DataFrame(
        {
            "venue_id": [50] * len(PARK_COMPONENTS),
            "component": list(PARK_COMPONENTS),
            "training_precision": [1000.0] * len(PARK_COMPONENTS),
            "training_seasons": [2] * len(PARK_COMPONENTS),
            "park_clr_effect": [0.1] * len(PARK_COMPONENTS),
        }
    )
    vintage = make_park_vintage(factors, source_season=2023, prior_exposure=1000.0)
    events = pl.DataFrame({"season": [2023, 2023], "venue_id": [50, 99]})
    result = attach_as_of_park_features(events, vintage)
    assert result["park_factor_known"].to_list() == [True, False]
    assert result["park_effect__hr"].to_list() == [0.1, 0.0]
    assert result["park_factor_through_season"].to_list() == [2023, 2023]


def test_fold_manifest_uses_only_targets_known_at_evaluation_origin() -> None:
    rows = pl.DataFrame(
        {
            "origin_year": [2021, 2022, 2023],
            "target_season": [2022, 2023, 2024],
            "player_id": [1, 2, 3],
        }
    )
    manifest = build_fold_manifest(rows)
    fold_2023 = manifest.filter(pl.col("evaluation_origin") == 2023)
    assert fold_2023.filter(pl.col("role") == "training")["row_origin"].to_list() == [2021, 2022]
    assert fold_2023.filter(pl.col("role") == "evaluation")["row_origin"].to_list() == [2023]


def test_protected_contacts_are_rejected() -> None:
    contacts = _contacts().with_columns(pl.lit(2026).alias("season"))
    with pytest.raises(ValueError, match="protected 2026"):
        join_contact_context_events(contacts, _context(), _games())
