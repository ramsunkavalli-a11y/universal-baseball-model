#!/usr/bin/env python3
"""Materialize chronology-safe playing-time v1 predictor candidates.

This is a feature *surface*, not a frozen model feature set. It joins already-
certified player-game evidence, frozen B2 October snapshots, and certified binary
40-man membership. No target outcomes are used to construct predictors and no
2025 data is accessed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_projection_batting_v1_development_evidence import _load_one_season
from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.projection_composition import projection_profile_to_ilr
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS
from universal_baseball.storage import write_canonical_parquet


SOURCE_SEASONS = (2021, 2022, 2023, 2024)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--membership-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-predictor-surface"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def _season_pa(summary: pl.DataFrame, *, prefix: str) -> pl.DataFrame:
    return (
        summary.group_by("player_id")
        .agg(
            pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias(f"{prefix}_affiliated_pa"),
            pl.when(pl.col("level_group") == "MLB")
            .then(pl.col("batting_plate_appearances"))
            .otherwise(0)
            .sum()
            .cast(pl.Int64)
            .alias(f"{prefix}_mlb_pa"),
            pl.when(pl.col("level_group") != "MLB")
            .then(pl.col("batting_plate_appearances"))
            .otherwise(0)
            .sum()
            .cast(pl.Int64)
            .alias(f"{prefix}_milb_pa"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias(f"{prefix}_affiliated_games"),
        )
        .sort("player_id")
    )


def _b2_ilr(profile: pl.DataFrame) -> pl.DataFrame:
    required = {"player_id", "core_bin", "baseline2_latent_probability"}
    missing = sorted(required - set(profile.columns))
    if missing:
        raise RuntimeError(f"B2 profile missing fields: {missing}")
    rows: list[dict[str, object]] = []
    for key, group in profile.group_by("player_id", maintain_order=True):
        player_id = int(key[0] if isinstance(key, tuple) else key)
        values = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        if set(values) != set(ALL_CORE_BINS):
            raise RuntimeError(f"B2 profile incomplete for player {player_id}")
        coords = projection_profile_to_ilr(values)
        row: dict[str, object] = {"player_id": player_id}
        row.update({f"b2_ilr_{index:02d}": float(value) for index, value in enumerate(coords)})
        row["b2_bb_hbp_probability"] = values["BB_HBP"]
        row["b2_k_probability"] = values["K"]
        rows.append(row)
    return pl.DataFrame(rows).sort("player_id")


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    season_data: dict[int, pl.DataFrame] = {}
    for season in SOURCE_SEASONS:
        summary, _profile, _report = _load_one_season(args.evidence_root, season)
        season_data[season] = summary

    membership = pl.read_parquet(
        _one(
            args.membership_root,
            "historical_40man_membership.parquet",
            "certified historical 40-man membership",
        )
    )
    required_membership = {"season", "player_id", "team_id", "on_40man"}
    if required_membership - set(membership.columns):
        raise RuntimeError("historical 40-man membership artifact has unexpected schema")
    if membership.group_by(["season", "player_id"]).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("historical 40-man membership violates season + player grain")

    fold_reports: list[dict[str, object]] = []
    for fold in PROJECTION_V1_DEVELOPMENT_FOLDS:
        year = fold.snapshot_date.year
        current_summary = season_data[year].with_columns(
            pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_date")
        ).filter(pl.col("_date") < pl.lit(fold.snapshot_date))
        previous_summary = (
            season_data[year - 1].with_columns(
                pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_date")
            ).filter(pl.col("_date") < pl.lit(fold.snapshot_date))
            if year - 1 in season_data
            else pl.DataFrame()
        )
        current_pa = _season_pa(current_summary, prefix="current_season")
        previous_pa = (
            _season_pa(previous_summary, prefix="prior_season")
            if not previous_summary.is_empty()
            else pl.DataFrame(schema={"player_id": pl.Int64})
        )

        snapshot_fold_root = args.snapshot_root / "tables" / fold.label
        context = pl.read_parquet(
            _one(snapshot_fold_root, "player_context.parquet", f"{fold.label} player context")
        )
        b2_profile = pl.read_parquet(
            _one(snapshot_fold_root, "frozen_b2_profile.parquet", f"{fold.label} B2 profile")
        )
        ilr = _b2_ilr(b2_profile)
        membership_year = membership.filter(pl.col("season") == year).select(
            "player_id",
            pl.col("team_id").alias("forty_man_team_id"),
            "on_40man",
            "source_row_count",
            "source_status_conflict",
        )

        predictors = (
            context.join(current_pa, on="player_id", how="left")
            .join(previous_pa, on="player_id", how="left")
            .join(ilr, on="player_id", how="left")
            .join(membership_year, on="player_id", how="left")
        )
        count_columns = [
            "current_season_affiliated_pa",
            "current_season_mlb_pa",
            "current_season_milb_pa",
            "current_season_affiliated_games",
            "prior_season_affiliated_pa",
            "prior_season_mlb_pa",
            "prior_season_milb_pa",
            "prior_season_affiliated_games",
        ]
        existing_counts = [column for column in count_columns if column in predictors.columns]
        predictors = predictors.with_columns(
            *[pl.col(column).fill_null(0).cast(pl.Int64) for column in existing_counts],
            pl.col("on_40man").fill_null(False).cast(pl.Boolean),
            pl.col("source_row_count").fill_null(0).cast(pl.Int64),
            pl.col("source_status_conflict").fill_null(False).cast(pl.Boolean),
        ).sort("player_id")

        if predictors.filter(pl.col("age_years").is_null() | pl.col("as_of_level_group").is_null()).height:
            raise RuntimeError(f"{fold.label} predictor surface has missing age/level")
        if predictors.filter(pl.col("current_season_affiliated_pa") <= 0).height:
            raise RuntimeError(f"{fold.label} snapshot player lacks positive current-season PA")
        if predictors.select(pl.col("b2_ilr_00").is_null().sum()).item() != 0:
            raise RuntimeError(f"{fold.label} predictor surface lacks B2 ILR state")

        fold_dir = table_root / fold.label
        fold_dir.mkdir(parents=True, exist_ok=True)
        storage = write_canonical_parquet(
            predictors,
            fold_dir / "predictors.parquet",
            table_name=f"{fold.label}_playing_time_predictor_surface",
        ).as_record()
        by_level = (
            predictors.group_by("as_of_level_group")
            .agg(
                pl.len().cast(pl.Int64).alias("players"),
                pl.col("on_40man").sum().cast(pl.Int64).alias("on_40man_players"),
                pl.col("current_season_mlb_pa").sum().cast(pl.Int64).alias("current_mlb_pa"),
            )
            .sort("as_of_level_group")
        )
        fold_reports.append(
            {
                "fold": fold.label,
                "snapshot_date": fold.snapshot_date.isoformat(),
                "player_count": int(predictors.height),
                "on_40man_player_count": int(predictors.get_column("on_40man").sum()),
                "players_with_current_mlb_pa": int((predictors.get_column("current_season_mlb_pa") > 0).sum()),
                "players_with_prior_mlb_pa": int((predictors.get_column("prior_season_mlb_pa") > 0).sum())
                if "prior_season_mlb_pa" in predictors.columns
                else 0,
                "source_status_conflict_members_retained_as_membership_only": int(
                    predictors.get_column("source_status_conflict").sum()
                ),
                "by_as_of_level": by_level.to_dicts(),
                "storage": storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_predictor_surface_pre_model",
        "source_seasons": list(SOURCE_SEASONS),
        "folds": fold_reports,
        "feature_surface_semantics": {
            "frozen_model_feature_set": False,
            "40man_authorized_fact": "binary membership only",
            "40man_row_status_used_as_predictor": False,
            "b2_skill_state": "fixed pre-target 11-D ILR composition plus BB/HBP and K diagnostics",
        },
        "boundary": {
            "2025_accessed": False,
            "playing_time_model_fit": False,
            "candidate_selected": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 predictor surface",
        "",
        "- Frozen model feature set: False",
        "- 40-man semantic: binary membership only",
        "- 2025 accessed: False",
        "- Model fit: False",
        "",
    ]
    for row in fold_reports:
        lines.extend(
            [
                f"## {row['fold']}",
                f"- players: {row['player_count']:,}",
                f"- on 40-man: {row['on_40man_player_count']:,}",
                f"- current-season MLB PA > 0: {row['players_with_current_mlb_pa']:,}",
                f"- prior-season MLB PA > 0: {row['players_with_prior_mlb_pa']:,}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
