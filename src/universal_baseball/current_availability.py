"""Current official roster-status availability boundaries."""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl

from universal_baseball.injury_return import (
    INJURY_RETURN_COHORT_SCHEMA,
    INJURY_RETURN_REFERENCE_SCHEMA,
    elapsed_days_band,
)


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
    *,
    injury_stints: pl.DataFrame | None = None,
    return_references: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Apply official status plus optional historically fitted IL return timing."""

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
    if (injury_stints is None) != (return_references is None):
        raise ValueError("injury stints and return references must be supplied together")
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
    historical_model = injury_stints is not None
    if historical_model:
        assert injury_stints is not None and return_references is not None
        missing_stints = sorted(
            set(INJURY_RETURN_COHORT_SCHEMA) - set(injury_stints.columns)
        )
        missing_references = sorted(
            set(INJURY_RETURN_REFERENCE_SCHEMA) - set(return_references.columns)
        )
        if missing_stints or missing_references:
            raise ValueError(
                "historical injury-return inputs missing fields: "
                f"stints={missing_stints}, references={missing_references}"
            )
        if injury_stints.group_by("player_id").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError("current injury stints violate player grain")
        population = return_references.filter(
            pl.col("reference_level") == "population"
        )
        if population.height != 1:
            raise ValueError("injury-return references require one population row")
        population_return = float(population.item(0, "return_probability"))
        population_fraction = float(
            population.item(0, "mean_remaining_availability_fraction")
        )
        stints = injury_stints.select(
            "player_id",
            "injury_list_type",
            "days_on_il_at_cutoff",
        ).with_columns(
            pl.col("days_on_il_at_cutoff")
            .map_elements(elapsed_days_band, return_dtype=pl.String)
            .alias("elapsed_days_band")
        )
        cells = return_references.filter(
            pl.col("reference_level") != "population"
        ).select(
            "injury_list_type",
            "elapsed_days_band",
            pl.col("return_probability").alias("historical_return_probability"),
            pl.col("mean_remaining_availability_fraction").alias(
                "historical_availability_factor"
            ),
            pl.col("reference_level").alias("availability_reference_level"),
        )
        joined = joined.join(stints, on="player_id", how="left", validate="m:1").join(
            cells,
            on=["injury_list_type", "elapsed_days_band"],
            how="left",
            validate="m:1",
        ).with_columns(
            pl.when(pl.col("injury_list_type").is_not_null())
            .then(
                pl.col("historical_return_probability").fill_null(
                    population_return
                )
            )
            .otherwise(None)
            .alias("historical_return_probability"),
            pl.when(pl.col("injury_list_type").is_not_null())
            .then(
                pl.col("historical_availability_factor").fill_null(
                    population_fraction
                )
            )
            .otherwise(None)
            .alias("historical_availability_factor"),
            pl.when(
                pl.col("injury_list_type").is_not_null()
                & pl.col("availability_reference_level").is_null()
            )
            .then(pl.lit("population_fallback"))
            .otherwise(pl.col("availability_reference_level"))
            .alias("availability_reference_level"),
        )
    else:
        joined = joined.with_columns(
            pl.lit(None, dtype=pl.String).alias("injury_list_type"),
            pl.lit(None, dtype=pl.Int64).alias("days_on_il_at_cutoff"),
            pl.lit(None, dtype=pl.String).alias("elapsed_days_band"),
            pl.lit(None, dtype=pl.Float64).alias(
                "historical_return_probability"
            ),
            pl.lit(None, dtype=pl.Float64).alias(
                "historical_availability_factor"
            ),
            pl.lit(None, dtype=pl.String).alias(
                "availability_reference_level"
            ),
        )
    season_out = pl.col("availability_category") == "official_season_out"
    uncertain = (
        pl.col("availability_category") == "injured_return_date_unresolved"
    )
    calibrated_return = uncertain & pl.col(
        "historical_availability_factor"
    ).is_not_null()
    baseline = pl.col("unadjusted_projected_remaining_war")
    return joined.with_columns(
        pl.when(season_out)
        .then(0.0)
        .when(calibrated_return)
        .then(baseline * pl.col("historical_availability_factor"))
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
        pl.when(calibrated_return)
        .then(
            pl.lit(
                "historical_activation_timing_point_zero_to_baseline_bound"
            )
        )
        .otherwise(pl.col("availability_point_policy"))
        .alias("availability_point_policy"),
        pl.lit(
            "official_status_plus_historical_il_activation_v1"
            if historical_model
            else "official_status_availability_sensitivity_v1"
        ).alias(
            "availability_model_id"
        ),
    )
