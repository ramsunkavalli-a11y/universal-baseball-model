#!/usr/bin/env python3
"""Assemble checkpointed 2024 Hitter v2 MiLB source-only slices."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.hitter_v2_outcomes import (
    TERMINAL_OUTCOMES,
    aggregate_player_season_outcomes,
    assert_outcome_invariants,
)
from universal_baseball.storage import write_canonical_parquet


LEVEL_SLUGS = ("aaa", "aa", "aplus", "a", "rk")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slice-roots", nargs="+", type=Path, required=True)
    parser.add_argument("--source-work-root", type=Path, required=True)
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-2024-milb"),
    )
    return parser.parse_args()


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _find_slices(roots: list[Path]) -> dict[str, Path]:
    found: dict[str, list[Path]] = {level: [] for level in LEVEL_SLUGS}
    for root in roots:
        for level in LEVEL_SLUGS:
            found[level].extend(
                root.rglob(f"hitter_v2_player_game_outcomes_2024_{level}_milb.parquet")
            )
    result: dict[str, Path] = {}
    for level, paths in found.items():
        unique = sorted(set(path.resolve() for path in paths))
        if len(unique) != 1:
            raise RuntimeError(f"expected one 2024 {level} slice, found {unique}")
        result[level] = unique[0]
    return result


def _raw_manifest(root: Path) -> list[dict[str, Any]]:
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".csv", ".zip"}
        and not path.name.endswith(".part")
    )
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha(path),
        }
        for path in files
    ]


def main() -> int:
    args = _parse_args()
    slices = _find_slices(args.slice_roots)
    frames: list[pl.DataFrame] = []
    inputs: list[dict[str, Any]] = []
    for level in LEVEL_SLUGS:
        path = slices[level]
        frame = pl.read_parquet(path)
        if set(frame["season"].unique().to_list()) != {2024}:
            raise RuntimeError(f"2024 {level} slice has wrong season")
        frames.append(frame)
        inputs.append(
            {
                "level": level,
                "path": path.as_posix(),
                "row_count": frame.height,
                "sha256": _sha(path),
            }
        )

    player_games = pl.concat(frames, how="vertical").sort(
        ["season", "league_id", "game_id", "player_id"]
    )
    duplicate = (
        player_games.group_by(["season", "league_id", "game_id", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise RuntimeError("2024 MiLB checkpoint slices overlap at canonical grain")
    assert_outcome_invariants(player_games)
    player_seasons = aggregate_player_season_outcomes(player_games)
    model_ready = player_games.filter(pl.col("modeling_eligible"))
    exceptions = player_games.filter(~pl.col("modeling_eligible"))

    table_dir = args.report_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    game_artifact = write_canonical_parquet(
        player_games,
        table_dir / "hitter_v2_player_game_outcomes_2024_milb.parquet",
        table_name="hitter_v2_player_game_outcomes_milb",
    ).as_record()
    season_artifact = write_canonical_parquet(
        player_seasons,
        table_dir / "hitter_v2_player_season_outcomes_2024_milb.parquet",
        table_name="hitter_v2_player_season_outcomes_milb",
    ).as_record()
    exception_artifact = write_canonical_parquet(
        exceptions,
        table_dir / "hitter_v2_player_game_exceptions_2024_milb.parquet",
        table_name="hitter_v2_player_game_exceptions_milb",
    ).as_record()

    status_counts = (
        player_games.group_by(["season", "level_group", "source_status"])
        .agg(
            pl.len().alias("player_game_rows"),
            pl.col("batting_PA").sum().alias("official_pa"),
        )
        .sort(["season", "level_group", "source_status"])
        .to_dicts()
    )
    raw_manifest = _raw_manifest(args.source_work_root)
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "scope": "affiliated_milb_2024_disclosed_validation_source_only",
        "accepted": True,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "taxonomy": list(TERMINAL_OUTCOMES),
        "slice_inputs": inputs,
        "raw_source_manifest": raw_manifest,
        "raw_source_manifest_count": len(raw_manifest),
        "totals": {
            "player_game_rows": player_games.height,
            "model_ready_player_game_rows": model_ready.height,
            "failed_closed_player_game_rows": exceptions.height,
            "player_season_rows": player_seasons.height,
            "games": player_games["game_id"].n_unique(),
            "players": player_games["player_id"].n_unique(),
            "official_pa": int(player_games["batting_PA"].sum()),
            "model_ready_official_pa": int(model_ready["batting_PA"].sum()),
            "accepted_terminal_pa": int(player_games["accepted_terminal_pa"].sum()),
            "pbp_terminal_contacts": int(
                player_games["observed_terminal_contact_count"].sum()
            ),
        },
        "status_counts": status_counts,
        "storage": {
            "player_game": game_artifact,
            "player_season": season_artifact,
            "exceptions": exception_artifact,
        },
        "limitations": [
            "Game 774353 has no reusable same-game league authority and its exact official endpoint returned 404; its PBP terminal rows remain quarantined.",
            "Declared historical source-residual player-games remain failed closed rather than receiving guessed terminal outcomes.",
        ],
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
