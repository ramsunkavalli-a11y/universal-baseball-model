#!/usr/bin/env python3
"""Build the browser payload for the frozen 2026 hitter-model explorer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    _lgbm_regressor,
    feature_columns,
    matrix_from_panel,
)
from universal_baseball.hitter_value_panel import (
    build_hitter_contact_features,
    build_hitter_forecast_panel,
)


SITE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SITE_ROOT.parents[1]
ARCHIVE_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
FORECAST_ROOT = (
    REPO_ROOT
    / "model_artifacts/hitter-full-2026-confirmation-forecast-2026-09-20"
)
PEOPLE_PATH = (
    ARCHIVE_ROOT
    / "historical-people-control/2025-10-15/tables/people.parquet"
)
POSITION_PATH = (
    ARCHIVE_ROOT
    / "position-capacity-source/2025/reports/generated/"
    "position-role-2025-confirmation-source/tables/"
    "position_role_2025_fielding_usage.parquet"
)
MODEL_PANEL_PATH = (
    REPO_ROOT / "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
STAT_FEATURE_PATH = (
    REPO_ROOT
    / "reports/generated/hitter-value-panel-v2/tables/hitter-stat-features.parquet"
)
CONTACT_FEATURE_PATH = (
    REPO_ROOT
    / "reports/generated/hitter-value-panel-v2/tables/hitter-contact-features.parquet"
)
HISTORY_YEARS = (2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025)


def _primary_positions() -> pl.DataFrame:
    usage = pl.read_parquet(POSITION_PATH).filter(pl.col("fielding_outs") > 0)
    return (
        usage.group_by("player_id", "position_abbreviation")
        .agg(pl.col("fielding_outs").sum())
        .sort(
            ["player_id", "fielding_outs", "position_abbreviation"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", pl.col("position_abbreviation").alias("primary_position"))
    )


def _people_with_organizations() -> pl.DataFrame:
    organizations = (
        pl.read_parquet(POSITION_PATH)
        .filter(pl.col("level_group") == "MLB")
        .select(
            pl.col("team_id").alias("organization_id"),
            pl.col("team_name").alias("organization_name"),
        )
        .unique("organization_id")
    )
    organization_ids = organizations["organization_id"].to_list()
    return (
        pl.read_parquet(PEOPLE_PATH)
        .select(
            "player_id",
            "player_name",
            "birth_date",
            "mlb_debut_date",
            "current_team_id",
            "current_team_parent_org_id",
        )
        .with_columns(
            pl.when(pl.col("current_team_parent_org_id").is_in(organization_ids))
            .then(pl.col("current_team_parent_org_id"))
            .when(pl.col("current_team_id").is_in(organization_ids))
            .then(pl.col("current_team_id"))
            .otherwise(None)
            .alias("organization_id")
        )
        .join(organizations, on="organization_id", how="left", validate="m:1")
        .with_columns(
            pl.col("organization_name").fill_null("Unassigned / inactive")
        )
        .drop("current_team_id", "current_team_parent_org_id")
    )


def _hitting_ability() -> pl.DataFrame:
    """Reproduce the frozen three-part model's conditional hitting rate."""
    training = pl.read_parquet(MODEL_PANEL_PATH)
    historical_contacts = pl.read_parquet(CONTACT_FEATURE_PATH).filter(
        pl.col("season") < 2025
    )
    official_contacts = build_hitter_contact_features(
        pl.read_parquet(
            ARCHIVE_ROOT
            / "official-full-bip-context-2025/tables/"
            "hitter_full_bip_event_outcomes.parquet"
        )
    )
    contacts = pl.concat(
        [historical_contacts, official_contacts], how="vertical_relaxed"
    )
    ages = pl.concat(
        [
            pl.read_parquet(
                ARCHIVE_ROOT
                / f"hitter-multiyear-age-level-base/tables/annual-{year}.parquet"
            )
            .select("player_id", "age", "relative_age", "age_missing")
            .with_columns(pl.lit(year).alias("season"))
            for year in HISTORY_YEARS
        ],
        how="vertical_relaxed",
    )
    scoring = build_hitter_forecast_panel(
        pl.read_parquet(STAT_FEATURE_PATH), contacts, ages, origin=2025
    )
    columns = feature_columns(training)
    missing = sorted(set(columns) - set(scoring.columns))
    if missing:
        raise RuntimeError(f"hitting-ability panel lacks features: {missing}")
    x_train = matrix_from_panel(training, columns)
    x_score = matrix_from_panel(scoring, columns)
    active = training["target_mlb_active"].to_numpy().astype(np.int8)
    target_pa = training["target_mlb_pa"].to_numpy()
    active_rows = active == 1
    model = _lgbm_regressor(421)
    model.fit(
        x_train[active_rows],
        training["target_conditional_component_war_per_600"].to_numpy()[active_rows],
        sample_weight=np.sqrt(np.maximum(target_pa[active_rows], 1.0)),
    )
    rate = np.clip(model.predict(x_score), -5.0, 10.0)
    return scoring.select("player_id").with_columns(
        pl.Series("prediction_hitting_war_per_600", rate)
    )


def _rounded_records(frame: pl.DataFrame) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in frame.iter_rows(named=True):
        clean: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, float):
                clean[key] = round(value, 6)
            elif hasattr(value, "isoformat"):
                clean[key] = value.isoformat()
            else:
                clean[key] = value
        records.append(clean)
    return records


def main() -> int:
    forecast = pl.read_parquet(FORECAST_ROOT / "forecast-2026.parquet")
    inputs = pl.read_parquet(FORECAST_ROOT / "forecast-inputs-2025.parquet")
    people = _people_with_organizations()
    positions = _primary_positions()
    hitting_ability = _hitting_ability()

    history_columns = ["player_id"]
    for lag in range(3):
        prefix = f"lag{lag}__"
        history_columns.extend(
            [
                f"{prefix}plate_appearances",
                f"{prefix}highest_level",
                f"{prefix}age",
                f"{prefix}reported_age",
                f"{prefix}ubb_rate",
                f"{prefix}strikeout_rate",
                f"{prefix}single_rate",
                f"{prefix}double_rate",
                f"{prefix}triple_rate",
                f"{prefix}home_run_rate",
                f"{prefix}stolen_bases",
                f"{prefix}caught_stealing",
                f"{prefix}contact_events",
                f"{prefix}contact_feature_available",
                f"{prefix}season_available",
            ]
        )
    frame = (
        forecast.join(people, on="player_id", how="left", validate="1:1")
        .join(positions, on="player_id", how="left", validate="1:1")
        .join(hitting_ability, on="player_id", how="left", validate="1:1")
        .join(inputs.select(history_columns), on="player_id", how="left", validate="1:1")
    )
    if frame["player_name"].null_count():
        raise RuntimeError("pre-2026 identity coverage is incomplete")

    member_columns = [
        column for column in frame.columns if column.startswith("prediction_member__")
    ]
    frame = frame.with_columns(
        pl.max_horizontal(member_columns).sub(pl.min_horizontal(member_columns)).alias(
            "model_member_spread"
        ),
        pl.max_horizontal(
            "prediction_expected_mlb_pa",
            "benchmark_incumbent_expected_mlb_pa",
            "benchmark_parametric_expected_mlb_pa",
        )
        .sub(
            pl.min_horizontal(
                "prediction_expected_mlb_pa",
                "benchmark_incumbent_expected_mlb_pa",
                "benchmark_parametric_expected_mlb_pa",
            )
        )
        .alias("opportunity_spread"),
        (pl.col("selected_upper_90") - pl.col("selected_lower_90")).alias(
            "interval_width_90"
        ),
        (
            pl.col("prediction_routed_batting_replacement_war")
            - pl.col("prediction_batting_replacement_war")
        ).alias("routed_batting_delta"),
        pl.sum_horizontal(
            [pl.col(f"lag{lag}__season_available").fill_null(0) for lag in range(3)]
        ).alias("history_seasons"),
    )
    thresholds = {
        "model_member_spread": float(frame["model_member_spread"].quantile(0.9)),
        "opportunity_spread": float(frame["opportunity_spread"].quantile(0.9)),
        "interval_width_90": float(frame["interval_width_90"].quantile(0.9)),
        "routed_delta_abs": float(
            frame["routed_batting_delta"].abs().quantile(0.9)
        ),
    }
    frame = frame.with_columns(
        (pl.col("model_member_spread") >= thresholds["model_member_spread"]).alias(
            "flag_model_disagreement"
        ),
        (pl.col("opportunity_spread") >= thresholds["opportunity_spread"]).alias(
            "flag_opportunity_disagreement"
        ),
        (pl.col("interval_width_90") >= thresholds["interval_width_90"]).alias(
            "flag_wide_interval"
        ),
        (pl.col("routed_batting_delta").abs() >= thresholds["routed_delta_abs"]).alias(
            "flag_routing_sensitive"
        ),
        (pl.col("lag0__contact_feature_available").fill_null(0) == 0).alias(
            "flag_no_current_contact"
        ),
        (pl.col("position_profile_available") == 0).alias("flag_no_position_profile"),
        (
            pl.col("batting_evidence_tier")
            == "opportunity_scaled_population_rate_prior"
        ).alias("flag_population_prior"),
        pl.col("prediction_selected_partial_war")
        .rank(method="ordinal", descending=True)
        .cast(pl.Int64)
        .alias("overall_rank"),
    )
    frame = frame.with_columns(
        pl.sum_horizontal(
            [
                pl.col("flag_model_disagreement").cast(pl.Int8),
                pl.col("flag_opportunity_disagreement").cast(pl.Int8),
                pl.col("flag_wide_interval").cast(pl.Int8),
                pl.col("flag_routing_sensitive").cast(pl.Int8),
                pl.col("flag_no_current_contact").cast(pl.Int8),
                pl.col("flag_no_position_profile").cast(pl.Int8),
                pl.col("flag_population_prior").cast(pl.Int8),
            ]
        ).alias("gap_count")
    ).sort(["prediction_selected_partial_war", "player_id"], descending=[True, False])

    keep = [
        "player_id",
        "player_name",
        "birth_date",
        "mlb_debut_date",
        "organization_id",
        "organization_name",
        "primary_position",
        "overall_rank",
        "player_stage",
        "batting_evidence_tier",
        "baserunning_evidence_tier",
        "position_profile_available",
        "catcher_evidence_available",
        "prediction_mlb_active_probability",
        "prediction_positive_mlb_pa",
        "prediction_expected_mlb_pa",
        "benchmark_incumbent_active_probability",
        "benchmark_incumbent_expected_mlb_pa",
        "benchmark_parametric_active_probability",
        "benchmark_parametric_expected_mlb_pa",
        "prediction_model_active_probability",
        "prediction_stats_only_active_probability",
        "prediction_batting_replacement_war",
        "prediction_hitting_war_per_600",
        "prediction_routed_batting_replacement_war",
        "prediction_position_war",
        "prediction_steal_war",
        "prediction_advancement_war",
        "prediction_baserunning_war",
        "prediction_catcher_defense_war",
        "prediction_general_defense_war",
        "prediction_selected_partial_war",
        "prediction_routed_partial_war",
        "benchmark_previous_batting_replacement_war",
        "selected_lower_50",
        "selected_upper_50",
        "selected_lower_80",
        "selected_upper_80",
        "selected_lower_90",
        "selected_upper_90",
        "model_member_spread",
        "opportunity_spread",
        "interval_width_90",
        "routed_batting_delta",
        "history_seasons",
        "gap_count",
        "flag_model_disagreement",
        "flag_opportunity_disagreement",
        "flag_wide_interval",
        "flag_routing_sensitive",
        "flag_no_current_contact",
        "flag_no_position_profile",
        "flag_population_prior",
        *member_columns,
        *[column for column in history_columns if column != "player_id"],
    ]
    payload = {
        "meta": {
            "title": "UBM Hitter Model Explorer",
            "forecast_season": 2026,
            "source_season": 2025,
            "players": frame.height,
            "forecast_sha256": (
                "d1953a28d35d87d141ecc65ec4b107906edad877982e79c0d3a216245b9e4708"
            ),
            "protected_2026_outcomes_opened": False,
            "thresholds": thresholds,
        },
        "players": _rounded_records(frame.select(keep)),
    }
    SITE_ROOT.joinpath("dist").mkdir(parents=True, exist_ok=True)
    text = "window.UBM_EXPLORER_DATA=" + json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ) + ";\n"
    SITE_ROOT.joinpath("dist/data.js").write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "players": frame.height,
                "named": frame["player_name"].is_not_null().sum(),
                "bytes": len(text.encode("utf-8")),
                "outcome_data_opened": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
