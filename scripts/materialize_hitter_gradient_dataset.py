#!/usr/bin/env python3
"""Build the frozen, chronology-safe dataset for the hitter gradient challenger."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_schedule_opponent_adjustments,
    fit_component_park_factors,
)
from universal_baseball.hitter_gradient_materialization import (
    CONTACT_OUTCOMES,
    PARK_COMPONENTS,
    attach_as_of_park_features,
    build_fold_manifest,
    build_modeling_rows,
    build_player_season_features,
    join_contact_context_events,
    make_park_vintage,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ORIGINS = (2021, 2022, 2023, 2024)
PARK_PRIOR_EXPOSURE = 5000.0
PLAYER_CELL_PRIOR = 100.0


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--context-events", type=Path, required=True)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-gradient-dataset-v1"),
    )
    return parser.parse_args()


def _load_contacts(root: Path) -> pl.DataFrame:
    frames = []
    for year in ORIGINS:
        path = (
            root
            / f"full-bip-context-{year}/tables/hitter_full_bip_event_outcomes.parquet"
        )
        frames.append(pl.read_parquet(path))
    result = pl.concat(frames, how="vertical_relaxed")
    if set(result["season"].unique().to_list()) != set(ORIGINS):
        raise ValueError("terminal contacts do not cover the frozen origins")
    return result


def _load_games(root: Path) -> pl.DataFrame:
    path = root / "affiliated-game-context/tables/affiliated-game-context.parquet"
    return pl.read_parquet(path).filter(pl.col("season").is_in(ORIGINS))


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_by_pitch").alias("hbp"),
        (
            pl.col("hits")
            - pl.col("doubles")
            - pl.col("triples")
            - pl.col("home_runs")
        ).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("plate_appearances")
            - pl.sum_horizontal(*PARK_COMPONENTS[:-1])
        ).alias("other")
    )


def _pitcher_as_hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        (
            pl.col("hits")
            - pl.col("doubles")
            - pl.col("triples")
            - pl.col("home_runs")
        ).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("batters_faced")
            - pl.sum_horizontal(*PARK_COMPONENTS[:-1])
        ).alias("other")
    )


def _park_vintages(root: Path, games: pl.DataFrame) -> pl.DataFrame:
    split_root = root / "affiliated-home-away-components/tables"
    hitters = _hitter_components(
        pl.read_parquet(split_root / "affiliated-hitter-home-away.parquet")
    )
    pitchers = _pitcher_as_hitter_components(
        pl.read_parquet(split_root / "affiliated-pitcher-home-away.parquet")
    )
    team_context = pl.read_parquet(
        root / "affiliated-team-context/tables/affiliated-team-context.parquet"
    )
    park_games = pl.read_parquet(
        root / "affiliated-game-context/tables/affiliated-game-context.parquet"
    ).filter(pl.col("season").is_in(ORIGINS))
    adjustments = build_schedule_opponent_adjustments(
        park_games,
        pitchers.filter(pl.col("season").is_in(ORIGINS)),
        exposure_column="batters_faced",
        component_columns=PARK_COMPONENTS,
    )
    observations = build_component_park_observations(
        hitters.filter(pl.col("season").is_in(ORIGINS)),
        team_context.filter(pl.col("season").is_in(ORIGINS)),
        exposure_column="plate_appearances",
        component_columns=PARK_COMPONENTS,
        opponent_adjustments=adjustments,
    )
    vintages = []
    for origin in ORIGINS:
        factors = fit_component_park_factors(
            observations,
            through_season=origin,
            component_columns=PARK_COMPONENTS,
            prior_exposure=PARK_PRIOR_EXPOSURE,
        )
        vintages.append(
            make_park_vintage(
                factors,
                source_season=origin,
                prior_exposure=PARK_PRIOR_EXPOSURE,
            )
        )
    return pl.concat(vintages, how="vertical_relaxed")


def _annual_surfaces(root: Path) -> pl.DataFrame:
    frames = []
    for year in ORIGINS:
        frame = pl.read_parquet(
            root / f"hitter-multiyear-age-level-base/tables/annual-{year}.parquet"
        ).with_columns(pl.lit(year).alias("season"))
        frames.append(frame)
    return pl.concat(frames, how="vertical_relaxed")


def _assert_probability_blocks(frame: pl.DataFrame) -> None:
    bad = 0
    for contact_bin in (
        "PULL_GB",
        "CENTER_GB",
        "OPPO_GB",
        "PULL_LD",
        "CENTER_LD",
        "OPPO_LD",
        "PULL_OFFB",
        "CENTER_OFFB",
        "OPPO_OFFB",
        "IFFB",
    ):
        total = pl.sum_horizontal(
            *(
                f"contact_result__{contact_bin}__{outcome}"
                for outcome in CONTACT_OUTCOMES
            )
        )
        bad += frame.filter((total - 1.0).abs() > 1e-9).height
    if bad:
        raise ValueError(f"{bad} player contact probability blocks do not sum to one")


def _source_records(paths: dict[str, Path]) -> dict[str, dict[str, str | int]]:
    return {
        label: {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for label, path in paths.items()
    }


def main() -> int:
    args = _args()
    if args.as_of_date.year < 2025:
        raise ValueError("as-of date predates the final development target season")
    contacts = _load_contacts(args.generated_root)
    context = pl.read_parquet(args.context_events).filter(
        pl.col("season").is_in(ORIGINS)
    )
    games = _load_games(args.generated_root)
    events = join_contact_context_events(contacts, context, games)
    vintages = _park_vintages(args.generated_root, games)
    events = attach_as_of_park_features(events, vintages)
    player_features = build_player_season_features(
        events,
        _annual_surfaces(args.generated_root),
        player_prior=PLAYER_CELL_PRIOR,
    )
    _assert_probability_blocks(player_features)
    benchmark_path = (
        args.generated_root
        / "hitter-componentwise-reconciled-base/tables/player-predictions.parquet"
    )
    benchmark = pl.read_parquet(benchmark_path)
    modeling_rows = build_modeling_rows(player_features, benchmark)
    manifest = build_fold_manifest(modeling_rows)

    event_exact_rate = float(events["opponent_context_known"].mean())
    venue_rate = float(events["venue_known"].mean())
    benchmark_match_rate = modeling_rows.height / benchmark.height
    if event_exact_rate < 0.94 or venue_rate < 0.99 or benchmark_match_rate < 0.99:
        raise ValueError(
            "materialization coverage gate failed: "
            f"opponent={event_exact_rate:.4f}, venue={venue_rate:.4f}, "
            f"benchmark={benchmark_match_rate:.4f}"
        )
    if events.filter(
        pl.col("park_factor_through_season") > pl.col("season")
    ).height:
        raise ValueError("park factor uses a future vintage")
    if modeling_rows.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 targets entered the modeling table")

    table_root = args.output_root / "tables"
    artifacts = {
        "events": write_canonical_parquet(
            events,
            table_root / "contact-context-events.parquet",
            table_name="hitter_gradient_contact_context_events_v1",
        ).as_record(),
        "park_vintages": write_canonical_parquet(
            vintages,
            table_root / "park-factor-vintages.parquet",
            table_name="hitter_gradient_park_factor_vintages_v1",
        ).as_record(),
        "player_features": write_canonical_parquet(
            player_features,
            table_root / "player-season-features.parquet",
            table_name="hitter_gradient_player_season_features_v1",
        ).as_record(),
        "modeling_rows": write_canonical_parquet(
            modeling_rows,
            table_root / "modeling-rows.parquet",
            table_name="hitter_gradient_modeling_rows_v1",
        ).as_record(),
        "fold_manifest": write_canonical_parquet(
            manifest,
            table_root / "fold-manifest.parquet",
            table_name="hitter_gradient_fold_manifest_v1",
        ).as_record(),
    }
    source_paths = {
        **{
            f"contacts_{year}": args.generated_root
            / f"full-bip-context-{year}/tables/hitter_full_bip_event_outcomes.parquet"
            for year in ORIGINS
        },
        "pa_context": args.context_events,
        "games": args.generated_root
        / "affiliated-game-context/tables/affiliated-game-context.parquet",
        "team_context": args.generated_root
        / "affiliated-team-context/tables/affiliated-team-context.parquet",
        "hitter_home_away": args.generated_root
        / "affiliated-home-away-components/tables/affiliated-hitter-home-away.parquet",
        "pitcher_home_away": args.generated_root
        / "affiliated-home-away-components/tables/affiliated-pitcher-home-away.parquet",
        "benchmark": benchmark_path,
    }
    report = {
        "schema_version": "1.0",
        "status": "chronology_safe_hitter_gradient_dataset_materialized",
        "as_of_date": args.as_of_date.isoformat(),
        "scope": "affiliated_milb_hitter_next_season_contact_outcomes",
        "protected_2026_outcomes_used": False,
        "origins": list(ORIGINS),
        "targets": [year + 1 for year in ORIGINS],
        "counts": {
            "contact_events": events.height,
            "player_seasons": player_features.height,
            "benchmark_rows": benchmark.height,
            "modeling_rows": modeling_rows.height,
            "fold_manifest_rows": manifest.height,
            "park_vintage_rows": vintages.height,
            "player_feature_columns": player_features.width,
            "modeling_columns": modeling_rows.width,
        },
        "coverage": {
            "exact_strict_opponent_context": event_exact_rate,
            "venue": venue_rate,
            "park_factor_known": float(events["park_factor_known"].mean()),
            "benchmark_player_match": benchmark_match_rate,
        },
        "chronology": {
            "opponent_features": "strictly prior to each plate appearance",
            "park_features": "fit through the completed source season only",
            "player_features": "source season or earlier",
            "targets": "exactly source season plus one",
            "outer_folds": "expanding window; training targets known by evaluation origin",
        },
        "fallbacks": {
            "missing_or_disagreeing_opponent_context": "zero residual plus known-rate flag",
            "unknown_venue_or_park": "zero park effect plus known-rate/reliability flags",
            "sparse_contact_result_cell": (
                f"pooled to source-level contact-bin outcome distribution with "
                f"{PLAYER_CELL_PRIOR:.0f} event prior"
            ),
        },
        "fixed_parameters": {
            "park_prior_exposure": PARK_PRIOR_EXPOSURE,
            "player_contact_cell_prior": PLAYER_CELL_PRIOR,
        },
        "sources": _source_records(source_paths),
        "artifacts": artifacts,
        "next_gate": (
            "Fit simple regularized and tree challengers on these exact rows; compare "
            "each with contact-only overall and by workload/level-transition strata."
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
