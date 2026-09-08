"""External team-control snapshots used only where StatsAPI history is incomplete."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from universal_baseball.team_control import (
    CONTROL_STINT_SCHEMA,
    SEASON_WINDOW_SCHEMA,
    SERVICE_DAYS_PER_YEAR,
    calculate_control_years,
)


CONTROL_BASELINE_SCHEMA: dict[str, pl.DataType] = {
    "baseline_as_of_date": pl.Date,
    "player_id": pl.Int64,
    "fangraphs_id": pl.String,
    "player_name": pl.String,
    "service_days": pl.Int64,
    "options_remaining": pl.Int64,
    "rule5_status": pl.String,
    "rule5_year": pl.Int64,
    "identity_match_status": pl.String,
    "baseline_status": pl.String,
    "source_snapshot_id": pl.String,
}

ADVANCED_CONTROL_SCHEMA: dict[str, pl.DataType] = {
    "baseline_as_of_date": pl.Date,
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "baseline_service_days": pl.Int64,
    "added_service_days": pl.Int64,
    "service_days": pl.Int64,
    "service_time": pl.String,
    "baseline_options_remaining": pl.Int64,
    "new_option_years": pl.Int64,
    "options_remaining": pl.Int64,
    "forward_status": pl.String,
    "source_snapshot_id": pl.String,
}


def service_time_to_days(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    parts = text.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"invalid service time: {value}")
    years, remainder = map(int, parts)
    if remainder >= SERVICE_DAYS_PER_YEAR:
        raise ValueError(f"invalid service-day remainder: {value}")
    return years * SERVICE_DAYS_PER_YEAR + remainder


def build_control_baselines(
    references: pl.DataFrame,
    identity_matches: pl.DataFrame,
    *,
    baseline_as_of_date: date,
) -> pl.DataFrame:
    """Stage service/options snapshots with an explicit identity acceptance gate."""

    reference_fields = {
        "fangraphs_id",
        "player_name",
        "reference_service_time",
        "reference_options_remaining",
        "reference_rule5_status",
        "reference_rule5_year",
        "source_snapshot_id",
    }
    match_fields = {
        "fangraphs_id",
        "reference_player_name",
        "player_id",
        "match_status",
    }
    if reference_fields - set(references.columns):
        raise ValueError("control references missing baseline fields")
    if match_fields - set(identity_matches.columns):
        raise ValueError("identity matches missing baseline fields")
    joined = references.join(
        identity_matches.select(
            "fangraphs_id", "reference_player_name", "player_id", "match_status"
        ),
        left_on=["fangraphs_id", "player_name"],
        right_on=["fangraphs_id", "reference_player_name"],
        how="left",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        match_status = str(row["match_status"] or "unmatched")
        if match_status == "matched_stable_id":
            baseline_status = "accepted_stable_identity"
        elif match_status == "stable_id_outside_statsapi_candidates":
            baseline_status = "accepted_stable_identity_outside_expected_team"
        elif match_status == "matched_official_roster_confirmed_name":
            baseline_status = "accepted_official_roster_confirmed_identity"
        elif match_status == "matched_validation_only":
            baseline_status = "review_name_only_identity"
        else:
            baseline_status = "unresolved_identity"
        rows.append(
            {
                "baseline_as_of_date": baseline_as_of_date,
                "player_id": row["player_id"],
                "fangraphs_id": str(row["fangraphs_id"]),
                "player_name": str(row["player_name"]),
                "service_days": service_time_to_days(str(row["reference_service_time"])),
                "options_remaining": row["reference_options_remaining"],
                "rule5_status": str(row["reference_rule5_status"]),
                "rule5_year": row["reference_rule5_year"],
                "identity_match_status": match_status,
                "baseline_status": baseline_status,
                "source_snapshot_id": str(row["source_snapshot_id"]),
            }
        )
    result = pl.DataFrame(rows, schema=CONTROL_BASELINE_SCHEMA).sort(
        ["baseline_status", "player_name"]
    )
    accepted = result.filter(
        pl.col("baseline_status").is_in(
            [
                "accepted_stable_identity",
                "accepted_official_roster_confirmed_identity",
                "accepted_stable_identity_outside_expected_team",
            ]
        )
    )
    if (
        accepted.drop_nulls("player_id")
        .group_by("player_id")
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("accepted control baselines have duplicate player IDs")
    return result


def advance_control_baselines(
    baselines: pl.DataFrame,
    stints: pl.DataFrame,
    season_windows: pl.DataFrame,
    *,
    as_of_date: date,
) -> pl.DataFrame:
    """Add post-snapshot StatsAPI service and later option years to a baseline."""

    source = baselines.select(list(CONTROL_BASELINE_SCHEMA)).cast(
        CONTROL_BASELINE_SCHEMA, strict=True
    )
    intervals = stints.select(list(CONTROL_STINT_SCHEMA)).cast(
        CONTROL_STINT_SCHEMA, strict=True
    )
    windows = season_windows.select(list(SEASON_WINDOW_SCHEMA)).cast(
        SEASON_WINDOW_SCHEMA, strict=True
    )
    accepted = source.filter(
        pl.col("baseline_status").is_in(
            [
                "accepted_stable_identity",
                "accepted_official_roster_confirmed_identity",
                "accepted_stable_identity_outside_expected_team",
            ]
        )
    )
    if accepted.filter(
        pl.col("player_id").is_null() | pl.col("service_days").is_null()
    ).height:
        raise ValueError("accepted baseline lacks player identity or service days")
    clipped_rows: list[dict[str, object]] = []
    baseline_by_player = {
        int(row["player_id"]): row for row in accepted.iter_rows(named=True)
    }
    for row in intervals.iter_rows(named=True):
        player_id = int(row["player_id"])
        baseline = baseline_by_player.get(player_id)
        if baseline is None:
            continue
        baseline_date = baseline["baseline_as_of_date"]
        if baseline_date > as_of_date:
            raise ValueError("control baseline is after requested as-of date")
        start = max(row["start_date"], baseline_date + timedelta(days=1))
        end = min(row["end_date"], as_of_date)
        if start <= end:
            clipped_rows.append({**row, "start_date": start, "end_date": end})
    clipped = (
        pl.DataFrame(clipped_rows, schema=CONTROL_STINT_SCHEMA)
        if clipped_rows
        else pl.DataFrame(schema=CONTROL_STINT_SCHEMA)
    )
    additions = calculate_control_years(clipped, windows, as_of_date=as_of_date)
    additions_by_player: dict[int, list[dict[str, object]]] = {}
    for row in additions.iter_rows(named=True):
        additions_by_player.setdefault(int(row["player_id"]), []).append(row)

    rows: list[dict[str, object]] = []
    for baseline in accepted.iter_rows(named=True):
        player_id = int(baseline["player_id"])
        annual = additions_by_player.get(player_id, [])
        added_service = sum(int(row["service_days"]) for row in annual)
        new_option_years = sum(
            bool(row["option_year_used"])
            for row in annual
            if int(row["season"]) > baseline["baseline_as_of_date"].year
        )
        total_service = int(baseline["service_days"]) + added_service
        years, remainder = divmod(total_service, SERVICE_DAYS_PER_YEAR)
        baseline_options = baseline["options_remaining"]
        remaining_options = (
            max(int(baseline_options) - new_option_years, 0)
            if baseline_options is not None
            else None
        )
        rows.append(
            {
                "baseline_as_of_date": baseline["baseline_as_of_date"],
                "as_of_date": as_of_date,
                "player_id": player_id,
                "player_name": str(baseline["player_name"]),
                "baseline_service_days": int(baseline["service_days"]),
                "added_service_days": added_service,
                "service_days": total_service,
                "service_time": f"{years}.{remainder:03d}",
                "baseline_options_remaining": baseline_options,
                "new_option_years": new_option_years,
                "options_remaining": remaining_options,
                "forward_status": "calculated_forward" if annual else "baseline_only",
                "source_snapshot_id": str(baseline["source_snapshot_id"]),
            }
        )
    return (
        pl.DataFrame(rows, schema=ADVANCED_CONTROL_SCHEMA)
        if rows
        else pl.DataFrame(schema=ADVANCED_CONTROL_SCHEMA)
    ).sort("player_id")
