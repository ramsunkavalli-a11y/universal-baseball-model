from datetime import date

import polars as pl
import pytest

from universal_baseball.organization_rights import resolve_current_organizations
from universal_baseball.playing_time_roster_source import (
    FORTY_MAN_MEMBERSHIP_SCHEMA,
    FULL_ROSTER_CANDIDATE_SCHEMA,
)
from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA


AS_OF = date(2026, 9, 8)
MLB_TEAMS = {100, 200, 300}


def _candidates(*rows: tuple[int, int]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": AS_OF,
                "season": 2026,
                "candidate_organization_id": team,
                "player_id": player,
                "player_name": f"Player {player}",
                "source_row_count": 1,
                "source_status_codes": "",
                "source_status_conflict": False,
            }
            for player, team in rows
        ],
        schema=FULL_ROSTER_CANDIDATE_SCHEMA,
    )


def _forty(*rows: tuple[int, int]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": AS_OF,
                "season": 2026,
                "team_id": team,
                "player_id": player,
                "on_40man": True,
                "source_row_count": 1,
                "source_status_codes": "A",
                "source_status_conflict": False,
                "source_parent_team_ids": str(team),
                "source_parent_team_id_mismatch": False,
            }
            for player, team in rows
        ],
        schema=FORTY_MAN_MEMBERSHIP_SCHEMA,
    )


def _transactions(
    *rows: tuple[int, int, str, str, int | None, int | None]
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": AS_OF,
                "transaction_id": transaction_id,
                "player_id": player,
                "player_name": f"Player {player}",
                "transaction_date": date.fromisoformat(event_date),
                "effective_date": date.fromisoformat(event_date),
                "resolution_date": None,
                "type_code": code,
                "type_description": "",
                "from_team_id": from_team,
                "to_team_id": to_team,
                "description": "",
                "source_snapshot_id": "statsapi:people-control:test",
            }
            for transaction_id, player, event_date, code, from_team, to_team in rows
        ],
        schema=RIGHTS_TRANSACTION_SCHEMA,
    )


def test_unique_40man_membership_resolves_multi_team_candidate() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100), (1, 200)),
        _forty((1, 200)),
        _transactions(),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] == 200
    assert result["organization_status"] == "resolved_official_40man"


def test_latest_conclusive_transaction_resolves_non_40man_candidate() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100), (1, 200)),
        _forty(),
        _transactions(
            (10, 1, "2026-05-01", "SFA", None, 100),
            (11, 1, "2026-08-01", "TR", 100, 200),
            (12, 1, "2026-08-02", "ASG", None, 999),
        ),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] == 200
    assert result["organization_status"] == "resolved_official_transaction"


def test_internal_option_and_outright_keep_mlb_owner() -> None:
    for code in ("OPT", "OUT"):
        result = resolve_current_organizations(
            _candidates((1, 100), (1, 200)),
            _forty(),
            _transactions((10, 1, "2026-08-01", code, 200, 999)),
            as_of_date=AS_OF,
            mlb_team_ids=MLB_TEAMS,
        ).row(0, named=True)
        assert result["organization_id"] == 200


def test_same_day_direct_transaction_conflict_fails_closed() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100), (1, 200)),
        _forty(),
        _transactions(
            (10, 1, "2026-08-01", "TR", 100, 200),
            (11, 1, "2026-08-01", "SFA", None, 300),
        ),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] is None
    assert result["organization_status"] == "review_conflicting_same_day_ownership_transactions"


def test_later_clear_transaction_supersedes_old_same_day_conflict() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100), (1, 200), (1, 300)),
        _forty(),
        _transactions(
            (10, 1, "2026-05-01", "TR", 100, 200),
            (11, 1, "2026-05-01", "SFA", None, 300),
            (12, 1, "2026-08-01", "TR", 200, 100),
        ),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] == 100
    assert result["organization_status"] == "resolved_official_transaction"


def test_two_40man_teams_fail_closed() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100), (1, 200)),
        _forty((1, 100), (1, 200)),
        _transactions((10, 1, "2026-08-01", "TR", 100, 200)),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] is None
    assert result["organization_status"] == "review_multiple_40man_organizations"


def test_unique_full_roster_candidate_remains_provisional() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100)),
        _forty(),
        _transactions(),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] == 100
    assert result["organization_status"] == "provisional_unique_full_roster"


def test_exact_mlb_release_overrides_stale_unique_full_roster_candidate() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100)),
        _forty(),
        _transactions((10, 1, "2026-08-01", "REL", None, 100)),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] is None
    assert result["organization_status"] == "resolved_official_release_no_rights"


def test_later_signing_supersedes_prior_release() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100)),
        _forty(),
        _transactions(
            (10, 1, "2026-07-01", "REL", None, 100),
            (11, 1, "2026-08-01", "SFA", None, 200),
        ),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)
    assert result["organization_id"] == 200
    assert result["organization_status"] == "resolved_official_transaction"


def test_exact_affiliate_release_uses_official_parent_mapping() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100)),
        _forty(),
        _transactions((10, 1, "2026-08-01", "REL", None, 999)),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
        affiliate_parent_organization_ids={999: 100},
    ).row(0, named=True)
    assert result["organization_id"] is None
    assert result["organization_status"] == "resolved_official_release_no_rights"


def test_old_affiliate_release_does_not_use_current_parent_mapping() -> None:
    result = resolve_current_organizations(
        _candidates((1, 100)),
        _forty(),
        _transactions((10, 1, "2025-08-01", "REL", None, 999)),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
        affiliate_parent_organization_ids={999: 100},
    ).row(0, named=True)
    assert result["organization_id"] == 100
    assert result["organization_status"] == "provisional_unique_full_roster"


def test_future_transaction_is_rejected() -> None:
    with pytest.raises(ValueError, match="cross the as-of cutoff"):
        resolve_current_organizations(
            _candidates((1, 100), (1, 200)),
            _forty(),
            _transactions((10, 1, "2026-09-09", "TR", 100, 200)),
            as_of_date=AS_OF,
            mlb_team_ids=MLB_TEAMS,
        )


def test_prior_roster_snapshot_is_allowed_and_keeps_its_evidence_date() -> None:
    candidates = _candidates((1, 100)).with_columns(
        pl.lit(date(2025, 10, 15)).alias("as_of_date"),
        pl.lit(2025).alias("season"),
    )
    result = resolve_current_organizations(
        candidates,
        _forty(),
        _transactions(),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)

    assert result["organization_id"] == 100
    assert "2025-10-15" in result["organization_evidence"]


def test_transaction_after_prior_40man_snapshot_takes_precedence() -> None:
    candidates = _candidates((1, 100)).with_columns(
        pl.lit(date(2025, 10, 15)).alias("as_of_date"),
        pl.lit(2025).alias("season"),
    )
    forty = _forty((1, 100)).with_columns(
        pl.lit(date(2025, 10, 15)).alias("as_of_date"),
        pl.lit(2025).alias("season"),
    )
    result = resolve_current_organizations(
        candidates,
        forty,
        _transactions((10, 1, "2026-01-10", "TR", 100, 200)),
        as_of_date=AS_OF,
        mlb_team_ids=MLB_TEAMS,
    ).row(0, named=True)

    assert result["organization_id"] == 200
    assert result["organization_status"] == "resolved_official_transaction"
