#!/usr/bin/env python
"""Materialize complete source-only 2019 MiLB Hitter v2 outcomes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import download_file, sha256_file
from universal_baseball.current_talent_contact_value_source import (
    attach_narrative_terminal_groups,
    project_terminal_pa_descriptions,
)
from universal_baseball.current_talent_milb_source import derive_player_game_league_map
from universal_baseball.hitter_v2_outcomes import (
    OFFICIAL_BATTING_FIELDS,
    aggregate_player_season_outcomes,
    aggregate_projected_terminal_pas,
    assemble_player_game_outcomes,
    assert_outcome_invariants,
    project_official_player_game_outcomes,
    project_terminal_pa_identities,
    resolve_official_player_game_outcomes,
)
from universal_baseball.storage import write_canonical_parquet


SEASON = 2019
LEVELS = ("aaa", "aa", "a+", "a", "rk")
LEVEL_GROUP = {
    "aaa": "AAA",
    "aa": "AA",
    "a+": "HIGH_A",
    "a": "SINGLE_A",
    "rk": "ROOKIE_COMPLEX",
}
PINNED_PERIODS = {
    "aaa": (3, 4, 5, 6, 7, 8, 9, 10),
    "aa": (4, 5, 6, 7, 8, 9),
    "a+": (4, 5, 6, 7, 8, 9),
    "a": (4, 5, 6, 7, 8, 9),
    "rk": (6, 7, 8, 9),
}
PBP_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "game_type",
    "batter",
    "des",
    "description",
)
PLAYER_GAME_COLUMNS = (
    "game_id",
    "game_date",
    "game_type",
    "league_id",
    "team_id",
    "player_id",
    *OFFICIAL_BATTING_FIELDS,
)


@dataclass(frozen=True, slots=True)
class HistoricalAssetSpec:
    name: str
    filename_period: int
    browser_download_url: str
    family: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=SEASON)
    parser.add_argument("--levels", nargs="+", choices=LEVELS, default=list(LEVELS))
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-historical-materialization/milb"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-historical-materialization/milb"),
    )
    return parser.parse_args()


def _pinned_assets(level: str, family: str) -> list[HistoricalAssetSpec]:
    if family not in {"pbp", "game_player_stats"}:
        raise ValueError(f"unsupported historical asset family: {family}")
    suffix = "pbp" if family == "pbp" else "player_game_stats"
    return [
        HistoricalAssetSpec(
            name=f"{SEASON}_{period}_{level}_{suffix}.csv",
            filename_period=period,
            browser_download_url=(
                "https://github.com/armstjc/milb-data-repository/releases/download/"
                f"{family}/{SEASON}_{period}_{level}_{suffix}.csv"
            ),
            family=family,
        )
        for period in PINNED_PERIODS[level]
    ]


def _download(asset: Any, destination: Path) -> dict[str, Any]:
    retrieval: dict[str, Any] | str
    if not destination.exists() or destination.stat().st_size <= 0:
        retrieval = download_file(
            asset.browser_download_url,
            destination,
            timeout_seconds=600,
        )
    else:
        retrieval = "reused_local_quarantine"
    return {
        "selection_authority": "sha256_pinned_2019_inventory_period_set",
        "name": asset.name,
        "family": asset.family,
        "filename_period": int(asset.filename_period),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "retrieval": retrieval,
    }


def _scan_text_columns(path: Path, columns: tuple[str, ...]) -> pl.DataFrame:
    return (
        pl.scan_csv(
            path,
            infer_schema=False,
            null_values=["", "NA", "NaN", "null", "None"],
            truncate_ragged_lines=False,
        )
        .select(list(columns))
        .collect()
    )


def _load_player_games(
    assets: list[HistoricalAssetSpec],
    *,
    root: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    raw_frames: list[pl.DataFrame] = []
    projected_frames: list[pl.DataFrame] = []
    records: list[dict[str, Any]] = []
    for asset in assets:
        path = root / asset.name
        records.append(_download(asset, path))
        raw = _scan_text_columns(path, PLAYER_GAME_COLUMNS)
        raw_frames.append(raw)
        projected_frames.append(
            project_official_player_game_outcomes(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type="R",
            )
        )
    raw_combined = pl.concat(raw_frames, how="vertical_relaxed")
    league_map, league_metrics = derive_player_game_league_map(
        raw_combined.select("game_id", "league_id", "game_type"),
        game_type="R",
    )
    official, official_metrics = resolve_official_player_game_outcomes(
        pl.concat(projected_frames, how="vertical_relaxed")
    )
    return official, league_map, {
        "asset_count": len(records),
        "assets": records,
        "raw_row_count": raw_combined.height,
        "league_authority": league_metrics,
        "official_resolution": official_metrics,
    }


def _load_terminal_contacts(
    assets: list[HistoricalAssetSpec],
    *,
    league_map: pl.DataFrame,
    root: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    frames: list[pl.DataFrame] = []
    records: list[dict[str, Any]] = []
    for asset in assets:
        path = root / asset.name
        records.append(_download(asset, path))
        frames.append(_scan_text_columns(path, PBP_COLUMNS))
    raw = pl.concat(frames, how="vertical_relaxed")
    terminal = attach_narrative_terminal_groups(
        project_terminal_pa_descriptions(raw, game_type="R")
    )
    empty_overlay = pl.DataFrame(
        schema={
            "game_pk": pl.Int64,
            "at_bat_index": pl.Int64,
            "player_id": pl.Int64,
            "league_id": pl.Int64,
        }
    )
    projected = project_terminal_pa_identities(raw, terminal, empty_overlay)
    counts, terminal_metrics = aggregate_projected_terminal_pas(projected, league_map)
    status_counts = {
        str(row["terminal_outcome_status"]): int(row["len"])
        for row in terminal.group_by("terminal_outcome_status").len().to_dicts()
    }
    return counts, {
        "asset_count": len(records),
        "assets": records,
        "raw_row_count": raw.height,
        "terminal_status_counts": dict(sorted(status_counts.items())),
        "repeated_terminal_snapshot_row_count": int(
            terminal.select((pl.col("raw_terminal_row_count") - 1).sum()).item() or 0
        ),
        **terminal_metrics,
    }


def _coverage(frame: pl.DataFrame) -> list[dict[str, Any]]:
    return (
        frame.group_by(["level_group", "league_id", "source_status"])
        .agg(
            pl.len().alias("player_game_rows"),
            pl.col("game_id").n_unique().alias("games"),
            pl.col("player_id").n_unique().alias("players"),
            pl.col("batting_PA").sum().alias("official_pa"),
            pl.col("accepted_terminal_pa").sum().alias("accounted_pa"),
            pl.col("observed_terminal_contact_count")
            .sum()
            .alias("pbp_terminal_contacts"),
        )
        .sort(["level_group", "league_id", "source_status"])
        .to_dicts()
    )


def main() -> int:
    args = parse_args()
    if int(args.season) != SEASON:
        raise ValueError("the frozen historical materialization gate authorizes 2019 only")
    levels = list(dict.fromkeys(args.levels))
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)
    table_root = args.report_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    frames: list[pl.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    for level in levels:
        pbp_assets = _pinned_assets(level, "pbp")
        player_game_assets = _pinned_assets(level, "game_player_stats")
        if {row.filename_period for row in pbp_assets} != {
            row.filename_period for row in player_game_assets
        }:
            raise RuntimeError(f"2019 {level} PBP/player-game period sets do not match")

        official, league_map, player_game_record = _load_player_games(
            player_game_assets,
            root=args.work_root / level.replace("+", "plus") / "player-game",
        )
        contacts, pbp_record = _load_terminal_contacts(
            pbp_assets,
            league_map=league_map,
            root=args.work_root / level.replace("+", "plus") / "pbp",
        )
        player_games = assemble_player_game_outcomes(
            official,
            contacts,
            season=SEASON,
            level_group=LEVEL_GROUP[level],
        )
        assert_outcome_invariants(player_games)
        frames.append(player_games)
        slice_artifact = write_canonical_parquet(
            player_games,
            table_root
            / f"hitter_v2_player_game_outcomes_2019_{level.replace('+', 'plus')}_milb.parquet",
            table_name=f"hitter_v2_player_game_outcomes_2019_{level}_milb",
        ).as_record()
        provenance.append(
            {
                "filename_level": level,
                "level_group": LEVEL_GROUP[level],
                "actual_league_ids": sorted(
                    int(value)
                    for value in player_games.get_column("league_id").drop_nulls().unique().to_list()
                ),
                "player_game_source": player_game_record,
                "pbp_source": pbp_record,
                "slice_storage": slice_artifact,
            }
        )
        print(
            json.dumps(
                {
                    "season": SEASON,
                    "level": level,
                    "rows": player_games.height,
                    "pa": int(player_games.get_column("batting_PA").sum() or 0),
                    "model_ready_rows": player_games.filter(
                        pl.col("source_status").str.starts_with("accepted")
                    ).height,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    combined = pl.concat(frames, how="vertical_relaxed").sort(
        ["season", "level_group", "league_id", "game_id", "player_id"]
    )
    assert_outcome_invariants(combined)
    player_seasons = aggregate_player_season_outcomes(combined)
    exceptions = combined.filter(~pl.col("source_status").str.starts_with("accepted"))
    model_ready = combined.filter(pl.col("source_status").str.starts_with("accepted"))

    game_artifact = write_canonical_parquet(
        combined,
        table_root / "hitter_v2_player_game_outcomes_2019_milb.parquet",
        table_name="hitter_v2_player_game_outcomes_2019_milb",
    ).as_record()
    season_artifact = write_canonical_parquet(
        player_seasons,
        table_root / "hitter_v2_player_season_outcomes_2019_milb.parquet",
        table_name="hitter_v2_player_season_outcomes_2019_milb",
    ).as_record()
    exception_artifact = write_canonical_parquet(
        exceptions,
        table_root / "hitter_v2_player_game_exceptions_2019_milb.parquet",
        table_name="hitter_v2_player_game_exceptions_2019_milb",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "program": "hitter_v2",
        "scope": "2019_milb_full_source_only",
        "authorization_commit": "9ea191c2d38b4d3bd506a60c369a6b2f213045f1",
        "source_inventory_report_sha256": "91e6cc5f7ff777eb574f0bbdcefe714fc5aab01b7852826e8386fff51f23c492",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "accepted": True,
        "totals": {
            "player_game_rows": combined.height,
            "model_ready_player_game_rows": model_ready.height,
            "failed_closed_player_game_rows": exceptions.height,
            "model_ready_rate": model_ready.height / combined.height if combined.height else None,
            "player_season_rows": player_seasons.height,
            "games": combined.get_column("game_id").n_unique(),
            "players": combined.get_column("player_id").n_unique(),
            "official_pa": int(combined.get_column("batting_PA").sum() or 0),
            "accounted_pa": int(combined.get_column("accepted_terminal_pa").sum() or 0),
            "actual_league_ids": sorted(
                int(value)
                for value in combined.get_column("league_id").drop_nulls().unique().to_list()
            ),
        },
        "coverage": _coverage(combined),
        "source_status_counts": {
            str(row["source_status"]): int(row["len"])
            for row in combined.group_by("source_status").len().sort("source_status").to_dicts()
        },
        "source_provenance": provenance,
        "storage": {
            "player_game": game_artifact,
            "player_season": season_artifact,
            "exceptions": exception_artifact,
        },
        "model_use_authorized": False,
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
