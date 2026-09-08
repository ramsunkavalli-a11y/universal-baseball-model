"""Normalize FanGraphs depth charts as validation evidence, not authority."""

from __future__ import annotations

from pathlib import Path
from math import isnan
import re
from typing import Mapping

import polars as pl

from universal_baseball.contract_terms import read_fangraphs_payroll_xlsx


DEPTH_CHART_REFERENCE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "team_name": pl.String,
    "depth_chart_section": pl.String,
    "player_name": pl.String,
    "fangraphs_id": pl.String,
    "reference_service_time": pl.String,
    "reference_options_remaining": pl.Int64,
    "reference_rule5_status": pl.String,
    "reference_rule5_year": pl.Int64,
    "how_acquired": pl.String,
    "first_pro_year_text": pl.String,
    "source_snapshot_id": pl.String,
}

PLAYER_COLUMNS = (
    "PLAYER",
    "POSITION PLAYERS",
    "STARTING PITCHERS",
    "RELIEF PITCHERS",
    "PITCHERS",
)


def _text(value: object) -> str:
    if value is None or (isinstance(value, float) and isnan(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _service_time(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return _text(value)


def _control_reference(value: object) -> tuple[int | None, str, int | None]:
    if value is None or _text(value) == "":
        return None, "", None
    if isinstance(value, (float, int)):
        return int(value), "", None
    text = _text(value)
    if text.lower() in {"n/a", "na"}:
        return None, "", None
    if text.isdigit():
        return int(text), "", None
    if text.upper() == "R5":
        return None, "rule5_eligible", None
    match = re.fullmatch(r"Dec'(\d{2})", text, re.IGNORECASE)
    if match:
        return None, "rule5_not_yet_eligible", 2000 + int(match.group(1))
    return None, "unparsed", None


def normalize_fangraphs_depth_chart(
    sheets: Mapping[str, pl.DataFrame],
    *,
    team_name: str,
    season: int,
    source_snapshot_id: str,
) -> pl.DataFrame:
    """Create one comparison row per depth-chart player."""

    rows: list[dict[str, object]] = []
    for section, original in sheets.items():
        frame = original.rename({column: str(column) for column in original.columns})
        player_column = next((column for column in PLAYER_COLUMNS if column in frame.columns), None)
        if player_column is None:
            raise ValueError(f"depth-chart section {section} has no player column")
        control_column = next(
            (column for column in ("Options or R5 Status", "Options") if column in frame.columns),
            None,
        )
        for source in frame.iter_rows(named=True):
            player_name = _text(source[player_column])
            if not player_name:
                continue
            options, rule5_status, rule5_year = _control_reference(
                source.get(control_column) if control_column else None
            )
            rows.append(
                {
                    "season": season,
                    "team_name": team_name,
                    "depth_chart_section": section,
                    "player_name": player_name,
                    "fangraphs_id": _text(source.get("playerId")),
                    "reference_service_time": _service_time(source.get("MLB Service Time")),
                    "reference_options_remaining": options,
                    "reference_rule5_status": rule5_status,
                    "reference_rule5_year": rule5_year,
                    "how_acquired": _text(source.get("HOW ACQUIRED")),
                    "first_pro_year_text": _text(source.get("Year")),
                    "source_snapshot_id": source_snapshot_id,
                }
            )
    result = pl.DataFrame(rows, schema=DEPTH_CHART_REFERENCE_SCHEMA)
    duplicate_ids = (
        result.filter(pl.col("fangraphs_id") != "")
        .group_by("fangraphs_id")
        .len()
        .filter(pl.col("len") > 1)
    )
    if duplicate_ids.height:
        raise ValueError("depth chart has duplicate nonblank FanGraphs IDs")
    if result.group_by("player_name").len().filter(pl.col("len") > 1).height:
        raise ValueError("depth chart has duplicate player names")
    return result.sort(["depth_chart_section", "player_name"])


def read_fangraphs_depth_chart_xlsx(path: Path) -> dict[str, pl.DataFrame]:
    """Read a depth-chart workbook using the same optional xlsx boundary."""

    return read_fangraphs_payroll_xlsx(path)
