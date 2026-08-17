#!/usr/bin/env python3
"""Materialize MLB Challenger-2 target contacts from certified cached sources.

This source-only gate intentionally performs no network requests.  It consumes the
raw Savant chunks and MLB team authority already preserved inside the certified
historical Current Talent MLB artifacts, reuses the certified Savant projection /
league assignment / contact classifier, and writes the same target schema as the
accepted MiLB contact-value source.

Only 2021 and 2022 are permitted.  No terminal values, baseline fit, richer fit,
model score, or 2023 evidence is accessed here.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value_mlb_source import (
    DEVELOPMENT_SOURCE_SEASONS,
    materialize_mlb_contact_value_target_contacts,
)
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS, MlbTeamLeague
from universal_baseball.savant import project_savant_performance_rows, read_savant_csv_bytes
from universal_baseball.storage import write_canonical_parquet


CERTIFIED_HISTORY_RUN = {2021: 31986504169, 2022: 31988255280}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True, choices=sorted(DEVELOPMENT_SOURCE_SEASONS))
    parser.add_argument(
        "--history-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-mlb-game-evidence"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-mlb-source"),
    )
    return parser.parse_args()


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load_team_authority(path: Path) -> tuple[list[MlbTeamLeague], dict[str, Any]]:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"missing certified cached MLB team authority: {path}")
    content = path.read_bytes()
    payload = json.loads(content)
    rows: list[MlbTeamLeague] = []
    for team in payload.get("teams") or []:
        league = team.get("league") or {}
        league_id = league.get("id")
        if league_id not in MLB_LEAGUE_IDS:
            continue
        abbreviation = str(team.get("abbreviation") or "").strip()
        if not abbreviation:
            raise RuntimeError("cached MLB team authority contains blank abbreviation")
        rows.append(
            MlbTeamLeague(
                team_id=int(team["id"]),
                abbreviation=abbreviation,
                league_id=int(league_id),
                league_name=str(league.get("name") or ""),
            )
        )
    if len(rows) != 30:
        raise RuntimeError(f"expected 30 cached MLB AL/NL teams, found {len(rows)}")
    if len({row.abbreviation for row in rows}) != len(rows):
        raise RuntimeError("cached MLB team authority has duplicate abbreviations")
    return sorted(rows, key=lambda row: row.team_id), {
        "path": str(path),
        "sha256": sha256(content).hexdigest(),
        "byte_count": len(content),
        "team_count": len(rows),
    }


def _load_cached_savant(raw_dir: Path, *, season: int) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    paths = sorted(raw_dir.glob("savant_*.csv"))
    if not paths:
        raise RuntimeError(f"no certified cached Savant chunks found under {raw_dir}")

    frames: list[pl.DataFrame] = []
    captures: list[dict[str, Any]] = []
    for path in paths:
        content = path.read_bytes()
        if not content:
            raise RuntimeError(f"empty certified Savant chunk: {path}")
        raw = read_savant_csv_bytes(content)
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        frames.append(projected)
        captures.append(
            {
                "path": str(path),
                "sha256": sha256(content).hexdigest(),
                "byte_count": len(content),
                "raw_row_count": int(raw.height),
                "projected_regular_row_count": int(projected.height),
            }
        )

    nonempty = [frame for frame in frames if not frame.is_empty()]
    if not nonempty:
        raise RuntimeError(f"cached Savant chunks contain no regular-season rows for {season}")
    combined = pl.concat(nonempty, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index", "pitch_number"]
    )
    years = sorted(
        int(value)
        for value in combined.get_column("game_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    )
    if years != [int(season)]:
        raise RuntimeError(f"cached Savant season mismatch: observed={years}, expected={[season]}")
    duplicates = combined.group_by(["game_pk", "at_bat_index", "pitch_number"]).len().filter(
        pl.col("len") > 1
    )
    if not duplicates.is_empty():
        raise RuntimeError(
            f"cached Savant source contains {duplicates.height} duplicate canonical pitch keys"
        )
    return combined, captures


def _count_rows(frame: pl.DataFrame, column: str) -> dict[str, int]:
    if frame.is_empty():
        return {}
    return {
        str(row[column]): int(row["count"])
        for row in frame.group_by(column)
        .agg(pl.len().cast(pl.Int64).alias("count"))
        .sort(column)
        .to_dicts()
    }


def main() -> int:
    args = _parse_args()
    season = int(args.season)
    if season not in DEVELOPMENT_SOURCE_SEASONS:
        raise ValueError(f"MLB contact-value development source rejects season {season}")

    season_root = args.history_root / str(season)
    savant_dir = season_root / "raw" / "savant"
    teams_path = season_root / "raw" / "official" / f"teams_{season}.json"
    output_dir = args.output_root / str(season)
    table_dir = output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    savant, savant_captures = _load_cached_savant(savant_dir, season=season)
    teams, team_capture = _load_team_authority(teams_path)
    assigned = assign_savant_actual_league(savant, teams)
    target, metrics = materialize_mlb_contact_value_target_contacts(assigned)
    if target.is_empty():
        raise RuntimeError(f"MLB contact-value target is empty for {season}")
    observed_level = set(target.get_column("level_group").unique().to_list())
    if observed_level != {"MLB"}:
        raise RuntimeError(f"MLB contact-value target has unexpected level groups: {observed_level}")
    observed_leagues = {
        int(value) for value in target.get_column("league_id").unique().to_list()
    }
    if observed_leagues != set(MLB_LEAGUE_IDS):
        raise RuntimeError(
            f"MLB contact-value target lost AL/NL coverage: {sorted(observed_leagues)}"
        )

    parquet_path = table_dir / f"current_talent_contact_value_target_{season}_mlb.parquet"
    storage = write_canonical_parquet(
        target,
        parquet_path,
        table_name=f"current_talent_contact_value_target_{season}_mlb",
    ).as_record()
    target.write_csv(table_dir / f"current_talent_contact_value_target_{season}_mlb.csv")

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_mlb_source_materialization",
        "season": season,
        "accepted_source_materialization": True,
        "certified_history_seed_run_id": CERTIFIED_HISTORY_RUN[season],
        "source_boundary": {
            "offline_cached_historical_source": True,
            "network_requests_performed": False,
            "model_scoring": False,
            "accessed_2023": False,
            "terminal_values_attached": False,
            "baseline_fitted": False,
            "richer_residual_fitted": False,
        },
        "source": {
            "savant_chunk_count": len(savant_captures),
            "savant_projected_row_count": int(savant.height),
            "savant_captures": savant_captures,
            "team_authority": team_capture,
        },
        "materialization": metrics,
        "target": {
            "row_count": int(target.height),
            "game_count": int(target.get_column("game_pk").n_unique()),
            "player_count": int(target.get_column("player_id").n_unique()),
            "league_ids": sorted(observed_leagues),
            "level_groups": sorted(observed_level),
            "first_event_date": target.get_column("event_date").min().isoformat(),
            "last_event_date": target.get_column("event_date").max().isoformat(),
            "terminal_outcome_group_counts": _count_rows(target, "terminal_outcome_group"),
            "contact_bin_counts": _count_rows(target, "contact_bin"),
            "participant_authority_counts": _count_rows(target, "participant_authority"),
        },
        "storage": storage,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
