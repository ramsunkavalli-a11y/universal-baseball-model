"""Current official roster-status availability boundaries."""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl


SEASON_OUT_CODES = frozenset({"ILF", "RET", "MIL", "IN"})
INJURY_RETURN_UNRESOLVED_CODES = frozenset({"D7", "D10", "D15", "D60", "RA"})


CURRENT_AVAILABILITY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "status_codes": pl.String,
    "status_descriptions": pl.String,
    "source_row_count": pl.Int64,
    "availability_category": pl.String,
    "availability_point_policy": pl.String,
}


def project_current_affiliated_status_payload(
    payload: dict[str, Any],
    *,
    organization_id: int,
    as_of_date: date,
) -> pl.DataFrame:
    """Collapse one full-roster payload without treating it as rights proof."""

    roster = payload.get("roster")
    if not isinstance(roster, list):
        raise ValueError("current availability payload missing roster list")
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in roster:
        if not isinstance(row, dict):
            raise ValueError("current availability roster row must be an object")
        player_id = (row.get("person") or {}).get("id")
        if player_id is None:
            raise ValueError("current availability row missing player ID")
        grouped.setdefault(int(player_id), []).append(row)
    rows: list[dict[str, object]] = []
    for player_id, player_rows in sorted(grouped.items()):
        codes = sorted(
            {str((row.get("status") or {}).get("code") or "") for row in player_rows}
        )
        descriptions = sorted(
            {
                str((row.get("status") or {}).get("description") or "")
                for row in player_rows
            }
        )
        code_set = set(codes)
        if len(code_set) != 1 or "" in code_set:
            category = "unresolved_status_conflict"
            policy = "point_unchanged_no_availability_bound"
        elif code_set <= SEASON_OUT_CODES:
            category = "official_season_out"
            policy = "zero_remaining_point_and_bounds"
        elif code_set <= INJURY_RETURN_UNRESOLVED_CODES:
            category = "injured_return_date_unresolved"
            policy = "point_unchanged_zero_to_baseline_bound"
        elif code_set == {"A"}:
            category = "official_active"
            policy = "point_unchanged_no_availability_bound"
        else:
            category = "other_roster_status"
            policy = "point_unchanged_no_availability_bound"
        rows.append(
            {
                "as_of_date": as_of_date,
                "player_id": player_id,
                "organization_id": int(organization_id),
                "status_codes": ",".join(codes),
                "status_descriptions": ",".join(descriptions),
                "source_row_count": len(player_rows),
                "availability_category": category,
                "availability_point_policy": policy,
            }
        )
    return pl.DataFrame(rows, schema=CURRENT_AVAILABILITY_SCHEMA).sort("player_id")


def apply_current_availability_sensitivity(
    whole_player_war: pl.DataFrame,
    statuses: pl.DataFrame,
) -> pl.DataFrame:
    """Apply only official season-out facts; bound unresolved injury returns."""

    required = {
        "player_id",
        "organization_id",
        "projected_remaining_war_mean",
    }
    if missing := sorted(required - set(whole_player_war.columns)):
        raise ValueError(f"whole-player availability input missing fields: {missing}")
    if statuses.group_by("player_id", "organization_id").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("current availability violates player-organization grain")
    joined = whole_player_war.join(
        statuses.select(
            "player_id",
            "organization_id",
            "status_codes",
            "status_descriptions",
            "availability_category",
            "availability_point_policy",
        ),
        on=["player_id", "organization_id"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.col("projected_remaining_war_mean").alias(
            "unadjusted_projected_remaining_war"
        ),
        pl.col("availability_category").fill_null("status_unavailable"),
        pl.col("availability_point_policy").fill_null(
            "point_unchanged_no_availability_bound"
        ),
    )
    season_out = pl.col("availability_category") == "official_season_out"
    uncertain = (
        pl.col("availability_category") == "injured_return_date_unresolved"
    )
    baseline = pl.col("unadjusted_projected_remaining_war")
    return joined.with_columns(
        pl.when(season_out)
        .then(0.0)
        .otherwise(baseline)
        .alias("projected_remaining_war_mean"),
        pl.when(season_out)
        .then(0.0)
        .when(uncertain)
        .then(pl.min_horizontal(baseline, pl.lit(0.0)))
        .otherwise(baseline)
        .alias("projected_remaining_war_lower"),
        pl.when(season_out)
        .then(0.0)
        .when(uncertain)
        .then(pl.max_horizontal(baseline, pl.lit(0.0)))
        .otherwise(baseline)
        .alias("projected_remaining_war_upper"),
        pl.lit("official_status_availability_sensitivity_v1").alias(
            "availability_model_id"
        ),
    )
