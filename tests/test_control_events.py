from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.control_events import (
    CONTROL_EVENT_SCHEMA,
    OPENING_CONTROL_STATE_SCHEMA,
    classify_control_transactions,
    materialize_control_stints,
)
from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA
from universal_baseball.team_control import SEASON_WINDOW_SCHEMA


AS_OF = date(2024, 10, 15)


def _transactions(*events: tuple[int, str, str, date]) -> pl.DataFrame:
    rows = []
    for transaction_id, code, description, effective_date in events:
        rows.append(
            {
                "as_of_date": AS_OF,
                "transaction_id": transaction_id,
                "player_id": 10,
                "player_name": "Player Ten",
                "transaction_date": effective_date,
                "effective_date": effective_date,
                "resolution_date": None,
                "type_code": code,
                "type_description": code,
                "from_team_id": None,
                "to_team_id": 135,
                "description": description,
                "source_snapshot_id": "statsapi:test",
            }
        )
    return pl.DataFrame(rows, schema=RIGHTS_TRANSACTION_SCHEMA)


def _windows() -> pl.DataFrame:
    return pl.DataFrame(
        [{"season": 2024, "start_date": date(2024, 3, 20), "end_date": AS_OF}],
        schema=SEASON_WINDOW_SCHEMA,
    )


def _opening(state: str = "mlb_active") -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "player_id": 10,
                "season": 2024,
                "roster_state": state,
                "source_snapshot_id": "opening:test",
            }
        ],
        schema=OPENING_CONTROL_STATE_SCHEMA,
    )


def test_classifier_accepts_specific_control_transitions() -> None:
    result = classify_control_transactions(
        _transactions(
            (1, "OPT", "Optioned to El Paso.", date(2024, 4, 1)),
            (2, "RE", "Recalled from El Paso.", date(2024, 5, 1)),
            (3, "SC", "Placed on the 10-day injured list.", date(2024, 6, 1)),
            (4, "SC", "Activated from the 10-day injured list.", date(2024, 6, 11)),
        )
    )
    assert result.schema == CONTROL_EVENT_SCHEMA
    assert result.get_column("target_state").to_list() == [
        "minors_optioned",
        "mlb_active",
        "mlb_injured",
        "mlb_active",
    ]


def test_classifier_preserves_rehab_and_reviews_generic_status_change() -> None:
    result = classify_control_transactions(
        _transactions(
            (1, "ASG", "Sent on a rehab assignment.", date(2024, 5, 1)),
            (2, "SC", "Roster status changed.", date(2024, 5, 2)),
        )
    )
    assert result.get_column("action").to_list() == ["preserve_state", "review"]


def test_materializer_replays_only_accepted_events_and_closes_release() -> None:
    events = classify_control_transactions(
        _transactions(
            (1, "OPT", "Optioned to El Paso.", date(2024, 4, 1)),
            (2, "SC", "Roster status changed.", date(2024, 4, 10)),
            (3, "RE", "Recalled from El Paso.", date(2024, 4, 21)),
            (4, "REL", "Released.", date(2024, 5, 1)),
        )
    )
    result = materialize_control_stints(_opening(), events, _windows(), as_of_date=AS_OF)
    assert result.stints.select("start_date", "end_date", "roster_state").rows() == [
        (date(2024, 3, 20), date(2024, 3, 31), "mlb_active"),
        (date(2024, 4, 1), date(2024, 4, 20), "minors_optioned"),
        (date(2024, 4, 21), date(2024, 4, 30), "mlb_active"),
    ]
    assert result.review_events.get_column("transaction_id").to_list() == [2]


def test_materializer_can_begin_at_first_known_transition() -> None:
    events = classify_control_transactions(
        _transactions((1, "SE", "Selected contract.", date(2024, 7, 1)))
    )
    result = materialize_control_stints(
        pl.DataFrame(schema=OPENING_CONTROL_STATE_SCHEMA),
        events,
        _windows(),
        as_of_date=AS_OF,
    )
    assert result.stints.row(0, named=True)["start_date"] == date(2024, 7, 1)
