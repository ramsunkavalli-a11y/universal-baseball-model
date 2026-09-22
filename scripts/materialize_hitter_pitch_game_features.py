#!/usr/bin/env python3
"""Materialize universal hitter pitch-sequence and official game-feed features."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_pitch_game_features import (
    attach_pitch_game_lags,
    build_player_season_pitch_game_features,
)
from universal_baseball.storage import write_canonical_parquet


DEFAULT_SEASONS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
PITCH_COLUMNS = (
    "season",
    "level",
    "game_pk",
    "at_bat_index",
    "pitch_number",
    "batter",
    "pitcher",
    "stand",
    "p_throws",
    "balls",
    "strikes",
    "pitch_result_code",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pbp-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--game-context",
        type=Path,
        default=Path(
            "reports/generated/defensive-venue-context-v1/affiliated-game-context.parquet"
        ),
    )
    parser.add_argument(
        "--base-panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-pitch-game-features-v1"),
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=list(DEFAULT_SEASONS))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def _season_paths(root: Path, season: int) -> list[Path]:
    return sorted(root.glob(f"season={season}/level=*/catcher_pitches/*.parquet"))


def _read_season(paths: list[Path]) -> pl.DataFrame:
    if not paths:
        raise ValueError("no catcher pitch partitions selected")
    return pl.scan_parquet([str(path) for path in paths]).select(PITCH_COLUMNS).collect()


def main() -> int:
    args = _args()
    seasons = tuple(sorted(set(args.seasons)))
    if not seasons or any(season >= 2025 for season in seasons):
        raise ValueError("development pitch/game seasons must be nonempty and end by 2024")
    if 2020 in seasons:
        raise ValueError("2020 has no affiliated MiLB season and must remain explicitly absent")
    context = pl.read_parquet(args.game_context)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    annual_frames: list[pl.DataFrame] = []
    season_reports: list[dict[str, object]] = []
    for season in seasons:
        output = tables / f"player-season-features-{season}.parquet"
        paths = _season_paths(args.pbp_root, season)
        if output.exists() and not args.overwrite:
            features = pl.read_parquet(output)
            source_pitch_count = int(features["pitch_count"].sum())
        else:
            pitches = _read_season(paths)
            source_pitch_count = pitches.height
            features = build_player_season_pitch_game_features(
                pitches,
                context.filter(pl.col("season") == season),
            )
            write_canonical_parquet(
                features,
                output,
                table_name=f"hitter_pitch_game_features_{season}_v1",
            )
        annual_frames.append(features)
        season_reports.append(
            {
                "season": season,
                "source_partitions": len(paths),
                "pitch_count": source_pitch_count,
                "plate_appearances": int(features["pa_count"].sum()),
                "player_seasons": features.height,
                "player_game_exposures": int(features["game_count"].sum()),
                "weighted_game_context_coverage": float(
                    (
                        features["game_context_coverage"] * features["pa_count"]
                    ).sum()
                    / max(int(features["pa_count"].sum()), 1)
                ),
            }
        )
        print(json.dumps(season_reports[-1], sort_keys=True), flush=True)

    annual = pl.concat(annual_frames, how="diagonal_relaxed").sort(
        "season", "player_id"
    )
    base_panel = pl.read_parquet(args.base_panel)
    extended = attach_pitch_game_lags(base_panel, annual)
    annual_artifact = write_canonical_parquet(
        annual,
        tables / "player-season-features.parquet",
        table_name="hitter_pitch_game_player_season_features_v1",
    )
    panel_artifact = write_canonical_parquet(
        extended,
        tables / "modeling-panel.parquet",
        table_name="hitter_value_panel_with_pitch_game_features_v1",
    )
    coverage_by_origin = (
        extended.group_by("origin_year")
        .agg(
            pl.len().alias("panel_rows"),
            pl.col("pitch_lag0__available").sum().alias("lag0_rows"),
            pl.col("pitch_lag1__available").sum().alias("lag1_rows"),
            pl.col("pitch_lag2__available").sum().alias("lag2_rows"),
        )
        .sort("origin_year")
        .with_columns(
            (pl.col("lag0_rows") / pl.col("panel_rows")).alias("lag0_rate"),
            (pl.col("lag1_rows") / pl.col("panel_rows")).alias("lag1_rate"),
            (pl.col("lag2_rows") / pl.col("panel_rows")).alias("lag2_rate"),
        )
    )
    feature_columns = [column for column in annual.columns if column not in {"season", "player_id"}]
    report = {
        "schema_version": "1.0",
        "status": "universal_pitch_sequence_and_game_environment_materialized",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "seasons": list(seasons),
        "missing_2020_milb_season": True,
        "scope": "all affiliated levels; regular-season result/count pitch sequences",
        "counts": {
            "pitch_rows": sum(int(row["pitch_count"]) for row in season_reports),
            "player_seasons": annual.height,
            "annual_feature_columns": len(feature_columns),
            "base_panel_columns": base_panel.width,
            "extended_panel_columns": extended.width,
        },
        "season_coverage": season_reports,
        "panel_coverage": coverage_by_origin.to_dicts(),
        "feature_blocks": {
            "sequence": [
                column
                for column in feature_columns
                if not column.startswith("oa_")
                and column
                not in {
                    "game_context_coverage",
                    "mean_temperature_f",
                    "sd_temperature_f",
                    "mean_wind_mph",
                    "night_pa_share",
                    "wind_out_pa_share",
                    "wind_in_pa_share",
                    "wind_cross_pa_share",
                    "wind_calm_pa_share",
                    "hot_pa_share",
                    "cold_pa_share",
                    "rain_pa_share",
                    "cloudy_pa_share",
                    "artificial_surface_pa_share",
                    "closed_roof_pa_share",
                    "mean_left_field_line_ft",
                    "mean_center_field_ft",
                    "mean_right_field_line_ft",
                    "mean_attendance",
                    "mean_game_duration_minutes",
                    "mean_delay_minutes",
                    "unique_venues",
                    "unique_home_plate_umpires",
                }
            ],
            "opponent_and_umpire_adjusted": [
                column for column in feature_columns if column.startswith("oa_")
            ],
            "game_environment": [
                column
                for column in feature_columns
                if column
                in {
                    "game_context_coverage",
                    "mean_temperature_f",
                    "sd_temperature_f",
                    "mean_wind_mph",
                    "night_pa_share",
                    "wind_out_pa_share",
                    "wind_in_pa_share",
                    "wind_cross_pa_share",
                    "wind_calm_pa_share",
                    "hot_pa_share",
                    "cold_pa_share",
                    "rain_pa_share",
                    "cloudy_pa_share",
                    "artificial_surface_pa_share",
                    "closed_roof_pa_share",
                    "mean_left_field_line_ft",
                    "mean_center_field_ft",
                    "mean_right_field_line_ft",
                    "mean_attendance",
                    "mean_game_duration_minutes",
                    "mean_delay_minutes",
                    "unique_venues",
                    "unique_home_plate_umpires",
                }
            ],
        },
        "method": {
            "universal_pitch_evidence": "result code, post-pitch count, batter/pitcher handedness",
            "count_reconstruction": "previous physical pitch post-count within plate appearance",
            "raw_rate_shrinkage": "100-opportunity season-wide empirical prior",
            "handedness_split_shrinkage": "75-opportunity player overall prior",
            "opponent_adjustment": "level/count/batter-side/pitcher-side cell plus 250-pitch pitcher shrinkage",
            "called_strike_adjustment": "opponent adjustment plus 200-decision home-plate umpire shrinkage",
            "weather_semantics": "official game-baseline snapshot, not time-varying play weather",
        },
        "artifacts": {
            "annual_features": annual_artifact.as_record(),
            "extended_modeling_panel": panel_artifact.as_record(),
        },
        "next_gate": "identical chronological base-vs-added-feature ablation",
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
