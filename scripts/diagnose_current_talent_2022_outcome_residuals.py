#!/usr/bin/env python
"""Localize the six sparse 2022 player-game vs season-aggregate residuals.

This is a certification diagnostic, not a production repair path.  It fetches
current official MLB Stats API ``gameLog`` hitting splits only for the six
player × actual-league rows identified by the independent 2022 outcome-backbone
audit.  Reusable player-game rows are resolved with the production chronology
rules, then compared game-by-game where official game identity is available.

The diagnostic must never inject a season-end residual into an earlier game. It
exists to classify whether a discrepancy is a mutable player-game revision,
season-aggregate revision, official representation difference, or unresolved
source-history issue.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory


SEASON = 2022
GAME_TYPE = "R"
CASES = (
    {"level": "aaa", "sport_id": 11, "league_id": 117, "player_id": 592261},
    {"level": "a", "sport_id": 14, "league_id": 110, "player_id": 702112},
    {"level": "a", "sport_id": 14, "league_id": 122, "player_id": 700998},
    {"level": "a", "sport_id": 14, "league_id": 123, "player_id": 686577},
    {"level": "rk", "sport_id": 16, "league_id": 124, "player_id": 695467},
    {"level": "rk", "sport_id": 16, "league_id": 130, "player_id": 800313},
)
FIELD_MAP = {
    "plateAppearances": "batting_PA",
    "baseOnBalls": "batting_BB",
    "hitByPitch": "batting_HBP",
    "strikeOuts": "batting_SO",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer():
        return None
    return int(numeric)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _game_log_endpoint(player_id: int, sport_id: int) -> str:
    params = {
        "stats": "gameLog",
        "group": "hitting",
        "season": SEASON,
        "sportId": int(sport_id),
    }
    return f"people/{int(player_id)}/stats?{urlencode(params)}"


def _official_game_splits(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stats_group in payload.get("stats") or []:
        group = _mapping(stats_group)
        for raw_split in group.get("splits") or []:
            split = _mapping(raw_split)
            game = _mapping(split.get("game"))
            league = _mapping(split.get("league"))
            team = _mapping(split.get("team"))
            sport = _mapping(split.get("sport"))
            stat = _mapping(split.get("stat"))
            game_pk = _int(game.get("gamePk"))
            if game_pk is None:
                game_pk = _int(game.get("pk"))
            if game_pk is None:
                game_pk = _int(game.get("id"))
            rows.append(
                {
                    "game_pk": game_pk,
                    "date": _text(split.get("date")),
                    "is_home": split.get("isHome"),
                    "league_id": _int(league.get("id")),
                    "league_name": _text(league.get("name")),
                    "team_id": _int(team.get("id")),
                    "team_name": _text(team.get("name")),
                    "sport_id": _int(sport.get("id")),
                    "sport_name": _text(sport.get("name")),
                    "plateAppearances": _int(stat.get("plateAppearances")),
                    "baseOnBalls": _int(stat.get("baseOnBalls")),
                    "hitByPitch": _int(stat.get("hitByPitch")),
                    "strikeOuts": _int(stat.get("strikeOuts")),
                    "split_keys": sorted(str(key) for key in split.keys()),
                    "game_keys": sorted(str(key) for key in game.keys()),
                    "stat_keys": sorted(str(key) for key in stat.keys()),
                }
            )
    return rows


def _load_resolved_level(level: str, work_root: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no {SEASON} {level} player-game assets found")
    raw_dir = work_root / level
    raw_dir.mkdir(parents=True, exist_ok=True)
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
                game_type=GAME_TYPE,
            )
        )
    resolved, metrics = resolve_milb_player_game_outcomes(
        pl.concat(frames, how="vertical_relaxed")
    )
    if metrics["unresolved_player_game_count"]:
        raise RuntimeError(
            f"{SEASON} {level} has unresolved player-game rows; diagnostic would be ambiguous"
        )
    return resolved, {"asset_names": [asset.name for asset in assets], **metrics}


def _sum_source(rows: pl.DataFrame) -> dict[str, int]:
    return {
        field: int(rows.get_column(field).fill_null(0).sum() or 0)
        for field in FIELD_MAP.values()
    }


def _sum_official(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        official_field: sum(int(row.get(official_field) or 0) for row in rows)
        for official_field in FIELD_MAP
    }


def main() -> int:
    work_root = Path("data/quarantine/current-talent-2022-outcome-residual-diagnostic")
    report_root = Path("reports/generated/current-talent-2022-outcome-residual-diagnostic")
    work_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    by_level: dict[str, tuple[pl.DataFrame, dict[str, Any]]] = {}
    for level in sorted({str(case["level"]) for case in CASES}):
        by_level[level] = _load_resolved_level(level, work_root)

    session = new_official_session()
    case_reports: list[dict[str, Any]] = []
    game_rows: list[dict[str, Any]] = []
    try:
        for case in CASES:
            level = str(case["level"])
            player_id = int(case["player_id"])
            league_id = int(case["league_id"])
            sport_id = int(case["sport_id"])
            source_all = by_level[level][0]
            source = source_all.filter(
                (pl.col("player_id") == player_id)
                & (pl.col("league_id") == league_id)
                & pl.col("batting_PA").is_not_null()
                & (pl.col("batting_PA") > 0)
            )
            source_games = {
                int(value) for value in source.get_column("game_id").unique().to_list()
            }
            endpoint = _game_log_endpoint(player_id, sport_id)
            capture = capture_official_json(endpoint, session=session)
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official gameLog for player {player_id} is not an object")
            official_all = _official_game_splits(capture.data)
            official_by_game = {
                int(row["game_pk"]): row
                for row in official_all
                if row.get("game_pk") is not None
            }
            duplicate_official_games = len(official_by_game) != sum(
                1 for row in official_all if row.get("game_pk") is not None
            )

            common_games = sorted(source_games & set(official_by_game))
            source_only_games = sorted(source_games - set(official_by_game))
            official_only_games = sorted(set(official_by_game) - source_games)
            common_differences: list[dict[str, Any]] = []
            for game_pk in common_games:
                source_row = source.filter(pl.col("game_id") == game_pk).row(0, named=True)
                official_row = official_by_game[game_pk]
                differences: dict[str, dict[str, int]] = {}
                for official_field, source_field in FIELD_MAP.items():
                    source_value = int(source_row[source_field] or 0)
                    official_value = int(official_row.get(official_field) or 0)
                    if source_value != official_value:
                        differences[source_field] = {
                            "source": source_value,
                            "official": official_value,
                        }
                game_rows.append(
                    {
                        "level": level,
                        "league_id": league_id,
                        "player_id": player_id,
                        "game_pk": game_pk,
                        "source_game_date": str(source_row.get("game_date")),
                        "official_date": official_row.get("date"),
                        "source_PA": int(source_row["batting_PA"] or 0),
                        "official_PA": int(official_row.get("plateAppearances") or 0),
                        "source_BB": int(source_row["batting_BB"] or 0),
                        "official_BB": int(official_row.get("baseOnBalls") or 0),
                        "source_HBP": int(source_row["batting_HBP"] or 0),
                        "official_HBP": int(official_row.get("hitByPitch") or 0),
                        "source_SO": int(source_row["batting_SO"] or 0),
                        "official_SO": int(official_row.get("strikeOuts") or 0),
                        "difference_count": len(differences),
                    }
                )
                if differences:
                    common_differences.append(
                        {"game_pk": game_pk, "differences": differences}
                    )

            target_official_rows = [
                row
                for row in official_all
                if row.get("league_id") == league_id
            ]
            case_reports.append(
                {
                    **case,
                    "endpoint": endpoint,
                    "official_snapshot_sha256": capture.content_sha256,
                    "official_split_count": len(official_all),
                    "official_split_with_game_pk_count": sum(
                        1 for row in official_all if row.get("game_pk") is not None
                    ),
                    "official_duplicate_game_pk": duplicate_official_games,
                    "official_split_example": official_all[:2],
                    "source_game_count": len(source_games),
                    "common_game_count": len(common_games),
                    "source_only_game_ids": source_only_games,
                    "official_only_game_ids": official_only_games,
                    "common_game_difference_count": len(common_differences),
                    "common_game_differences": common_differences,
                    "source_totals": _sum_source(source),
                    "official_target_league_split_count": len(target_official_rows),
                    "official_target_league_totals": _sum_official(target_official_rows),
                    "official_all_sport_totals": _sum_official(official_all),
                }
            )
    finally:
        session.close()

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "case_count": len(CASES),
        "cases": case_reports,
        "source_level_resolution": {
            level: metrics for level, (_, metrics) in by_level.items()
        },
        "interpretation": (
            "Certification diagnostic only. Official game logs are used to localize sparse source "
            "residuals; no source or historical predictor is mutated by this report."
        ),
    }
    (report_root / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    if game_rows:
        pl.DataFrame(game_rows).sort(["level", "league_id", "player_id", "game_pk"]).write_csv(
            report_root / "common_game_comparison.csv"
        )

    lines = [
        "# 2022 Current Talent sparse outcome residual diagnostic",
        "",
    ]
    for case in case_reports:
        lines.append(
            f"- {case['level']} league={case['league_id']} player={case['player_id']}: "
            f"source_games={case['source_game_count']}; official_splits={case['official_split_count']}; "
            f"common_games={case['common_game_count']}; "
            f"common_game_differences={case['common_game_difference_count']}; "
            f"source_only={len(case['source_only_game_ids'])}; "
            f"official_only={len(case['official_only_game_ids'])}"
        )
    text = "\n".join(lines)
    (report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
