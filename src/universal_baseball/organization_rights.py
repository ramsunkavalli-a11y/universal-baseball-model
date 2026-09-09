"""Fail-closed current organization resolution from official MLB evidence."""

from __future__ import annotations

from datetime import date
from typing import Mapping

import polars as pl

from universal_baseball.playing_time_roster_source import (
    FORTY_MAN_MEMBERSHIP_SCHEMA,
    FULL_ROSTER_CANDIDATE_SCHEMA,
)
from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA


ORGANIZATION_RESOLUTION_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "player_name": pl.String,
    "organization_count": pl.Int64,
    "organization_id": pl.Int64,
    "organization_status": pl.String,
    "organization_evidence": pl.String,
}

# These events establish an MLB organization's rights. Internal assignments and
# roster-status changes intentionally do not change the owner.
_ACQUISITION_CODES = frozenset({"CLW", "IFA", "SFA", "SGN", "TR"})
_MLB_ROSTER_CODES = frozenset({"CU", "OPT", "OUT", "RE", "SE"})
_NO_RIGHTS_CODES = frozenset({"REL"})


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(schema))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    return frame.select(list(schema)).cast(schema, strict=True)


def _transaction_resolution(
    row: dict[str, object],
    mlb_team_ids: set[int],
    affiliate_parent_organization_ids: Mapping[int, int],
    *,
    as_of_date: date,
) -> tuple[str, int | None] | None:
    code = str(row["type_code"])
    from_team = row["from_team_id"]
    to_team = row["to_team_id"]
    direct_from_owner = int(from_team) if from_team in mlb_team_ids else None
    direct_to_owner = int(to_team) if to_team in mlb_team_ids else None
    if code in _ACQUISITION_CODES and direct_to_owner is not None:
        return "owner", direct_to_owner
    if code in {"CU", "RE", "SE"} and direct_to_owner is not None:
        return "owner", direct_to_owner
    if code in {"OPT", "OUT"} and direct_from_owner is not None:
        return "owner", direct_from_owner
    current_season_affiliate_release = (
        code in _NO_RIGHTS_CODES
        and row["effective_date"].year == as_of_date.year
        and (
            (
                from_team is not None
                and affiliate_parent_organization_ids.get(int(from_team)) in mlb_team_ids
            )
            or (
                to_team is not None
                and affiliate_parent_organization_ids.get(int(to_team)) in mlb_team_ids
            )
        )
    )
    if code in _NO_RIGHTS_CODES and (
        direct_from_owner is not None
        or direct_to_owner is not None
        or current_season_affiliate_release
    ):
        return "no_incumbent_rights", None
    return None


def resolve_current_organizations(
    candidates: pl.DataFrame,
    forty_man: pl.DataFrame,
    transactions: pl.DataFrame,
    *,
    as_of_date: date,
    mlb_team_ids: set[int],
    affiliate_parent_organization_ids: Mapping[int, int] | None = None,
) -> pl.DataFrame:
    """Resolve current owners while preserving broad-roster uncertainty.

    Evidence order is: unique dated 40-man membership, latest conclusive official
    ownership transaction for multi-organization candidates, then a unique broad
    full-roster candidate as a provisional fallback. Conflicting direct evidence
    remains unresolved.
    """

    roster = _conform(candidates, FULL_ROSTER_CANDIDATE_SCHEMA, "full_roster_candidates")
    forty = _conform(forty_man, FORTY_MAN_MEMBERSHIP_SCHEMA, "forty_man")
    tx = _conform(transactions, RIGHTS_TRANSACTION_SCHEMA, "transactions")
    if not mlb_team_ids or any(team_id <= 0 for team_id in mlb_team_ids):
        raise ValueError("mlb_team_ids must contain positive identities")
    affiliate_parents = dict(affiliate_parent_organization_ids or {})
    if any(
        team_id <= 0 or parent_id not in mlb_team_ids
        for team_id, parent_id in affiliate_parents.items()
    ):
        raise ValueError("affiliate parent map must contain positive teams and MLB parents")
    if roster.filter(pl.col("as_of_date") > pl.lit(as_of_date)).height:
        raise ValueError("full-roster candidates cross the as-of cutoff")
    if forty.filter(pl.col("as_of_date") > pl.lit(as_of_date)).height:
        raise ValueError("40-man membership crosses the as-of cutoff")
    if tx.filter(pl.col("effective_date") > pl.lit(as_of_date)).height:
        raise ValueError("transactions cross the as-of cutoff")

    candidate_groups: dict[int, dict[str, object]] = {}
    for group in roster.partition_by("player_id", maintain_order=True):
        player_id = int(group.item(0, "player_id"))
        names = [str(value) for value in group.get_column("player_name") if str(value)]
        teams = sorted(set(group.get_column("candidate_organization_id").to_list()))
        candidate_groups[player_id] = {
            "player_name": names[0] if names else "",
            "teams": teams,
            "evidence_date": max(group.get_column("as_of_date")),
        }

    forty_teams: dict[int, set[int]] = {}
    forty_dates: dict[int, date] = {}
    for row in forty.filter(pl.col("on_40man")).iter_rows(named=True):
        player_id = int(row["player_id"])
        forty_teams.setdefault(player_id, set()).add(int(row["team_id"]))
        forty_dates[player_id] = max(
            row["as_of_date"], forty_dates.get(player_id, row["as_of_date"])
        )

    tx_resolutions: dict[int, tuple[date, int, str, int | None]] = {}
    tx_conflicts: set[int] = set()
    accepted_by_key: dict[
        tuple[int, date], list[tuple[int, str, int | None]]
    ] = {}
    for row in tx.iter_rows(named=True):
        resolution = _transaction_resolution(
            row, mlb_team_ids, affiliate_parents, as_of_date=as_of_date
        )
        if resolution is None:
            continue
        state, owner = resolution
        player_id = int(row["player_id"])
        event_date = row["effective_date"]
        accepted_by_key.setdefault((player_id, event_date), []).append(
            (int(row["transaction_id"]), state, owner)
        )
    latest_dates: dict[int, date] = {}
    for player_id, event_date in accepted_by_key:
        latest_dates[player_id] = max(event_date, latest_dates.get(player_id, event_date))
    for player_id, event_date in latest_dates.items():
        events = accepted_by_key[(player_id, event_date)]
        outcomes = {(state, owner) for _, state, owner in events}
        if len(outcomes) > 1:
            tx_conflicts.add(player_id)
            continue
        transaction_id, state, owner = max(events)
        tx_resolutions[player_id] = (event_date, transaction_id, state, owner)

    rows: list[dict[str, object]] = []
    for player_id, candidate in sorted(candidate_groups.items()):
        teams = candidate["teams"]
        direct = forty_teams.get(player_id, set())
        forty_date = forty_dates.get(player_id)
        transaction = tx_resolutions.get(player_id)
        later_transaction = (
            transaction is not None
            and (forty_date is None or transaction[0] > forty_date)
        )
        later_transaction_conflict = (
            player_id in tx_conflicts
            and (
                forty_date is None
                or latest_dates[player_id] > forty_date
            )
        )
        organization_id: int | None = None
        status: str
        evidence: str
        if later_transaction_conflict:
            status = "review_conflicting_same_day_ownership_transactions"
            evidence = "official_transaction_conflict"
        elif later_transaction:
            assert transaction is not None
            event_date, transaction_id, state, organization_id = transaction
            status = (
                "resolved_official_transaction"
                if state == "owner"
                else "resolved_official_release_no_rights"
            )
            evidence = f"official_mlb_stats_api_transaction:{transaction_id}:{event_date}"
        elif len(direct) == 1:
            organization_id = next(iter(direct))
            status = "resolved_official_40man"
            evidence = (
                f"official_mlb_stats_api_40Man:{forty_dates[player_id]}:"
                f"team:{organization_id}"
            )
        elif len(direct) > 1:
            status = "review_multiple_40man_organizations"
            evidence = "official_40man_conflict:" + ",".join(map(str, sorted(direct)))
        elif player_id in tx_conflicts:
            status = "review_conflicting_same_day_ownership_transactions"
            evidence = "official_transaction_conflict"
        elif transaction is not None:
            event_date, transaction_id, state, organization_id = transaction
            status = (
                "resolved_official_transaction"
                if state == "owner"
                else "resolved_official_release_no_rights"
            )
            evidence = f"official_mlb_stats_api_transaction:{transaction_id}:{event_date}"
        elif len(teams) == 1:
            organization_id = int(teams[0])
            status = "provisional_unique_full_roster"
            evidence = (
                f"official_mlb_stats_api_fullRoster:{candidate['evidence_date']}:"
                f"team:{organization_id}"
            )
        else:
            status = "review_multiple_full_roster_organizations"
            evidence = "official_full_roster_conflict:" + ",".join(map(str, teams))
        rows.append(
            {
                "player_id": player_id,
                "player_name": candidate["player_name"],
                "organization_count": len(teams),
                "organization_id": organization_id,
                "organization_status": status,
                "organization_evidence": evidence,
            }
        )
    return pl.DataFrame(rows, schema=ORGANIZATION_RESOLUTION_SCHEMA).sort("player_id")
