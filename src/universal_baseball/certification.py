"""Certification utilities for reusable baseball source files.

This module is intentionally narrow. It profiles a quarantined source file and
produces evidence about row grain, duplicates, scope, identity fields, and
measurement availability. It does not normalize the source into production
tables and it does not silently repair defects.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import polars as pl


ARMSTJC_PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")

TRACKING_FIELDS = (
    "release_speed",
    "release_pos_x",
    "release_pos_y",
    "release_pos_z",
    "plate_x",
    "plate_z",
    "pfx_x",
    "pfx_z",
    "release_spin_rate",
    "release_extension",
    "launch_speed",
    "launch_angle",
    "hc_x",
    "hc_y",
)

SCOPE_FIELDS = (
    "game_date",
    "game_year",
    "game_month",
    "league_id",
    "league_name",
    "league_level_id",
    "league_level_name",
)

EXPECTED_LEVEL_NAMES = {
    "aaa": {"triple-a"},
    "aa": {"double-a"},
    "a+": {"high-a"},
    "high-a": {"high-a"},
    "a": {"single-a"},
    "single-a": {"single-a"},
    "rk": {"rookie"},
    "rookie": {"rookie"},
}

EVENT_FIELDS = ("events", "type", "bb_type")


@dataclass(frozen=True)
class ReleaseSpec:
    """Expected scope and location of a reusable release asset."""

    source_name: str
    asset_name: str
    url: str
    expected_year: int | None = None
    expected_month: int | None = None
    expected_level: str | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(
    url: str,
    destination: Path,
    *,
    attempts: int = 3,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Download to a temporary file, then atomically promote it."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    if temporary.exists():
        temporary.unlink()

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(
                url,
                headers={"User-Agent": "universal-baseball-model/source-certification"},
            )
            with urlopen(request, timeout=timeout_seconds) as response, temporary.open(
                "wb"
            ) as output:
                resolved_url = response.geturl()
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)

            temporary.replace(destination)
            return {
                "retrieved_at_utc": utc_now_iso(),
                "resolved_url": resolved_url,
                "file_size_bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if temporary.exists():
                temporary.unlink()
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(f"failed to download {url!r} after {attempts} attempts") from last_error


def read_quarantined_csv(path: Path) -> pl.DataFrame:
    """Read source CSV without trusting upstream inferred types.

    Certification initially treats every source field as text. This prevents a
    parser's type inference from becoming an accidental normalization decision
    and makes historical schema drift easier to observe.
    """

    return pl.read_csv(
        path,
        infer_schema=False,
        null_values=["", "NA", "NaN", "null", "None"],
        truncate_ragged_lines=False,
    )


def _nonblank_expr(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (pl.col(column).str.strip_chars() != "")


def _blank_count(frame: pl.DataFrame, column: str) -> int | None:
    if column not in frame.columns:
        return None
    value = frame.select((~_nonblank_expr(column)).sum().alias("blank")).item()
    return int(value)


def _nonblank_fraction(frame: pl.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.height == 0:
        return None
    value = frame.select(_nonblank_expr(column).mean().alias("coverage")).item()
    return None if value is None else float(value)


def _distinct_values(
    frame: pl.DataFrame, column: str, *, limit: int = 200
) -> list[str] | None:
    if column not in frame.columns:
        return None

    values = (
        frame.select(pl.col(column).drop_nulls().unique().sort())
        .get_column(column)
        .to_list()
    )
    return [str(value) for value in values[:limit]]


def _normalized_label(value: str) -> str:
    return value.strip().lower().replace("–", "-").replace("—", "-")


def _scope_profile(frame: pl.DataFrame, spec: ReleaseSpec) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "expected": {
            "year": spec.expected_year,
            "month": spec.expected_month,
            "level": spec.expected_level,
        },
        "observed": {},
    }

    if "game_date" in frame.columns:
        dates = frame.get_column("game_date").drop_nulls()
        if len(dates):
            profile["observed"]["game_date_min"] = str(dates.min())
            profile["observed"]["game_date_max"] = str(dates.max())

    for column in SCOPE_FIELDS[1:]:
        values = _distinct_values(frame, column)
        if values is not None:
            profile["observed"][column] = values

    warnings: list[str] = []
    if spec.expected_year is not None and "game_year" in frame.columns:
        observed = set(_distinct_values(frame, "game_year") or [])
        if observed and observed != {str(spec.expected_year)}:
            warnings.append(
                f"expected game_year {spec.expected_year}, observed {sorted(observed)}"
            )

    if spec.expected_month is not None and "game_month" in frame.columns:
        observed = set(_distinct_values(frame, "game_month") or [])
        if observed and observed != {str(spec.expected_month)}:
            warnings.append(
                f"expected game_month {spec.expected_month}, observed {sorted(observed)}"
            )

    if spec.expected_level is not None and "league_level_name" in frame.columns:
        expected_key = _normalized_label(spec.expected_level)
        expected_names = EXPECTED_LEVEL_NAMES.get(expected_key)
        observed_names = {
            _normalized_label(value)
            for value in (_distinct_values(frame, "league_level_name") or [])
        }
        if expected_names is None:
            warnings.append(
                f"no level-taxonomy rule defined for expected level {spec.expected_level!r}"
            )
        elif observed_names and not observed_names.issubset(expected_names):
            warnings.append(
                "expected league_level_name "
                f"{sorted(expected_names)}, observed {sorted(observed_names)}"
            )

    profile["warnings"] = warnings
    return profile


def _grain_profile(frame: pl.DataFrame) -> dict[str, Any]:
    missing_key_columns = [
        column for column in ARMSTJC_PITCH_KEY if column not in frame.columns
    ]
    if missing_key_columns:
        return {
            "natural_key": list(ARMSTJC_PITCH_KEY),
            "missing_key_columns": missing_key_columns,
            "exact_duplicate_extra_rows": None,
            "duplicate_key_extra_rows": None,
            "conflicting_key_extra_rows": None,
            "duplicate_key_groups": None,
            "key_blank_counts": {},
        }

    exact_unique = frame.unique()
    key_unique = frame.unique(subset=list(ARMSTJC_PITCH_KEY))
    exact_duplicate_extra_rows = frame.height - exact_unique.height
    duplicate_key_extra_rows = frame.height - key_unique.height

    # After exact duplicates are removed, any remaining repeated natural key
    # implies two distinct payloads occupy the same claimed pitch grain.
    exact_then_key_unique = exact_unique.unique(subset=list(ARMSTJC_PITCH_KEY))
    conflicting_key_extra_rows = exact_unique.height - exact_then_key_unique.height

    duplicate_groups = (
        frame.group_by(list(ARMSTJC_PITCH_KEY))
        .len()
        .filter(pl.col("len") > 1)
        .height
    )

    return {
        "natural_key": list(ARMSTJC_PITCH_KEY),
        "missing_key_columns": [],
        "exact_duplicate_extra_rows": int(exact_duplicate_extra_rows),
        "duplicate_key_extra_rows": int(duplicate_key_extra_rows),
        "conflicting_key_extra_rows": int(conflicting_key_extra_rows),
        "duplicate_key_groups": int(duplicate_groups),
        "key_blank_counts": {
            column: _blank_count(frame, column) for column in ARMSTJC_PITCH_KEY
        },
    }


def _identity_profile(frame: pl.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in ("batter", "pitcher"):
        if column in frame.columns:
            result[column] = {
                "blank_rows": _blank_count(frame, column),
                "unique_nonblank_ids": int(
                    frame.select(pl.col(column).drop_nulls().n_unique()).item()
                ),
            }
        else:
            result[column] = {"missing_column": True}
    return result


def _tracking_profile(frame: pl.DataFrame) -> dict[str, Any]:
    return {
        column: {
            "present": column in frame.columns,
            "row_nonblank_fraction": _nonblank_fraction(frame, column),
        }
        for column in TRACKING_FIELDS
    }


def _event_profile(frame: pl.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in EVENT_FIELDS:
        if column not in frame.columns:
            result[column] = {"present": False}
            continue

        counts = (
            frame.group_by(column)
            .len()
            .sort("len", descending=True)
            .head(100)
            .to_dicts()
        )
        result[column] = {
            "present": True,
            "distinct_count": int(frame.select(pl.col(column).n_unique()).item()),
            "top_values": counts,
        }
    return result


def build_release_report(
    frame: pl.DataFrame,
    spec: ReleaseSpec,
    file_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a source-certification smoke report without repairing the data."""

    grain = _grain_profile(frame)
    scope = _scope_profile(frame, spec)

    warnings = list(scope["warnings"])
    if grain["missing_key_columns"]:
        warnings.append(
            "natural pitch key cannot be tested because key columns are missing"
        )
    if grain["exact_duplicate_extra_rows"]:
        warnings.append(
            f"found {grain['exact_duplicate_extra_rows']} exact duplicate extra rows"
        )
    if grain["conflicting_key_extra_rows"]:
        warnings.append(
            f"found {grain['conflicting_key_extra_rows']} distinct rows sharing a pitch key"
        )
    for column, count in grain["key_blank_counts"].items():
        if count:
            warnings.append(f"{count} rows have blank {column}")

    unique_games = (
        int(frame.select(pl.col("game_pk").drop_nulls().n_unique()).item())
        if "game_pk" in frame.columns
        else None
    )

    return {
        "report_schema_version": 1,
        "generated_at_utc": utc_now_iso(),
        "source": asdict(spec),
        "file": file_metadata,
        "shape": {
            "rows": int(frame.height),
            "columns": int(frame.width),
            "column_names": frame.columns,
            "unique_games": unique_games,
        },
        "scope": scope,
        "grain": grain,
        "identity": _identity_profile(frame),
        "tracking": _tracking_profile(frame),
        "events": _event_profile(frame),
        "assessment": {
            "source_state": "quarantined",
            "warnings": warnings,
            "note": (
                "This smoke report tests release integrity only. Passing it does not "
                "certify official statistical reconciliation or level taxonomy."
            ),
        },
    }


def markdown_summary(report: dict[str, Any]) -> str:
    grain = report["grain"]
    shape = report["shape"]
    warnings = report["assessment"]["warnings"]

    lines = [
        "# armstjc PBP release smoke report",
        "",
        f"- Asset: `{report['source']['asset_name']}`",
        f"- Rows: {shape['rows']:,}",
        f"- Columns: {shape['columns']:,}",
        f"- Unique games: {shape['unique_games']}",
        f"- Exact duplicate extra rows: {grain['exact_duplicate_extra_rows']}",
        f"- Duplicate natural-key extra rows: {grain['duplicate_key_extra_rows']}",
        f"- Conflicting natural-key extra rows: {grain['conflicting_key_extra_rows']}",
        f"- Duplicate natural-key groups: {grain['duplicate_key_groups']}",
        "",
        "## Assessment",
        "",
        f"State: **{report['assessment']['source_state']}**",
        "",
    ]

    if warnings:
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("No smoke-test warnings.")

    lines.extend(
        [
            "",
            report["assessment"]["note"],
            "",
            "This report intentionally does not repair or deduplicate the upstream file.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "armstjc_release_smoke.json"
    markdown_path = output_dir / "armstjc_release_smoke.md"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(markdown_summary(report), encoding="utf-8")
    return json_path, markdown_path
