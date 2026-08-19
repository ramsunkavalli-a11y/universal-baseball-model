"""Source-semantic audits for Player Value v1 baserunning evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
import io
import math
from typing import Any


MLB_BASERUNNING_SOURCE_FIELDS = (
    "hits",
    "doubles",
    "triples",
    "homeRuns",
    "stolenBases",
    "caughtStealing",
    "groundIntoDoublePlay",
    "gidpOpp",
)

SAVANT_BASERUNNING_RUN_VALUE_URL = (
    "https://baseballsavant.mlb.com/leaderboard/baserunning-run-value"
)
SAVANT_BASERUNNING_REQUIRED_FIELDS = (
    "player_id",
    "runner_runs_tot",
    "runner_runs_xb",
    "runner_runs_sbx",
    "n_runner_moved",
    "n_runner_moved_xb",
    "n_runner_moved_sbx",
)
SAVANT_BASERUNNING_RUN_FIELDS = (
    "runner_runs_tot",
    "runner_runs_xb",
    "runner_runs_sbx",
)
SAVANT_BASERUNNING_COUNT_FIELDS = (
    "n_runner_moved",
    "n_runner_moved_xb",
    "n_runner_moved_sbx",
)


def savant_baserunning_query_params(season: int) -> dict[str, str]:
    """Return the frozen runner-level regular-season CSV query for one season."""

    if int(season) < 2016:
        raise ValueError("Savant baserunning run value is only audited for 2016+")
    year = str(int(season))
    return {
        "game_type": "Regular",
        "n": "1",
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Run",
        "with_team_only": "0",
        "csv": "true",
    }


def _optional_integer_count(value: Any, label: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    numeric = float(str(value))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid {label}: {value!r}")
    return int(numeric)


def _optional_finite_number(value: Any, label: str) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    numeric = float(str(value))
    if not math.isfinite(numeric):
        raise ValueError(f"invalid {label}: {value!r}")
    return numeric


def _normalize_csv_name(value: str) -> str:
    return str(value).strip().lower()


def parse_savant_baserunning_csv(text: str) -> list[dict[str, str]]:
    """Parse the public Savant baserunning leaderboard with normalized headers."""

    if not str(text).strip():
        raise ValueError("Savant baserunning CSV response is empty")
    stripped = str(text).lstrip("\ufeff")
    if stripped.lstrip().startswith("<"):
        raise ValueError("Savant baserunning endpoint returned HTML instead of CSV")

    reader = csv.DictReader(io.StringIO(stripped))
    if not reader.fieldnames:
        raise ValueError("Savant baserunning CSV has no header row")

    normalized_headers = [_normalize_csv_name(field) for field in reader.fieldnames]
    if len(set(normalized_headers)) != len(normalized_headers):
        raise ValueError("Savant baserunning CSV has duplicate normalized headers")

    rows: list[dict[str, str]] = []
    for raw in reader:
        normalized = {
            _normalize_csv_name(key): "" if value is None else str(value).strip()
            for key, value in raw.items()
            if key is not None
        }
        if any(value != "" for value in normalized.values()):
            rows.append(normalized)
    return rows


def audit_savant_baserunning_rows(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit Savant runner-level run-value rows without zero-filling missing data."""

    if not rows:
        raise ValueError("Savant baserunning audit requires at least one row")

    field_present_rows = {field: 0 for field in SAVANT_BASERUNNING_REQUIRED_FIELDS}
    field_nonnull_rows = {field: 0 for field in SAVANT_BASERUNNING_REQUIRED_FIELDS}
    player_ids: list[int] = []
    run_decomposition_checked_rows = 0
    max_abs_run_decomposition_delta = 0.0
    opportunity_identity_checked_rows = 0
    opportunity_identity_violation_rows = 0

    for row in rows:
        parsed: dict[str, int | float | None] = {}
        for field in SAVANT_BASERUNNING_REQUIRED_FIELDS:
            if field in row:
                field_present_rows[field] += 1
            if field == "player_id" or field in SAVANT_BASERUNNING_COUNT_FIELDS:
                value = _optional_integer_count(row.get(field), field)
            else:
                value = _optional_finite_number(row.get(field), field)
            parsed[field] = value
            if value is not None:
                field_nonnull_rows[field] += 1

        player_id = parsed["player_id"]
        if player_id is not None:
            if int(player_id) <= 0:
                raise ValueError(f"invalid player_id: {player_id!r}")
            player_ids.append(int(player_id))

        total = parsed["runner_runs_tot"]
        xb = parsed["runner_runs_xb"]
        sbx = parsed["runner_runs_sbx"]
        if total is not None and xb is not None and sbx is not None:
            run_decomposition_checked_rows += 1
            delta = abs(float(total) - float(xb) - float(sbx))
            max_abs_run_decomposition_delta = max(
                max_abs_run_decomposition_delta,
                delta,
            )

        total_opportunities = parsed["n_runner_moved"]
        xb_opportunities = parsed["n_runner_moved_xb"]
        sbx_opportunities = parsed["n_runner_moved_sbx"]
        if (
            total_opportunities is not None
            and xb_opportunities is not None
            and sbx_opportunities is not None
        ):
            opportunity_identity_checked_rows += 1
            if int(total_opportunities) != int(xb_opportunities) + int(sbx_opportunities):
                opportunity_identity_violation_rows += 1

    row_count = len(rows)
    duplicate_player_id_rows = len(player_ids) - len(set(player_ids))
    fields = {
        field: {
            "present_rows": field_present_rows[field],
            "nonnull_rows": field_nonnull_rows[field],
            "missing_rows": row_count - field_nonnull_rows[field],
            "complete": field_nonnull_rows[field] == row_count,
        }
        for field in SAVANT_BASERUNNING_REQUIRED_FIELDS
    }
    required_fields_complete = all(
        fields[field]["complete"] for field in SAVANT_BASERUNNING_REQUIRED_FIELDS
    )
    return {
        "row_count": row_count,
        "fields": fields,
        "duplicate_player_id_rows": duplicate_player_id_rows,
        "run_decomposition": {
            "checked_rows": run_decomposition_checked_rows,
            "max_abs_delta": max_abs_run_decomposition_delta,
            "identity_is_diagnostic_only": True,
        },
        "opportunity_identity": {
            "checked_rows": opportunity_identity_checked_rows,
            "violation_rows": opportunity_identity_violation_rows,
            "identity_is_diagnostic_only": True,
        },
        "advancement_source_usable": (
            required_fields_complete
            and duplicate_player_id_rows == 0
            and field_nonnull_rows["n_runner_moved_xb"] > 0
        ),
    }


def audit_mlb_baserunning_splits(
    splits: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit field presence and count semantics without filling missing values."""

    if not splits:
        raise ValueError("MLB baserunning audit requires at least one hitting split")

    field_present_rows = {field: 0 for field in MLB_BASERUNNING_SOURCE_FIELDS}
    field_nonnull_rows = {field: 0 for field in MLB_BASERUNNING_SOURCE_FIELDS}
    gidp_checked_rows = 0
    gidp_violation_rows = 0
    hit_identity_checked_rows = 0
    hit_identity_violation_rows = 0

    for split in splits:
        stat = split.get("stat") or {}
        parsed: dict[str, int | None] = {}
        for field in MLB_BASERUNNING_SOURCE_FIELDS:
            if field in stat:
                field_present_rows[field] += 1
            value = _optional_integer_count(stat.get(field), field)
            parsed[field] = value
            if value is not None:
                field_nonnull_rows[field] += 1

        gidp = parsed["groundIntoDoublePlay"]
        opportunities = parsed["gidpOpp"]
        if gidp is not None and opportunities is not None:
            gidp_checked_rows += 1
            if gidp > opportunities:
                gidp_violation_rows += 1

        hit_components = [parsed[field] for field in ("hits", "doubles", "triples", "homeRuns")]
        if all(value is not None for value in hit_components):
            hits, doubles, triples, home_runs = (int(value) for value in hit_components)
            hit_identity_checked_rows += 1
            if hits - doubles - triples - home_runs < 0:
                hit_identity_violation_rows += 1

    if gidp_violation_rows:
        raise ValueError(
            "MLB baserunning source violates groundIntoDoublePlay <= gidpOpp "
            f"in {gidp_violation_rows} rows"
        )
    if hit_identity_violation_rows:
        raise ValueError(
            "MLB baserunning source implies negative singles in "
            f"{hit_identity_violation_rows} rows"
        )

    row_count = len(splits)
    return {
        "row_count": row_count,
        "fields": {
            field: {
                "present_rows": field_present_rows[field],
                "nonnull_rows": field_nonnull_rows[field],
                "missing_rows": row_count - field_nonnull_rows[field],
                "complete": field_nonnull_rows[field] == row_count,
            }
            for field in MLB_BASERUNNING_SOURCE_FIELDS
        },
        "gidp_opportunity_identity": {
            "checked_rows": gidp_checked_rows,
            "violation_rows": 0,
        },
        "singles_identity": {
            "checked_rows": hit_identity_checked_rows,
            "violation_rows": 0,
        },
    }
