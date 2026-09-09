#!/usr/bin/env python3
"""Compare March and October 2025 projection checkpoints under one frozen fit."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.projection_checkpoint_comparison import (
    compare_projection_checkpoints,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _summary(frame: pl.DataFrame, component: str) -> dict[str, object]:
    career = frame.group_by("player_id").agg(
        pl.col("earlier_expected_war").sum(),
        pl.col("later_expected_war").sum(),
        pl.col("expected_war_delta").sum(),
    )
    correlation = frame.select(
        pl.corr("earlier_expected_war", "later_expected_war")
    ).item()
    return {
        "component": component,
        "shared_player_seasons": frame.height,
        "shared_players": frame.get_column("player_id").n_unique(),
        "shared_earlier_expected_war": float(
            frame.get_column("earlier_expected_war").sum()
        ),
        "shared_later_expected_war": float(
            frame.get_column("later_expected_war").sum()
        ),
        "expected_war_correlation": float(correlation),
        "mean_absolute_player_season_delta_war": float(
            frame.get_column("expected_war_delta").abs().mean()
        ),
        "p90_absolute_player_season_delta_war": float(
            frame.get_column("expected_war_delta").abs().quantile(0.9)
        ),
        "material_player_season_changes_at_0_25_war": frame.filter(
            pl.col("expected_war_delta").abs() >= 0.25
        ).height,
        "opportunity_effect_war": float(
            frame.get_column("opportunity_effect_war").sum()
        ),
        "skill_effect_war": float(frame.get_column("skill_effect_war").sum()),
        "mean_absolute_shared_player_four_year_delta_war": float(
            career.get_column("expected_war_delta").abs().mean()
        ),
    }


def _season_summaries(frame: pl.DataFrame) -> list[dict[str, object]]:
    return (
        frame.group_by("projection_component", "season")
        .agg(
            pl.len().alias("shared_players"),
            pl.corr("earlier_expected_war", "later_expected_war").alias(
                "expected_war_correlation"
            ),
            pl.col("expected_war_delta")
            .abs()
            .mean()
            .alias("mean_absolute_delta_war"),
            pl.col("expected_war_delta").sum().alias("expected_war_delta"),
            pl.col("opportunity_effect_war").sum().alias("opportunity_effect_war"),
            pl.col("skill_effect_war").sum().alias("skill_effect_war"),
        )
        .sort(["projection_component", "season"])
        .to_dicts()
    )


def main() -> int:
    earlier_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    later_root = Path("reports/generated/historical-projection-paths/2025-10-15")
    output = Path("reports/generated/historical-projection-stability/2025-03-27_to_2025-10-15")
    earlier_report_path = earlier_root / "report.json"
    later_report_path = later_root / "report.json"
    earlier_report = json.loads(earlier_report_path.read_text(encoding="utf-8"))
    later_report = json.loads(later_report_path.read_text(encoding="utf-8"))
    if (
        later_report["frozen_fit"]["hitter_sha256"]
        != earlier_report["frozen_fit_artifacts"]["hitter"]["sha256"]
        or later_report["frozen_fit"]["pitcher_sha256"]
        != earlier_report["frozen_fit_artifacts"]["pitcher"]["sha256"]
    ):
        raise ValueError("checkpoint comparison requires identical frozen fit hashes")

    specifications = [
        ("hitter", "expected_mlb_pa", "conditional_war_per_600_pa", 600.0),
        ("pitcher", "expected_mlb_bf", "conditional_war_per_800_bf", 800.0),
    ]
    all_changes = []
    all_universe = []
    summaries = []
    source_paths = [earlier_report_path, later_report_path]
    for component, workload, rate, unit in specifications:
        earlier_path = earlier_root / "tables" / f"{component}-expected-war-paths.parquet"
        later_path = later_root / "tables" / f"{component}-expected-war-paths.parquet"
        source_paths.extend([earlier_path, later_path])
        changes, universe = compare_projection_checkpoints(
            pl.read_parquet(earlier_path),
            pl.read_parquet(later_path),
            component=component,
            workload_column=workload,
            rate_column=rate,
            workload_unit=unit,
        )
        all_changes.append(changes)
        all_universe.append(universe)
        summaries.append(_summary(changes, component))

    changes = pl.concat(all_changes, how="diagonal_relaxed").sort(
        ["projection_component", "player_id", "season"]
    )
    universe = pl.concat(all_universe).sort(
        ["projection_component", "player_id"]
    )
    player_changes = changes.group_by("projection_component", "player_id").agg(
        pl.col("earlier_expected_war").sum(),
        pl.col("later_expected_war").sum(),
        pl.col("expected_war_delta").sum(),
        pl.col("opportunity_effect_war").sum(),
        pl.col("skill_effect_war").sum(),
    ).sort("expected_war_delta", descending=True)

    output.mkdir(parents=True, exist_ok=True)
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "player_season_changes": write_canonical_parquet(
            changes,
            tables / "shared-player-season-changes.parquet",
            table_name="same_model_shared_player_season_changes",
        ).as_record(),
        "player_changes": write_canonical_parquet(
            player_changes,
            tables / "shared-player-four-year-changes.parquet",
            table_name="same_model_shared_player_four_year_changes",
        ).as_record(),
        "universe_changes": write_canonical_parquet(
            universe,
            tables / "player-universe-changes.parquet",
            table_name="same_model_player_universe_changes",
        ).as_record(),
    }
    universe_counts = (
        universe.group_by("projection_component", "universe_status")
        .len()
        .sort(["projection_component", "universe_status"])
        .to_dicts()
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "same_model_projection_checkpoint_stability",
        "earlier_checkpoint": earlier_report["checkpoint_date"],
        "later_checkpoint": later_report["checkpoint_date"],
        "overlapping_target_seasons": [2026, 2027, 2028, 2029],
        "identical_frozen_opportunity_fit_hashes": True,
        "component_summaries": summaries,
        "season_summaries": _season_summaries(changes),
        "universe_counts": universe_counts,
        "source_files": {path.as_posix(): sha256_file(path) for path in source_paths},
        "interpretation_boundaries": {
            "same_model_form": True,
            "opportunity_fit_refit": False,
            "new_2025_performance_and_roster_evidence": True,
            "forecast_horizon_rolled_forward_one_year": True,
            "same_target_season_can_use_a_different_horizon_component": True,
            "future_team_depth_used": False,
            "fangraphs_projection_values_used": False,
            "overlap_only_metrics_exclude_new_and_departed_players": True,
            "decomposition": "exact opportunity effect at earlier rate plus skill effect at later workload",
            "not_an_outcome_accuracy_score": True,
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
