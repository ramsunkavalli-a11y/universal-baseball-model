#!/usr/bin/env python3
"""Inventory frozen Player Value inputs without fitting or scoring models."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl


INTERESTING = (
    "player", "season", "year", "fold", "projection", "predicted", "probability",
    "profile", "plate", "pa", "outs", "position", "dh", "range", "throw",
    "block", "fram", "skill", "run", "attempt", "success", "advance", "opportun",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_record(path: Path, root: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    frame = pl.read_parquet(path) if suffix == ".parquet" else pl.read_csv(path, infer_schema_length=10000)
    columns = list(frame.columns)
    record: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "format": suffix.removeprefix("."),
        "rows": frame.height,
        "columns": columns,
        "candidate_columns": [
            column for column in columns if any(token in column.lower() for token in INTERESTING)
        ],
    }
    for column in ("player_id", "batter_id", "season", "current_season", "next_season", "target_year"):
        if column not in columns:
            continue
        series = frame.get_column(column).drop_nulls()
        record.setdefault("column_diagnostics", {})[column] = {
            "non_null": series.len(),
            "unique": series.n_unique(),
            "min": series.min() if series.len() else None,
            "max": series.max() if series.len() else None,
        }
    return record


def json_record(path: Path, root: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "format": "json",
    }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        record["read_error"] = f"{type(exc).__name__}: {exc}"
        return record
    record["top_level_keys"] = sorted(payload) if isinstance(payload, dict) else []
    provenance: dict[str, Any] = {}

    def visit(value: Any, dotted: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                path_key = f"{dotted}.{key}" if dotted else key
                if any(token in key.lower() for token in ("run_id", "artifact", "digest", "sha256", "source_sha")) and not isinstance(child, (dict, list)):
                    provenance[path_key] = child
                visit(child, path_key)
        elif isinstance(value, list):
            for index, child in enumerate(value[:100]):
                visit(child, f"{dotted}[{index}]")

    visit(payload)
    record["provenance_values"] = provenance
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.input_root
    manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            if path.suffix.lower() in {".parquet", ".csv"}:
                records.append(table_record(path, root))
            elif path.suffix.lower() == ".json":
                records.append(json_record(path, root))
            else:
                records.append({
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                    "format": path.suffix.lower().removeprefix("") or "binary",
                })
        except Exception as exc:
            records.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "read_error": f"{type(exc).__name__}: {exc}",
            })

    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_mlb_centering_source_inventory_completed",
        "boundary": {
            "model_fit": False,
            "model_selection": False,
            "model_scoring": False,
            "component_runs_calculated": False,
            "centering_constant_calculated": False,
            "park_audit_opened": False,
            "war_calculated": False,
        },
        "source_manifest": manifest,
        "file_count": len(records),
        "files": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"file_count": len(records), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


