from datetime import date

import polars as pl
import pytest

from universal_baseball.projection_validation import (
    PROJECTION_V1_CONFIRMATION_FOLD,
    PROJECTION_V1_DEVELOPMENT_FOLDS,
    ProjectionFold,
    add_projection_membership,
    development_fold_for_snapshot,
    require_development_fold,
    select_projection_target_events,
)


def test_projection_v1_development_folds_are_frozen_october15_to_next_calendar_year():
    assert [fold.snapshot_date for fold in PROJECTION_V1_DEVELOPMENT_FOLDS] == [
        date(2021, 10, 15),
        date(2022, 10, 15),
        date(2023, 10, 15),
    ]
    assert [fold.target_start for fold in PROJECTION_V1_DEVELOPMENT_FOLDS] == [
        date(2022, 1, 1),
        date(2023, 1, 1),
        date(2024, 1, 1),
    ]
    assert all(not fold.confirmation for fold in PROJECTION_V1_DEVELOPMENT_FOLDS)


def test_projection_fold_rejects_non_contract_dates():
    with pytest.raises(ValueError, match="October 15"):
        ProjectionFold(
            label="bad",
            snapshot_date=date(2023, 10, 1),
            target_start=date(2024, 1, 1),
            target_end=date(2025, 1, 1),
        )

    with pytest.raises(ValueError, match="full calendar year"):
        ProjectionFold(
            label="bad",
            snapshot_date=date(2023, 10, 15),
            target_start=date(2024, 4, 1),
            target_end=date(2025, 1, 1),
        )


def test_projection_membership_uses_strict_snapshot_and_half_open_target_window():
    fold = development_fold_for_snapshot(date(2023, 10, 15))
    frame = pl.DataFrame(
        {
            "game_date": [
                "2023-10-14",
                "2023-10-15",
                "2023-12-31",
                "2024-01-01",
                "2024-12-31",
                "2025-01-01",
            ],
            "value": list(range(6)),
        }
    )

    annotated = add_projection_membership(frame, fold=fold)
    assert annotated.get_column("is_projection_predictor_evidence").to_list() == [
        True,
        False,
        False,
        False,
        False,
        False,
    ]
    assert annotated.get_column("is_projection_target_evidence").to_list() == [
        False,
        False,
        False,
        True,
        True,
        False,
    ]


def test_projection_target_selection_preserves_complete_target_rows():
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[0]
    frame = pl.DataFrame(
        {
            "game_date": ["2021-09-01", "2022-04-01", "2022-08-15", "2023-04-01"],
            "event_id": [1, 2, 3, 4],
        }
    )

    target, metrics = select_projection_target_events(frame, fold=fold)
    assert target.get_column("event_id").to_list() == [2, 3]
    assert metrics["target_row_count"] == 2
    assert metrics["confirmation"] is False
    assert metrics["confirmation_access_explicitly_authorized"] is False


def test_projection_confirmation_is_quarantined_by_default():
    frame = pl.DataFrame({"game_date": ["2025-05-01"], "event_id": [1]})

    with pytest.raises(ValueError, match="quarantined"):
        add_projection_membership(frame, fold=PROJECTION_V1_CONFIRMATION_FOLD)
    with pytest.raises(ValueError, match="quarantined"):
        select_projection_target_events(frame, fold=PROJECTION_V1_CONFIRMATION_FOLD)
    with pytest.raises(ValueError, match="quarantined"):
        require_development_fold(PROJECTION_V1_CONFIRMATION_FOLD)


def test_projection_confirmation_requires_explicit_authorization():
    frame = pl.DataFrame(
        {"game_date": ["2024-10-14", "2025-05-01", "2026-01-01"], "event_id": [1, 2, 3]}
    )

    target, metrics = select_projection_target_events(
        frame,
        fold=PROJECTION_V1_CONFIRMATION_FOLD,
        allow_confirmation=True,
    )
    assert target.get_column("event_id").to_list() == [2]
    assert metrics["confirmation"] is True
    assert metrics["confirmation_access_explicitly_authorized"] is True


def test_projection_membership_fails_closed_on_unparseable_dates():
    frame = pl.DataFrame({"game_date": ["2024-04-01", "not-a-date"]})
    with pytest.raises(ValueError, match="unparseable"):
        add_projection_membership(frame, fold=PROJECTION_V1_DEVELOPMENT_FOLDS[-1])
