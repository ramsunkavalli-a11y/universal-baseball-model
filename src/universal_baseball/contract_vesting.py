"""Evaluate contract-defined vesting thresholds from official counting stats."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


VESTING_TRIGGER_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "player_name": pl.String,
    "organization_id": pl.Int64,
    "option_season": pl.Int64,
    "trigger_season": pl.Int64,
    "metric": pl.String,
    "threshold_count": pl.Int64,
    "other_conditions": pl.String,
    "vested_contract_effect": pl.String,
    "unvested_contract_effect": pl.String,
    "source_url": pl.String,
    "source_snapshot_id": pl.String,
}

VESTING_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "metric": pl.String,
    "observed_count": pl.Int64,
    "season_complete": pl.Boolean,
}


@dataclass(frozen=True, slots=True)
class VestingTriggerEvaluation:
    rows: pl.DataFrame
    coverage: dict[str, int]


def evaluate_vesting_triggers(
    triggers: pl.DataFrame,
    observations: pl.DataFrame,
) -> VestingTriggerEvaluation:
    """Evaluate observable thresholds without guessing future or non-stat conditions."""

    missing = sorted(set(VESTING_TRIGGER_SCHEMA) - set(triggers.columns))
    if missing:
        raise ValueError(f"vesting triggers missing fields: {missing}")
    missing_observations = sorted(
        set(VESTING_OBSERVATION_SCHEMA) - set(observations.columns)
    )
    if missing_observations:
        raise ValueError(
            f"vesting observations missing fields: {missing_observations}"
        )
    source = triggers.select(list(VESTING_TRIGGER_SCHEMA)).cast(
        VESTING_TRIGGER_SCHEMA, strict=True
    )
    observed = observations.select(list(VESTING_OBSERVATION_SCHEMA)).cast(
        VESTING_OBSERVATION_SCHEMA, strict=True
    )
    key = ["player_id", "organization_id", "option_season"]
    if source.group_by(key).len().filter(pl.col("len") != 1).height:
        raise ValueError("vesting triggers violate player-team-option-season grain")
    if observed.group_by("player_id", "season", "metric").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("vesting observations violate player-season-metric grain")
    supported_metrics = {"plate_appearances", "pitching_outs"}
    if source.filter(
        (~pl.col("metric").is_in(supported_metrics))
        | (pl.col("threshold_count") <= 0)
        | (pl.col("option_season") <= pl.col("trigger_season"))
        | (pl.col("vested_contract_effect") == "")
        | (pl.col("unvested_contract_effect") == "")
        | (pl.col("source_url") == "")
        | (pl.col("source_snapshot_id") == "")
    ).height:
        raise ValueError("vesting triggers contain invalid threshold or provenance")
    if observed.filter(pl.col("observed_count") < 0).height:
        raise ValueError("vesting observations contain a negative count")

    rows = source.join(
        observed.rename({"season": "trigger_season"}),
        on=["player_id", "trigger_season", "metric"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.when(pl.col("observed_count").is_null())
        .then(pl.lit("missing_evidence"))
        .when(pl.col("observed_count") >= pl.col("threshold_count"))
        .then(
            pl.when(pl.col("other_conditions") == "")
            .then(pl.lit("vested"))
            .otherwise(pl.lit("stat_threshold_met_other_conditions_pending"))
        )
        .when(pl.col("season_complete"))
        .then(pl.lit("not_vested"))
        .otherwise(pl.lit("pending"))
        .alias("trigger_status")
    ).sort(key)
    return VestingTriggerEvaluation(
        rows=rows,
        coverage={
            "trigger_rows": rows.height,
            "observed_rows": rows.filter(pl.col("observed_count").is_not_null()).height,
            "vested_rows": rows.filter(pl.col("trigger_status") == "vested").height,
            "not_vested_rows": rows.filter(
                pl.col("trigger_status") == "not_vested"
            ).height,
            "pending_rows": rows.filter(
                pl.col("trigger_status").is_in(
                    ["pending", "stat_threshold_met_other_conditions_pending"]
                )
            ).height,
            "missing_evidence_rows": rows.filter(
                pl.col("trigger_status") == "missing_evidence"
            ).height,
        },
    )
