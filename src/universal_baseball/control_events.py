"""Conservative StatsAPI transaction grammar for team-control intervals.

Only transaction meanings that are sufficiently specific change a player's
control state. Everything else is retained in an explicit review queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import re

import polars as pl

from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA
from universal_baseball.team_control import (
    CONTROL_STINT_SCHEMA,
    ROSTER_STATES,
    SEASON_WINDOW_SCHEMA,
)


CONTROL_EVENT_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "event_date": pl.Date,
    "transaction_id": pl.Int64,
    "action": pl.String,
    "target_state": pl.String,
    "rule_id": pl.String,
    "reason": pl.String,
    "source_snapshot_id": pl.String,
}

OPENING_CONTROL_STATE_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "roster_state": pl.String,
    "source_snapshot_id": pl.String,
}

CONTROL_EVENT_ACTIONS = frozenset({"set_state", "close_state", "preserve_state", "review"})


@dataclass(frozen=True)
class ControlMaterialization:
    stints: pl.DataFrame
    review_events: pl.DataFrame


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(schema))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    return frame.select(list(schema)).cast(schema, strict=True)


def _classify(
    type_code: str,
    description: str,
    *,
    from_team_id: int | None,
    to_team_id: int | None,
    mlb_team_ids: set[int] | None,
) -> tuple[str, str | None, str, str]:
    text = " ".join(description.lower().split())
    team_ids_supplied = mlb_team_ids is not None
    is_mlb_event = bool(
        mlb_team_ids
        and ({value for value in (from_team_id, to_team_id) if value is not None} & mlb_team_ids)
    )

    if "rehab assignment" in text:
        return (
            "preserve_state",
            None,
            "description.rehab_assignment.v1",
            "A rehabilitation assignment does not end the MLB injured-list state.",
        )
    if re.search(
        r"\b(?:activated|reinstated)\b.*\bfrom the (?:7|10|15|60)-day injured list",
        text,
    ):
        return (
            "set_state",
            "mlb_active" if is_mlb_event or not team_ids_supplied else "pro_active",
            "description.il_activated.v2",
            "Activated or reinstated from a specifically identified injured list.",
        )
    injured_match = re.search(
        r"\b(?:placed\b.*\bon|transferred\b.*\bto) the "
        r"(?:(?P<days>7|10|15|60)-day|full-season) injured list",
        text,
    )
    if injured_match:
        return (
            "set_state",
            "mlb_injured" if is_mlb_event or not team_ids_supplied else "pro_injured",
            "description.il_placement.v2",
            "Placed on or transferred to a specifically identified injured list.",
        )
    if any(
        list_name in text
        for list_name in (
            "temporarily inactive list",
            "development list",
            "administrative leave",
            "restricted list",
            "reserve list",
        )
    ) and not is_mlb_event:
        return (
            "set_state",
            "pro_inactive",
            "description.minor_inactive_list.v1",
            "Placed on a specifically identified non-active minor-league list.",
        )
    if any(list_name in text for list_name in ("paternity list", "bereavement list")):
        if re.search(r"\b(?:activated|reinstated)\b.*\bfrom\b", text) and is_mlb_event:
            return "set_state", "mlb_active", "description.mlb_paid_list_activated.v1", "Returned from an MLB paid service list."
        if "placed" in text and is_mlb_event:
            return "set_state", "mlb_service_list", "description.mlb_paid_list_placement.v1", "Placed on an MLB list that continues service accrual."
    if type_code == "SC" and "roster status changed" in text:
        return "preserve_state", None, "description.generic_status_preserve.v1", "Generic status text does not establish a new control state."
    if type_code == "SC" and "activated" in text:
        return (
            "set_state",
            "mlb_active" if is_mlb_event else "pro_active",
            "description.generic_activation.v1",
            "Activation changes the active state at the identified level.",
        )
    if type_code == "SC" and "reassigned" in text and "minor leagues" in text:
        return (
            "set_state",
            "pro_active",
            "description.reassigned_to_minors.v1",
            "Reassigned to the minor leagues without treating the event as an option.",
        )

    transitions = {
        "OPT": ("set_state", "minors_optioned", "type.OPT.v1", "Optioned to the minors."),
        "RE": ("set_state", "mlb_active", "type.RE.v1", "Recalled to the MLB roster."),
        "CU": ("set_state", "mlb_active", "type.CU.v1", "Called up to the MLB roster."),
        "SE": ("set_state", "mlb_active", "type.SE.v1", "Contract selected to the MLB roster."),
        "OUT": ("set_state", "pro_active", "type.OUT.v1", "Outrighted from the MLB roster."),
        "REL": ("close_state", None, "type.REL.v1", "Released from the organization."),
    }
    if type_code in transitions:
        return transitions[type_code]

    preserves = {
        "ACQ",
        "ARB",
        "AWD",
        "CP",
        "CV",
        "DR",
        "IFA",
        "NOA",
        "NTC",
        "NUM",
        "SFA",
        "SGN",
        "TR",
        "ASG",
    }
    if type_code in preserves:
        return (
            "preserve_state",
            None,
            f"type.{type_code}.preserve.v1",
            "The event alone does not establish a new service or option state.",
        )
    return (
        "review",
        None,
        "unmapped.v1",
        "The transaction is not specific enough for an automatic state change.",
    )


def classify_control_transactions(
    transactions: pl.DataFrame, *, mlb_team_ids: set[int] | None = None
) -> pl.DataFrame:
    """Translate raw transactions with a versioned, fail-closed grammar."""

    source = _conform(transactions, RIGHTS_TRANSACTION_SCHEMA, "rights_transactions")
    rows: list[dict[str, object]] = []
    for row in source.iter_rows(named=True):
        action, target, rule_id, reason = _classify(
            str(row["type_code"]),
            str(row["description"]),
            from_team_id=row["from_team_id"],
            to_team_id=row["to_team_id"],
            mlb_team_ids=mlb_team_ids,
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "season": row["effective_date"].year,
                "event_date": row["effective_date"],
                "transaction_id": int(row["transaction_id"]),
                "action": action,
                "target_state": target,
                "rule_id": rule_id,
                "reason": reason,
                "source_snapshot_id": str(row["source_snapshot_id"]),
            }
        )
    return (
        pl.DataFrame(rows, schema=CONTROL_EVENT_SCHEMA)
        if rows
        else pl.DataFrame(schema=CONTROL_EVENT_SCHEMA)
    ).sort(["player_id", "event_date", "transaction_id"])


def materialize_control_stints(
    opening_states: pl.DataFrame,
    events: pl.DataFrame,
    season_windows: pl.DataFrame,
    *,
    as_of_date: date,
) -> ControlMaterialization:
    """Replay accepted transactions from an official opening roster state."""

    openings = _conform(opening_states, OPENING_CONTROL_STATE_SCHEMA, "opening_states")
    changes = _conform(events, CONTROL_EVENT_SCHEMA, "control_events")
    windows = _conform(season_windows, SEASON_WINDOW_SCHEMA, "season_windows")
    if openings.group_by(["player_id", "season"]).len().filter(pl.col("len") > 1).height:
        raise ValueError("opening_states has duplicate player-season")
    if openings.filter(~pl.col("roster_state").is_in(sorted(ROSTER_STATES))).height:
        raise ValueError("opening_states has invalid roster_state")
    if changes.filter(
        (~pl.col("action").is_in(sorted(CONTROL_EVENT_ACTIONS)))
        | (
            (pl.col("action") == "set_state")
            & (~pl.col("target_state").is_in(sorted(ROSTER_STATES)))
        )
        | (pl.col("event_date") > pl.lit(as_of_date))
    ).height:
        raise ValueError("control_events has invalid action, state or date")
    window_map = {
        int(row["season"]): (row["start_date"], min(row["end_date"], as_of_date))
        for row in windows.iter_rows(named=True)
    }
    referenced_seasons = set(openings.get_column("season").to_list()) | set(
        changes.get_column("season").to_list()
    )
    if referenced_seasons - set(window_map):
        raise ValueError("control input contains a season without a season window")

    opening_map = {
        (int(row["player_id"]), int(row["season"])): row
        for row in openings.iter_rows(named=True)
    }
    event_map: dict[tuple[int, int], list[dict[str, object]]] = {}
    for row in changes.iter_rows(named=True):
        event_map.setdefault((int(row["player_id"]), int(row["season"])), []).append(row)

    stint_rows: list[dict[str, object]] = []
    keys = sorted(set(opening_map) | set(event_map))
    for player_id, season in keys:
        window_start, window_end = window_map[season]
        if window_start > window_end:
            continue
        opening = opening_map.get((player_id, season))
        state = str(opening["roster_state"]) if opening else None
        state_start = window_start if opening else None
        state_source = str(opening["source_snapshot_id"]) if opening else None
        for event in event_map.get((player_id, season), []):
            event_date = event["event_date"]
            if event_date < window_start or event_date > window_end:
                continue
            action = str(event["action"])
            if action in {"preserve_state", "review"}:
                continue
            if state is not None and state_start is not None and event_date > state_start:
                stint_rows.append(
                    {
                        "player_id": player_id,
                        "season": season,
                        "start_date": state_start,
                        "end_date": event_date - timedelta(days=1),
                        "roster_state": state,
                        "source_snapshot_id": state_source,
                    }
                )
            if action == "close_state":
                state = None
                state_start = None
                state_source = None
            else:
                state = str(event["target_state"])
                state_start = event_date
                state_source = str(event["source_snapshot_id"])
        if state is not None and state_start is not None and state_start <= window_end:
            stint_rows.append(
                {
                    "player_id": player_id,
                    "season": season,
                    "start_date": state_start,
                    "end_date": window_end,
                    "roster_state": state,
                    "source_snapshot_id": state_source,
                }
            )

    stints = (
        pl.DataFrame(stint_rows, schema=CONTROL_STINT_SCHEMA)
        if stint_rows
        else pl.DataFrame(schema=CONTROL_STINT_SCHEMA)
    ).sort(["player_id", "season", "start_date"])
    review = changes.filter(pl.col("action") == "review")
    return ControlMaterialization(stints=stints, review_events=review)
