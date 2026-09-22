from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.historical_injury_features import (
    build_historical_injury_features,
    parse_injury_event,
)


def test_parse_injury_event_supports_disabled_and_injured_list_eras() -> None:
    assert parse_injury_event(
        "Club placed C Example on the 10-day disabled list."
    ) == ("placement", 10, 0)
    assert parse_injury_event(
        "Club activated C Example from the 15-day injured list."
    ) == ("activation", 15, 0)
    assert parse_injury_event(
        "Club placed C Example on the COVID-19 injured list."
    ) == ("placement", 0, 1)
    assert parse_injury_event("Club optioned C Example to Triple-A.") is None


def test_build_features_uses_only_events_known_by_cutoff() -> None:
    events = pl.DataFrame(
        {
            "transaction_id": [1, 2, 3, 4],
            "player_id": [10, 10, 10, 10],
            "event_date": [
                date(2023, 8, 1),
                date(2023, 8, 11),
                date(2024, 10, 1),
                date(2024, 10, 20),
            ],
            "event_kind": ["placement", "activation", "placement", "activation"],
            "list_days": [10, 10, 60, 60],
            "covid_list": [0, 0, 0, 0],
            "source_path": [Path("capture.json").as_posix()] * 4,
        }
    )
    result = build_historical_injury_features(events, origin_years=[2024])
    assert result.height == 1
    row = result.row(0, named=True)
    assert row["injury__placements_365"] == 1
    assert row["injury__placements_730"] == 2
    assert row["injury__long_placements_730"] == 1
    assert row["injury__on_list_at_cutoff"] == 1
    assert row["injury__current_spell_days"] == 15
    assert row["injury__days_365"] == 15
    assert row["injury__days_730"] == 26
