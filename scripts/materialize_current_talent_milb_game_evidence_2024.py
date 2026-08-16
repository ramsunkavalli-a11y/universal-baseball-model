#!/usr/bin/env python
"""Materialize one 2024 affiliated level at Current Talent player-game grain.

For one armstjc filename level this script reuses the certified Performance
contact/participant path, resolves chronology-safe player-game outcome snapshots,
and requires exact roll-up reconciliation to the frozen 2024 Performance artifact.
No talent estimation or cross-level translation occurs here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

import build_batting_performance_level_poc as performance
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    build_milb_current_talent_player_game_evidence,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_reconciliation import (
    reconcile_player_game_to_performance,
)
from universal_baseball.performance_level_config import performance_level_spec_2024
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, choices=LEVELS)
    parser.add_argument("--performance-root", type=Path, required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-milb-game-evidence-2024"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-milb-game-evidence-2024"),
    )
    return parser.parse_args()


def _find_unique(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename} under {root}, found {len(matches)}: {matches}"
        )
    return matches[0]


def _load_current_outcomes(
    *,
    level: str,
    work_dir: Path,
    league_ids: frozenset[int],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    raw_dir = work_dir / "player-game"
    raw_dir.mkdir(parents=True, exist_ok=True)
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {SEASON} {level} player-game assets found")

    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        frames.append(
            project_milb_player_game_outcomes(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type="R",
            )
        )
        del raw

    observations = pl.concat(frames, how="vertical_relaxed")
    resolved, metrics = resolve_milb_player_game_outcomes(observations)
    if metrics["unresolved_player_game_count"]:
        raise RuntimeError(
            f"{level} Current Talent outcome evidence has unresolved player-game snapshots: "
            f"{metrics['unresolved_player_game_count']}"
        )

    eligible = resolved.filter(
        (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    observed = {
        int(value)
        for value in eligible.get_column("league_id").drop_nulls().unique().to_list()
    }
    if observed != set(league_ids):
        raise RuntimeError(
            f"{level} Current Talent actual-league coverage mismatch: observed={sorted(observed)}, "
            f"expected={sorted(league_ids)}"
        )
    return resolved, {"asset_count": len(assets), "asset_names": [a.name for a in assets], **metrics}


def main() -> int:
    args = parse_args()
    spec = performance_level_spec_2024(args.level)
    work_dir = args.work_root / args.level
    report_dir = args.report_root / args.level
    table_dir = report_dir / "tables"
    reconciliation_dir = report_dir / "reconciliation"
    for path in (work_dir, table_dir, reconciliation_dir):
        path.mkdir(parents=True, exist_ok=True)

    contacts, contact_metrics = performance._load_reusable_contacts(
        args.level, spec.league_ids, work_dir
    )
    contact_controls, control_metrics = performance._load_player_game_controls(
        args.level, spec.league_ids, work_dir
    )
    authorized, authority_metrics, _ = performance._participant_authority_and_false_negative_gate(
        contacts,
        contact_controls,
        unflagged_sample_games=0,
    )
    classified = performance._classify_contacts(authorized)

    resolved_outcomes, outcome_metrics = _load_current_outcomes(
        level=args.level,
        work_dir=work_dir,
        league_ids=spec.league_ids,
    )
    summary, profile, evidence_metrics = build_milb_current_talent_player_game_evidence(
        resolved_outcomes,
        classified,
    )

    frozen_summary_path = _find_unique(
        args.performance_root, f"batting_performance_summary_{SEASON}_{args.level}.parquet"
    )
    frozen_profile_path = _find_unique(
        args.performance_root, f"batting_performance_bins_{SEASON}_{args.level}.parquet"
    )
    frozen_summary = pl.read_parquet(frozen_summary_path)
    frozen_profile = pl.read_parquet(frozen_profile_path)
    summary_comparison, bin_comparison, reconciliation = reconcile_player_game_to_performance(
        summary,
        profile,
        frozen_summary,
        frozen_profile,
        require_exact=False,
    )
    summary_mismatch = summary_comparison.filter(
        (pl.col("pa_difference") != 0) | (pl.col("core_event_difference") != 0)
    )
    bin_mismatch = bin_comparison.filter(pl.col("occurrence_difference") != 0)
    summary_mismatch.write_csv(reconciliation_dir / "summary_mismatches.csv")
    bin_mismatch.write_csv(reconciliation_dir / "bin_mismatches.csv")
    if not reconciliation["exact_reconciliation"]:
        raise RuntimeError(
            f"{args.level} game evidence failed frozen Performance reconciliation: "
            f"summary={reconciliation['summary_mismatch_row_count']}, "
            f"bins={reconciliation['profile_bin_mismatch_row_count']}"
        )

    summary_storage = write_canonical_parquet(
        summary,
        table_dir / f"current_talent_game_summary_{SEASON}_{args.level}.parquet",
        table_name=f"current_talent_game_summary_{args.level}",
    ).as_record()
    profile_storage = write_canonical_parquet(
        profile,
        table_dir / f"current_talent_game_profile_{SEASON}_{args.level}.parquet",
        table_name=f"current_talent_game_profile_{args.level}",
    ).as_record()

    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "display_name": spec.display_name,
        "league_ids": sorted(spec.league_ids),
        "source_contacts": contact_metrics,
        "contact_controls": control_metrics,
        "participant_authority": authority_metrics,
        "current_outcomes": outcome_metrics,
        "evidence": evidence_metrics,
        "frozen_performance": {
            "summary_path": str(frozen_summary_path),
            "profile_path": str(frozen_profile_path),
        },
        "reconciliation": reconciliation,
        "storage": {"summary": summary_storage, "profile": profile_storage},
        "accepted": bool(reconciliation["exact_reconciliation"]),
        "interpretation": (
            "Game-grain observed Performance evidence only; no talent estimate or level translation."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    text = "\n".join(
        [
            f"# {SEASON} Current Talent game evidence — {spec.display_name}",
            "",
            f"- Player-games: {summary.height:,}",
            f"- PA: {reconciliation['game_plate_appearances']:,}",
            f"- Actual leagues: {len(spec.league_ids)}",
            f"- Frozen Performance reconciliation: {reconciliation['exact_reconciliation']}",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
