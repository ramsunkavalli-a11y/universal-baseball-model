#!/usr/bin/env python3
"""Recover historical MiLB player-game and venue authority from official feeds."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import gzip
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import quote

import polars as pl
import requests

from universal_baseball.historical_milb_feed import (
    OFFICIAL_BATTING_MAP,
    project_historical_milb_game_feed,
)
from universal_baseball.hitter_v2_outcomes import (
    OFFICIAL_BATTING_FIELDS,
    project_official_player_game_outcomes,
    resolve_official_player_game_outcomes,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


DEFAULT_SEASON = 2018
LEVELS = ("aaa", "aa", "a+", "a", "a-", "rk")
FEED_FIELDS = ",".join(
    (
        "gameData",
        "game",
        "pk",
        "type",
        "season",
        "datetime",
        "officialDate",
        "venue",
        "id",
        "name",
        "location",
        "teams",
        "away",
        "home",
        "league",
        "liveData",
        "boxscore",
        "players",
        "person",
        "stats",
        "batting",
        *OFFICIAL_BATTING_MAP.values(),
    )
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=DEFAULT_SEASON)
    parser.add_argument("--levels", nargs="+", choices=LEVELS, default=list(LEVELS))
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--max-games", type=int)
    parser.add_argument("--overlap-validation-games", type=int, default=50)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-2018-game-authority"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-2018-game-authority"),
    )
    return parser.parse_args()


def _download(url: str, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size <= 0:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        path.write_bytes(response.content)
        retrieval = "downloaded"
    else:
        retrieval = "reused_local_quarantine"
    return {
        "url": url,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "retrieval": retrieval,
    }


def _schedule(
    level: str, work_root: Path, *, season: int
) -> tuple[pl.DataFrame, dict[str, Any]]:
    release_level = "rookie" if level == "rk" else level
    filename = f"{season}_{release_level}_schedule.csv"
    url = (
        "https://github.com/armstjc/milb-data-repository/releases/download/schedule/"
        + quote(filename, safe="_.-")
    )
    path = work_root / "schedules" / filename.replace("+", "plus")
    provenance = _download(url, path)
    frame = pl.read_csv(path, infer_schema_length=1000)
    required = {
        "game_pk",
        "game_type",
        "official_date",
        "game_month",
        "status_abstract_game_state",
        "status_coded_game_state",
        "status_detailed_state",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{filename} lacks schedule fields: {missing}")
    selected = (
        frame.filter(
            (pl.col("game_type") == "R")
            & (pl.col("status_abstract_game_state") == "Final")
            & (
                (pl.col("status_coded_game_state") == "F")
                | pl.col("status_detailed_state")
                .cast(pl.String)
                .str.starts_with("Forfeit")
            )
            & pl.col("official_date").cast(pl.String).str.starts_with(f"{season}-")
        )
        .select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("official_date").cast(pl.String),
        )
        .unique(subset="game_pk")
        .sort("game_pk")
        .with_columns(pl.lit(level).alias("filename_level"))
    )
    return selected, provenance


def _feed_url(game_id: int) -> str:
    return f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"


def _read_cache(path: Path) -> bytes:
    with gzip.open(path, "rb") as handle:
        return handle.read()


def _write_cache(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.gz.part")
    with temporary.open("wb") as raw_handle:
        with gzip.GzipFile(
            filename="", mode="wb", compresslevel=6, mtime=0, fileobj=raw_handle
        ) as handle:
            handle.write(content)
    temporary.replace(path)


def _capture_game(game_id: int, cache_root: Path) -> dict[str, Any]:
    path = cache_root / f"{game_id}.json.gz"
    retrieval = "reused_local_quarantine"
    if path.exists() and path.stat().st_size > 0:
        content = _read_cache(path)
    else:
        retrieval = "downloaded"
        error: Exception | None = None
        for attempt in range(5):
            try:
                response = requests.get(
                    _feed_url(game_id),
                    params={"fields": FEED_FIELDS},
                    timeout=60,
                )
                response.raise_for_status()
                content = response.content
                json.loads(content)
                _write_cache(path, content)
                break
            except (requests.RequestException, json.JSONDecodeError, OSError) as exc:
                error = exc
                if attempt == 4:
                    raise RuntimeError(
                        f"official feed failed for game {game_id} after five attempts"
                    ) from error
                time.sleep(0.5 * (2**attempt))
    payload = json.loads(content)
    players, context = project_historical_milb_game_feed(
        payload, expected_game_id=game_id
    )
    return {
        "game_id": game_id,
        "players": players,
        "context": context,
        "provenance": {
            "game_id": game_id,
            "url": _feed_url(game_id),
            "retrieval": retrieval,
            "content_bytes": len(content),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "cache_path": str(path),
            "cache_bytes": path.stat().st_size,
        },
    }


def _validate_published_overlap(
    *,
    work_root: Path,
    season: int,
    game_limit: int,
    workers: int,
) -> dict[str, Any]:
    """Compare regenerated rows with the archived August High-A release."""

    if game_limit <= 0:
        return {"status": "disabled", "requested_games": game_limit}
    filename = f"{season}_8_a+_player_game_stats.csv"
    url = (
        "https://github.com/armstjc/milb-data-repository/releases/download/"
        "game_player_stats/"
        + quote(filename, safe="_.-")
    )
    path = work_root / "validation" / filename.replace("+", "plus")
    source = _download(url, path)
    raw = pl.read_csv(
        path,
        infer_schema=False,
        null_values=["", "NA", "NaN", "null", "None"],
        truncate_ragged_lines=False,
    )
    published, _ = resolve_official_player_game_outcomes(
        project_official_player_game_outcomes(
            raw,
            source_asset=filename,
            season=season,
            game_type="R",
        )
    )
    game_ids = sorted(
        int(value)
        for value in published.filter(pl.col("batting_PA") > 0)
        .get_column("game_id")
        .unique()
        .to_list()
    )[:game_limit]
    regenerated_frames: list[pl.DataFrame] = []
    errors: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _capture_game, game_id, work_root / "validation-feeds"
            ): game_id
            for game_id in game_ids
        }
        for future in as_completed(futures):
            game_id = futures[future]
            try:
                regenerated_frames.append(future.result()["players"])
            except Exception as exc:
                errors.append({"game_id": game_id, "error": str(exc)})
    if not regenerated_frames:
        return {
            "status": "failed",
            "requested_games": game_limit,
            "errors": errors,
            "source": source,
        }

    keys = ["game_id", "player_id"]
    fields = ["game_date", "game_type", "league_id", "team_id", *OFFICIAL_BATTING_FIELDS]
    regenerated = pl.concat(regenerated_frames, how="vertical_relaxed").filter(
        pl.col("batting_PA") > 0
    )
    published = published.filter(
        pl.col("game_id").is_in(game_ids) & (pl.col("batting_PA") > 0)
    )
    published = published.with_columns(pl.col("game_date").cast(pl.String))
    regenerated = regenerated.with_columns(pl.col("game_date").cast(pl.String))
    joined = published.select(*keys, *fields).join(
        regenerated.select(*keys, *fields),
        on=keys,
        how="full",
        suffix="__regenerated",
        coalesce=True,
    )
    equality = [
        pl.col(field).eq_missing(pl.col(f"{field}__regenerated"))
        for field in fields
    ]
    mismatch = joined.filter(~pl.all_horizontal(equality))
    published_keys = set(published.select(keys).iter_rows())
    regenerated_keys = set(regenerated.select(keys).iter_rows())
    return {
        "status": "passed" if not errors and mismatch.is_empty() else "failed",
        "requested_games": game_limit,
        "compared_games": len(game_ids),
        "published_positive_pa_rows": published.height,
        "regenerated_positive_pa_rows": regenerated.height,
        "missing_from_regenerated": len(published_keys - regenerated_keys),
        "new_in_regenerated": len(regenerated_keys - published_keys),
        "field_mismatch_rows": mismatch.height,
        "errors": errors,
        "source": source,
    }


def main() -> int:
    args = _args()
    if args.workers < 1 or args.workers > 32:
        raise ValueError("workers must be between 1 and 32")
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)
    table_root = args.report_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    schedule_frames: list[pl.DataFrame] = []
    schedule_provenance: list[dict[str, Any]] = []
    for level in dict.fromkeys(args.levels):
        frame, provenance = _schedule(level, args.work_root, season=args.season)
        schedule_frames.append(frame)
        schedule_provenance.append({"filename_level": level, **provenance})
    games = pl.concat(schedule_frames, how="vertical_relaxed").sort(
        "filename_level", "game_pk"
    )
    duplicate_levels = (
        games.group_by("game_pk")
        .agg(pl.col("filename_level").n_unique().alias("level_count"))
        .filter(pl.col("level_count") > 1)
    )
    if duplicate_levels.height:
        raise RuntimeError("historical recovery schedules assign a game to multiple levels")
    if args.max_games is not None:
        games = games.head(args.max_games)

    level_by_game = {
        int(row["game_pk"]): str(row["filename_level"])
        for row in games.to_dicts()
    }
    player_frames: list[pl.DataFrame] = []
    context_frames: list[pl.DataFrame] = []
    provenance_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(_capture_game, game_id, args.work_root / "feeds"): game_id
            for game_id in level_by_game
        }
        for index, future in enumerate(as_completed(futures), start=1):
            game_id = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # retain every source failure in the report
                failures.append({"game_id": game_id, "error": str(exc)})
                continue
            level = level_by_game[game_id]
            player_frames.append(
                result["players"].with_columns(pl.lit(level).alias("filename_level"))
            )
            context_frames.append(
                result["context"].with_columns(pl.lit(level).alias("filename_level"))
            )
            provenance_rows.append(result["provenance"])
            if index % 100 == 0 or index == len(futures):
                print(
                    json.dumps(
                        {
                            "completed": index,
                            "scheduled": len(futures),
                            "failures": len(failures),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    if not player_frames or not context_frames:
        raise RuntimeError("historical recovery produced no usable game feeds")
    players = pl.concat(player_frames, how="vertical_relaxed").sort(
        "game_id", "team_id", "player_id"
    )
    contexts = pl.concat(context_frames, how="vertical_relaxed").sort("game_id")
    if players.select("game_id", "player_id").is_duplicated().any():
        raise RuntimeError("recovered authority contains duplicate player-game rows")
    if contexts.get_column("game_id").n_unique() != contexts.height:
        raise RuntimeError("recovered context contains duplicate games")

    player_artifact = write_canonical_parquet(
        players,
        table_root / f"hitter_v2_player_game_authority_{args.season}_recovered.parquet",
        table_name=f"hitter_v2_player_game_authority_{args.season}_recovered",
    ).as_record()
    context_artifact = write_canonical_parquet(
        contexts,
        table_root / f"hitter_v2_game_context_{args.season}_recovered.parquet",
        table_name=f"hitter_v2_game_context_{args.season}_recovered",
    ).as_record()
    provenance = pl.DataFrame(provenance_rows).sort("game_id")
    provenance_artifact = write_canonical_parquet(
        provenance,
        table_root / f"hitter_v2_game_feed_provenance_{args.season}_recovered.parquet",
        table_name=f"hitter_v2_game_feed_provenance_{args.season}_recovered",
    ).as_record()

    recovered_games = set(contexts.get_column("game_id").to_list())
    expected_games = set(level_by_game)
    missing_games = sorted(expected_games - recovered_games)
    report = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "season": args.season,
        "scope": "full_historical_milb_player_game_and_venue_authority",
        "source": "official Stats API game feed, independently of archived PBP",
        "levels": list(dict.fromkeys(args.levels)),
        "expected_games": len(expected_games),
        "recovered_games": len(recovered_games),
        "missing_game_count": len(missing_games),
        "missing_game_ids": missing_games,
        "failed_game_count": len(failures),
        "failures": sorted(failures, key=lambda row: int(row["game_id"])),
        "player_game_rows": players.height,
        "positive_pa_player_game_rows": players.filter(pl.col("batting_PA") > 0).height,
        "players": players.get_column("player_id").n_unique(),
        "venues": contexts.get_column("venue_id").n_unique(),
        "leagues": sorted(
            set(contexts.get_column("away_league_id").to_list())
            | set(contexts.get_column("home_league_id").to_list())
        ),
        "schedule_provenance": schedule_provenance,
        "published_overlap_validation": _validate_published_overlap(
            work_root=args.work_root,
            season=args.season,
            game_limit=args.overlap_validation_games,
            workers=args.workers,
        ),
        "storage": {
            "player_game": player_artifact,
            "game_context": context_artifact,
            "game_feed_provenance": provenance_artifact,
        },
        "accepted": not missing_games and not failures,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
    }
    report["accepted"] = bool(
        report["accepted"]
        and report["published_overlap_validation"]["status"] in {"passed", "disabled"}
    )
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
