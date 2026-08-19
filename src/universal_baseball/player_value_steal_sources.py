"""Portable MLB/MiLB steal evidence loaders for Player Value v1 diagnostics."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import io
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS
from universal_baseball.player_value_mlb_run_environment import _fetch_group_splits
from universal_baseball.player_value_steal_data import StealStint
from universal_baseball.season_stat_assets import fetch_season_stat_asset_inventory
from universal_baseball.season_stats import standardize_armstjc_season_stats


MLB_REQUIRED_STEAL_FIELDS = (
    "plateAppearances",
    "hits",
    "doubles",
    "triples",
    "homeRuns",
    "baseOnBalls",
    "intentionalWalks",
    "hitByPitch",
    "stolenBases",
    "caughtStealing",
)

MILB_REQUIRED_STEAL_COLUMNS = (
    "season",
    "league_id",
    "player_id",
    "batting_plate_appearances",
    "batting_hits",
    "batting_doubles",
    "batting_triples",
    "batting_home_runs",
    "batting_base_on_balls",
    "batting_intentional_walks",
    "batting_hit_by_pitch",
    "batting_stolen_bases",
    "batting_caught_stealing",
)

TIER_BY_ASSET_LEVEL = {
    "aaa": "AAA",
    "aa": "AA",
    "a+": "A+",
    "a": "A",
    "a-": "A-",
    "rk": "RK",
}


def _integer_count(value: Any, label: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing required steal source count {label}")
    numeric = float(str(value))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid steal source count {label}: {value!r}")
    return int(numeric)


def project_mlb_steal_splits(
    splits: Iterable[dict[str, Any]],
    *,
    season: int,
) -> list[StealStint]:
    rows: list[StealStint] = []
    for split in splits:
        player = split.get("player") or split.get("person") or {}
        stat = split.get("stat") or {}
        player_id = _integer_count(player.get("id"), "player.id")
        missing = [field for field in MLB_REQUIRED_STEAL_FIELDS if field not in stat]
        if missing:
            raise ValueError(f"MLB steal split for {player_id} missing fields: {missing}")
        rows.append(
            StealStint(
                season=int(season),
                source="MLB",
                environment_id="MLB",
                tier="MLB",
                player_id=player_id,
                player_name=str(player.get("fullName") or ""),
                plate_appearances=_integer_count(stat.get("plateAppearances"), "plateAppearances"),
                hits=_integer_count(stat.get("hits"), "hits"),
                doubles=_integer_count(stat.get("doubles"), "doubles"),
                triples=_integer_count(stat.get("triples"), "triples"),
                home_runs=_integer_count(stat.get("homeRuns"), "homeRuns"),
                walks=_integer_count(stat.get("baseOnBalls"), "baseOnBalls"),
                intentional_walks=_integer_count(stat.get("intentionalWalks"), "intentionalWalks"),
                hit_by_pitch=_integer_count(stat.get("hitByPitch"), "hitByPitch"),
                stolen_bases=_integer_count(stat.get("stolenBases"), "stolenBases"),
                caught_stealing=_integer_count(stat.get("caughtStealing"), "caughtStealing"),
            )
        )
    return rows


def fetch_mlb_steal_stints(
    seasons: Iterable[int],
    *,
    session: requests.Session,
    timeout_seconds: int = 120,
) -> tuple[list[StealStint], list[dict[str, Any]]]:
    stints: list[StealStint] = []
    captures: list[dict[str, Any]] = []
    for season in sorted({int(value) for value in seasons}):
        for league_id in MLB_LEAGUE_IDS:
            splits, source_captures = _fetch_group_splits(
                session,
                season=season,
                league_id=int(league_id),
                group="hitting",
                page_limit=500,
                timeout_seconds=timeout_seconds,
            )
            stints.extend(project_mlb_steal_splits(splits, season=season))
            captures.extend(asdict(capture) for capture in source_captures)
    return stints, captures


def _project_milb_frame(
    frame: pl.DataFrame,
    *,
    season: int,
    tier: str,
) -> list[StealStint]:
    standardized, _ = standardize_armstjc_season_stats(frame, "batting")
    missing = sorted(set(MILB_REQUIRED_STEAL_COLUMNS) - set(standardized.columns))
    if missing:
        raise ValueError(f"MiLB steal source missing required standardized columns: {missing}")

    rows: list[StealStint] = []
    for raw in standardized.to_dicts():
        row_season = _integer_count(raw.get("season"), "season")
        if row_season != int(season):
            raise ValueError(
                f"MiLB steal asset season mismatch: expected {season}, found {row_season}"
            )
        league_id = _integer_count(raw.get("league_id"), "league_id")
        player_id = _integer_count(raw.get("player_id"), "player_id")
        rows.append(
            StealStint(
                season=row_season,
                source="MiLB",
                environment_id=f"MILB:{league_id}",
                tier=tier,
                player_id=player_id,
                player_name=str(raw.get("player_name") or ""),
                plate_appearances=_integer_count(
                    raw.get("batting_plate_appearances"), "batting_plate_appearances"
                ),
                hits=_integer_count(raw.get("batting_hits"), "batting_hits"),
                doubles=_integer_count(raw.get("batting_doubles"), "batting_doubles"),
                triples=_integer_count(raw.get("batting_triples"), "batting_triples"),
                home_runs=_integer_count(raw.get("batting_home_runs"), "batting_home_runs"),
                walks=_integer_count(raw.get("batting_base_on_balls"), "batting_base_on_balls"),
                intentional_walks=_integer_count(
                    raw.get("batting_intentional_walks"), "batting_intentional_walks"
                ),
                hit_by_pitch=_integer_count(raw.get("batting_hit_by_pitch"), "batting_hit_by_pitch"),
                stolen_bases=_integer_count(raw.get("batting_stolen_bases"), "batting_stolen_bases"),
                caught_stealing=_integer_count(
                    raw.get("batting_caught_stealing"), "batting_caught_stealing"
                ),
            )
        )
    return rows


def fetch_milb_steal_stints(
    seasons: Iterable[int],
    *,
    session: requests.Session,
    timeout_seconds: int = 120,
) -> tuple[list[StealStint], list[dict[str, Any]]]:
    requested = {int(value) for value in seasons}
    inventory = fetch_season_stat_asset_inventory("batting", session=session)
    assets = [
        asset
        for asset in inventory
        if asset.year in requested
        and asset.is_nonempty
        and asset.filename_level in TIER_BY_ASSET_LEVEL
    ]
    if not assets:
        raise RuntimeError("no eligible MiLB steal source assets found")

    stints: list[StealStint] = []
    captures: list[dict[str, Any]] = []
    for asset in sorted(assets, key=lambda row: (row.year, row.filename_level, row.asset_id)):
        response = session.get(asset.browser_download_url, timeout=timeout_seconds)
        response.raise_for_status()
        content = response.content
        if not content:
            raise RuntimeError(f"empty MiLB steal asset response: {asset.name}")
        frame = pl.read_csv(
            io.BytesIO(content),
            infer_schema_length=10000,
            null_values=["", "NA", "N/A", "null", "None"],
        )
        tier = TIER_BY_ASSET_LEVEL[asset.filename_level]
        projected = _project_milb_frame(frame, season=asset.year, tier=tier)
        if not projected:
            raise RuntimeError(f"MiLB steal asset has no projected rows: {asset.name}")
        stints.extend(projected)
        captures.append(
            {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "year": asset.year,
                "filename_level": asset.filename_level,
                "tier": tier,
                "size_bytes_metadata": asset.size_bytes,
                "response_byte_count": len(content),
                "response_sha256": sha256(content).hexdigest(),
                "projected_row_count": len(projected),
                "updated_at_utc": asset.updated_at_utc.isoformat(),
            }
        )
    return stints, captures


def full_mlb_reference_steal_rates(stints: Iterable[StealStint], *, season: int) -> dict[str, float]:
    rows = [row for row in stints if row.source == "MLB" and row.season == int(season)]
    if not rows:
        raise ValueError(f"no MLB steal stints for reference season {season}")
    plate_appearances = sum(row.plate_appearances for row in rows)
    opportunities = sum(row.opportunity_proxy for row in rows)
    attempts = sum(row.attempts for row in rows)
    successes = sum(row.stolen_bases for row in rows)
    if min(plate_appearances, opportunities, attempts) <= 0:
        raise ValueError("MLB reference steal rates require positive PA, opportunities, and attempts")
    return {
        "plate_appearances": plate_appearances,
        "opportunity_proxy": opportunities,
        "steal_attempts": attempts,
        "stolen_bases": successes,
        "opportunity_proxy_per_pa": opportunities / plate_appearances,
        "attempt_rate_per_opportunity_proxy": attempts / opportunities,
        "success_rate_per_attempt": successes / attempts,
    }
