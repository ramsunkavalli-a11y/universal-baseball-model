"""Chronology-safe injured-list return cohorts from official transactions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

import polars as pl

from universal_baseball.rights_transactions import RIGHTS_TRANSACTION_SCHEMA


INJURY_RETURN_COHORT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "cutoff_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "injury_list_type": pl.String,
    "il_start_date": pl.Date,
    "days_on_il_at_cutoff": pl.Int64,
    "season_end_date": pl.Date,
    "activation_date": pl.Date,
    "returned_by_season_end": pl.Boolean,
    "days_until_activation": pl.Int64,
    "remaining_season_availability_fraction": pl.Float64,
    "source_snapshot_ids": pl.String,
}

INJURY_RETURN_REFERENCE_SCHEMA: dict[str, pl.DataType] = {
    "injury_list_type": pl.String,
    "elapsed_days_band": pl.String,
    "reference_level": pl.String,
    "observation_count": pl.Int64,
    "returned_count": pl.Int64,
    "return_probability": pl.Float64,
    "mean_remaining_availability_fraction": pl.Float64,
}

_LIST_PATTERN = re.compile(r"(?P<days>7|10|15|60)-day injured list")


def _event(description: object) -> tuple[str, str] | None:
    text = str(description or "").strip().lower()
    if "injured list" not in text:
        return None
    match = _LIST_PATTERN.search(text)
    list_type = f"{match.group('days')}_day" if match else "other_il"
    if " activated " in f" {text} " and " from the " in text:
        return "activation", list_type
    if " reinstated " in f" {text} " and " from the " in text:
        return "activation", list_type
    if " transferred " in f" {text} " and " to the " in text:
        return "transfer", list_type
    if " placed " in f" {text} " and " on the " in text:
        return "placement", list_type
    return None


def normalize_injury_transaction_payload(
    payload: dict[str, object], *, season: int
) -> tuple[dict[str, object], dict[str, int]]:
    """Keep identifiable IL events and repair only cross-year effective dates."""

    source_rows = payload.get("transactions")
    if not isinstance(source_rows, list):
        raise ValueError("injury transaction response missing transactions list")
    normalized: list[dict[str, object]] = []
    dropped_without_identity = 0
    cross_year_corrections = 0
    duplicate_event_rows_removed = 0
    for raw in source_rows:
        if not isinstance(raw, dict) or _event(raw.get("description")) is None:
            continue
        if (raw.get("person") or {}).get("id") is None or not str(
            raw.get("typeCode") or ""
        ).strip():
            dropped_without_identity += 1
            continue
        transaction_date = str(raw.get("date") or "")
        effective_date = str(raw.get("effectiveDate") or transaction_date)
        if transaction_date[:4] != str(season):
            raise ValueError("injury transaction date falls outside requested season")
        if effective_date[:4] != transaction_date[:4]:
            effective_date = transaction_date
            cross_year_corrections += 1
        normalized.append(
            {**raw, "effectiveDate": effective_date, "resolutionDate": None}
        )
    deduplicated: dict[tuple[int, int], dict[str, object]] = {}
    for row in normalized:
        key = (int(row["id"]), int((row.get("person") or {})["id"]))
        previous = deduplicated.get(key)
        if previous is not None:
            duplicate_event_rows_removed += 1
        if previous is None or str(row.get("date") or "") > str(
            previous.get("date") or ""
        ):
            deduplicated[key] = row
    normalized = list(deduplicated.values())
    return (
        {**payload, "transactions": normalized},
        {
            "source_rows": len(source_rows),
            "recognized_injury_rows": len(normalized),
            "injury_rows_dropped_without_identity": dropped_without_identity,
            "cross_year_effective_date_corrections": cross_year_corrections,
            "duplicate_event_rows_removed": duplicate_event_rows_removed,
        },
    )


def elapsed_days_band(days: int) -> str:
    """Return a broad, prespecified elapsed-time band."""

    if days < 0:
        raise ValueError("injured-list elapsed days cannot be negative")
    if days < 15:
        return "00_14"
    if days < 30:
        return "15_29"
    if days < 60:
        return "30_59"
    return "60_plus"


def build_injury_return_cohort(
    transactions: pl.DataFrame,
    *,
    cutoff_date: date,
    season_end_date: date,
) -> pl.DataFrame:
    """Label players on an injured list at cutoff using later activation facts."""

    if cutoff_date.year != season_end_date.year or cutoff_date >= season_end_date:
        raise ValueError("injury-return dates require one season and time after cutoff")
    missing = sorted(set(RIGHTS_TRANSACTION_SCHEMA) - set(transactions.columns))
    if missing:
        raise ValueError(f"injury-return transactions missing fields: {missing}")
    source = transactions.select(list(RIGHTS_TRANSACTION_SCHEMA)).cast(
        RIGHTS_TRANSACTION_SCHEMA, strict=True
    )
    if source.filter(pl.col("effective_date").dt.year() != cutoff_date.year).height:
        raise ValueError("injury-return transaction input crosses the target season")
    if source.group_by("transaction_id", "player_id").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("injury-return transactions violate event-player grain")

    output: list[dict[str, object]] = []
    for player_rows in source.sort(
        ["player_id", "effective_date", "transaction_id"]
    ).partition_by("player_id", maintain_order=True):
        player_id = int(player_rows.item(0, "player_id"))
        player_name = str(player_rows.item(0, "player_name"))
        injured = False
        il_start: date | None = None
        list_type = ""
        activation_after_cutoff: date | None = None
        snapshot_ids: set[str] = set()
        for row in player_rows.iter_rows(named=True):
            effective = row["effective_date"]
            assert isinstance(effective, date)
            if effective > season_end_date:
                continue
            parsed = _event(row["description"])
            if parsed is None:
                continue
            snapshot_ids.add(str(row["source_snapshot_id"]))
            kind, event_list_type = parsed
            if effective <= cutoff_date:
                if kind == "placement":
                    injured = True
                    il_start = effective
                    list_type = event_list_type
                elif kind == "transfer" and injured:
                    list_type = event_list_type
                elif kind == "activation":
                    injured = False
                    il_start = None
                    list_type = ""
            elif injured and activation_after_cutoff is None and kind == "activation":
                activation_after_cutoff = effective
        if not injured or il_start is None:
            continue
        elapsed = (cutoff_date - il_start).days
        remaining_days = (season_end_date - cutoff_date).days
        availability_fraction = (
            min(
                1.0,
                ((season_end_date - activation_after_cutoff).days + 1)
                / remaining_days,
            )
            if activation_after_cutoff is not None
            else 0.0
        )
        output.append(
            {
                "season": cutoff_date.year,
                "cutoff_date": cutoff_date,
                "player_id": player_id,
                "player_name": player_name,
                "injury_list_type": list_type,
                "il_start_date": il_start,
                "days_on_il_at_cutoff": elapsed,
                "season_end_date": season_end_date,
                "activation_date": activation_after_cutoff,
                "returned_by_season_end": activation_after_cutoff is not None,
                "days_until_activation": (
                    (activation_after_cutoff - cutoff_date).days
                    if activation_after_cutoff is not None
                    else None
                ),
                "remaining_season_availability_fraction": availability_fraction,
                "source_snapshot_ids": ",".join(sorted(snapshot_ids)),
            }
        )
    return (
        pl.DataFrame(output, schema=INJURY_RETURN_COHORT_SCHEMA)
        if output
        else pl.DataFrame(schema=INJURY_RETURN_COHORT_SCHEMA)
    ).sort(["season", "player_id"])


@dataclass(frozen=True, slots=True)
class InjuryReturnFit:
    references: pl.DataFrame
    prior_players: float


def fit_injury_return_references(
    cohort: pl.DataFrame, *, prior_players: float = 25.0
) -> InjuryReturnFit:
    """Fit broad IL-type/elapsed references shrunk to the full population."""

    if prior_players <= 0:
        raise ValueError("injury-return prior strength must be positive")
    missing = sorted(set(INJURY_RETURN_COHORT_SCHEMA) - set(cohort.columns))
    if missing:
        raise ValueError(f"injury-return cohort missing fields: {missing}")
    source = cohort.select(list(INJURY_RETURN_COHORT_SCHEMA)).cast(
        INJURY_RETURN_COHORT_SCHEMA, strict=True
    )
    if source.is_empty():
        raise ValueError("injury-return cohort cannot be empty")
    source = source.with_columns(
        pl.col("days_on_il_at_cutoff")
        .map_elements(elapsed_days_band, return_dtype=pl.String)
        .alias("elapsed_days_band")
    )
    global_n = source.height
    global_return = float(source.get_column("returned_by_season_end").mean())
    global_fraction = float(
        source.get_column("remaining_season_availability_fraction").mean()
    )
    rows: list[dict[str, object]] = [
        {
            "injury_list_type": "ALL",
            "elapsed_days_band": "ALL",
            "reference_level": "population",
            "observation_count": global_n,
            "returned_count": int(
                source.get_column("returned_by_season_end").sum()
            ),
            "return_probability": global_return,
            "mean_remaining_availability_fraction": global_fraction,
        }
    ]
    for cell in source.partition_by(
        ["injury_list_type", "elapsed_days_band"], maintain_order=True
    ):
        n = cell.height
        returned = int(cell.get_column("returned_by_season_end").sum())
        fraction_sum = float(
            cell.get_column("remaining_season_availability_fraction").sum()
        )
        rows.append(
            {
                "injury_list_type": str(cell.item(0, "injury_list_type")),
                "elapsed_days_band": str(cell.item(0, "elapsed_days_band")),
                "reference_level": "il_type_elapsed_shrunk",
                "observation_count": n,
                "returned_count": returned,
                "return_probability": (
                    returned + prior_players * global_return
                ) / (n + prior_players),
                "mean_remaining_availability_fraction": (
                    fraction_sum + prior_players * global_fraction
                ) / (n + prior_players),
            }
        )
    return InjuryReturnFit(
        references=pl.DataFrame(rows, schema=INJURY_RETURN_REFERENCE_SCHEMA).sort(
            ["injury_list_type", "elapsed_days_band"]
        ),
        prior_players=prior_players,
    )
