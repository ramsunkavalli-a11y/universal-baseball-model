#!/usr/bin/env python3
"""Test a cutoff-safe current-organization cap on pitcher workload and value."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
TEAM_CAPTURE_ROOT = OLD_ROOT / "affiliated-team-context/captures"
WORKLOAD_PATH = Path("reports/generated/pitcher-workload-v2/predictions.parquet")
VALUE_PATH = Path("reports/generated/pitcher-role-ensemble-v2/predictions.parquet")
OUTPUT_ROOT = Path("reports/generated/pitcher-team-capacity-v2")
ORIGINS = (2021, 2022, 2023, 2024)


def _team_mapping() -> tuple[pl.DataFrame, list[Path]]:
    paths = sorted(TEAM_CAPTURE_ROOT.glob("teams-*-sport-*.json"))
    rows: list[dict[str, int]] = []
    used_paths: list[Path] = []
    for path in paths:
        season = int(path.name.split("-")[1])
        if season not in ORIGINS:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        used_paths.append(path)
        for team in payload.get("teams", []):
            team_id = int(team["id"])
            rows.append(
                {
                    "season": season,
                    "team_id": team_id,
                    "organization_id": int(team.get("parentOrgId") or team_id),
                }
            )
    mapping = pl.DataFrame(rows).unique(["season", "team_id"])
    if mapping.group_by("season", "team_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("team mapping is not unique by season and team")
    return mapping, used_paths


def _pitching_components() -> tuple[pl.DataFrame, list[Path]]:
    paths = sorted(
        OLD_ROOT.glob(
            "affiliated-skill-source*/tables/affiliated_pitching_components.parquet"
        )
    )
    pieces = [
        pl.read_parquet(path)
        .filter(pl.col("season").is_in(ORIGINS))
        .select("season", "player_id", "team_id", "level_group", "batters_faced")
        for path in paths
    ]
    frame = pl.concat(pieces).unique(["season", "player_id", "team_id"], keep="last")
    return frame, paths


def _regression(frame: pl.DataFrame, actual: str, prediction: str) -> dict[str, float]:
    return regression_metrics(frame[actual].to_numpy(), frame[prediction].to_numpy())


def main() -> None:
    team_mapping, capture_paths = _team_mapping()
    components, component_paths = _pitching_components()
    player_org = (
        components.join(
            team_mapping,
            on=["season", "team_id"],
            how="inner",
            validate="m:1",
        )
        .group_by("season", "player_id", "organization_id")
        .agg(pl.col("batters_faced").sum().alias("organization_bf"))
        .group_by("season", "player_id")
        .agg(
            pl.col("organization_id").n_unique().alias("organization_count"),
            pl.col("organization_id")
            .sort_by("organization_bf")
            .last()
            .alias("organization_id"),
        )
    )
    capacities = (
        components.filter(pl.col("level_group") == "MLB")
        .group_by("season", "team_id")
        .agg(pl.col("batters_faced").sum().alias("team_mlb_bf"))
        .group_by("season")
        .agg(
            pl.col("team_mlb_bf").mean().alias("team_capacity_bf"),
            pl.col("team_id").n_unique().alias("mlb_team_count"),
        )
    )
    if capacities.filter(pl.col("mlb_team_count") != 30).height:
        raise ValueError("capacity source does not contain 30 MLB teams per season")

    workload = (
        pl.read_parquet(WORKLOAD_PATH)
        .filter(pl.col("origin_year").is_in(ORIGINS))
        .join(
            player_org,
            left_on=["origin_year", "player_id"],
            right_on=["season", "player_id"],
            how="left",
            validate="1:1",
        )
        .join(
            capacities.select("season", "team_capacity_bf"),
            left_on="origin_year",
            right_on="season",
            validate="m:1",
        )
    )
    if workload["organization_id"].null_count():
        raise ValueError("organization mapping does not cover every workload row")

    groups = (
        workload.filter(pl.col("organization_count") == 1)
        .group_by("origin_year", "organization_id")
        .agg(
            pl.col("prediction_selected_expected_bf").sum().alias(
                "raw_expected_bf"
            ),
            pl.col("team_capacity_bf").first(),
        )
        .with_columns(
            pl.min_horizontal(
                pl.lit(1.0), pl.col("team_capacity_bf") / pl.col("raw_expected_bf")
            ).alias("capacity_scale")
        )
        .with_columns(
            (pl.col("raw_expected_bf") * pl.col("capacity_scale")).alias(
                "capacity_adjusted_expected_bf"
            )
        )
    )
    workload = (
        workload.join(
            groups.select("origin_year", "organization_id", "capacity_scale"),
            on=["origin_year", "organization_id"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.when(pl.col("organization_count") == 1)
            .then(pl.col("capacity_scale").fill_null(1.0))
            .otherwise(1.0)
            .alias("selected_capacity_scale")
        )
        .with_columns(
            (
                pl.col("prediction_selected_expected_bf")
                * pl.col("selected_capacity_scale")
            ).alias("prediction_capacity_adjusted_expected_bf")
        )
    )
    values = pl.read_parquet(VALUE_PATH).filter(pl.col("origin_year").is_in(ORIGINS))
    frame = workload.join(
        values.select(
            "origin_year",
            "player_id",
            "actual_component_war",
            "prediction_role_chronology_pruned_equal",
        ),
        on=["origin_year", "player_id"],
        validate="1:1",
    ).with_columns(
        (
            pl.col("prediction_role_chronology_pruned_equal")
            * pl.col("selected_capacity_scale")
        ).alias("prediction_capacity_adjusted_component_war")
    )

    ids = frame["player_id"].to_numpy()
    workload_actual = frame["actual_bf"].to_numpy()
    value_actual = frame["actual_component_war"].to_numpy()
    workload_comparison = paired_cluster_rmse_delta(
        workload_actual,
        frame["prediction_capacity_adjusted_expected_bf"].to_numpy(),
        frame["prediction_selected_expected_bf"].to_numpy(),
        ids,
        bootstrap_samples=5_000,
    )
    value_comparison = paired_cluster_rmse_delta(
        value_actual,
        frame["prediction_capacity_adjusted_component_war"].to_numpy(),
        frame["prediction_role_chronology_pruned_equal"].to_numpy(),
        ids,
        bootstrap_samples=5_000,
    )
    by_origin = {
        str(origin): {
            "rows": fold.height,
            "stable_organization_rows": fold.filter(
                pl.col("organization_count") == 1
            ).height,
            "workload_base": _regression(
                fold, "actual_bf", "prediction_selected_expected_bf"
            ),
            "workload_capacity": _regression(
                fold, "actual_bf", "prediction_capacity_adjusted_expected_bf"
            ),
            "value_base": _regression(
                fold,
                "actual_component_war",
                "prediction_role_chronology_pruned_equal",
            ),
            "value_capacity": _regression(
                fold,
                "actual_component_war",
                "prediction_capacity_adjusted_component_war",
            ),
        }
        for origin in ORIGINS
        for fold in [frame.filter(pl.col("origin_year") == origin)]
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "players": write_canonical_parquet(
            frame,
            OUTPUT_ROOT / "player-predictions.parquet",
            table_name="pitcher_team_capacity_v2_player_predictions",
        ).as_record(),
        "groups": write_canonical_parquet(
            groups,
            OUTPUT_ROOT / "organization-groups.parquet",
            table_name="pitcher_team_capacity_v2_organization_groups",
        ).as_record(),
    }
    report = {
        "schema_version": "0.1",
        "status": "pitcher_team_capacity_context_only",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "decision": (
            "retain only as a current-organization opportunity view; do not scale "
            "portable pitcher value"
        ),
        "method": (
            "map each forecast-time affiliate to its same-season parent MLB club; "
            "leave multi-organization players unchanged; for a stable organization "
            "only, scale forecasts down when their total exceeds the same-season "
            "league-average MLB team BF"
        ),
        "origins": list(ORIGINS),
        "rows": frame.height,
        "stable_organization_rows": frame.filter(
            pl.col("organization_count") == 1
        ).height,
        "multi_organization_rows_left_unadjusted": frame.filter(
            pl.col("organization_count") > 1
        ).height,
        "over_capacity_organization_seasons": groups.filter(
            pl.col("capacity_scale") < 1.0
        ).height,
        "workload": {
            "base": _regression(
                frame, "actual_bf", "prediction_selected_expected_bf"
            ),
            "capacity": _regression(
                frame, "actual_bf", "prediction_capacity_adjusted_expected_bf"
            ),
            "capacity_minus_base": workload_comparison,
        },
        "value": {
            "base": _regression(
                frame,
                "actual_component_war",
                "prediction_role_chronology_pruned_equal",
            ),
            "capacity": _regression(
                frame,
                "actual_component_war",
                "prediction_capacity_adjusted_component_war",
            ),
            "capacity_minus_base": value_comparison,
        },
        "by_origin": by_origin,
        "capacities": capacities.sort("season").to_dicts(),
        "artifacts": artifacts,
        "sources": {
            "workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "value": {"path": str(VALUE_PATH), "sha256": sha256_file(VALUE_PATH)},
            "team_captures": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in capture_paths
            ],
            "pitching_components": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in component_paths
            ],
        },
        "limitations": [
            "Forecast-time playing organization is not the same as verified offseason rights or next-season destination.",
            "Uniform downward scaling does not decide which individual pitcher loses innings.",
            "The workload gain is small and the player-value interval includes help and harm.",
            "Multi-organization player-seasons are left untouched rather than guessed.",
            "The final 2026 outcome remains sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
