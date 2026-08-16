#!/usr/bin/env python
"""Combine accepted 2024 MLB + all affiliated player-game evidence.

All source-specific components must have passed their own frozen-Performance
reconciliation before entering this script.  The output is the first complete
2024 universal game-evidence surface used by later leakage-safe snapshots.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.performance_level_config import PERFORMANCE_LEVEL_SPECS_2024
from universal_baseball.storage import write_canonical_parquet
from universal_baseball.universal_performance import UNIVERSAL_LEAGUE_IDS


SEASON = 2024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--milb-root", type=Path, required=True)
    parser.add_argument("--mlb-root", type=Path, required=True)
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-universal-game-evidence-2024"),
    )
    return parser.parse_args()


def _find_unique(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename} under {root}, found {len(matches)}: {matches}"
        )
    return matches[0]


def main() -> int:
    args = parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    table_dir = args.report_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    inputs: list[dict[str, str]] = []

    for level in PERFORMANCE_LEVEL_SPECS_2024:
        summary_path = _find_unique(
            args.milb_root, f"current_talent_game_summary_{SEASON}_{level}.parquet"
        )
        profile_path = _find_unique(
            args.milb_root, f"current_talent_game_profile_{SEASON}_{level}.parquet"
        )
        summaries.append(pl.read_parquet(summary_path))
        profiles.append(pl.read_parquet(profile_path))
        inputs.append(
            {"component": level, "summary_path": str(summary_path), "profile_path": str(profile_path)}
        )

    mlb_summary_path = _find_unique(
        args.mlb_root, f"current_talent_game_summary_{SEASON}_mlb.parquet"
    )
    mlb_profile_path = _find_unique(
        args.mlb_root, f"current_talent_game_profile_{SEASON}_mlb.parquet"
    )
    summaries.append(pl.read_parquet(mlb_summary_path))
    profiles.append(pl.read_parquet(mlb_profile_path))
    inputs.append(
        {
            "component": "mlb",
            "summary_path": str(mlb_summary_path),
            "profile_path": str(mlb_profile_path),
        }
    )

    summary, profile, metrics = combine_universal_player_game_evidence(
        summaries,
        profiles,
        expected_seasons={SEASON},
        require_all_universal_leagues=True,
    )
    observed = {
        int(value) for value in summary.get_column("league_id").unique().to_list()
    }
    if observed != set(UNIVERSAL_LEAGUE_IDS):
        raise RuntimeError(
            f"universal 2024 game-evidence league coverage mismatch: observed={sorted(observed)}"
        )

    summary_storage = write_canonical_parquet(
        summary,
        table_dir / f"current_talent_game_summary_{SEASON}_universal.parquet",
        table_name="current_talent_game_summary_universal",
    ).as_record()
    profile_storage = write_canonical_parquet(
        profile,
        table_dir / f"current_talent_game_profile_{SEASON}_universal.parquet",
        table_name="current_talent_game_profile_universal",
    ).as_record()

    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "inputs": inputs,
        "metrics": metrics,
        "observed_league_ids": sorted(observed),
        "expected_league_ids": sorted(UNIVERSAL_LEAGUE_IDS),
        "storage": {"summary": summary_storage, "profile": profile_storage},
        "accepted": True,
        "interpretation": (
            "Complete 2024 universal player-game observed Performance evidence for Current Talent "
            "snapshots. No talent estimate, translation, age adjustment, projection, or ranking."
        ),
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    text = "\n".join(
        [
            "# 2024 universal Current Talent game-evidence surface",
            "",
            f"- Player-games: {summary.height:,}",
            f"- PA: {metrics['total_plate_appearances']:,}",
            f"- Actual leagues: {metrics['actual_league_count']}",
            f"- Level groups: {', '.join(metrics['level_groups'])}",
            "- Universal league coverage: complete",
        ]
    )
    (args.report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
