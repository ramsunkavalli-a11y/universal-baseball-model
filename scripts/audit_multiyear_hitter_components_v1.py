"""Inventory completed-season component evidence; never open current-season outcomes."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file

OLD = Path("C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated")
OUT = Path("reports/generated/multiyear-hitter-components-v1")
SOURCES = {
    "milb_origin_fielding": OLD / "milb-fielding-origin-inventory/tables/milb_fielding_usage_at_origins.parquet",
    "affiliated_fielding_2025": OLD / "position-capacity-source/2025/reports/generated/position-role-2025-confirmation-source/tables/position_role_2025_fielding_usage.parquet",
    "mlb_fielding": OLD / "mlb-fielding-outcome-inventory-2004-2025/tables/mlb_fielding_usage_2004_2025.parquet",
    "affiliated_fielding": OLD / "position-capacity-source/historical/reports/generated/position-role-historical-source/tables/historical_fielding_usage.parquet",
    "mlb_batting": OLD / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet",
    "panel": Path("reports/generated/multiyear-hitter-v1/panel.parquet"),
    "targets": Path("reports/generated/multiyear-hitter-v1/targets.parquet"),
    "catcher": Path("reports/generated/hitter-catcher-defense-value-v2/public-catcher-history-2022-2025.parquet"),
    "catcher_predictions": Path("reports/generated/hitter-catcher-defense-value-v2/component-predictions.parquet"),
    "one_year_components": Path("reports/generated/hitter-value-components-chronological-v2/chronological-predictions.parquet"),
    "infield_effects": Path("reports/generated/pbp-infield-range-re24-v1/player-position-season-effects.parquet"),
    "outfield_effects": Path("reports/generated/pbp-outfield-range-re24-v1/player-position-season-effects.parquet"),
    "runner_effects": Path("reports/generated/pbp-runner-re24-v1/runner-season-effects.parquet"),
    "range_actual_2025": Path("reports/generated/hitter-general-defense-value-v2/actual-defense-by-position.parquet"),
    "mlb_range_2025": Path("reports/generated/defense-v1-2025-target-source/tables/general_range_targets_2025.parquet"),
}


def audit():
    report = {}
    for name, path in SOURCES.items():
        if not path.exists():
            report[name] = {"path": str(path), "exists": False}
            continue
        schema = pl.read_parquet_schema(path)
        year = next((c for c in ("season", "origin_year", "target_year", "target_season") if c in schema), None)
        frame = pl.scan_parquet(path)
        if year:
            frame = frame.filter(pl.col(year) <= 2025)
        frame = frame.collect()
        row = {"path": str(path), "sha256": sha256_file(path), "rows": frame.height,
               "columns": list(schema), "year_column": year}
        if year:
            row["by_year"] = frame.group_by(year).len().sort(year).to_dicts()
        for c in ("position_abbreviation", "position", "component", "level_group"):
            if c in frame.columns:
                row[c] = frame[c].unique().sort().to_list()
        report[name] = row
        print(name, frame.shape, row.get("by_year"), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "source-audit.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    audit()
