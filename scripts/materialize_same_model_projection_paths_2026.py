#!/usr/bin/env python3
"""Update the 2025 replay projection with 2025 evidence and frozen model fits."""

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
    build_universal_hitter_opportunity_predictors,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_predictors,
)
from universal_baseball.pitcher_opportunity_paths import (
    PitcherOpportunityFit,
    score_pitcher_opportunity_paths,
)
from universal_baseball.playing_time_fit_artifact import (
    playing_time_fit_from_artifact,
)
from universal_baseball.playing_time_model import (
    build_playing_time_design,
    predict_playing_time_hurdle,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


CHECKPOINT_DATE = date(2025, 10, 15)
SNAPSHOT_YEAR = 2025
FORECAST_YEAR = 2026
FORECAST_SEASONS = (2026, 2027, 2028, 2029, 2030)
POSITION_CODES = {"C": "2", "1B": "3", "2B": "4", "3B": "5", "SS": "6",
                  "LF": "7", "CF": "8", "RF": "9", "OF": "O", "DH": "10"}
FIT_PACKAGE_ROOT = Path("model_artifacts/opportunity-v2-pre2025-replay")


def _load_frozen_fit(path: Path, expected_sha256: str):
    if sha256_file(path) != expected_sha256:
        raise ValueError(f"frozen fit hash differs from March replay: {path}")
    return playing_time_fit_from_artifact(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _hitter_position_players(
    universe: pl.DataFrame, current_stats: pl.DataFrame
) -> pl.DataFrame:
    positions = (
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
    return universe.select(
        "player_id", (pl.col("age_years") + 1.0).alias("age_years")
    ).join(positions, on="player_id", how="left").with_columns(
        pl.col("position_code")
        .str.to_uppercase()
        .replace_strict(POSITION_CODES, default=pl.col("position_code"))
        .fill_null("")
    )


def _coverage(paths: pl.DataFrame) -> list[dict[str, object]]:
    return (
        paths.group_by("horizon", "coverage_tier")
        .len()
        .sort(["horizon", "coverage_tier"])
        .to_dicts()
    )


def main() -> int:
    source_root = Path("reports/generated/opportunity-history-sources-v2/tables")
    membership_path = Path(
        "reports/generated/opportunity-40man-history/tables/"
        "historical_40man_membership.parquet"
    )
    fallback_root = Path("reports/generated/opportunity-historical-fits")
    march_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    skill_root = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
    environment_root = Path("reports/generated/current-mlb-skill-source/2026-09-08")
    output = Path("reports/generated/historical-projection-paths/2025-10-15")

    march_report = json.loads((march_root / "report.json").read_text(encoding="utf-8"))
    fit_manifest_path = FIT_PACKAGE_ROOT / "manifest.json"
    fit_manifest = json.loads(fit_manifest_path.read_text(encoding="utf-8"))
    hitter_fit_path = FIT_PACKAGE_ROOT / "hitter-opportunity-fit.json"
    pitcher_fit_path = FIT_PACKAGE_ROOT / "pitcher-opportunity-fit.json"
    if (
        sha256_file(hitter_fit_path)
        != fit_manifest["artifacts"][hitter_fit_path.name]["sha256"]
        or sha256_file(pitcher_fit_path)
        != fit_manifest["artifacts"][pitcher_fit_path.name]["sha256"]
    ):
        raise ValueError("durable replay fit differs from its manifest")
    hitter_fit = _load_frozen_fit(
        hitter_fit_path, march_report["frozen_fit_artifacts"]["hitter"]["sha256"]
    )
    pitcher_fit = _load_frozen_fit(
        pitcher_fit_path, march_report["frozen_fit_artifacts"]["pitcher"]["sha256"]
    )

    membership = pl.read_parquet(membership_path)
    current_stats_path = source_root / str(SNAPSHOT_YEAR) / "affiliated_season_stats.parquet"
    current_stats = pl.read_parquet(current_stats_path)
    hitter_snapshot_path = source_root / str(SNAPSHOT_YEAR) / "hitter_snapshot.parquet"
    pitcher_snapshot_path = source_root / str(SNAPSHOT_YEAR) / "pitcher_snapshot.parquet"
    hitter_universe = pl.read_parquet(hitter_snapshot_path)
    pitcher_universe = pl.read_parquet(pitcher_snapshot_path)

    hitter_predictors = build_universal_hitter_opportunity_predictors(
        hitter_universe, current_stats, membership, snapshot_year=SNAPSHOT_YEAR
    )
    pitcher_predictors = build_universal_pitcher_opportunity_predictors(
        pitcher_universe, current_stats, membership, snapshot_year=SNAPSHOT_YEAR
    )
    fit_id = "pre2025_frozen_fit"
    hitter_selected = predict_playing_time_hurdle(
        hitter_fit, build_playing_time_design(hitter_predictors, form=hitter_fit.form)
    ).with_columns(
        pl.lit(hitter_fit.nb_alpha).alias("model_nb_alpha"),
        pl.lit(f"hitter_opportunity_v2_{fit_id}").alias("model_id"),
        pl.lit("same_fit_updated_2025_evidence").alias("model_status"),
    )
    pitcher_selected = predict_playing_time_hurdle(
        pitcher_fit,
        build_playing_time_design(pitcher_predictors, form=pitcher_fit.form),
    ).rename(
        {
            "predicted_any_mlb_pa_probability": "predicted_any_mlb_bf_probability",
            "predicted_positive_mlb_pa_mean": "predicted_positive_mlb_bf_mean",
            "predicted_expected_mlb_pa": "predicted_expected_mlb_bf",
        }
    ).with_columns(
        pl.lit(pitcher_fit.nb_alpha).alias("model_nb_alpha"),
        pl.lit(f"pitcher_opportunity_v2_{fit_id}").alias("model_id"),
        pl.lit("same_fit_updated_2025_evidence").alias("model_status"),
    )

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

    environment_report = json.loads(
        (environment_root / "report.json").read_text(encoding="utf-8")
    )
    reference = environment_report["reference_environment"]
    if int(reference["season"]) != SNAPSHOT_YEAR:
        raise ValueError("same-model replay requires the completed 2025 run environment")
    hitting_path = skill_root / "tables/mlb_hitting_components.parquet"
    pitching_path = skill_root / "tables/mlb_pitching_components.parquet"
    hitting_history = pl.read_parquet(hitting_path).filter(
        pl.col("season") <= SNAPSHOT_YEAR
    )
    pitching_history = pl.read_parquet(pitching_path).filter(
        pl.col("season") <= SNAPSHOT_YEAR
    )
    hitter_rates = build_hitter_conditional_war_rates(
        _hitter_position_players(hitter_universe, current_stats),
        hitting_history,
        current_season=FORECAST_YEAR,
        forecast_seasons=FORECAST_SEASONS,
        reference_plate_appearances=int(reference["batting_plate_appearances"]),
        runs_per_win=float(reference["runs_per_win"]),
        evidence_anchor_season=SNAPSHOT_YEAR,
        reference_season=SNAPSHOT_YEAR,
    )
    pitcher_rates = build_pitcher_conditional_war_rates(
        pitcher_universe.select(
            "player_id", (pl.col("age_years") + 1.0).alias("age_years")
        ),
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
        raise RuntimeError("same-model hitter rate coverage differs from opportunity")
    if pitcher_paths.height != pitcher_opportunity.height:
        raise RuntimeError("same-model pitcher rate coverage differs from opportunity")

    output.mkdir(parents=True, exist_ok=True)
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_selected": write_canonical_parquet(
            hitter_selected,
            tables / "hitter-selected-2026.parquet",
            table_name="same_model_hitter_selected_opportunity_2026",
        ).as_record(),
        "pitcher_selected": write_canonical_parquet(
            pitcher_selected,
            tables / "pitcher-selected-2026.parquet",
            table_name="same_model_pitcher_selected_opportunity_2026",
        ).as_record(),
        "hitter_paths": write_canonical_parquet(
            hitter_paths,
            tables / "hitter-expected-war-paths.parquet",
            table_name="same_model_hitter_expected_war_paths",
        ).as_record(),
        "pitcher_paths": write_canonical_parquet(
            pitcher_paths,
            tables / "pitcher-expected-war-paths.parquet",
            table_name="same_model_pitcher_expected_war_paths",
        ).as_record(),
    }
    source_paths = [
        hitter_snapshot_path,
        pitcher_snapshot_path,
        current_stats_path,
        membership_path,
        hitter_fit_path,
        pitcher_fit_path,
        fit_manifest_path,
        fallback_root / "tables/hitter_references.parquet",
        fallback_root / "tables/pitcher_references.parquet",
        hitting_path,
        pitching_path,
        environment_root / "report.json",
    ]
    report = {
        "report_schema_version": "0.1",
        "gate": "same_model_2025_evidence_projection_paths",
        "checkpoint_date": CHECKPOINT_DATE.isoformat(),
        "forecast_seasons": list(FORECAST_SEASONS),
        "hitter_players": hitter_universe.height,
        "pitcher_players": pitcher_universe.height,
        "two_component_players": len(
            set(hitter_universe.get_column("player_id"))
            & set(pitcher_universe.get_column("player_id"))
        ),
        "frozen_fit": {
            "source_checkpoint": "2025-03-27",
            "hitter_form": hitter_fit.form,
            "hitter_sha256": sha256_file(hitter_fit_path),
            "pitcher_form": pitcher_fit.form,
            "pitcher_sha256": sha256_file(pitcher_fit_path),
            "refit_after_march_checkpoint": False,
        },
        "hitter_coverage": _coverage(hitter_opportunity),
        "pitcher_coverage": _coverage(pitcher_opportunity),
        "expected_war": {
            "hitter": float(hitter_paths.get_column("expected_war").sum()),
            "pitcher": float(pitcher_paths.get_column("expected_war").sum()),
        },
        "source_files": {path.as_posix(): sha256_file(path) for path in source_paths},
        "boundaries": {
            "2025_completed_results_used_as_updated_evidence": True,
            "2026_outcomes_used": False,
            "opportunity_model_refit_after_march_checkpoint": False,
            "conditional_skill_method_changed_after_march_checkpoint": False,
            "future_team_depth_used": False,
            "fangraphs_projection_values_used": False,
            "later_horizons": "same_pre2025_age_level_role_historical_fallbacks",
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
