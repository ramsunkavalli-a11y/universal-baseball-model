#!/usr/bin/env python3
"""Build cutoff-safe 2025 hitter and pitcher WAR paths for historical replay."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.conditional_war_rates import (
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)
from universal_baseball.hitter_opportunity_paths import (
    HitterOpportunityFit,
    score_hitter_opportunity_paths,
)
from universal_baseball.opportunity_model_v2 import (
    build_universal_hitter_opportunity_fold,
    build_universal_hitter_opportunity_predictors,
    fit_universal_hitter_opportunity_form,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_fold,
    build_universal_pitcher_opportunity_predictors,
    fit_universal_pitcher_opportunity_form,
)
from universal_baseball.pitcher_opportunity_paths import (
    PitcherOpportunityFit,
    score_pitcher_opportunity_paths,
)
from universal_baseball.playing_time_model import (
    PT_FORM_P,
    PT_FORM_U,
    build_playing_time_design,
    predict_playing_time_hurdle,
)
from universal_baseball.playing_time_fit_artifact import playing_time_fit_to_artifact
from universal_baseball.storage import sha256_file, write_canonical_parquet


CHECKPOINT_DATE = date(2025, 3, 27)
SNAPSHOT_YEAR = 2024
FORECAST_YEAR = 2025
FORECAST_SEASONS = (2025, 2026, 2027, 2028, 2029)
TRAINING_SNAPSHOT_YEARS = (2018, 2021, 2022, 2023)
PITCHER_POSITION_PATTERN = r"(?:^|/)(?:P|SP|RP)(?:/|$)"
POSITION_CODES = {
    "C": "2",
    "1B": "3",
    "2B": "4",
    "3B": "5",
    "SS": "6",
    "LF": "7",
    "CF": "8",
    "RF": "9",
    "OF": "O",
    "DH": "10",
}
FIT_PACKAGE_ROOT = Path("model_artifacts/opportunity-v2-pre2025-replay")


def _extend_universes(
    hitter_snapshot: pl.DataFrame,
    pitcher_snapshot: pl.DataFrame,
    opening: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    pitcher_position = pl.col("position").str.to_uppercase().str.contains(
        PITCHER_POSITION_PATTERN
    )
    opening_hitters = opening.filter(
        pl.col("projected_pa").is_not_null() | ~pitcher_position
    ).select(
        pl.lit(SNAPSHOT_YEAR, dtype=pl.Int64).alias("snapshot_year"),
        "player_id",
        (pl.col("age") - 1.0).alias("age_years"),
        pl.lit("UNKNOWN").alias("as_of_level_group"),
    )
    opening_pitchers = opening.filter(
        pl.col("projected_ip").is_not_null() | pitcher_position
    ).select(
        pl.lit(SNAPSHOT_YEAR, dtype=pl.Int64).alias("snapshot_year"),
        "player_id",
        (pl.col("age") - 1.0).alias("age_years"),
        pl.lit("UNKNOWN").alias("as_of_level_group"),
        pl.when(pl.col("position").str.to_uppercase().str.contains("SP"))
        .then(pl.lit("starter"))
        .when(pl.col("position").str.to_uppercase().str.contains("RP"))
        .then(pl.lit("reliever"))
        .otherwise(pl.lit("unknown"))
        .alias("as_of_role"),
    )
    hitters = pl.concat(
        [
            hitter_snapshot,
            opening_hitters.join(
                hitter_snapshot.select("player_id"), on="player_id", how="anti"
            ),
        ]
    ).sort("player_id")
    pitchers = pl.concat(
        [
            pitcher_snapshot,
            opening_pitchers.join(
                pitcher_snapshot.select("player_id"), on="player_id", how="anti"
            ),
        ]
    ).sort("player_id")
    return hitters, pitchers


def _hitter_position_players(
    universe: pl.DataFrame, current_stats: pl.DataFrame, opening: pl.DataFrame
) -> pl.DataFrame:
    history_positions = (
        current_stats.filter(pl.col("stat_group") == "hitting")
        .group_by("player_id", "position_code")
        .agg(pl.col("plate_appearances").sum().alias("position_pa"))
        .sort(
            ["player_id", "position_pa", "position_code"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "position_code")
    )
    opening_positions = opening.with_columns(
        pl.col("position")
        .str.to_uppercase()
        .str.split("/")
        .list.first()
        .replace_strict(POSITION_CODES, default="", return_dtype=pl.String)
        .alias("opening_position_code")
    ).select("player_id", "opening_position_code")
    return (
        universe.select(
            "player_id",
            (pl.col("age_years") + 1.0).alias("age_years"),
        )
        .join(history_positions, on="player_id", how="left")
        .join(opening_positions, on="player_id", how="left")
        .with_columns(
            pl.coalesce("position_code", "opening_position_code", pl.lit("")).alias(
                "position_code"
            )
        )
        .select("player_id", "age_years", "position_code")
    )


def _fit_selected_predictions(
    snapshots_root: Path,
    membership: pl.DataFrame,
) -> tuple[
    pl.DataFrame,
    pl.DataFrame,
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    hitter_snapshots = pl.read_parquet(snapshots_root / "hitter_snapshots.parquet")
    pitcher_snapshots = pl.read_parquet(snapshots_root / "pitcher_snapshots.parquet")
    hitter_folds = []
    pitcher_folds = []
    for year in TRAINING_SNAPSHOT_YEARS:
        current = pl.read_parquet(
            snapshots_root / str(year) / "affiliated_season_stats.parquet"
        )
        following = pl.read_parquet(
            snapshots_root / str(year + 1) / "affiliated_season_stats.parquet"
        )
        hitter_folds.append(
            build_universal_hitter_opportunity_fold(
                hitter_snapshots,
                current,
                following,
                membership,
                snapshot_year=year,
            )
        )
        pitcher_folds.append(
            build_universal_pitcher_opportunity_fold(
                pitcher_snapshots,
                current,
                following,
                membership,
                snapshot_year=year,
            )
        )
    hitter_fit = fit_universal_hitter_opportunity_form(
        hitter_folds, form=PT_FORM_U
    )
    pitcher_fit = fit_universal_pitcher_opportunity_form(
        pitcher_folds, form=PT_FORM_P
    )
    current = pl.read_parquet(
        snapshots_root / str(SNAPSHOT_YEAR) / "affiliated_season_stats.parquet"
    )
    hitter_predictors = build_universal_hitter_opportunity_predictors(
        hitter_snapshots,
        current,
        membership,
        snapshot_year=SNAPSHOT_YEAR,
    )
    pitcher_predictors = build_universal_pitcher_opportunity_predictors(
        pitcher_snapshots,
        current,
        membership,
        snapshot_year=SNAPSHOT_YEAR,
    )
    hitter_predictions = predict_playing_time_hurdle(
        hitter_fit,
        build_playing_time_design(hitter_predictors, form=PT_FORM_U),
    ).with_columns(
        pl.lit(hitter_fit.nb_alpha).alias("model_nb_alpha"),
        pl.lit("hitter_opportunity_v2_pre2025_refit").alias("model_id"),
        pl.lit("retrospective_cutoff_safe_selected_form").alias("model_status"),
    )
    pitcher_predictions = predict_playing_time_hurdle(
        pitcher_fit,
        build_playing_time_design(pitcher_predictors, form=PT_FORM_P),
    ).rename(
        {
            "predicted_any_mlb_pa_probability": "predicted_any_mlb_bf_probability",
            "predicted_positive_mlb_pa_mean": "predicted_positive_mlb_bf_mean",
            "predicted_expected_mlb_pa": "predicted_expected_mlb_bf",
        }
    ).with_columns(
        pl.lit(pitcher_fit.nb_alpha).alias("model_nb_alpha"),
        pl.lit("pitcher_opportunity_v2_pre2025_refit").alias("model_id"),
        pl.lit("retrospective_cutoff_safe_selected_form").alias("model_status"),
    )
    fit_summary = {
        "training_snapshot_years": list(TRAINING_SNAPSHOT_YEARS),
        "latest_training_target_year": 2024,
        "hitter_form": PT_FORM_U,
        "pitcher_form": PT_FORM_P,
        "hitter_training_players": hitter_fit.participation_training_players,
        "pitcher_training_players": pitcher_fit.participation_training_players,
        "hitter_nb_alpha": hitter_fit.nb_alpha,
        "pitcher_nb_alpha": pitcher_fit.nb_alpha,
    }
    return (
        hitter_predictions,
        pitcher_predictions,
        fit_summary,
        playing_time_fit_to_artifact(hitter_fit),
        playing_time_fit_to_artifact(pitcher_fit),
    )


def _coverage(paths: pl.DataFrame) -> list[dict[str, object]]:
    return (
        paths.group_by("horizon", "coverage_tier")
        .len()
        .sort(["horizon", "coverage_tier"])
        .to_dicts()
    )


def _verify_durable_fits(
    hitter_fit_artifact: dict[str, object],
    pitcher_fit_artifact: dict[str, object],
) -> tuple[Path, Path]:
    manifest = json.loads(
        (FIT_PACKAGE_ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    paths = (
        FIT_PACKAGE_ROOT / "hitter-opportunity-fit.json",
        FIT_PACKAGE_ROOT / "pitcher-opportunity-fit.json",
    )
    expected_payloads = (hitter_fit_artifact, pitcher_fit_artifact)
    for path, expected_payload in zip(paths, expected_payloads, strict=True):
        artifact = manifest["artifacts"][path.name]
        if sha256_file(path) != artifact["sha256"]:
            raise ValueError(f"durable fit hash differs from manifest: {path}")
        if json.loads(path.read_text(encoding="utf-8")) != expected_payload:
            raise ValueError(f"durable fit differs from deterministic refit: {path}")
    return paths


def main() -> int:
    source_root = Path("reports/generated/opportunity-history-sources-v2/tables")
    membership_path = Path(
        "reports/generated/opportunity-40man-history/tables/"
        "historical_40man_membership.parquet"
    )
    fallback_root = Path("reports/generated/opportunity-historical-fits")
    skill_root = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
    opening_path = Path(
        "reports/generated/fangraphs-opening-day-workbooks/2025/"
        "opening-day-projections.parquet"
    )
    output = Path("reports/generated/historical-projection-paths/2025-03-27")
    membership = pl.read_parquet(membership_path)
    opening = pl.read_parquet(opening_path)
    hitter_snapshot = pl.read_parquet(source_root / "hitter_snapshots.parquet").filter(
        pl.col("snapshot_year") == SNAPSHOT_YEAR
    )
    pitcher_snapshot = pl.read_parquet(
        source_root / "pitcher_snapshots.parquet"
    ).filter(pl.col("snapshot_year") == SNAPSHOT_YEAR)
    hitter_universe, pitcher_universe = _extend_universes(
        hitter_snapshot, pitcher_snapshot, opening
    )
    (
        hitter_selected,
        pitcher_selected,
        fit_summary,
        hitter_fit_artifact,
        pitcher_fit_artifact,
    ) = _fit_selected_predictions(source_root, membership)
    hitter_fit_path, pitcher_fit_path = _verify_durable_fits(
        hitter_fit_artifact, pitcher_fit_artifact
    )

    fallback_report = json.loads(
        (fallback_root / "report.json").read_text(encoding="utf-8")
    )
    if int(fallback_report["forecast_cutoff_year"]) != FORECAST_YEAR:
        raise ValueError("historical opportunity fallbacks have the wrong cutoff")
    horizons = tuple(range(1, len(FORECAST_SEASONS) + 1))
    hitter_fallback = HitterOpportunityFit(
        references=pl.read_parquet(fallback_root / "tables/hitter_references.parquet"),
        horizons=horizons,
        age_band_width=2,
        participation_prior_players=50.0,
        workload_prior_positive_players=20.0,
    )
    pitcher_fallback = PitcherOpportunityFit(
        references=pl.read_parquet(fallback_root / "tables/pitcher_references.parquet"),
        horizons=horizons,
        age_band_width=2,
    )
    hitter_opportunity = score_hitter_opportunity_paths(
        hitter_universe,
        hitter_fallback,
        as_of_date=CHECKPOINT_DATE,
        forecast_year=FORECAST_YEAR,
        selected_next_year=hitter_selected,
    )
    pitcher_opportunity = score_pitcher_opportunity_paths(
        pitcher_universe,
        pitcher_fallback,
        as_of_date=CHECKPOINT_DATE,
        forecast_year=FORECAST_YEAR,
        selected_next_year=pitcher_selected,
    )

    skill_report = json.loads((skill_root / "report.json").read_text(encoding="utf-8"))
    reference = skill_report["reference_environment"]
    if int(reference["season"]) != SNAPSHOT_YEAR:
        raise ValueError("historical skill reference environment is not 2024")
    current_stats = pl.read_parquet(
        source_root / str(SNAPSHOT_YEAR) / "affiliated_season_stats.parquet"
    )
    hitter_players = _hitter_position_players(
        hitter_universe, current_stats, opening
    )
    pitcher_players = pitcher_universe.select(
        "player_id", (pl.col("age_years") + 1.0).alias("age_years")
    )
    hitting_history = pl.read_parquet(
        skill_root / "tables/mlb_hitting_components.parquet"
    ).filter(pl.col("season") <= SNAPSHOT_YEAR)
    pitching_history = pl.read_parquet(
        skill_root / "tables/mlb_pitching_components.parquet"
    ).filter(pl.col("season") <= SNAPSHOT_YEAR)
    hitter_rates = build_hitter_conditional_war_rates(
        hitter_players,
        hitting_history,
        current_season=FORECAST_YEAR,
        forecast_seasons=FORECAST_SEASONS,
        reference_plate_appearances=int(reference["batting_plate_appearances"]),
        runs_per_win=float(reference["runs_per_win"]),
        evidence_anchor_season=SNAPSHOT_YEAR,
        reference_season=SNAPSHOT_YEAR,
    )
    pitcher_rates = build_pitcher_conditional_war_rates(
        pitcher_players,
        pitching_history,
        current_season=FORECAST_YEAR,
        forecast_seasons=FORECAST_SEASONS,
        reference_batters_faced=int(reference["pitching_batters_faced"]),
        runs_per_win=float(reference["runs_per_win"]),
        evidence_anchor_season=SNAPSHOT_YEAR,
        reference_season=SNAPSHOT_YEAR,
    )
    hitter_paths = hitter_opportunity.join(
        hitter_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (
            pl.col("mlb_active_probability")
            * pl.col("conditional_mlb_pa")
            * pl.col("conditional_war_per_600_pa")
            / 600.0
        ).alias("expected_war")
    )
    pitcher_paths = pitcher_opportunity.join(
        pitcher_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (
            pl.col("mlb_active_probability")
            * pl.col("conditional_mlb_bf")
            * pl.col("conditional_war_per_800_bf")
            / 800.0
        ).alias("expected_war")
    )
    if hitter_paths.height != hitter_opportunity.height:
        raise RuntimeError("historical hitter rate coverage differs from opportunity")
    if pitcher_paths.height != pitcher_opportunity.height:
        raise RuntimeError("historical pitcher rate coverage differs from opportunity")

    hitter_comparison = opening.filter(pl.col("projected_pa").is_not_null()).select(
        "player_id", pl.col("projected_pa").alias("fangraphs_projected_pa")
    ).join(
        hitter_paths.filter(pl.col("season") == FORECAST_YEAR).select(
            "player_id", pl.col("expected_mlb_pa").alias("model_expected_pa")
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    ).with_columns(
        (pl.col("model_expected_pa") - pl.col("fangraphs_projected_pa")).alias(
            "difference_pa"
        )
    )
    bf_per_ip = float(reference["pitching_batters_faced"]) / (
        float(reference["pitching_outs"]) / 3.0
    )
    pitcher_comparison = opening.filter(pl.col("projected_ip").is_not_null()).select(
        "player_id",
        "projected_ip",
        (pl.col("projected_ip") * bf_per_ip).alias("fangraphs_implied_bf"),
    ).join(
        pitcher_paths.filter(pl.col("season") == FORECAST_YEAR).select(
            "player_id", pl.col("expected_mlb_bf").alias("model_expected_bf")
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    ).with_columns(
        (pl.col("model_expected_bf") - pl.col("fangraphs_implied_bf")).alias(
            "difference_bf"
        )
    )

    output.mkdir(parents=True, exist_ok=True)
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_selected": write_canonical_parquet(
            hitter_selected,
            tables / "hitter-selected-2025.parquet",
            table_name="historical_hitter_selected_opportunity_2025",
        ).as_record(),
        "pitcher_selected": write_canonical_parquet(
            pitcher_selected,
            tables / "pitcher-selected-2025.parquet",
            table_name="historical_pitcher_selected_opportunity_2025",
        ).as_record(),
        "hitter_paths": write_canonical_parquet(
            hitter_paths,
            tables / "hitter-expected-war-paths.parquet",
            table_name="historical_hitter_expected_war_paths",
        ).as_record(),
        "pitcher_paths": write_canonical_parquet(
            pitcher_paths,
            tables / "pitcher-expected-war-paths.parquet",
            table_name="historical_pitcher_expected_war_paths",
        ).as_record(),
        "hitter_fangraphs_comparison": write_canonical_parquet(
            hitter_comparison,
            tables / "hitter-fangraphs-opportunity-comparison.parquet",
            table_name="historical_hitter_fangraphs_opportunity_comparison",
        ).as_record(),
        "pitcher_fangraphs_comparison": write_canonical_parquet(
            pitcher_comparison,
            tables / "pitcher-fangraphs-opportunity-comparison.parquet",
            table_name="historical_pitcher_fangraphs_opportunity_comparison",
        ).as_record(),
    }
    source_paths = [
        membership_path,
        opening_path,
        fallback_root / "tables/hitter_references.parquet",
        fallback_root / "tables/pitcher_references.parquet",
        skill_root / "tables/mlb_hitting_components.parquet",
        skill_root / "tables/mlb_pitching_components.parquet",
    ]
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_cutoff_safe_projection_paths",
        "checkpoint_date": CHECKPOINT_DATE.isoformat(),
        "forecast_seasons": list(FORECAST_SEASONS),
        "fit": fit_summary,
        "frozen_fit_artifacts": {
            "package_manifest": (FIT_PACKAGE_ROOT / "manifest.json").as_posix(),
            "hitter": {
                "path": hitter_fit_path.as_posix(),
                "sha256": sha256_file(hitter_fit_path),
            },
            "pitcher": {
                "path": pitcher_fit_path.as_posix(),
                "sha256": sha256_file(pitcher_fit_path),
            },
        },
        "hitter_players": hitter_universe.height,
        "pitcher_players": pitcher_universe.height,
        "two_component_players": len(
            set(hitter_universe.get_column("player_id"))
            & set(pitcher_universe.get_column("player_id"))
        ),
        "opening_workbook_added_hitters": hitter_universe.height
        - hitter_snapshot.height,
        "opening_workbook_added_pitchers": pitcher_universe.height
        - pitcher_snapshot.height,
        "hitter_coverage": _coverage(hitter_opportunity),
        "pitcher_coverage": _coverage(pitcher_opportunity),
        "expected_war": {
            "hitter": float(hitter_paths.get_column("expected_war").sum()),
            "pitcher": float(pitcher_paths.get_column("expected_war").sum()),
        },
        "fangraphs_opportunity_comparison": {
            "role": "external_scale_check_not_target_or_model_input",
            "hitter_players": hitter_comparison.height,
            "hitter_mean_fangraphs_pa": float(
                hitter_comparison.get_column("fangraphs_projected_pa").mean()
            ),
            "hitter_mean_model_pa": float(
                hitter_comparison.get_column("model_expected_pa").mean()
            ),
            "hitter_mean_absolute_difference_pa": float(
                hitter_comparison.get_column("difference_pa").abs().mean()
            ),
            "pitcher_players": pitcher_comparison.height,
            "pitcher_bf_per_ip_conversion": bf_per_ip,
            "pitcher_mean_fangraphs_implied_bf": float(
                pitcher_comparison.get_column("fangraphs_implied_bf").mean()
            ),
            "pitcher_mean_model_bf": float(
                pitcher_comparison.get_column("model_expected_bf").mean()
            ),
            "pitcher_mean_absolute_difference_bf": float(
                pitcher_comparison.get_column("difference_bf").abs().mean()
            ),
        },
        "source_files": {
            path.as_posix(): sha256_file(path) for path in source_paths
        },
        "boundaries": {
            "latest_model_training_target_year": 2024,
            "2025_outcomes_used": False,
            "future_team_depth_used": False,
            "fangraphs_projection_values_used_as_predictors": False,
            "later_horizons": "pre2025_age_level_role_historical_fallbacks",
            "affiliated_skill_translation_used": False,
            "baserunning_and_defense": "league_average_zero_phase1_fallback",
            "replay_mode": "retrospective_event_cutoff_not_vintage_information_set",
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
