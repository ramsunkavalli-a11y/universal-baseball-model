from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.roster_entry_source import (
    ROSTER_ENTRY_SCHEMA,
    build_opening_control_states,
    project_roster_entries_payload,
)
from universal_baseball.team_control import SEASON_WINDOW_SCHEMA


AS_OF = date(2024, 10, 15)


def _entry(
    team_id: int,
    code: str,
    description: str,
    start: str,
    *,
    end: str | None = None,
    on_40man: bool = False,
    parent_org_id: int | None = 135,
) -> dict[str, object]:
    team: dict[str, object] = {"id": team_id}
    if parent_org_id is not None:
        team["parentOrgId"] = parent_org_id
    return {
        "team": team,
        "status": {"code": code, "description": description},
        "startDate": start,
        "endDate": end,
        "isActiveFortyMan": on_40man,
    }


def _payload(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"people": [{"id": 10, "fullName": "Player Ten", "rosterEntries": entries}]}


def _windows() -> pl.DataFrame:
    return pl.DataFrame(
        [{"season": 2024, "start_date": date(2024, 3, 20), "end_date": AS_OF}],
        schema=SEASON_WINDOW_SCHEMA,
    )


def test_roster_entry_projection_clips_future_knowledge() -> None:
    result = project_roster_entries_payload(
        _payload(
            [
                _entry(135, "A", "Active", "2023-03-01", end="2025-01-01", on_40man=True),
                _entry(135, "A", "Active", "2025-02-01", on_40man=True),
            ]
        ),
        as_of_date=AS_OF,
        source_snapshot_id="statsapi:test",
    )
    assert result.schema == ROSTER_ENTRY_SCHEMA
    assert result.height == 1
    assert result.item(0, "end_date") == AS_OF


def test_latest_minor_rehab_entry_overrides_broad_mlb_entry_at_opening() -> None:
    entries = project_roster_entries_payload(
        _payload(
            [
                _entry(135, "A", "Active", "2019-03-28", on_40man=True, parent_org_id=None),
                _entry(4904, "RA", "Rehab Assignment", "2024-03-10", end="2024-04-01", on_40man=True),
            ]
        ),
        as_of_date=AS_OF,
        source_snapshot_id="statsapi:test",
    )
    result = build_opening_control_states(entries, _windows(), mlb_team_ids={135})
    assert result.opening_states.item(0, "roster_state") == "mlb_injured"
    assert result.review_players.is_empty()


def test_minor_entry_maps_40man_to_optioned_and_non40man_to_pro_active() -> None:
    rows = []
    for player_id, on_40man in ((10, True), (11, False)):
        frame = project_roster_entries_payload(
            {"people": [{"id": player_id, "rosterEntries": [_entry(4904, "A", "Active", "2024-01-01", on_40man=on_40man)]}]},
            as_of_date=AS_OF,
            source_snapshot_id=f"statsapi:{player_id}",
        )
        rows.append(frame)
    result = build_opening_control_states(
        pl.concat(rows), _windows(), mlb_team_ids={135}
    ).opening_states
    assert result.get_column("roster_state").to_list() == ["minors_optioned", "pro_active"]


def test_unknown_covering_status_is_reviewed_not_guessed() -> None:
    entries = project_roster_entries_payload(
        _payload([_entry(135, "DES", "Designated for Assignment", "2024-03-01", on_40man=False)]),
        as_of_date=AS_OF,
        source_snapshot_id="statsapi:test",
    )
    result = build_opening_control_states(entries, _windows(), mlb_team_ids={135})
    assert result.opening_states.is_empty()
    assert result.review_players.item(0, "reason") == "no_specific_opening_state"
