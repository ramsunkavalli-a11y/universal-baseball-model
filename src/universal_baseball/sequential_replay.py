"""Chronology and coverage guardrails for dated Phase 1 value replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

import polars as pl


UTC_DATETIME = pl.Datetime(time_unit="us", time_zone="UTC")
REPLAY_MODES = {"retrospective_event_cutoff", "vintage_information_set"}

REPLAY_UNIVERSE_SCHEMA: dict[str, pl.DataType] = {
    "checkpoint_id": pl.String,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "rights_state": pl.String,
}

REPLAY_SOURCE_EVIDENCE_SCHEMA: dict[str, pl.DataType] = {
    "checkpoint_id": pl.String,
    "source_snapshot_id": pl.String,
    "maximum_predictor_event_date": pl.Date,
    "knowledge_available_at_utc": UTC_DATETIME,
}

REPLAY_VALUE_RECORD_SCHEMA: dict[str, pl.DataType] = {
    "checkpoint_id": pl.String,
    "as_of_at_utc": UTC_DATETIME,
    "evidence_cutoff_at_utc": UTC_DATETIME,
    "replay_mode": pl.String,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "rights_state": pl.String,
    "last_completed_game_date": pl.Date,
    "model_version": pl.String,
    "evidence_bundle_id": pl.String,
    "projection_source_id": pl.String,
    "contract_source_id": pl.String,
    "coverage_tier": pl.String,
    "calculation_status": pl.String,
    "expected_remaining_war": pl.Float64,
    "expected_remaining_war_lower": pl.Float64,
    "expected_remaining_war_upper": pl.Float64,
    "expected_remaining_cost_dollars": pl.Float64,
    "transferable_value_dollars": pl.Float64,
    "transferable_value_lower_dollars": pl.Float64,
    "transferable_value_upper_dollars": pl.Float64,
    "declared_change_reasons": pl.String,
}

REPLAY_CHECKPOINT_SUMMARY_SCHEMA: dict[str, pl.DataType] = {
    "checkpoint_id": pl.String,
    "as_of_at_utc": UTC_DATETIME,
    "evidence_cutoff_at_utc": UTC_DATETIME,
    "replay_mode": pl.String,
    "model_version": pl.String,
    "evidence_bundle_id": pl.String,
    "players": pl.Int64,
    "available_players": pl.Int64,
    "review_players": pl.Int64,
    "no_incumbent_rights_players": pl.Int64,
    "expected_remaining_war": pl.Float64,
    "expected_remaining_cost_dollars": pl.Float64,
    "transferable_value_dollars": pl.Float64,
}

REPLAY_DELTA_SCHEMA: dict[str, pl.DataType] = {
    "from_checkpoint_id": pl.String,
    "to_checkpoint_id": pl.String,
    "player_id": pl.Int64,
    "from_organization_id": pl.Int64,
    "to_organization_id": pl.Int64,
    "expected_remaining_war_change": pl.Float64,
    "expected_remaining_cost_change_dollars": pl.Float64,
    "transferable_value_change_dollars": pl.Float64,
    "is_material_value_change": pl.Boolean,
    "change_reasons": pl.String,
    "delta_status": pl.String,
}


@dataclass(frozen=True, slots=True)
class ReplayResult:
    records: pl.DataFrame
    checkpoints: pl.DataFrame
    deltas: pl.DataFrame


def _cast_required(frame: pl.DataFrame, schema: dict[str, pl.DataType], name: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing fields: {missing}")
    return frame.select(list(schema)).cast(schema, strict=True)


def _one(frame: pl.DataFrame, column: str, checkpoint_id: str) -> object:
    values = frame.get_column(column).unique().to_list()
    if len(values) != 1:
        raise ValueError(f"checkpoint {checkpoint_id} has inconsistent {column}")
    return values[0]


def _validate_checkpoint(
    records: pl.DataFrame,
    universe: pl.DataFrame,
    evidence: pl.DataFrame,
) -> dict[str, object]:
    checkpoint_id = str(_one(records, "checkpoint_id", "unknown"))
    if not checkpoint_id:
        raise ValueError("checkpoint_id cannot be blank")
    if records.get_column("player_id").n_unique() != records.height:
        raise ValueError(f"checkpoint {checkpoint_id} duplicates player rights")
    if universe.get_column("player_id").n_unique() != universe.height:
        raise ValueError(f"checkpoint {checkpoint_id} universe duplicates players")
    record_rights = set(
        records.select("player_id", "organization_id", "rights_state").iter_rows()
    )
    universe_rights = set(
        universe.select("player_id", "organization_id", "rights_state").iter_rows()
    )
    if record_rights != universe_rights:
        raise ValueError(f"checkpoint {checkpoint_id} differs from its frozen rights universe")

    as_of = _one(records, "as_of_at_utc", checkpoint_id)
    cutoff = _one(records, "evidence_cutoff_at_utc", checkpoint_id)
    mode = str(_one(records, "replay_mode", checkpoint_id))
    model = str(_one(records, "model_version", checkpoint_id))
    bundle = str(_one(records, "evidence_bundle_id", checkpoint_id))
    if not isinstance(as_of, datetime) or not isinstance(cutoff, datetime):
        raise ValueError(f"checkpoint {checkpoint_id} has invalid timestamps")
    if cutoff > as_of:
        raise ValueError(f"checkpoint {checkpoint_id} evidence cutoff follows its as-of time")
    if mode not in REPLAY_MODES:
        raise ValueError(f"checkpoint {checkpoint_id} has unsupported replay mode")
    if not model or not bundle:
        raise ValueError(f"checkpoint {checkpoint_id} lacks model or evidence identity")
    if evidence.is_empty():
        raise ValueError(f"checkpoint {checkpoint_id} has no source evidence")
    if evidence.filter(
        pl.col("maximum_predictor_event_date").is_not_null()
        & (pl.col("maximum_predictor_event_date") > cutoff.date())
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} source evidence crosses the event cutoff")
    if mode == "vintage_information_set" and evidence.filter(
        pl.col("knowledge_available_at_utc").is_null()
        | (pl.col("knowledge_available_at_utc") > cutoff)
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} lacks valid vintage source timing")
    if records.filter(
        pl.col("last_completed_game_date").is_not_null()
        & (pl.col("last_completed_game_date") > cutoff.date())
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} includes a future completed game")

    required_text = [
        "rights_state",
        "projection_source_id",
        "contract_source_id",
        "coverage_tier",
        "calculation_status",
    ]
    if records.filter(
        (pl.col("player_id") <= 0)
        | pl.any_horizontal([pl.col(column) == "" for column in required_text])
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} has invalid identity or labels")

    numeric = [
        "expected_remaining_war",
        "expected_remaining_war_lower",
        "expected_remaining_war_upper",
        "expected_remaining_cost_dollars",
        "transferable_value_dollars",
        "transferable_value_lower_dollars",
        "transferable_value_upper_dollars",
    ]
    available = records.filter(pl.col("calculation_status") == "available")
    if sum(available.select(numeric).null_count().row(0)):
        raise ValueError(f"checkpoint {checkpoint_id} available rows have missing values")
    if any(
        not isfinite(float(value))
        for column in numeric
        for value in available.get_column(column).to_list()
    ):
        raise ValueError(f"checkpoint {checkpoint_id} available rows have nonfinite values")
    if available.filter(
        (pl.col("expected_remaining_cost_dollars") < 0)
        | (pl.col("expected_remaining_war_lower") > pl.col("expected_remaining_war"))
        | (pl.col("expected_remaining_war_upper") < pl.col("expected_remaining_war"))
        | (pl.col("transferable_value_lower_dollars") > pl.col("transferable_value_dollars"))
        | (pl.col("transferable_value_upper_dollars") < pl.col("transferable_value_dollars"))
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} has invalid cost or bounds")
    if records.filter(
        (pl.col("rights_state") == "no_incumbent_rights")
        & pl.col("transferable_value_dollars").is_not_null()
        & (pl.col("transferable_value_dollars").abs() > 1e-9)
    ).height:
        raise ValueError(f"checkpoint {checkpoint_id} values rights that are not transferable")

    return {
        "checkpoint_id": checkpoint_id,
        "as_of_at_utc": as_of,
        "evidence_cutoff_at_utc": cutoff,
        "replay_mode": mode,
        "model_version": model,
        "evidence_bundle_id": bundle,
        "players": records.height,
        "available_players": available.height,
        "review_players": records.filter(pl.col("calculation_status") == "review").height,
        "no_incumbent_rights_players": records.filter(
            pl.col("rights_state") == "no_incumbent_rights"
        ).height,
        "expected_remaining_war": float(available.get_column("expected_remaining_war").sum()),
        "expected_remaining_cost_dollars": float(
            available.get_column("expected_remaining_cost_dollars").sum()
        ),
        "transferable_value_dollars": float(
            available.get_column("transferable_value_dollars").sum()
        ),
    }


def _value(row: dict[str, object] | None, key: str) -> float:
    if row is None or row[key] is None:
        return 0.0
    return float(row[key])


def _build_deltas(
    previous: pl.DataFrame,
    current: pl.DataFrame,
    *,
    material_value_tolerance_dollars: float,
) -> list[dict[str, object]]:
    prior_id = str(previous.item(0, "checkpoint_id"))
    current_id = str(current.item(0, "checkpoint_id"))
    if current.item(0, "as_of_at_utc") <= previous.item(0, "as_of_at_utc"):
        raise ValueError("replay checkpoints must be strictly chronological")
    prior = {int(row["player_id"]): row for row in previous.iter_rows(named=True)}
    now = {int(row["player_id"]): row for row in current.iter_rows(named=True)}
    rows: list[dict[str, object]] = []
    for player_id in sorted(set(prior) | set(now)):
        before = prior.get(player_id)
        after = now.get(player_id)
        reasons: list[str] = []
        if before is None:
            reasons.append("new_universe_member")
        elif after is None:
            reasons.append("departed_universe_member")
        else:
            if before["organization_id"] != after["organization_id"]:
                reasons.append("rights_owner_change")
            if before["last_completed_game_date"] != after["last_completed_game_date"]:
                reasons.append("completed_games_added")
            if before["projection_source_id"] != after["projection_source_id"]:
                reasons.append("projection_evidence_change")
            if before["contract_source_id"] != after["contract_source_id"]:
                reasons.append("contract_evidence_change")
            if before["model_version"] != after["model_version"]:
                reasons.append("model_revision")
            declared = str(after["declared_change_reasons"] or "").strip()
            if declared:
                reasons.extend(reason.strip() for reason in declared.split(",") if reason.strip())
        war_change = _value(after, "expected_remaining_war") - _value(
            before, "expected_remaining_war"
        )
        cost_change = _value(after, "expected_remaining_cost_dollars") - _value(
            before, "expected_remaining_cost_dollars"
        )
        value_change = _value(after, "transferable_value_dollars") - _value(
            before, "transferable_value_dollars"
        )
        material = abs(value_change) > material_value_tolerance_dollars
        status = "available"
        if material and not reasons:
            status = "review_unexplained_material_change"
        rows.append(
            {
                "from_checkpoint_id": prior_id,
                "to_checkpoint_id": current_id,
                "player_id": player_id,
                "from_organization_id": None if before is None else before["organization_id"],
                "to_organization_id": None if after is None else after["organization_id"],
                "expected_remaining_war_change": war_change,
                "expected_remaining_cost_change_dollars": cost_change,
                "transferable_value_change_dollars": value_change,
                "is_material_value_change": material,
                "change_reasons": ",".join(dict.fromkeys(reasons)),
                "delta_status": status,
            }
        )
    return rows


def replay_value_checkpoints(
    records: pl.DataFrame,
    universes: pl.DataFrame,
    source_evidence: pl.DataFrame,
    *,
    material_value_tolerance_dollars: float = 1000.0,
) -> ReplayResult:
    """Validate and compare complete dated player-value checkpoints."""

    if material_value_tolerance_dollars < 0:
        raise ValueError("material value tolerance must be nonnegative")
    values = _cast_required(records, REPLAY_VALUE_RECORD_SCHEMA, "replay value records")
    universe = _cast_required(universes, REPLAY_UNIVERSE_SCHEMA, "replay universes")
    evidence = _cast_required(
        source_evidence, REPLAY_SOURCE_EVIDENCE_SCHEMA, "replay source evidence"
    )
    if values.is_empty():
        raise ValueError("replay requires at least one checkpoint")
    checkpoint_ids = set(values.get_column("checkpoint_id").to_list())
    if set(universe.get_column("checkpoint_id").to_list()) != checkpoint_ids:
        raise ValueError("replay universe checkpoints differ from value checkpoints")
    if set(evidence.get_column("checkpoint_id").to_list()) != checkpoint_ids:
        raise ValueError("replay evidence checkpoints differ from value checkpoints")

    groups: list[pl.DataFrame] = []
    summaries: list[dict[str, object]] = []
    for checkpoint in values.partition_by("checkpoint_id", maintain_order=True):
        checkpoint_id = str(checkpoint.item(0, "checkpoint_id"))
        checkpoint_universe = universe.filter(pl.col("checkpoint_id") == checkpoint_id)
        checkpoint_evidence = evidence.filter(pl.col("checkpoint_id") == checkpoint_id)
        summaries.append(_validate_checkpoint(checkpoint, checkpoint_universe, checkpoint_evidence))
        groups.append(checkpoint)
    order = sorted(range(len(groups)), key=lambda index: groups[index].item(0, "as_of_at_utc"))
    groups = [groups[index] for index in order]
    summaries = [summaries[index] for index in order]

    delta_rows: list[dict[str, object]] = []
    for previous, current in zip(groups, groups[1:], strict=False):
        delta_rows.extend(
            _build_deltas(
                previous,
                current,
                material_value_tolerance_dollars=material_value_tolerance_dollars,
            )
        )
    deltas = pl.DataFrame(delta_rows, schema=REPLAY_DELTA_SCHEMA)
    if deltas.filter(pl.col("delta_status") != "available").height:
        raise ValueError("replay contains unexplained material value changes")
    return ReplayResult(
        records=pl.concat(groups).sort(["as_of_at_utc", "player_id"]),
        checkpoints=pl.DataFrame(summaries, schema=REPLAY_CHECKPOINT_SUMMARY_SCHEMA).sort(
            "as_of_at_utc"
        ),
        deltas=deltas.sort(["to_checkpoint_id", "player_id"]),
    )
