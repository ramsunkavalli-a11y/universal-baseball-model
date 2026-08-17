#!/usr/bin/env python3
"""Tiny official Baseball Savant Minor League tracking source probe.

This is deliberately not a season materializer. It verifies the current official
tracked-only Minor League CSV detail endpoint on one fixed historical date,
retains exact raw bytes, checks broad tracking capability, and runs the corrected
result-producing/non-bunt model-BBE projection through the same certified
player-game reconciliation used by later materialization.

A successful rerun therefore proves the *tiny-date* source contract needed before
bulk historical MiLB capture. It does not certify full-season completeness.
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

from universal_baseball.current_talent_batted_ball_materialization import (
    materialize_reconciled_tracked_bbe,
)
from universal_baseball.current_talent_savant_minors import build_tracked_minor_savant_url


PROBE_DATE = "2023-07-01"
MODEL_BBE_CONTRACT = "result_producing_non_bunt_pitch_grain_v1"
REQUIRED_FIELDS = {
    "game_date",
    "game_pk",
    "batter",
    "events",
    "type",
    "des",
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
    except Exception as exc:  # pragma: no cover - live source drift only
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
        pl.read_parquet(path).select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
            pl.col("level_group").cast(pl.String),
        )
        for path in paths
    ]
    combined = (
        pl.concat(frames, how="vertical_relaxed")
        .unique()
        .with_columns(pl.lit(season).cast(pl.Int64).alias("season"))
    )
    duplicate = (
        combined.group_by(["game_pk", "player_id"])
        .agg(
            pl.struct(["season", "level_group", "league_id"])
            .n_unique()
            .alias("environment_count")
        )
        .filter(pl.col("environment_count") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("certified MiLB evidence has ambiguous game_pk + player_id environment")
    if combined.filter(pl.col("level_group") == "MLB").height:
        raise ValueError("certified MiLB evidence unexpectedly contains MLB rows")
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
        certified.select("game_pk", "player_id", "level_group", "league_id"),
        on=["game_pk", "player_id"],
        how="left",
    )

    # Broad capability surface: deliberately wider than the model BBE definition.
    bbe_like = reconciled.filter(
        _nonblank("bb_type")
        | (pl.col("description").str.to_lowercase() == "hit_into_play")
        | pl.col("launch_speed").is_not_null()
        | pl.col("launch_angle").is_not_null()
    )
    tracked_observation = bbe_like.filter(
        pl.col("launch_speed").is_not_null() | pl.col("launch_angle").is_not_null()
    )
    complete_observation = bbe_like.filter(
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

    # Corrected model surface: exact same projection and reconciliation as bulk
    # materialization. This is what makes the new probe distinguishable from the
    # older broad source-capability run.
    canonical = materialize_reconciled_tracked_bbe(
        raw,
        certified,
        source_family="MILB_SAVANT_TRACKED",
    )
    canonical_by_level = (
        canonical.group_by(["level_group", "league_id", "source_capability_tier"])
        .agg(
            pl.len().cast(pl.Int64).alias("canonical_model_bbe"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("batter_count"),
            pl.col("launch_speed").mean().alias("mean_exit_velocity"),
            pl.col("sweet_spot").mean().alias("sweet_spot_share"),
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
    by_level.write_csv(args.output_dir / "tracking_observations_by_certified_level.csv")
    canonical_by_level.write_csv(args.output_dir / "canonical_model_bbe_by_certified_level.csv")
    reconciled.head(500).write_csv(args.output_dir / "broad_reconciled_sample.csv")
    canonical.head(500).write_csv(args.output_dir / "canonical_model_bbe_sample.csv")

    bat_tracking_nonnull_counts = {
        field: int(raw.get_column(field).is_not_null().sum()) if field in raw.columns else None
        for field in BAT_TRACKING_FIELDS
    }

    report = {
        "report_schema_version": "0.4",
        "probe_date": probe_date,
        "season": season,
        "source": "Baseball Savant Minor League Statcast Search official CSV",
        "request_semantics": "tracked_only_helper_v1",
        "canonical_model_bbe_contract": MODEL_BBE_CONTRACT,
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
        "bbe_like_observation_count": bbe_like.height,
        "bbe_like_with_any_ev_or_la_count": tracked_observation.height,
        "bbe_like_with_complete_ev_la_count": complete_observation.height,
        "bbe_like_complete_ev_la_share": (
            complete_observation.height / bbe_like.height if bbe_like.height else None
        ),
        "canonical_model_bbe_count": canonical.height,
        "canonical_model_bbe_game_count": int(canonical.get_column("game_pk").n_unique()),
        "canonical_model_bbe_batter_count": int(canonical.get_column("player_id").n_unique()),
        "canonical_model_bbe_by_level": canonical_by_level.to_dicts(),
        "bat_tracking_nonnull_counts": bat_tracking_nonnull_counts,
        "broad_certified_level_summary": by_level.to_dicts(),
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
            "A successful run certifies the tracked-only request, required schema, certified "
            "game/player identity, broad EV/LA capability, and corrected result-producing/non-bunt "
            "pitch-grain BBE projection on these tiny historical dates. It does not certify "
            "full-season completeness or authorize a richer model without the later development gate."
        ),
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    if matched_keys.is_empty():
        raise ValueError(
            f"Minor League Savant rows did not reconcile to certified {season} evidence"
        )
    if complete_observation.is_empty():
        raise ValueError("Minor League Savant probe found no complete EV/LA source observations")
    if canonical.is_empty():
        raise ValueError(
            "Minor League Savant probe found no corrected result-producing non-bunt EV/LA BBE"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
