#!/usr/bin/env python3
"""Tiny official Baseball Savant Minor League tracking source probe.

This is deliberately not a season materializer. It verifies the current official
Minor League CSV detail endpoint on one fixed historical date, retains exact raw
bytes, checks the fields needed for an EV/launch-angle challenger, and reconciles
Savant game/batter identity to already-certified same-season Current Talent
player-game evidence.

Future probes use the frozen tracked-only request helper from the richer challenger
contract rather than maintaining a second request implementation here.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import io
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.current_talent_savant_minors import build_tracked_minor_savant_url


PROBE_DATE = "2023-07-01"
REQUIRED_FIELDS = {
    "game_date",
    "game_pk",
    "batter",
    "events",
    "description",
    "bb_type",
    "launch_speed",
    "launch_angle",
    "at_bat_number",
    "pitch_number",
}
BAT_TRACKING_FIELDS = (
    "bat_speed",
    "swing_length",
    "miss_distance",
    "attack_angle",
    "attack_direction",
    "swing_path_tilt",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certified-milb-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--probe-date", default=PROBE_DATE)
    return parser.parse_args()


def _request_url(probe_date: str) -> str:
    parsed = date.fromisoformat(probe_date)
    return build_tracked_minor_savant_url(parsed, parsed)


def _fetch(url: str) -> tuple[bytes, str, int, str]:
    headers = {
        "User-Agent": (
            "universal-baseball-model/0.1 "
            "(public baseball research; one-date source capability probe)"
        )
    }
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    return response.content, response.url, int(response.status_code), content_type


def _read_raw_csv(content: bytes) -> pl.DataFrame:
    if not content.strip():
        raise ValueError("Minor League Savant probe returned empty response bytes")
    try:
        frame = pl.read_csv(
            io.BytesIO(content),
            infer_schema=False,
            null_values=["", "null", "NA"],
            ignore_errors=False,
        )
    except Exception as exc:  # pragma: no cover - exercised only on live source drift
        preview = content[:300].decode("utf-8", errors="replace")
        raise ValueError(f"Minor League Savant response is not readable CSV: {preview!r}") from exc
    if frame.is_empty():
        raise ValueError("Minor League Savant probe returned a CSV with zero rows")
    return frame


def _integer_like(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def _load_certified_player_games(root: Path, season: int) -> pl.DataFrame:
    paths = sorted(root.rglob(f"current_talent_game_summary_{season}_*.parquet"))
    if not paths:
        raise ValueError(
            f"no certified {season} MiLB player-game summaries found under {root}"
        )
    frames = [
        pl.read_parquet(path).select("game_pk", "player_id", "level_group", "league_id")
        for path in paths
    ]
    combined = pl.concat(frames, how="vertical_relaxed").unique()
    duplicate = (
        combined.group_by(["game_pk", "player_id"])
        .agg(
            pl.col("level_group").n_unique().alias("level_count"),
            pl.col("league_id").n_unique().alias("league_count"),
        )
        .filter((pl.col("level_count") != 1) | (pl.col("league_count") != 1))
    )
    if not duplicate.is_empty():
        raise ValueError("certified MiLB evidence has ambiguous game_pk + player_id level identity")
    return combined


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (pl.col(column).str.strip_chars() != "")


def main() -> int:
    args = _parse_args()
    probe_date = str(args.probe_date)
    try:
        parsed_probe_date = date.fromisoformat(probe_date)
    except ValueError as exc:
        raise ValueError(f"probe date must be ISO YYYY-MM-DD: {probe_date}") from exc
    season = parsed_probe_date.year
    args.output_dir.mkdir(parents=True, exist_ok=True)

    request_url = _request_url(probe_date)
    content, retrieved_url, status_code, content_type = _fetch(request_url)
    raw_path = args.output_dir / f"savant-minors-{probe_date}.csv"
    raw_path.write_bytes(content)

    raw = _read_raw_csv(content)
    missing_fields = sorted(REQUIRED_FIELDS - set(raw.columns))
    if missing_fields:
        raise ValueError(f"Minor League Savant detail CSV missing required fields: {missing_fields}")

    projected = raw.select(
        pl.col("game_date").cast(pl.String),
        _integer_like("game_pk", "game_pk"),
        _integer_like("batter", "player_id"),
        _integer_like("at_bat_number", "at_bat_number"),
        _integer_like("pitch_number", "pitch_number"),
        pl.col("events").cast(pl.String),
        pl.col("description").cast(pl.String),
        pl.col("bb_type").cast(pl.String),
        pl.col("launch_speed").cast(pl.Float64, strict=False),
        pl.col("launch_angle").cast(pl.Float64, strict=False),
    ).drop_nulls(["game_pk", "player_id"])

    certified = _load_certified_player_games(args.certified_milb_root, season)
    reconciled = projected.join(
        certified,
        on=["game_pk", "player_id"],
        how="left",
    )

    # A BBE-like row is deliberately broad here. The goal is source capability,
    # not a final event definition. This exposes how often tracking values exist
    # on rows Savant itself marks as contact / batted-ball detail.
    bbe_like = reconciled.filter(
        _nonblank("bb_type")
        | (pl.col("description").str.to_lowercase() == "hit_into_play")
        | pl.col("launch_speed").is_not_null()
        | pl.col("launch_angle").is_not_null()
    )
    tracked_bbe = bbe_like.filter(
        pl.col("launch_speed").is_not_null() | pl.col("launch_angle").is_not_null()
    )
    complete_ev_la = bbe_like.filter(
        pl.col("launch_speed").is_not_null() & pl.col("launch_angle").is_not_null()
    )

    reconciled_keys = reconciled.select("game_pk", "player_id").unique()
    matched_keys = reconciled.filter(pl.col("level_group").is_not_null()).select(
        "game_pk", "player_id"
    ).unique()

    by_level = (
        bbe_like.filter(pl.col("level_group").is_not_null())
        .group_by(["level_group", "league_id"])
        .agg(
            pl.len().alias("bbe_like_rows"),
            pl.col("launch_speed").is_not_null().sum().alias("rows_with_ev"),
            pl.col("launch_angle").is_not_null().sum().alias("rows_with_la"),
            (
                pl.col("launch_speed").is_not_null()
                & pl.col("launch_angle").is_not_null()
            ).sum().alias("rows_with_complete_ev_la"),
            pl.col("game_pk").n_unique().alias("game_count"),
            pl.col("player_id").n_unique().alias("batter_count"),
        )
        .with_columns(
            (pl.col("rows_with_complete_ev_la") / pl.col("bbe_like_rows")).alias(
                "complete_ev_la_share"
            )
        )
        .sort(["level_group", "league_id"])
    )

    header_inventory = pl.DataFrame(
        {
            "column_index": list(range(len(raw.columns))),
            "column_name": raw.columns,
        }
    )
    header_inventory.write_csv(args.output_dir / "column_inventory.csv")
    by_level.write_csv(args.output_dir / "bbe_tracking_by_certified_level.csv")
    reconciled.head(500).write_csv(args.output_dir / "reconciled_sample.csv")

    bat_tracking_nonnull_counts = {
        field: int(raw.get_column(field).is_not_null().sum()) if field in raw.columns else None
        for field in BAT_TRACKING_FIELDS
    }

    report = {
        "report_schema_version": "0.3",
        "probe_date": probe_date,
        "season": season,
        "source": "Baseball Savant Minor League Statcast Search official CSV",
        "request_semantics": "tracked_only_helper_v1",
        "request_url": request_url,
        "retrieved_url": retrieved_url,
        "status_code": status_code,
        "content_type": content_type,
        "response_sha256": hashlib.sha256(content).hexdigest(),
        "response_bytes": len(content),
        "raw_row_count": raw.height,
        "raw_column_count": len(raw.columns),
        "required_fields_present": not missing_fields,
        "projected_identity_row_count": projected.height,
        "projected_unique_game_batter_count": reconciled_keys.height,
        "certified_matched_unique_game_batter_count": matched_keys.height,
        "certified_match_share": (
            matched_keys.height / reconciled_keys.height if reconciled_keys.height else None
        ),
        "bbe_like_row_count": bbe_like.height,
        "bbe_like_with_any_ev_or_la_count": tracked_bbe.height,
        "bbe_like_with_complete_ev_la_count": complete_ev_la.height,
        "bbe_like_complete_ev_la_share": (
            complete_ev_la.height / bbe_like.height if bbe_like.height else None
        ),
        "bat_tracking_nonnull_counts": bat_tracking_nonnull_counts,
        "certified_level_summary": by_level.to_dicts(),
        "observed_certified_levels": sorted(
            str(value)
            for value in reconciled.get_column("level_group").drop_nulls().unique().to_list()
        ),
        "observed_certified_league_ids": sorted(
            int(value)
            for value in reconciled.get_column("league_id").drop_nulls().unique().to_list()
        ),
        "raw_column_names": raw.columns,
        "raw_response_file": str(raw_path),
        "decision_boundary": (
            "This one-date probe certifies tracked-only endpoint/schema/identity feasibility. "
            "It does not certify full-season completeness, historical venue entitlement, "
            "or a richer Current Talent feature definition."
        ),
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    # Require some actual reconciled EV/LA evidence before calling the source
    # probe successful. Exact coverage thresholds belong to the later model gate.
    if matched_keys.is_empty():
        raise ValueError(
            f"Minor League Savant rows did not reconcile to certified {season} evidence"
        )
    if complete_ev_la.is_empty():
        raise ValueError("Minor League Savant probe found no complete EV/LA batted-ball rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
