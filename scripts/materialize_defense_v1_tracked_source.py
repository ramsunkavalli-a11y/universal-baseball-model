#!/usr/bin/env python3
"""Materialize frozen historical tracking proxies for Defense v1 development."""

from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

import polars as pl
import requests

from sportsdataverse.mlb.mlb_catcher_framing import mlb_catcher_framing
from sportsdataverse.mlb.mlb_fielding_oaa import mlb_fielding_oaa
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search, mlb_statcast_search_minors


PACKAGE_VERSION = "0.0.75"
REPORT_ROOT = Path("reports/generated/defense-v1-tracked-source")
TABLE_ROOT = REPORT_ROOT / "tables"
MLB_WINDOWS = {
    2021: ("2021-04-01", "2021-10-03"),
    2022: ("2022-04-07", "2022-10-05"),
    2023: ("2023-03-30", "2023-10-01"),
}
MILB_2023_WINDOW = ("2023-03-31", "2023-09-30")
POS_ABBR = {2: "C", 3: "1B", 4: "2B", 5: "3B", 6: "SS", 7: "LF", 8: "CF", 9: "RF"}


def _file_sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aaa_abbreviations() -> set[str]:
    response = requests.get(
        "https://statsapi.mlb.com/api/v1/teams",
        params={"sportId": 11, "season": 2023},
        headers={"User-Agent": "universal-baseball-model-defense-tracked-source/0.1"},
        timeout=60,
    )
    response.raise_for_status()
    abbreviations = {
        str(team.get("abbreviation") or "").strip()
        for team in (response.json().get("teams") or [])
        if str(team.get("abbreviation") or "").strip()
    }
    if len(abbreviations) < 20:
        raise RuntimeError(f"unexpected AAA abbreviation count: {len(abbreviations)}")
    return abbreviations


def _derive_level(
    pitches: pl.DataFrame,
    *,
    season: int,
    level_group: str,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    if pitches.is_empty():
        raise RuntimeError(f"empty tracked source season={season} level={level_group}")
    required = {
        "type",
        "description",
        "plate_x",
        "plate_z",
        "sz_top",
        "sz_bot",
        "fielder_2",
        "hc_x",
        "hc_y",
        "hit_distance_sc",
        "launch_angle",
        "hit_location",
        "events",
    }
    missing = sorted(required - set(pitches.columns))
    if missing:
        raise RuntimeError(f"tracked source missing columns season={season} level={level_group}: {missing}")

    bip = pitches.filter(pl.col("type") == "X")
    oaa = mlb_fielding_oaa(bip)
    range_rows = (
        oaa.with_columns(
            pl.col("fielder_id").cast(pl.Int64, strict=False).alias("player_id"),
            pl.col("position").cast(pl.Int64),
        )
        .filter(pl.col("player_id").is_not_null() & pl.col("position").is_in(sorted(POS_ABBR)))
        .with_columns(
            pl.col("position").replace_strict(POS_ABBR, return_dtype=pl.Utf8).alias("position_abbreviation"),
            pl.lit(int(season)).alias("season"),
            pl.lit(level_group).alias("level_group"),
            pl.when(pl.col("opportunities") > 0)
            .then(100.0 * pl.col("oaa") / pl.col("opportunities"))
            .otherwise(None)
            .alias("tracked_oaa_per_100"),
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "position",
            "position_abbreviation",
            "opportunities",
            "oaa",
            "tracked_oaa_per_100",
        )
        .sort(["season", "level_group", "player_id", "position"])
    )

    framing_raw = mlb_catcher_framing(pitches)
    framing_rows = (
        framing_raw.with_columns(
            pl.col("catcher_id").cast(pl.Int64, strict=False).alias("player_id"),
            pl.lit(int(season)).alias("season"),
            pl.lit(level_group).alias("level_group"),
            pl.when(pl.col("takes") > 0)
            .then(1000.0 * pl.col("framing_runs") / pl.col("takes"))
            .otherwise(None)
            .alias("tracked_framing_per_1000_takes"),
        )
        .filter(pl.col("player_id").is_not_null())
        .select(
            "season",
            "level_group",
            "player_id",
            "takes",
            "strikes_gained",
            "framing_runs",
            "tracked_framing_per_1000_takes",
        )
        .sort(["season", "level_group", "player_id"])
    )

    range_key = ["season", "level_group", "player_id", "position"]
    if range_rows.group_by(range_key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"range proxy violates grain season={season} level={level_group}")
    framing_key = ["season", "level_group", "player_id"]
    if framing_rows.group_by(framing_key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"framing proxy violates grain season={season} level={level_group}")

    eligible_range = range_rows.filter(
        pl.col("position_abbreviation").is_in(["1B", "2B", "3B", "SS", "LF", "CF", "RF"])
        & (pl.col("opportunities") >= 100)
    )
    eligible_framing = framing_rows.filter(pl.col("takes") >= 500)
    diagnostics = {
        "season": int(season),
        "level_group": level_group,
        "pitch_row_count": int(pitches.height),
        "column_count": len(pitches.columns),
        "bip_row_count": int(bip.height),
        "range_player_position_row_count": int(range_rows.height),
        "range_total_opportunities": int(range_rows.get_column("opportunities").sum() or 0),
        "eligible_range_player_position_count": int(eligible_range.height),
        "framing_catcher_row_count": int(framing_rows.height),
        "framing_total_takes": int(framing_rows.get_column("takes").sum() or 0),
        "eligible_framing_catcher_count": int(eligible_framing.height),
    }
    return range_rows, framing_rows, diagnostics


def main() -> int:
    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    TABLE_ROOT.mkdir(parents=True, exist_ok=True)
    range_frames: list[pl.DataFrame] = []
    framing_frames: list[pl.DataFrame] = []
    diagnostics: list[dict[str, Any]] = []
    query_records: list[dict[str, Any]] = []

    for season, (start, end) in MLB_WINDOWS.items():
        print(f"Fetching MLB Statcast {season}: {start}..{end}")
        pitches = mlb_statcast_search(
            start,
            end,
            season=season,
            game_type="R",
            chunk_days=7,
        )
        range_rows, framing_rows, diag = _derive_level(pitches, season=season, level_group="MLB")
        range_frames.append(range_rows)
        framing_frames.append(framing_rows)
        diagnostics.append(diag)
        query_records.append(
            {
                "source": "Baseball Savant MLB Statcast CSV via SportsDataverse",
                "season": season,
                "level_group": "MLB",
                "start": start,
                "end": end,
                "game_type": "R",
                "chunk_days": 7,
            }
        )
        del pitches

    start, end = MILB_2023_WINDOW
    print(f"Fetching tracked MiLB Statcast 2023: {start}..{end}")
    milb = mlb_statcast_search_minors(
        start,
        end,
        season=2023,
        game_type="R",
        minors="true",
        chunk_days=7,
    )
    if milb.is_empty() or "home_team" not in milb.columns:
        raise RuntimeError("tracked MiLB 2023 source empty or missing home_team")
    aaa_abbr = _aaa_abbreviations()
    milb = milb.with_columns(pl.col("home_team").cast(pl.Utf8).str.strip_chars())
    aaa = milb.filter(pl.col("home_team").is_in(sorted(aaa_abbr)))
    non_aaa = milb.filter(~pl.col("home_team").is_in(sorted(aaa_abbr)))
    observed_non_aaa_home_teams = sorted(
        str(value) for value in non_aaa.get_column("home_team").drop_nulls().unique().to_list()
    )
    for level_group, frame in (("AAA", aaa), ("TRACKED_NON_AAA", non_aaa)):
        range_rows, framing_rows, diag = _derive_level(frame, season=2023, level_group=level_group)
        range_frames.append(range_rows)
        framing_frames.append(framing_rows)
        diagnostics.append(diag)
        query_records.append(
            {
                "source": "Baseball Savant MiLB Statcast CSV via SportsDataverse",
                "season": 2023,
                "level_group": level_group,
                "start": start,
                "end": end,
                "game_type": "R",
                "minors": "true",
                "server_level_filter": False,
                "client_level_classification": "official 2023 AAA home-team abbreviation membership",
                "chunk_days": 7,
            }
        )

    range_all = pl.concat(range_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id", "position"]
    )
    framing_all = pl.concat(framing_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id"]
    )
    range_path = TABLE_ROOT / "tracked_range_proxy_2021_2023.parquet"
    framing_path = TABLE_ROOT / "tracked_framing_proxy_2021_2023.parquet"
    range_all.write_parquet(range_path, compression="zstd")
    framing_all.write_parquet(framing_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_tracked_source_materialization",
        "contract": "docs/defense-v1-tracked-challenger-contract.md",
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "range_function": "mlb_fielding_oaa",
            "framing_function": "mlb_catcher_framing",
        },
        "queries": query_records,
        "diagnostics": diagnostics,
        "milb_2023": {
            "tracked_pool_pitch_row_count": int(milb.height),
            "aaa_pitch_row_count": int(aaa.height),
            "tracked_non_aaa_pitch_row_count": int(non_aaa.height),
            "official_aaa_abbreviation_count": len(aaa_abbr),
            "observed_non_aaa_home_teams": observed_non_aaa_home_teams,
        },
        "storage": {
            "range": {
                "path": str(range_path),
                "row_count": int(range_all.height),
                "file_size_bytes": range_path.stat().st_size,
                "sha256": _file_sha(range_path),
            },
            "framing": {
                "path": str(framing_path),
                "row_count": int(framing_all.height),
                "file_size_bytes": framing_path.stat().st_size,
                "sha256": _file_sha(framing_path),
            },
        },
        "decision": {
            "tracked_source_materialized": True,
            "tracked_challenger_scoring_authorized_next": True,
            "2025_confirmation_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_source_accessed": False,
            "2025_defensive_targets_accessed": False,
            "model_fit": False,
            "source_filters_changed_from_contract": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Defense v1 tracked source materialization",
        "",
        f"- SportsDataverse: {installed}",
        f"- range rows: {range_all.height:,}",
        f"- framing rows: {framing_all.height:,}",
        f"- 2023 MiLB tracked pitches: {milb.height:,}",
        "- tracked challenger scoring authorized next: True",
        "- 2025 accessed: False",
        "- WAR/value authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
