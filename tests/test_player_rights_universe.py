from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.player_rights_universe import (
    PLAYER_RIGHTS_UNIVERSE_SCHEMA,
    REQUIRED_PLAYER_SCHEMA,
    RIGHTS_EVIDENCE_SCHEMA,
    build_player_rights_universe,
    project_40man_membership_to_rights_evidence,
    validate_player_rights_universe,
)
from universal_baseball.playing_time_roster_source import FORTY_MAN_MEMBERSHIP_SCHEMA


CUTOFF = date(2025, 3, 20)


def _required(*player_ids: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": list(player_ids),
            "player_name": [f"Player {player_id}" for player_id in player_ids],
        },
        schema=REQUIRED_PLAYER_SCHEMA,
    )


def _evidence(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=RIGHTS_EVIDENCE_SCHEMA)


def _controlled(player_id: int, *, snapshot: str = "snapshot-a") -> dict[str, object]:
    return {
        "as_of_date": CUTOFF,
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "rights_state": "organization_controlled",
        "organization_id": 137,
        "roster_scope": "reserve_list",
        "source_snapshot_id": snapshot,
        "observed_at_date": CUTOFF,
    }


def _membership(*rows: tuple[int, int]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": CUTOFF,
                "season": 2025,
                "team_id": team_id,
                "player_id": player_id,
                "on_40man": True,
                "source_row_count": 1,
                "source_status_codes": "A",
                "source_status_conflict": False,
                "source_parent_team_ids": str(team_id),
                "source_parent_team_id_mismatch": False,
            }
            for player_id, team_id in rows
        ],
        schema=FORTY_MAN_MEMBERSHIP_SCHEMA,
    )


def test_builder_keeps_missing_players_as_explicit_prior_only_unknowns() -> None:
    result = build_player_rights_universe(
        _required(1, 2),
        _evidence([_controlled(1)]),
        as_of_date=CUTOFF,
    )
    assert result.schema == PLAYER_RIGHTS_UNIVERSE_SCHEMA
    assert result.get_column("player_id").to_list() == [1, 2]
    missing = result.filter(pl.col("player_id") == 2).row(0, named=True)
    assert missing["rights_state"] == "unknown"
    assert missing["roster_scope"] == "unknown"
    assert missing["evidence_tier"] == "prior_only"
    assert missing["coverage_reason"] == "missing_rights_evidence"
    assert missing["organization_id"] is None


def test_corroborated_sources_are_retained_and_scope_priority_is_deterministic() -> None:
    reserve = _controlled(1, snapshot="snapshot-b")
    forty = {**_controlled(1, snapshot="snapshot-a"), "roster_scope": "mlb_40man"}
    result = build_player_rights_universe(
        _required(1),
        _evidence([reserve, forty]),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert result["roster_scope"] == "mlb_40man"
    assert result["evidence_tier"] == "corroborated"
    assert result["source_snapshot_ids"] == "snapshot-a,snapshot-b"


def test_free_agent_is_explicit_and_has_no_owner() -> None:
    row = {
        **_controlled(1),
        "rights_state": "free_agent",
        "organization_id": None,
        "roster_scope": "free_agent",
    }
    result = build_player_rights_universe(
        _required(1),
        _evidence([row]),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert result["rights_state"] == "free_agent"
    assert result["organization_id"] is None


def test_conflicting_organizations_fail_closed() -> None:
    other = {**_controlled(1, snapshot="snapshot-b"), "organization_id": 147}
    with pytest.raises(ValueError, match="conflicting state or organization"):
        build_player_rights_universe(
            _required(1),
            _evidence([_controlled(1), other]),
            as_of_date=CUTOFF,
        )


def test_conflicting_rights_states_fail_closed() -> None:
    free_agent = {
        **_controlled(1, snapshot="snapshot-b"),
        "rights_state": "free_agent",
        "organization_id": None,
        "roster_scope": "free_agent",
    }
    with pytest.raises(ValueError, match="conflicting state or organization"):
        build_player_rights_universe(
            _required(1),
            _evidence([_controlled(1), free_agent]),
            as_of_date=CUTOFF,
        )


def test_evidence_cannot_add_players_outside_frozen_denominator() -> None:
    with pytest.raises(ValueError, match="outside required denominator"):
        build_player_rights_universe(
            _required(1),
            _evidence([_controlled(2)]),
            as_of_date=CUTOFF,
        )


def test_future_observation_is_rejected() -> None:
    future = {**_controlled(1), "observed_at_date": date(2025, 3, 21)}
    with pytest.raises(ValueError, match="future observations"):
        build_player_rights_universe(
            _required(1),
            _evidence([future]),
            as_of_date=CUTOFF,
        )


def test_only_controlled_players_may_have_organization() -> None:
    invalid = {
        **_controlled(1),
        "rights_state": "unknown",
        "roster_scope": "unknown",
    }
    with pytest.raises(ValueError, match="only organization-controlled"):
        build_player_rights_universe(
            _required(1),
            _evidence([invalid]),
            as_of_date=CUTOFF,
        )


def test_empty_evidence_still_returns_complete_denominator() -> None:
    result = build_player_rights_universe(
        _required(1, 2),
        pl.DataFrame(schema=RIGHTS_EVIDENCE_SCHEMA),
        as_of_date=CUTOFF,
    )
    assert result.height == 2
    assert result.get_column("evidence_tier").to_list() == ["prior_only", "prior_only"]


def test_materialized_universe_rejects_duplicate_player_date() -> None:
    valid = build_player_rights_universe(
        _required(1),
        _evidence([_controlled(1)]),
        as_of_date=CUTOFF,
    )
    with pytest.raises(ValueError, match=r"violates as_of_date \+ player_id grain"):
        validate_player_rights_universe(pl.concat([valid, valid]))


def test_40man_adapter_projects_only_certified_membership_semantics() -> None:
    evidence = project_40man_membership_to_rights_evidence(
        _membership((1, 137)),
        expected_as_of_date=CUTOFF,
    ).row(0, named=True)
    assert evidence["rights_state"] == "organization_controlled"
    assert evidence["organization_id"] == 137
    assert evidence["roster_scope"] == "mlb_40man"
    assert evidence["player_name"] is None
    assert evidence["source_snapshot_id"].endswith("2025-03-20:team:137")


def test_40man_adapter_rejects_cross_organization_conflict() -> None:
    with pytest.raises(ValueError, match="cross-organization"):
        project_40man_membership_to_rights_evidence(
            _membership((1, 137), (1, 147)),
            expected_as_of_date=CUTOFF,
        )


def test_40man_adapter_rejects_negative_membership_rows() -> None:
    membership = _membership((1, 137)).with_columns(pl.lit(False).alias("on_40man"))
    with pytest.raises(ValueError, match="only certified positive"):
        project_40man_membership_to_rights_evidence(
            membership,
            expected_as_of_date=CUTOFF,
        )
