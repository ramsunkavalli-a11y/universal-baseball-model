#!/usr/bin/env python3
"""Materialize 2019-2020 MLB outcomes from already-certified cached sources."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_historical_mlb_outcomes import (
    summarize_historical_mlb_terminal_outcomes,
)
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import MlbTeamLeague
from universal_baseball.savant import (
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-historical-materialization/mlb"),
    )
    parser.add_argument(
        "--certification-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-historical-materialization/mlb"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-gap-aware-history/mlb"),
    )
    return parser.parse_args()


def _teams(path: Path) -> list[MlbTeamLeague]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for team in payload.get("teams") or []:
        league = team.get("league") or {}
        rows.append(
            MlbTeamLeague(
                team_id=int(team["id"]),
                abbreviation=str(team["abbreviation"]),
                league_id=int(league["id"]),
                league_name=str(league["name"]),
            )
        )
    return rows


def _load_season(root: Path, season: int) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    captures = []
    frames = []
    for path in sorted((root / str(season) / "raw" / "savant").glob("*.csv")):
        content = path.read_bytes()
        projected = project_savant_performance_rows(
            read_savant_csv_bytes(content), regular_season_only=True
        )
        captures.append(
            {
                "path": str(path),
                "sha256": sha256(content).hexdigest(),
                "bytes": len(content),
                "projected_rows": projected.height,
            }
        )
        if not projected.is_empty():
            frames.append(projected)
    if not frames:
        raise RuntimeError(f"no cached historical MLB source for {season}")
    combined = pl.concat(frames, how="vertical_relaxed").sort(
        "game_date", "game_pk", "at_bat_index", "pitch_number"
    )
    duplicates = (
        combined.group_by("game_pk", "at_bat_index", "pitch_number")
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise RuntimeError(f"duplicate cached pitch keys for {season}")
    return combined, captures


def _official_totals(root: Path, season: int) -> dict[str, int]:
    totals = {
        "PA": 0,
        "BB": 0,
        "IBB": 0,
        "HBP": 0,
        "K": 0,
        "H": 0,
        "2B": 0,
        "3B": 0,
        "HR": 0,
        "SF": 0,
        "SH": 0,
        "GIDP": 0,
    }
    fields = {
        "PA": "plateAppearances",
        "BB": "baseOnBalls",
        "IBB": "intentionalWalks",
        "HBP": "hitByPitch",
        "K": "strikeOuts",
        "H": "hits",
        "2B": "doubles",
        "3B": "triples",
        "HR": "homeRuns",
        "SF": "sacFlies",
        "SH": "sacBunts",
        "GIDP": "groundIntoDoublePlay",
    }
    for path in sorted(
        (root / str(season) / "raw" / "official" / "season-stats").glob("*.json")
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for block in payload.get("stats") or []:
            for split in block.get("splits") or []:
                stat = split.get("stat") or {}
                for name, field in fields.items():
                    totals[name] += int(stat[field])
    return totals


def main() -> int:
    args = _args()
    all_outcomes = []
    season_reports = []
    for season in (2019, 2020):
        certification_path = args.certification_root / str(season) / "report.json"
        certification = json.loads(certification_path.read_text(encoding="utf-8"))
        if not certification["accepted"] or not certification["reconciliation"][
            "exact_outcome_reconciliation"
        ]:
            raise RuntimeError(f"historical MLB season {season} is not certified")
        savant, captures = _load_season(args.source_root, season)
        team_path = (
            args.source_root / str(season) / "raw" / "official" / f"teams_{season}.json"
        )
        assigned = assign_savant_actual_league(savant, _teams(team_path))
        outcomes = summarize_historical_mlb_terminal_outcomes(assigned)
        official = _official_totals(args.source_root, season)
        observed = {
            "PA": int(outcomes["terminal_pa"].sum()),
            "BB": int((outcomes["UBB"] + outcomes["IBB"]).sum()),
            "IBB": int(outcomes["IBB"].sum()),
            "HBP": int(outcomes["HBP"].sum()),
            "K": int(outcomes["K"].sum()),
            "H": int(
                (outcomes["1B"] + outcomes["2B"] + outcomes["3B"] + outcomes["HR"]).sum()
            ),
            "2B": int(outcomes["2B"].sum()),
            "3B": int(outcomes["3B"].sum()),
            "HR": int(outcomes["HR"].sum()),
            "SF": int(outcomes["SF"].sum()),
            "SH": int(
                assigned.filter(
                    pl.col("is_plate_appearance_terminal")
                    & pl.col("events").is_in(["sac_bunt", "sac_bunt_double_play"])
                ).height
            ),
            "GIDP": int(outcomes["MULTI_OUT"].sum()),
        }
        exact_fields = ["PA", "BB", "IBB", "HBP", "K", "H", "2B", "3B", "HR", "SH"]
        mismatches = {
            field: observed[field] - official[field]
            for field in exact_fields
            if observed[field] != official[field]
        }
        if mismatches:
            raise RuntimeError(f"{season} historical terminal outcome mismatch: {mismatches}")
        all_outcomes.append(outcomes)
        season_reports.append(
            {
                "season": season,
                "players": outcomes["player_id"].n_unique(),
                "player_league_rows": outcomes.height,
                "terminal_pa": observed["PA"],
                "hitter_talent_pa": int(outcomes["hitter_talent_pa"].sum()),
                "official_exact_fields": exact_fields,
                "official_exact": True,
                "terminal_SF_minus_official_SF_diagnostic": observed["SF"] - official["SF"],
                "multi_out_minus_official_GIDP_diagnostic": observed["GIDP"] - official["GIDP"],
                "source_chunk_count": len(captures),
                "source_captures": captures,
                "certification_report": {
                    "path": str(certification_path),
                    "sha256": sha256_file(certification_path),
                },
            }
        )
    combined = pl.concat(all_outcomes, how="vertical_relaxed").sort(
        "season", "league_id", "player_id"
    )
    artifact = write_canonical_parquet(
        combined,
        args.report_root / "tables" / "hitter_v2_historical_mlb_outcomes_2019_2020.parquet",
        table_name="hitter_v2_historical_mlb_outcomes_2019_2020",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "accepted_exact_official_terminal_outcomes",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "seasons": season_reports,
        "storage": artifact,
        "interpretation": "Historical MLB predictor evidence only; MULTI_OUT versus official GIDP remains diagnostic because the terminal taxonomy includes all multi-out results.",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
