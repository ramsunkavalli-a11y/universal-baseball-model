#!/usr/bin/env python3
"""Assemble the universal Hitter v2 Stage 1 source-only artifact."""

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--milb-player-game",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1/tables/"
            "hitter_v2_player_game_outcomes_2021_2023_milb.parquet"
        ),
    )
    parser.add_argument(
        "--mlb-player-game",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-mlb/tables/"
            "hitter_v2_player_game_outcomes_2021_2023_mlb.parquet"
        ),
    )
    parser.add_argument(
        "--milb-report",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage1/report.json"),
    )
    parser.add_argument(
        "--mlb-report",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage1-mlb/report.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage1-universal"),
    )
    return parser.parse_args()


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _coverage(frame: pl.DataFrame, dimensions: list[str]) -> list[dict[str, Any]]:
    return (
        frame.group_by(dimensions)
        .agg(
            pl.len().alias("player_game_rows"),
            pl.col("game_id").n_unique().alias("games"),
            pl.col("player_id").n_unique().alias("players"),
            pl.col("batting_PA").sum().alias("official_pa"),
            pl.col("batting_PA")
            .filter(pl.col("modeling_eligible"))
            .sum()
            .alias("model_ready_pa"),
            pl.col("modeling_eligible").sum().alias("model_ready_player_games"),
        )
        .sort(dimensions)
        .to_dicts()
    )


def main() -> int:
    args = _parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    table_dir = args.report_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    milb = pl.read_parquet(args.milb_player_game)
    mlb = pl.read_parquet(args.mlb_player_game)
    milb = milb.with_columns(pl.col("season").cast(pl.Int64))
    mlb = mlb.with_columns(pl.col("season").cast(pl.Int64))
    if milb.schema != mlb.schema:
        raise RuntimeError("MiLB and MLB Hitter v2 player-game schemas differ")
    player_games = pl.concat([milb, mlb], how="vertical").sort(
        ["season", "league_id", "game_id", "player_id"]
    )
    duplicate = (
        player_games.group_by(["season", "league_id", "game_id", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise RuntimeError("universal Hitter v2 player-game key is not unique")
    assert_outcome_invariants(player_games)
    player_seasons = aggregate_player_season_outcomes(player_games)
    season_duplicate = (
        player_seasons.group_by(["season", "league_id", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not season_duplicate.is_empty():
        raise RuntimeError("universal Hitter v2 player-season key is not unique")
    exceptions = player_games.filter(~pl.col("modeling_eligible"))
    model_ready = player_games.filter(pl.col("modeling_eligible"))
    game_artifact = write_canonical_parquet(
        player_games,
        table_dir / "hitter_v2_player_game_outcomes_2021_2023.parquet",
        table_name="hitter_v2_player_game_outcomes",
    ).as_record()
    season_artifact = write_canonical_parquet(
        player_seasons,
        table_dir / "hitter_v2_player_season_outcomes_2021_2023.parquet",
        table_name="hitter_v2_player_season_outcomes",
    ).as_record()
    exception_artifact = write_canonical_parquet(
        exceptions,
        table_dir / "hitter_v2_player_game_exceptions_2021_2023.parquet",
        table_name="hitter_v2_player_game_exceptions",
    ).as_record()
    milb_report = json.loads(args.milb_report.read_text(encoding="utf-8"))
    mlb_report = json.loads(args.mlb_report.read_text(encoding="utf-8"))
    official_pa = int(player_games.get_column("batting_PA").sum())
    model_ready_pa = int(model_ready.get_column("batting_PA").sum())
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 1,
        "status": "stage1_source_gate_complete_awaiting_review",
        "scope": "affiliated_pbp_and_mlb_2021_2023_source_only",
        "accepted": True,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "taxonomy": list(TERMINAL_OUTCOMES),
        "totals": {
            "player_game_rows": player_games.height,
            "player_season_rows": player_seasons.height,
            "games": player_games.get_column("game_id").n_unique(),
            "players": player_games.get_column("player_id").n_unique(),
            "official_pa": official_pa,
            "model_ready_player_game_rows": model_ready.height,
            "model_ready_official_pa": model_ready_pa,
            "model_ready_pa_rate": model_ready_pa / official_pa,
            "failed_closed_player_game_rows": exceptions.height,
            "failed_closed_official_pa": int(exceptions.get_column("batting_PA").sum()),
            "official_unique_repairs": int(
                model_ready.get_column("official_unique_repair_count").sum()
            ),
            "mlb_gidp_definition_diagnostic_mismatch_rows": int(
                mlb_report["totals"]["gidp_definition_diagnostic_mismatch_rows"]
            ),
        },
        "model_ready_outcome_counts": {
            outcome: int(model_ready.get_column(outcome).sum())
            for outcome in TERMINAL_OUTCOMES
        },
        "status_counts": (
            player_games.group_by(
                ["season", "level_group", "source_capability_tier", "source_status"]
            )
            .agg(
                pl.len().alias("player_game_rows"),
                pl.col("batting_PA").sum().alias("official_pa"),
            )
            .sort(["season", "level_group", "source_status"])
            .to_dicts()
        ),
        "coverage_by_season_level_capability": _coverage(
            player_games, ["season", "level_group", "source_capability_tier"]
        ),
        "coverage_by_season_league": _coverage(
            player_games, ["season", "league_id", "source_capability_tier"]
        ),
        "coverage_by_season_team": _coverage(
            player_games, ["season", "team_id", "source_capability_tier"]
        ),
        "source_inputs": {
            "milb_player_game": {
                "path": str(args.milb_player_game),
                "sha256": _sha(args.milb_player_game),
                "source_report_sha256": _sha(args.milb_report),
                "source_totals": milb_report["totals"],
            },
            "mlb_player_game": {
                "path": str(args.mlb_player_game),
                "sha256": _sha(args.mlb_player_game),
                "source_report_sha256": _sha(args.mlb_report),
                "source_totals": mlb_report["totals"],
            },
        },
        "storage": {
            "player_game": game_artifact,
            "player_season": season_artifact,
            "exceptions": exception_artifact,
        },
        "limitations": [
            "MiLB ambiguous non-hit terminal results remain failed closed and are excluded from model-ready counts while retained in official coverage denominators.",
            "MLB structured GIDP and official GIDP definitions differ on 40 player-league-season rows; the diagnostic is retained and does not alter the exhaustive batter terminal-outcome taxonomy.",
            "Raw event-grain source bytes remain in quarantine; distributable artifacts are canonical player-game/player-season aggregates and source hashes.",
        ],
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
