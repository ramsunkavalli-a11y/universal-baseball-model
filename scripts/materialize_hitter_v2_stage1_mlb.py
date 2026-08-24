#!/usr/bin/env python3
"""Materialize source-only MLB Hitter v2 terminal outcomes for 2021–2023."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import io
import json
from pathlib import Path
import re
from typing import Any
import zipfile

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.hitter_v2_outcomes import (
    TERMINAL_OUTCOMES,
    aggregate_player_season_outcomes,
    assert_outcome_invariants,
    build_mlb_player_game_outcomes,
)
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import MlbTeamLeague
from universal_baseball.savant import (
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.storage import write_canonical_parquet


OWNER = "ramsunkavalli-a11y"
REPO = "universal-baseball-model"
ARTIFACTS = {
    2021: {
        "run_id": 31986504169,
        "name": "current-talent-historical-mlb-2021",
        "sha256": "8d1aae424cb287c0ae19ce8c6312fdf674ddd68d02d2192a2009941f3ac70363",
    },
    2022: {
        "run_id": 31988255280,
        "name": "current-talent-historical-mlb-2022",
        "sha256": "f376ca20ef40e9906a86118b87a4c6b3934bb6a963c28a226cb9b8b66663be8e",
    },
    2023: {
        "run_id": 31989561396,
        "name": "current-talent-historical-mlb-2023",
        "sha256": "4fde9a0a8774135bcea775bb369a3c4d484d53938a818c4c2bce803878e03d54",
    },
}
OFFICIAL_FIELD_MAP = {
    "batting_PA": "plateAppearances",
    "batting_AB": "atBats",
    "batting_H": "hits",
    "batting_2B": "doubles",
    "batting_3B": "triples",
    "batting_HR": "homeRuns",
    "batting_BB": "baseOnBalls",
    "batting_IBB": "intentionalWalks",
    "batting_HBP": "hitByPitch",
    "batting_SO": "strikeOuts",
    "batting_SF": "sacFlies",
    "batting_SH": "sacBunts",
    "batting_CI": "catchersInterference",
    "batting_GiDP": "groundIntoDoublePlay",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2021, 2022, 2023])
    parser.add_argument(
        "--work-root", type=Path, default=Path("data/quarantine/hitter-v2-stage1-mlb")
    )
    parser.add_argument(
        "--report-root", type=Path, default=Path("reports/generated/hitter-v2-stage1-mlb")
    )
    return parser.parse_args()


def _artifact(season: int, root: Path) -> tuple[bytes, dict[str, Any]]:
    registry = ARTIFACTS[season]
    path = root / "artifacts" / f"{registry['run_id']}-{registry['name']}.zip"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size <= 0:
        url = (
            f"https://nightly.link/{OWNER}/{REPO}/actions/runs/"
            f"{registry['run_id']}/{registry['name']}.zip"
        )
        download_file(url, path, timeout_seconds=600)
    content = path.read_bytes()
    digest = sha256(content).hexdigest()
    if digest != registry["sha256"]:
        raise RuntimeError(f"MLB artifact digest mismatch for {season}")
    return content, {
        **registry,
        "size_bytes": len(content),
        "digest_authority": "committed_certified_source_checkpoint",
    }


def _teams(archive: zipfile.ZipFile, season: int) -> tuple[list[MlbTeamLeague], pl.DataFrame]:
    names = [name for name in archive.namelist() if name.endswith(f"teams_{season}.json")]
    if len(names) != 1:
        raise RuntimeError(f"expected one MLB team authority for {season}")
    payload = json.loads(archive.read(names[0]))
    rows = [
        MlbTeamLeague(
            team_id=int(row["id"]),
            abbreviation=str(row["abbreviation"]),
            league_id=int(row["league"]["id"]),
            league_name=str(row["league"]["name"]),
        )
        for row in payload["teams"]
        if int(row.get("sport", {}).get("id", -1)) == 1
        and int(row.get("league", {}).get("id", -1)) in {103, 104}
    ]
    frame = pl.DataFrame([asdict(row) for row in rows])
    return rows, frame


def _savant(archive: zipfile.ZipFile, season: int) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    names = sorted(
        name
        for name in archive.namelist()
        if f"/{season}/raw/savant/savant_" in name and name.endswith(".csv")
    )
    if not names:
        raise RuntimeError(f"certified MLB artifact has no Savant chunks for {season}")
    frames: list[pl.DataFrame] = []
    records: list[dict[str, Any]] = []
    for name in names:
        content = archive.read(name)
        raw = read_savant_csv_bytes(content)
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        frames.append(projected)
        records.append(
            {
                "name": name,
                "size_bytes": len(content),
                "sha256": sha256(content).hexdigest(),
                "raw_rows": raw.height,
                "projected_rows": projected.height,
            }
        )
    combined = pl.concat(frames, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index", "pitch_number"]
    )
    return combined, records


def _official_backbone(archive: zipfile.ZipFile, season: int) -> pl.DataFrame:
    names = sorted(
        name
        for name in archive.namelist()
        if f"/{season}/raw/official/season-stats/stats_{season}_league_" in name
        and name.endswith(".json")
    )
    rows: list[dict[str, Any]] = []
    for name in names:
        match = re.search(r"_league_(\d+)_", name)
        if match is None:
            raise RuntimeError(f"cannot recover league from {name}")
        league_id = int(match.group(1))
        payload = json.loads(archive.read(name))
        for group in payload["stats"]:
            for split in group.get("splits", []):
                stat = split["stat"]
                rows.append(
                    {
                        "season": season,
                        "league_id": league_id,
                        "player_id": int(split["player"]["id"]),
                        **{
                            f"official_{output}": int(stat.get(source, 0))
                            for output, source in OFFICIAL_FIELD_MAP.items()
                        },
                    }
                )
    result = pl.DataFrame(rows)
    duplicate = result.group_by(["season", "league_id", "player_id"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise RuntimeError("MLB official backbone is not unique at player/league/season grain")
    return result


def _reconcile(player_games: pl.DataFrame, official: pl.DataFrame) -> pl.DataFrame:
    fields = list(OFFICIAL_FIELD_MAP)
    observed = player_games.group_by(["season", "league_id", "player_id"]).agg(
        *[pl.col(field).sum().alias(field) for field in fields]
    )
    joined = observed.join(
        official, on=["season", "league_id", "player_id"], how="full", coalesce=True
    )
    joined = joined.with_columns(
        *[
            (pl.col(field) - pl.col(f"official_{field}")).alias(f"{field}_residual")
            for field in fields
        ]
    )
    return joined.with_columns(
        pl.any_horizontal(
            [pl.col(f"{field}_residual") != 0 for field in fields]
        ).alias("has_mismatch"),
        pl.any_horizontal(
            [
                pl.col(f"{field}_residual") != 0
                for field in fields
                if field != "batting_GiDP"
            ]
        ).alias("has_blocking_mismatch"),
    ).sort(["season", "league_id", "player_id"])


def main() -> int:
    args = _parse_args()
    seasons = sorted(set(args.seasons))
    args.work_root.mkdir(parents=True, exist_ok=True)
    table_dir = args.report_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    player_game_frames: list[pl.DataFrame] = []
    official_frames: list[pl.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for season in seasons:
        content, artifact_record = _artifact(season, args.work_root)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            teams, team_frame = _teams(archive, season)
            savant, chunks = _savant(archive, season)
            assigned = assign_savant_actual_league(savant, teams)
            player_games, metrics = build_mlb_player_game_outcomes(assigned, team_frame)
            official = _official_backbone(archive, season)
        player_game_frames.append(player_games)
        official_frames.append(official)
        provenance.append({"season": season, "artifact": artifact_record, "savant": chunks})
        evidence.append({"season": season, **metrics})
        print(json.dumps({"season": season, **metrics}, sort_keys=True), flush=True)

    player_games = pl.concat(player_game_frames, how="vertical_relaxed")
    assert_outcome_invariants(player_games)
    player_seasons = aggregate_player_season_outcomes(player_games)
    comparison = _reconcile(player_games, pl.concat(official_frames, how="vertical_relaxed"))
    mismatches = comparison.filter(pl.col("has_mismatch"))
    blocking_mismatches = comparison.filter(pl.col("has_blocking_mismatch"))
    game_artifact = write_canonical_parquet(
        player_games,
        table_dir / "hitter_v2_player_game_outcomes_2021_2023_mlb.parquet",
        table_name="hitter_v2_player_game_outcomes_mlb",
    ).as_record()
    season_artifact = write_canonical_parquet(
        player_seasons,
        table_dir / "hitter_v2_player_season_outcomes_2021_2023_mlb.parquet",
        table_name="hitter_v2_player_season_outcomes_mlb",
    ).as_record()
    comparison_artifact = write_canonical_parquet(
        comparison,
        table_dir / "hitter_v2_official_season_reconciliation_2021_2023_mlb.parquet",
        table_name="hitter_v2_official_season_reconciliation_mlb",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 1,
        "scope": "mlb_2021_2023_source_only",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "taxonomy": list(TERMINAL_OUTCOMES),
        "accepted": blocking_mismatches.is_empty(),
        "totals": {
            "player_game_rows": player_games.height,
            "player_season_rows": player_seasons.height,
            "official_pa": int(player_games.get_column("batting_PA").sum()),
            "games": player_games.get_column("game_id").n_unique(),
            "players": player_games.get_column("player_id").n_unique(),
            "official_reconciliation_rows": comparison.height,
            "official_reconciliation_mismatch_rows": mismatches.height,
            "official_reconciliation_blocking_mismatch_rows": blocking_mismatches.height,
            "gidp_definition_diagnostic_mismatch_rows": comparison.filter(
                pl.col("batting_GiDP_residual") != 0
            ).height,
        },
        "evidence": evidence,
        "source_provenance": provenance,
        "storage": {
            "player_game": game_artifact,
            "player_season": season_artifact,
            "official_reconciliation": comparison_artifact,
        },
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    if not report["accepted"]:
        raise RuntimeError(
            "MLB Stage 1 failed required official season reconciliation: "
            f"{blocking_mismatches.height} rows"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
