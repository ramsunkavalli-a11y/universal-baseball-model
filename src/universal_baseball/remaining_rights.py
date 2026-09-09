"""Convert live production and obligations to remaining transferable rights."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import polars as pl

from universal_baseball.contract_economics import ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA


REMAINING_RIGHTS_INPUT_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "season": pl.Int64,
    "forecast_scope": pl.String,
    "realized_war_to_date": pl.Float64,
    "projected_remaining_war_mean": pl.Float64,
    "projected_remaining_war_lower": pl.Float64,
    "projected_remaining_war_upper": pl.Float64,
    "control_status": pl.String,
    "salary_obligation_dollars": pl.Int64,
    "buyout_dollars": pl.Int64,
    "arbitration_class": pl.Int64,
    "projection_source_id": pl.String,
    "contract_source_id": pl.String,
}

REMAINING_RIGHTS_TIMELINE_SCHEMA: dict[str, pl.DataType] = {
    **REMAINING_RIGHTS_INPUT_SCHEMA,
    "war_excluded_as_already_realized": pl.Float64,
    "war_entering_rights_value": pl.Float64,
    "economics_control_status": pl.String,
    "timeline_status": pl.String,
}


@dataclass(frozen=True, slots=True)
class RemainingRightsResult:
    timeline: pl.DataFrame
    economics_inputs: pl.DataFrame


def build_remaining_rights_inputs(frame: pl.DataFrame) -> RemainingRightsResult:
    """Exclude realized WAR/cost and prepare only acquirable future value.

    Current-season salary must already be the unpaid/transferred obligation as of
    the snapshot. Future salary is the full future-season obligation. This module
    deliberately does not estimate a remaining fraction from calendar days.
    """

    missing = sorted(set(REMAINING_RIGHTS_INPUT_SCHEMA) - set(frame.columns))
    if missing:
        raise ValueError(f"remaining rights input missing fields: {missing}")
    source = frame.select(list(REMAINING_RIGHTS_INPUT_SCHEMA)).cast(
        REMAINING_RIGHTS_INPUT_SCHEMA, strict=True
    )
    if source.is_empty():
        return RemainingRightsResult(
            timeline=pl.DataFrame(schema=REMAINING_RIGHTS_TIMELINE_SCHEMA),
            economics_inputs=pl.DataFrame(schema=ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA),
        )
    if source.get_column("as_of_date").n_unique() != 1:
        raise ValueError("remaining rights input requires one as-of date")
    if source.group_by(["player_id", "organization_id", "season"]).len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("remaining rights input violates player-organization-season grain")
    as_of_year = source.item(0, "as_of_date").year
    required = [
        "as_of_date",
        "player_id",
        "organization_id",
        "season",
        "forecast_scope",
        "realized_war_to_date",
        "projected_remaining_war_mean",
        "control_status",
        "projection_source_id",
        "contract_source_id",
    ]
    if sum(source.select(required).null_count().row(0)):
        raise ValueError("remaining rights input has null required values")

    timeline_rows = []
    economics_rows = []
    no_rights = {"free_agent", "free_agent_eligible"}
    for row in source.iter_rows(named=True):
        season = int(row["season"])
        scope = str(row["forecast_scope"])
        realized = float(row["realized_war_to_date"])
        mean = float(row["projected_remaining_war_mean"])
        lower = row["projected_remaining_war_lower"]
        upper = row["projected_remaining_war_upper"]
        salary = row["salary_obligation_dollars"]
        if (
            int(row["player_id"]) <= 0
            or int(row["organization_id"]) <= 0
            or season < as_of_year
            or any(not isfinite(value) for value in (realized, mean))
            or (lower is not None and not isfinite(float(lower)))
            or (upper is not None and not isfinite(float(upper)))
            or (salary is not None and int(salary) < 0)
        ):
            raise ValueError("remaining rights input has invalid identities, WAR, or salary")
        if (lower is not None and float(lower) > mean) or (
            upper is not None and float(upper) < mean
        ):
            raise ValueError("remaining WAR bounds must contain the mean")
        if season == as_of_year:
            if scope != "remaining_current_season":
                raise ValueError("current season must use remaining_current_season scope")
            if row["control_status"] not in no_rights and salary is None:
                raise ValueError("current controlled season requires remaining salary obligation")
            economics_status = (
                str(row["control_status"])
                if row["control_status"] in no_rights
                else "current_season_committed"
            )
        else:
            if scope != "full_future_season":
                raise ValueError("future season must use full_future_season scope")
            if abs(realized) > 1e-12:
                raise ValueError("future seasons cannot contain realized WAR")
            economics_status = str(row["control_status"])
        timeline_rows.append(
            {
                **row,
                "war_excluded_as_already_realized": realized,
                "war_entering_rights_value": mean,
                "economics_control_status": economics_status,
                "timeline_status": "remaining_only",
            }
        )
        economics_rows.append(
            {
                "as_of_date": row["as_of_date"],
                "player_id": row["player_id"],
                "organization_id": row["organization_id"],
                "season": season,
                "projected_war_mean": mean,
                "projected_war_lower": lower,
                "projected_war_upper": upper,
                "control_status": economics_status,
                "known_salary_dollars": salary,
                "buyout_dollars": row["buyout_dollars"],
                "arbitration_class": row["arbitration_class"],
                "projection_source_id": row["projection_source_id"],
                "contract_source_id": row["contract_source_id"],
            }
        )
    return RemainingRightsResult(
        timeline=pl.DataFrame(timeline_rows, schema=REMAINING_RIGHTS_TIMELINE_SCHEMA).sort(
            ["player_id", "organization_id", "season"]
        ),
        economics_inputs=pl.DataFrame(
            economics_rows, schema=ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA
        ).sort(["player_id", "organization_id", "season"]),
    )
