"""Fail-closed current organization resolution from official MLB evidence."""

from __future__ import annotations

from datetime import date

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


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(schema))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    return frame.select(list(schema)).cast(schema, strict=True)


def _transaction_owner(row: dict[str, object], mlb_team_ids: set[int]) -> int | None:
    code = str(row["type_code"])
    from_team = row["from_team_id"]
    to_team = row["to_team_id"]
    if code in _ACQUISITION_CODES and to_team in mlb_team_ids:
        return int(to_team)
    if code in {"CU", "RE", "SE"} and to_team in mlb_team_ids:
        return int(to_team)
    if code in {"OPT", "OUT"} and from_team in mlb_team_ids:
        return int(from_team)
    return None


def resolve_current_organizations(
    candidates: pl.DataFrame,
    forty_man: pl.DataFrame,
    transactions: pl.DataFrame,
    *,
    as_of_date: date,
    mlb_team_ids: set[int],
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
    if roster.filter(pl.col("as_of_date") != pl.lit(as_of_date)).height:
        raise ValueError("full-roster candidates contain an unexpected as_of_date")
    if forty.filter(pl.col("as_of_date") != pl.lit(as_of_date)).height:
        raise ValueError("40-man membership contains an unexpected as_of_date")
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
        }

    forty_teams: dict[int, set[int]] = {}
    for row in forty.filter(pl.col("on_40man")).iter_rows(named=True):
        forty_teams.setdefault(int(row["player_id"]), set()).add(int(row["team_id"]))

    tx_owners: dict[int, tuple[date, int, int]] = {}
    tx_conflicts: set[int] = set()
    accepted_by_key: dict[tuple[int, date], list[tuple[int, int]]] = {}
    for row in tx.iter_rows(named=True):
        owner = _transaction_owner(row, mlb_team_ids)
        if owner is None:
            continue
        player_id = int(row["player_id"])
        event_date = row["effective_date"]
        accepted_by_key.setdefault((player_id, event_date), []).append(
            (int(row["transaction_id"]), owner)
        )
    latest_dates: dict[int, date] = {}
    for player_id, event_date in accepted_by_key:
        latest_dates[player_id] = max(event_date, latest_dates.get(player_id, event_date))
    for player_id, event_date in latest_dates.items():
        events = accepted_by_key[(player_id, event_date)]
        owners = {owner for _, owner in events}
        if len(owners) > 1:
            tx_conflicts.add(player_id)
            continue
        transaction_id, owner = max(events)
        tx_owners[player_id] = (event_date, transaction_id, owner)

    rows: list[dict[str, object]] = []
    for player_id, candidate in sorted(candidate_groups.items()):
        teams = candidate["teams"]
        direct = forty_teams.get(player_id, set())
        organization_id: int | None = None
        status: str
        evidence: str
        if len(direct) == 1:
            organization_id = next(iter(direct))
            status = "resolved_official_40man"
            evidence = f"official_mlb_stats_api_40Man:{as_of_date}:team:{organization_id}"
        elif len(direct) > 1:
            status = "review_multiple_40man_organizations"
            evidence = "official_40man_conflict:" + ",".join(map(str, sorted(direct)))
        elif len(teams) > 1 and player_id in tx_conflicts:
            status = "review_conflicting_same_day_ownership_transactions"
            evidence = "official_transaction_conflict"
        elif len(teams) > 1 and player_id in tx_owners:
            event_date, transaction_id, organization_id = tx_owners[player_id]
            status = "resolved_official_transaction"
            evidence = f"official_mlb_stats_api_transaction:{transaction_id}:{event_date}"
        elif len(teams) == 1:
            organization_id = int(teams[0])
            status = "provisional_unique_full_roster"
            evidence = f"official_mlb_stats_api_fullRoster:{as_of_date}:team:{organization_id}"
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
