"""Evaluate contract-defined vesting thresholds from official counting stats."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    "alternative_conditions": pl.String,
    "vested_control_status": pl.String,
    "unvested_control_status": pl.String,
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


VESTING_CONTROL_CORRECTION_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "player_name": pl.String,
    "organization_id": pl.Int64,
    "season": pl.Int64,
    "expected_control_status": pl.String,
    "corrected_control_status": pl.String,
    "reason": pl.String,
    "source_url": pl.String,
    "source_snapshot_id": pl.String,
}


def load_vesting_trigger_config(path: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Load the reviewed trigger inventory and attach its source snapshot ID."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    snapshot_id = str(payload.get("snapshot_id") or "").strip()
    triggers = payload.get("triggers")
    outcomes = payload.get("control_status_outcomes")
    if (
        not snapshot_id
        or not isinstance(triggers, list)
        or not isinstance(outcomes, list)
    ):
        raise ValueError(
            "vesting trigger config requires snapshot_id, triggers and control outcomes"
        )
    rows = pl.DataFrame(triggers)
    control_outcomes = pl.DataFrame(outcomes)
    outcome_fields = {
        "player_id",
        "option_season",
        "vested_control_status",
        "unvested_control_status",
    }
    if missing_outcomes := sorted(outcome_fields - set(control_outcomes.columns)):
        raise ValueError(f"vesting control outcomes missing fields: {missing_outcomes}")
    if control_outcomes.group_by("player_id", "option_season").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("vesting control outcomes violate player-option-season grain")
    rows = rows.join(
        control_outcomes.select(sorted(outcome_fields)),
        on=["player_id", "option_season"],
        how="inner",
        validate="1:1",
    )
    if rows.height != len(triggers) or rows.height != len(outcomes):
        raise ValueError("vesting trigger and control-outcome coverage differs")
    rows = rows.with_columns(
        pl.lit(snapshot_id).alias("source_snapshot_id")
    )
    missing = sorted(set(VESTING_TRIGGER_SCHEMA) - set(rows.columns))
    if missing:
        raise ValueError(f"vesting trigger config missing fields: {missing}")
    return (
        rows.select(list(VESTING_TRIGGER_SCHEMA)).cast(
            VESTING_TRIGGER_SCHEMA, strict=True
        ),
        payload,
    )


def _nonnegative_count(value: Any, *, field: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing required count for {field}")
    number = float(str(value))
    if not number.is_integer() or number < 0:
        raise ValueError(f"invalid count for {field}: {value!r}")
    return int(number)


def project_statsapi_vesting_observations(
    triggers: pl.DataFrame,
    hitting: pl.DataFrame,
    pitching_payloads: Sequence[Mapping[str, Any]],
    *,
    season: int,
    season_complete: bool,
) -> pl.DataFrame:
    """Project current scalar triggers from retained official MLB source rows.

    League-split rows are summed so a midseason league change cannot lose work.
    A missing player remains missing evidence; it is never converted to zero.
    Multi-season catching and non-stat/award clauses remain separate work.
    """

    required_hitting = {"season", "player_id", "batting_plate_appearances"}
    missing_hitting = sorted(required_hitting - set(hitting.columns))
    if missing_hitting:
        raise ValueError(f"MLB hitting source missing fields: {missing_hitting}")
    current_triggers = triggers.filter(pl.col("trigger_season") == int(season))
    if current_triggers.is_empty():
        return pl.DataFrame(schema=VESTING_OBSERVATION_SCHEMA)

    hitting_counts = (
        hitting.filter(pl.col("season") == int(season))
        .group_by("player_id")
        .agg(pl.col("batting_plate_appearances").sum())
    )
    pa_by_player = {
        int(row["player_id"]): int(row["batting_plate_appearances"])
        for row in hitting_counts.to_dicts()
    }

    pitching_rows: list[dict[str, int]] = []
    for payload in pitching_payloads:
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise ValueError("expected one official MLB pitching stats group")
        for split in groups[0].get("splits") or []:
            player = split.get("player") or split.get("person") or {}
            stat = split.get("stat") or {}
            pitching_rows.append(
                {
                    "player_id": _nonnegative_count(
                        player.get("id"), field="player.id"
                    ),
                    "pitching_outs": _nonnegative_count(
                        stat.get("outs"), field="outs"
                    ),
                    "games_pitched": _nonnegative_count(
                        stat.get("gamesPlayed"), field="gamesPlayed"
                    ),
                }
            )
    pitching = (
        pl.DataFrame(
            pitching_rows,
            schema={
                "player_id": pl.Int64,
                "pitching_outs": pl.Int64,
                "games_pitched": pl.Int64,
            },
        )
        .group_by("player_id")
        .agg(
            pl.col("pitching_outs").sum(),
            pl.col("games_pitched").sum(),
        )
    )
    pitching_by_player = {
        int(row["player_id"]): {
            "pitching_outs": int(row["pitching_outs"]),
            "games_pitched": int(row["games_pitched"]),
        }
        for row in pitching.to_dicts()
    }

    observations: list[dict[str, object]] = []
    for trigger in current_triggers.select(
        ["player_id", "trigger_season", "metric"]
    ).unique().to_dicts():
        player_id = int(trigger["player_id"])
        metric = str(trigger["metric"])
        observed_count: int | None = None
        if metric == "plate_appearances":
            observed_count = pa_by_player.get(player_id)
        elif metric in {"pitching_outs", "games_pitched"}:
            pitching_counts = pitching_by_player.get(player_id)
            if pitching_counts is not None:
                observed_count = pitching_counts[metric]
        if observed_count is not None:
            observations.append(
                {
                    "player_id": player_id,
                    "season": int(season),
                    "metric": metric,
                    "observed_count": observed_count,
                    "season_complete": bool(season_complete),
                }
            )
    if not observations:
        return pl.DataFrame(schema=VESTING_OBSERVATION_SCHEMA)
    return pl.DataFrame(observations, schema=VESTING_OBSERVATION_SCHEMA).sort(
        ["player_id", "season", "metric"]
    )


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
    supported_metrics = {
        "games_pitched",
        "plate_appearances",
        "pitching_outs",
        "seasons_with_100_games_caught",
    }
    supported_control_statuses = {
        "club_option",
        "free_agent_eligible",
        "guaranteed_contract",
        "mutual_option",
        "player_option",
        "review",
    }
    if source.filter(
        (~pl.col("metric").is_in(supported_metrics))
        | (pl.col("threshold_count") <= 0)
        | (pl.col("option_season") <= pl.col("trigger_season"))
        | (pl.col("vested_contract_effect") == "")
        | (pl.col("unvested_contract_effect") == "")
        | (~pl.col("vested_control_status").is_in(supported_control_statuses))
        | (~pl.col("unvested_control_status").is_in(supported_control_statuses))
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
        .when(pl.col("alternative_conditions") != "")
        .then(pl.lit("primary_threshold_missed_alternatives_pending"))
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
                    [
                        "pending",
                        "stat_threshold_met_other_conditions_pending",
                        "primary_threshold_missed_alternatives_pending",
                    ]
                )
            ).height,
            "missing_evidence_rows": rows.filter(
                pl.col("trigger_status") == "missing_evidence"
            ).height,
        },
    )


def build_vesting_control_corrections(evaluations: pl.DataFrame) -> pl.DataFrame:
    """Translate only final, representable trigger outcomes into control states."""

    required = set(VESTING_TRIGGER_SCHEMA) | {"trigger_status"}
    if missing := sorted(required - set(evaluations.columns)):
        raise ValueError(f"vesting evaluations missing fields: {missing}")
    final = evaluations.filter(pl.col("trigger_status").is_in(["vested", "not_vested"]))
    if final.is_empty():
        return pl.DataFrame(schema=VESTING_CONTROL_CORRECTION_SCHEMA)
    resolved = final.with_columns(
        pl.when(pl.col("trigger_status") == "vested")
        .then(pl.col("vested_control_status"))
        .otherwise(pl.col("unvested_control_status"))
        .alias("corrected_control_status")
    ).filter(pl.col("corrected_control_status") != "review")
    if resolved.is_empty():
        return pl.DataFrame(schema=VESTING_CONTROL_CORRECTION_SCHEMA)
    corrections = resolved.select(
        "player_id",
        "player_name",
        "organization_id",
        pl.col("option_season").alias("season"),
        pl.lit("vesting_option").alias("expected_control_status"),
        "corrected_control_status",
        pl.concat_str(
            [
                pl.lit("contract vesting trigger resolved as "),
                pl.col("trigger_status"),
            ]
        ).alias("reason"),
        "source_url",
        "source_snapshot_id",
    ).cast(VESTING_CONTROL_CORRECTION_SCHEMA, strict=True)
    if corrections.group_by("player_id", "organization_id", "season").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("resolved vesting corrections violate player-team-season grain")
    return corrections.sort(["player_id", "organization_id", "season"])
