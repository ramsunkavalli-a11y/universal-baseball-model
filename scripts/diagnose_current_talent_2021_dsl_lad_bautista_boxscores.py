#!/usr/bin/env python
"""Audit 2021 DSL LAD Bautista player-game batting against official boxscores.

The independent armstjc Rookie season aggregate omits team 611 (DSL LAD
Bautista), so it cannot adjudicate that team's player-game chronology. This
script performs a diagnostic-only game-level audit against current official MLB
Stats API boxscores. It validates team/game batting totals, direct player IDs,
and identifies possible identity remaps only when an unmatched source row has a
unique official batter with the same complete outcome vector.

Nothing in this script mutates historical source rows or grants certification.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
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
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory


SEASON = 2021
LEVEL = "rk"
LEAGUE_ID = 130
TEAM_ID = 611
TEAM_NAME = "DSL LAD Bautista"
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
    session.headers["User-Agent"] = "universal-baseball-model-2021-bautista-boxscore-audit/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _vector(row: Mapping[str, Any]) -> tuple[int, ...] | None:
    values: list[int] = []
    for field in OUTCOME_FIELDS:
        value = row.get(field)
        if value is None:
            return None
        values.append(int(value))
    return tuple(values)


def _official_team_batters(
    payload: Mapping[str, Any],
    *,
    game_id: int,
    team_id: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    teams = _mapping(payload.get("teams"))
    matching_sides: list[str] = []
    for side in ("home", "away"):
        team = _mapping(teams.get(side))
        if _int(_mapping(team.get("team")).get("id")) != int(team_id):
            continue
        matching_sides.append(side)
        for raw_player in _mapping(team.get("players")).values():
            player = _mapping(raw_player)
            person = _mapping(player.get("person"))
            player_id = _int(person.get("id"))
            if player_id is None:
                continue
            batting = _mapping(_mapping(player.get("stats")).get("batting"))
            vector = {
                outcome_field: _int(batting.get(official_field))
                for official_field, outcome_field in OFFICIAL_FIELD_MAP.items()
            }
            if not vector["batting_PA"] or int(vector["batting_PA"]) <= 0:
                continue
            position = _mapping(player.get("position"))
            rows.append(
                {
                    "game_id": int(game_id),
                    "player_id": int(player_id),
                    "player_name": person.get("fullName"),
                    "team_id": int(team_id),
                    "side": side,
                    "batting_order": str(player.get("battingOrder") or "").strip() or None,
                    "position": position.get("abbreviation"),
                    **vector,
                }
            )
    if len(matching_sides) != 1:
        raise RuntimeError(
            f"official boxscore game={game_id} contains team={team_id} on {len(matching_sides)} sides"
        )
    return rows


def _metadata_value(values: set[str]) -> str | None:
    clean = {value for value in values if value}
    return next(iter(clean)) if len(clean) == 1 else None


def main() -> int:
    work_root = Path("data/quarantine/current-talent-2021-rk-team-residuals")
    player_game_dir = work_root / "player-game"
    report_root = Path("reports/generated/current-talent-outcome-residual-case")
    raw_official_dir = report_root / "official-team-611-boxscore-raw"
    for path in (work_root, player_game_dir, report_root, raw_official_dir):
        path.mkdir(parents=True, exist_ok=True)

    github_session = _github_session()
    metadata_sets: dict[tuple[int, int], dict[str, set[str]]] = defaultdict(
        lambda: {"player_name": set(), "batting_order": set(), "position": set()}
    )
    try:
        assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=github_session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        if not assets:
            raise RuntimeError("no reusable 2021 Rookie player-game assets found")

        outcome_frames: list[pl.DataFrame] = []
        team_map_frames: list[pl.DataFrame] = []
        for asset in assets:
            path = player_game_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            required = {
                "game_id",
                "game_type",
                "league_id",
                "player_id",
                "team_id",
                "team_name",
            }
            missing = sorted(required - set(raw.columns))
            if missing:
                raise RuntimeError(f"{asset.name} missing boxscore-audit fields: {missing}")

            team_map_frames.append(
                raw.select(
                    pl.col("game_id").cast(pl.Int64, strict=False),
                    pl.col("game_type").cast(pl.String),
                    pl.col("league_id").cast(pl.Int64, strict=False),
                    pl.col("player_id").cast(pl.Int64, strict=False),
                    pl.col("team_id").cast(pl.Int64, strict=False),
                    pl.col("team_name").cast(pl.String),
                )
            )
            target_raw = raw.filter(
                (pl.col("game_type").cast(pl.String) == GAME_TYPE)
                & (pl.col("league_id").cast(pl.Int64, strict=False) == LEAGUE_ID)
                & (pl.col("team_id").cast(pl.Int64, strict=False) == TEAM_ID)
                & pl.col("game_id").cast(pl.Int64, strict=False).is_not_null()
                & pl.col("player_id").cast(pl.Int64, strict=False).is_not_null()
            )
            name_col = "player_full_name" if "player_full_name" in target_raw.columns else None
            order_col = (
                "player_batitng_order"
                if "player_batitng_order" in target_raw.columns
                else "player_batting_order"
                if "player_batting_order" in target_raw.columns
                else None
            )
            position_col = "player_position" if "player_position" in target_raw.columns else None
            for raw_row in target_raw.iter_rows(named=True):
                game_id = _int(raw_row.get("game_id"))
                player_id = _int(raw_row.get("player_id"))
                if game_id is None or player_id is None:
                    continue
                values = metadata_sets[(game_id, player_id)]
                if name_col and raw_row.get(name_col) is not None:
                    values["player_name"].add(str(raw_row[name_col]).strip())
                if order_col and raw_row.get(order_col) is not None:
                    order_value = _int(raw_row.get(order_col))
                    if order_value is not None:
                        values["batting_order"].add(str(order_value))
                if position_col and raw_row.get(position_col) is not None:
                    values["position"].add(str(raw_row[position_col]).strip())

            outcome_frames.append(
                project_milb_player_game_outcomes(
                    raw,
                    source_asset=asset.name,
                    season=SEASON,
                    game_type=GAME_TYPE,
                )
            )
    finally:
        github_session.close()

    resolved, resolution_metrics = resolve_milb_player_game_outcomes(
        pl.concat(outcome_frames, how="vertical_relaxed")
    )
    if resolution_metrics["unresolved_player_game_count"]:
        raise RuntimeError("2021 Rookie has unresolved player-game outcomes")

    raw_team_map = (
        pl.concat(team_map_frames, how="vertical_relaxed")
        .filter(
            (pl.col("game_type") == GAME_TYPE)
            & (pl.col("league_id") == LEAGUE_ID)
            & pl.col("game_id").is_not_null()
            & pl.col("player_id").is_not_null()
            & pl.col("team_id").is_not_null()
        )
        .select("game_id", "player_id", "team_id", "team_name")
        .unique()
    )
    key_counts = raw_team_map.group_by(["game_id", "player_id"]).agg(
        pl.col("team_id").n_unique().alias("team_count")
    )
    valid_keys = key_counts.filter(pl.col("team_count") == 1).select("game_id", "player_id")
    team_map = (
        raw_team_map.join(valid_keys, on=["game_id", "player_id"], how="inner")
        .unique(["game_id", "player_id"], keep="first")
    )
    source = (
        resolved.filter(
            (pl.col("league_id") == LEAGUE_ID)
            & (pl.col("game_type") == GAME_TYPE)
            & pl.col("batting_PA").is_not_null()
            & (pl.col("batting_PA") > 0)
        )
        .join(team_map, on=["game_id", "player_id"], how="left")
        .filter(pl.col("team_id") == TEAM_ID)
        .sort(["game_id", "player_id"])
    )
    if source.is_empty():
        raise RuntimeError("no resolved positive-PA source rows found for team 611")
    source.write_csv(report_root / "team_611_source_player_games.csv")

    metadata_rows: list[dict[str, Any]] = []
    for row in source.select("game_id", "player_id").iter_rows(named=True):
        key = (int(row["game_id"]), int(row["player_id"]))
        values = metadata_sets.get(
            key, {"player_name": set(), "batting_order": set(), "position": set()}
        )
        metadata_rows.append(
            {
                "game_id": key[0],
                "player_id": key[1],
                "source_player_name": _metadata_value(values["player_name"]),
                "source_batting_order": _metadata_value(values["batting_order"]),
                "source_position": _metadata_value(values["position"]),
                "source_name_conflict": len({v for v in values["player_name"] if v}) > 1,
                "source_order_conflict": len({v for v in values["batting_order"] if v}) > 1,
                "source_position_conflict": len({v for v in values["position"] if v}) > 1,
            }
        )
    metadata = pl.DataFrame(metadata_rows, strict=False)
    source_with_metadata = source.join(metadata, on=["game_id", "player_id"], how="left")
    source_with_metadata.write_csv(report_root / "team_611_source_player_games_with_metadata.csv")

    official_rows: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    official_session = new_official_session()
    try:
        for game_id in source.get_column("game_id").unique().sort().to_list():
            game_id = int(game_id)
            capture = capture_official_json(f"game/{game_id}/boxscore", session=official_session)
            capture.write_raw(raw_official_dir / f"game_{game_id}_boxscore.json")
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official boxscore game={game_id} is not an object")
            rows = _official_team_batters(capture.data, game_id=game_id, team_id=TEAM_ID)
            if not rows:
                raise RuntimeError(f"official boxscore game={game_id} has no positive-PA team 611 hitters")
            official_rows.extend(rows)
            snapshots.append(
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

    official = pl.DataFrame(official_rows, strict=False).sort(["game_id", "player_id"])
    official.write_csv(report_root / "team_611_official_boxscore_player_games.csv")

    source_dict = {
        (int(row["game_id"]), int(row["player_id"])): row
        for row in source_with_metadata.iter_rows(named=True)
    }
    official_dict = {
        (int(row["game_id"]), int(row["player_id"])): row
        for row in official.iter_rows(named=True)
    }
    if len(official_dict) != official.height:
        raise RuntimeError("official team-611 boxscore rows are not unique by game/player")

    direct_rows: list[dict[str, Any]] = []
    source_only_keys = sorted(set(source_dict) - set(official_dict))
    official_only_keys = sorted(set(official_dict) - set(source_dict))
    for key in sorted(set(source_dict) & set(official_dict)):
        source_row = source_dict[key]
        official_row = official_dict[key]
        source_vector = _vector(source_row)
        official_vector = _vector(official_row)
        direct_rows.append(
            {
                "game_id": key[0],
                "player_id": key[1],
                "source_player_name": source_row.get("source_player_name"),
                "official_player_name": official_row.get("player_name"),
                "source_batting_order": source_row.get("source_batting_order"),
                "official_batting_order": official_row.get("batting_order"),
                "source_position": source_row.get("source_position"),
                "official_position": official_row.get("position"),
                "complete_vectors": source_vector is not None and official_vector is not None,
                "vector_equal": source_vector is not None and source_vector == official_vector,
            }
        )
    direct = pl.DataFrame(direct_rows, strict=False)
    direct.write_csv(report_root / "team_611_direct_identity_comparison.csv")

    official_by_game: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in official.iter_rows(named=True):
        official_by_game[int(row["game_id"])].append(row)

    remap_candidates: list[dict[str, Any]] = []
    for key in source_only_keys:
        source_row = source_dict[key]
        source_vector = _vector(source_row)
        vector_matches = [
            row
            for row in official_by_game[key[0]]
            if (key[0], int(row["player_id"])) in official_only_keys
            and source_vector is not None
            and _vector(row) == source_vector
        ]
        source_order = source_row.get("source_batting_order")
        source_position = source_row.get("source_position")
        for candidate in vector_matches:
            order_match = (
                source_order is not None
                and candidate.get("batting_order") is not None
                and str(source_order) == str(candidate.get("batting_order"))
            )
            position_match = (
                source_position is not None
                and candidate.get("position") is not None
                and str(source_position) == str(candidate.get("position"))
            )
            remap_candidates.append(
                {
                    "game_id": key[0],
                    "source_player_id": key[1],
                    "source_player_name": source_row.get("source_player_name"),
                    "source_batting_order": source_order,
                    "source_position": source_position,
                    "candidate_player_id": int(candidate["player_id"]),
                    "candidate_player_name": candidate.get("player_name"),
                    "candidate_batting_order": candidate.get("batting_order"),
                    "candidate_position": candidate.get("position"),
                    "full_vector_match": True,
                    "batting_order_match": order_match,
                    "position_match": position_match,
                    "strict_metadata_match": bool(order_match and position_match),
                    "same_game_source_vector_candidate_count": len(vector_matches),
                }
            )
    remaps = (
        pl.DataFrame(remap_candidates, strict=False).sort(
            ["game_id", "source_player_id", "candidate_player_id"]
        )
        if remap_candidates
        else pl.DataFrame(
            schema={
                "game_id": pl.Int64,
                "source_player_id": pl.Int64,
                "source_player_name": pl.String,
                "source_batting_order": pl.String,
                "source_position": pl.String,
                "candidate_player_id": pl.Int64,
                "candidate_player_name": pl.String,
                "candidate_batting_order": pl.String,
                "candidate_position": pl.String,
                "full_vector_match": pl.Boolean,
                "batting_order_match": pl.Boolean,
                "position_match": pl.Boolean,
                "strict_metadata_match": pl.Boolean,
                "same_game_source_vector_candidate_count": pl.Int64,
            }
        )
    )
    remaps.write_csv(report_root / "team_611_identity_remap_candidates.csv")

    def game_totals(frame: pl.DataFrame, prefix: str) -> pl.DataFrame:
        return frame.group_by("game_id").agg(
            *[
                pl.col(field).sum().cast(pl.Int64).alias(f"{prefix}_{field}")
                for field in OUTCOME_FIELDS
            ]
        )

    game_comparison = game_totals(source, "source").join(
        game_totals(official, "official"), on="game_id", how="full", coalesce=True
    ).sort("game_id")
    game_comparison = game_comparison.with_columns(
        pl.all_horizontal(
            [
                pl.col(f"source_{field}") == pl.col(f"official_{field}")
                for field in OUTCOME_FIELDS
            ]
        ).alias("all_outcome_totals_equal")
    )
    game_comparison.write_csv(report_root / "team_611_game_total_comparison.csv")

    source_totals = {
        field: int(source.get_column(field).fill_null(0).sum() or 0)
        for field in OUTCOME_FIELDS
    }
    official_totals = {
        field: int(official.get_column(field).fill_null(0).sum() or 0)
        for field in OUTCOME_FIELDS
    }
    direct_mismatch_count = (
        int(direct.filter(~pl.col("vector_equal")).height) if not direct.is_empty() else 0
    )
    strict_remaps = (
        remaps.filter(
            pl.col("strict_metadata_match")
            & (pl.col("same_game_source_vector_candidate_count") == 1)
        )
        if not remaps.is_empty()
        else remaps
    )

    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "league_id": LEAGUE_ID,
        "team_id": TEAM_ID,
        "team_name": TEAM_NAME,
        "source_game_count": int(source.get_column("game_id").n_unique()),
        "source_player_game_count": int(source.height),
        "official_player_game_count": int(official.height),
        "direct_identity_match_count": int(len(set(source_dict) & set(official_dict))),
        "direct_identity_vector_mismatch_count": direct_mismatch_count,
        "source_only_identity_count": int(len(source_only_keys)),
        "official_only_identity_count": int(len(official_only_keys)),
        "identity_remap_candidate_count": int(remaps.height),
        "strict_unique_identity_remap_candidate_count": int(strict_remaps.height),
        "game_count_with_exact_team_outcome_totals": int(
            game_comparison.filter(pl.col("all_outcome_totals_equal")).height
        ),
        "game_count_with_mismatched_team_outcome_totals": int(
            game_comparison.filter(~pl.col("all_outcome_totals_equal")).height
        ),
        "source_totals": source_totals,
        "official_totals": official_totals,
        "player_game_resolution": resolution_metrics,
        "official_snapshots": snapshots,
        "accepted": False,
        "interpretation": (
            "Diagnostic only. Exact team/game outcome totals support the reusable chronology, while "
            "source-only and official-only player identities require explicit participant authority. "
            "A strict remap candidate requires a unique same-game complete batting-vector match plus "
            "matching batting order and position; this report does not apply the remap."
        ),
    }
    (report_root / "team_611_boxscore_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    text = "\n".join(
        [
            "# 2021 DSL LAD Bautista official boxscore audit",
            "",
            f"- Source games: {report['source_game_count']}",
            f"- Source / official positive-PA player-games: {source.height} / {official.height}",
            f"- Direct identity matches: {report['direct_identity_match_count']}",
            f"- Direct identity vector mismatches: {direct_mismatch_count}",
            f"- Source-only / official-only identities: {len(source_only_keys)} / {len(official_only_keys)}",
            f"- Strict unique identity-remap candidates: {strict_remaps.height}",
            f"- Games with exact team outcome totals: {report['game_count_with_exact_team_outcome_totals']}/{report['source_game_count']}",
            f"- Source totals: {source_totals}",
            f"- Official totals: {official_totals}",
        ]
    )
    (report_root / "team_611_boxscore_audit.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
