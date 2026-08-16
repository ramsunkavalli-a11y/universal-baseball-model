#!/usr/bin/env python
"""Diagnose one historical MiLB outcome residual without mutating source history.

This utility is intentionally narrow. It materializes reusable player-game
outcomes for one configured player × league × season case, reproduces the
season-aggregate residual, captures the player's official season gameLog, and
then checks the exact reusable source game IDs against current official MLB
Stats API boxscores.

The report is evidence for deciding whether a game-level fallback can be
certified. It never repairs or inserts historical rows.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    OUTCOME_FIELDS,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_official_outcomes import (
    official_game_log_endpoint,
    project_official_hitting_game_log,
)
from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory
from universal_baseball.season_stat_assets import (
    fetch_season_stat_asset_inventory,
    select_season_stat_asset,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats


SEASON = 2021
LEVEL = "rk"
LEAGUE_ID = 130
PLAYER_ID = 703595
SPORT_ID = 16
GAME_TYPE = "R"

OFFICIAL_FIELD_MAP = {
    "plateAppearances": "batting_PA",
    "atBats": "batting_AB",
    "baseOnBalls": "batting_BB",
    "hitByPitch": "batting_HBP",
    "strikeOuts": "batting_SO",
    "sacFlies": "batting_SF",
    "sacBunts": "batting_SH",
    "catchersInterference": "batting_CI",
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
    return int(numeric) if numeric.is_integer() else None


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-residual-case/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _sum_outcomes(frame: pl.DataFrame) -> dict[str, int]:
    return {
        field: int(frame.get_column(field).fill_null(0).sum() or 0)
        for field in OUTCOME_FIELDS
    }


def _project_player_from_boxscore(
    payload: Mapping[str, Any],
    *,
    game_id: int,
    player_id: int,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    teams = _mapping(payload.get("teams"))
    for side in ("home", "away"):
        team = _mapping(teams.get(side))
        players = _mapping(team.get("players"))
        for value in players.values():
            player = _mapping(value)
            person = _mapping(player.get("person"))
            if _int(person.get("id")) != int(player_id):
                continue
            stats = _mapping(player.get("stats"))
            batting = _mapping(stats.get("batting"))
            matches.append(
                {
                    "game_id": int(game_id),
                    "player_id": int(player_id),
                    "side": side,
                    "team_id": _int(_mapping(team.get("team")).get("id")),
                    "player_name": person.get("fullName"),
                    **{
                        outcome_field: _int(batting.get(official_field))
                        for official_field, outcome_field in OFFICIAL_FIELD_MAP.items()
                    },
                }
            )
    if len(matches) > 1:
        raise RuntimeError(
            f"official boxscore contains multiple player matches for player={player_id} game={game_id}"
        )
    if matches:
        return {"found": True, **matches[0]}
    return {
        "found": False,
        "game_id": int(game_id),
        "player_id": int(player_id),
        "side": None,
        "team_id": None,
        "player_name": None,
        **{field: None for field in OUTCOME_FIELDS},
    }


def main() -> int:
    work_root = Path("data/quarantine/current-talent-outcome-residual-case")
    report_root = Path("reports/generated/current-talent-outcome-residual-case")
    player_game_dir = work_root / "player-game"
    season_dir = work_root / "season"
    raw_boxscore_dir = report_root / "official-game-boxscore-raw"
    raw_gamelog_dir = report_root / "official-gamelog-raw"
    for path in (work_root, report_root, player_game_dir, season_dir, raw_boxscore_dir, raw_gamelog_dir):
        path.mkdir(parents=True, exist_ok=True)

    github_session = _github_session()
    try:
        assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=github_session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        if not assets:
            raise RuntimeError("no reusable player-game assets found for diagnostic case")
        frames: list[pl.DataFrame] = []
        for asset in assets:
            path = player_game_dir / asset.name
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
        resolved, resolution_metrics = resolve_milb_player_game_outcomes(
            pl.concat(frames, how="vertical_relaxed")
        )
        if resolution_metrics["unresolved_player_game_count"]:
            raise RuntimeError("diagnostic source has unresolved player-game rows")

        season_inventory = fetch_season_stat_asset_inventory("batting", session=github_session)
        season_asset = select_season_stat_asset(
            season_inventory,
            year=SEASON,
            filename_level=LEVEL,
            kind="batting",
            require_nonempty=True,
        )
        season_path = season_dir / season_asset.name
        if not season_path.exists() or season_path.stat().st_size <= 0:
            download_file(season_asset.browser_download_url, season_path, timeout_seconds=240)
        season_raw = read_quarantined_csv(season_path)
        season_stats, season_schema_metrics = standardize_armstjc_season_stats(
            season_raw, "batting"
        )
    finally:
        github_session.close()

    source = resolved.filter(
        (pl.col("player_id") == PLAYER_ID)
        & (pl.col("league_id") == LEAGUE_ID)
        & (pl.col("game_type") == GAME_TYPE)
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    ).sort("game_id")
    if source.is_empty():
        raise RuntimeError("diagnostic source target has no positive-PA games")
    source.write_csv(report_root / "source_player_games.csv")

    comparison, reconciliation_metrics = reconcile_resolved_outcomes_to_season_aggregates(
        resolved,
        season_stats,
        season=SEASON,
        require_exact=False,
    )
    residual = comparison.filter(
        (pl.col("player_id") == PLAYER_ID) & (pl.col("league_id") == LEAGUE_ID)
    )
    if residual.height != 1:
        raise RuntimeError(f"expected one target season comparison row, found {residual.height}")
    residual.write_csv(report_root / "season_residual.csv")

    official_session = new_official_session()
    try:
        gamelog_endpoint = official_game_log_endpoint(
            player_id=PLAYER_ID,
            sport_id=SPORT_ID,
            season=SEASON,
        )
        gamelog_capture = capture_official_json(gamelog_endpoint, session=official_session)
        gamelog_capture.write_raw(
            raw_gamelog_dir / f"player_{PLAYER_ID}_sport_{SPORT_ID}_gamelog.json"
        )
        if not isinstance(gamelog_capture.data, Mapping):
            raise RuntimeError("official gameLog diagnostic response is not an object")
        projected_gamelog = project_official_hitting_game_log(
            gamelog_capture.data,
            player_id=PLAYER_ID,
            sport_id=SPORT_ID,
        )

        boxscore_rows: list[dict[str, Any]] = []
        boxscore_snapshots: list[dict[str, Any]] = []
        for game_id in source.get_column("game_id").unique().sort().to_list():
            game_id = int(game_id)
            endpoint = f"game/{game_id}/boxscore"
            capture = capture_official_json(endpoint, session=official_session)
            capture.write_raw(raw_boxscore_dir / f"game_{game_id}_boxscore.json")
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official boxscore for game {game_id} is not an object")
            boxscore_rows.append(
                _project_player_from_boxscore(
                    capture.data,
                    game_id=game_id,
                    player_id=PLAYER_ID,
                )
            )
            boxscore_snapshots.append(
                {
                    "game_id": game_id,
                    "endpoint": capture.endpoint,
                    "url": capture.url,
                    "retrieved_at_utc": capture.retrieved_at_utc.isoformat(),
                    "content_sha256": capture.content_sha256,
                }
            )
    finally:
        official_session.close()

    boxscore = pl.DataFrame(boxscore_rows, strict=False).sort("game_id")
    boxscore.write_csv(report_root / "official_boxscore_player_games.csv")
    comparison_games = source.select(
        "game_id",
        "game_date",
        "league_id",
        "player_id",
        *OUTCOME_FIELDS,
    ).join(
        boxscore.select(
            "game_id",
            pl.col("found").alias("official_found"),
            pl.col("team_id").alias("official_team_id"),
            *[
                pl.col(field).alias(f"official_{field}")
                for field in OUTCOME_FIELDS
            ],
        ),
        on="game_id",
        how="left",
    )
    comparison_games.write_csv(report_root / "source_vs_official_boxscore.csv")

    found = boxscore.filter(pl.col("found") == True)  # noqa: E712
    official_complete = found.filter(
        ~pl.any_horizontal([pl.col(field).is_null() for field in OUTCOME_FIELDS])
    )
    source_totals = _sum_outcomes(source)
    official_totals = _sum_outcomes(official_complete) if not official_complete.is_empty() else {
        field: 0 for field in OUTCOME_FIELDS
    }
    residual_row = residual.row(0, named=True)
    season_vector = {
        "batting_PA": int(residual_row["season_plate_appearances"]),
        "batting_BB": int(residual_row["season_walks"]),
        "batting_HBP": int(residual_row["season_hit_by_pitch"]),
        "batting_SO": int(residual_row["season_strikeouts"]),
    }
    source_reconciliation_vector = {
        "batting_PA": int(residual_row["game_plate_appearances"]),
        "batting_BB": int(residual_row["game_walks"]),
        "batting_HBP": int(residual_row["game_hit_by_pitch"]),
        "batting_SO": int(residual_row["game_strikeouts"]),
    }

    report = {
        "report_schema_version": 1,
        "case": {
            "season": SEASON,
            "level": LEVEL,
            "league_id": LEAGUE_ID,
            "player_id": PLAYER_ID,
            "sport_id": SPORT_ID,
        },
        "source": {
            "asset_names": [asset.name for asset in assets],
            "resolution": resolution_metrics,
            "positive_pa_game_count": int(source.height),
            "game_ids": [int(v) for v in source.get_column("game_id").to_list()],
            "totals": source_totals,
            "reconciliation_vector": source_reconciliation_vector,
        },
        "season_aggregate": {
            "asset": season_asset.as_record(),
            "schema": season_schema_metrics,
            "vector": season_vector,
            "reconciliation_metrics": reconciliation_metrics,
            "differences_game_minus_season": {
                "batting_PA": int(residual_row["plate_appearances_difference"]),
                "batting_BB": int(residual_row["walks_difference"]),
                "batting_HBP": int(residual_row["hit_by_pitch_difference"]),
                "batting_SO": int(residual_row["strikeouts_difference"]),
            },
        },
        "official_player_gamelog": {
            "endpoint": gamelog_capture.endpoint,
            "content_sha256": gamelog_capture.content_sha256,
            "projected_row_count": int(projected_gamelog.height),
        },
        "official_game_boxscores": {
            "requested_game_count": int(source.get_column("game_id").n_unique()),
            "player_found_game_count": int(found.height),
            "complete_vector_game_count": int(official_complete.height),
            "totals_across_complete_found_games": official_totals,
            "snapshots": boxscore_snapshots,
        },
        "interpretation": (
            "Diagnostic only. A game-boxscore fallback is eligible for further certification only "
            "if every source positive-PA game has one complete official player batting vector and "
            "the resulting totals resolve the independent season residual without inventing chronology."
        ),
    }
    (report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    text = "\n".join(
        [
            "# Current Talent historical outcome residual case diagnostic",
            "",
            f"- Case: {SEASON} {LEVEL} league={LEAGUE_ID} player={PLAYER_ID}",
            f"- Source positive-PA games: {source.height}",
            f"- Player gameLog projected rows: {projected_gamelog.height}",
            f"- Official boxscore player matches: {found.height}/{source.get_column('game_id').n_unique()}",
            f"- Complete official boxscore vectors: {official_complete.height}/{source.get_column('game_id').n_unique()}",
            f"- Source reconciliation vector: {source_reconciliation_vector}",
            f"- Season aggregate vector: {season_vector}",
            f"- Official boxscore totals: {official_totals}",
        ]
    )
    (report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
