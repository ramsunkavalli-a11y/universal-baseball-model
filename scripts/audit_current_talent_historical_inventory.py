#!/usr/bin/env python
"""Inventory historical MiLB source overlap needed for Current Talent snapshots.

Metadata only: no CSV downloads and no claim that file presence equals model
certification. The output is used to choose the first historical seasons worth
deep materialization/audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.current_talent_history import summarize_historical_source_coverage
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-inventory"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    pbp_assets = fetch_pbp_asset_inventory()
    player_game_assets = fetch_player_game_asset_inventory()
    report = summarize_historical_source_coverage(pbp_assets, player_game_assets)
    report["raw_inventory"] = {
        "recognized_pbp_asset_count": len(pbp_assets),
        "recognized_player_game_asset_count": len(player_game_assets),
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    cells = report["year_level_cells"]
    lines = [
        "# Current Talent historical MiLB source inventory",
        "",
        f"- Recognized PBP assets: {len(pbp_assets):,}",
        f"- Recognized player-game assets: {len(player_game_assets):,}",
        f"- Observed years: {report['observed_years'][0] if report['observed_years'] else 'none'}"
        f"–{report['observed_years'][-1] if report['observed_years'] else 'none'}",
        "- Complete current-level years with both source families: "
        + ", ".join(str(year) for year in report["complete_all_level_years"]),
        "",
        "## Recent year × level coverage",
        "",
    ]
    recent_years = set(report["observed_years"][-8:])
    for row in cells:
        if row["year"] not in recent_years:
            continue
        lines.append(
            f"- {row['year']} {row['filename_level']}: "
            f"PBP={row['pbp_asset_count']} assets/{row['pbp_periods']}; "
            f"player-game={row['player_game_asset_count']} assets/{row['player_game_periods']}; "
            f"both={row['has_both_source_families']}"
        )
    lines.extend(
        [
            "",
            "Inventory overlap only; deeper source semantics, league mapping, chronology, and "
            "Performance reconciliation remain required before a year enters model training.",
        ]
    )
    text = "\n".join(lines)
    (args.report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
