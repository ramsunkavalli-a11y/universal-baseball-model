#!/usr/bin/env python3
"""Compare the new hitter candidate with the older 2025 forecast on one target."""

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


NEW_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
INCUMBENT_PATH = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated/historical-projection-paths/"
    "2025-03-27/tables/hitter-expected-war-paths.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-incumbent-comparison-2025")


def _metrics(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_component_war"].to_numpy()
    return {
        "rows": frame.height,
        "new_candidate": regression_metrics(
            actual, frame["new_component_war_forecast"].to_numpy()
        ),
        "incumbent": regression_metrics(
            actual, frame["incumbent_component_war_forecast"].to_numpy()
        ),
    }


def main() -> None:
    new = pl.read_parquet(NEW_PATH).filter(pl.col("origin_year") == 2024)
    incumbent = (
        pl.read_parquet(INCUMBENT_PATH)
        .filter((pl.col("season") == 2025) & (pl.col("horizon") == 1))
        .with_columns(
            (
                (
                    pl.col("batting_runs_per_600")
                    + pl.col("baserunning_runs_per_600")
                    + pl.col("defense_runs_per_600")
                    + pl.col("positional_runs_per_600")
                    + pl.col("replacement_runs_per_600")
                )
                / pl.col("conditional_war_per_600_pa")
            ).alias("incumbent_runs_per_win")
        )
        .with_columns(
            (
                pl.col("expected_mlb_pa")
                / 600.0
                * (
                    pl.col("batting_runs_per_600")
                    + pl.col("replacement_runs_per_600")
                )
                / pl.col("incumbent_runs_per_win")
            ).alias("incumbent_component_war_forecast")
        )
    )
    rpw_min = float(incumbent["incumbent_runs_per_win"].min())
    rpw_max = float(incumbent["incumbent_runs_per_win"].max())
    if abs(rpw_max - rpw_min) > 1e-9:
        raise ValueError("incumbent runs-per-win is not constant")

    comparison = (
        new.rename(
            {"prediction_candidate_equal_mean": "new_component_war_forecast"}
        )
        .join(
            incumbent.select(
                "player_id",
                "as_of_date",
                "expected_mlb_pa",
                "batting_runs_per_600",
                "replacement_runs_per_600",
                "incumbent_runs_per_win",
                "incumbent_component_war_forecast",
            ),
            on="player_id",
            how="inner",
        )
        .sort("player_id")
    )
    actual = comparison["actual_component_war"].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        comparison["new_component_war_forecast"].to_numpy(),
        comparison["incumbent_component_war_forecast"].to_numpy(),
        comparison["player_id"].to_numpy(),
    )
    by_stage = {
        stage: _metrics(comparison.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_activity = {
        label: _metrics(comparison.filter(pl.col("actual_active") == active))
        for label, active in (("active_in_2025", 1), ("inactive_in_2025", 0))
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        comparison,
        OUTPUT_ROOT / "common-cohort-predictions.parquet",
        table_name="hitter_incumbent_comparison_2025_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "like_for_like_incumbent_comparison_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "forecast_target": "2025 MLB batting-plus-replacement WAR including zero",
        "information_boundary": {
            "new": "2024 season-end player history",
            "incumbent": "2025-03-27 opening-day forecast",
        },
        "population": {
            "new_2024_origin_players": new.height,
            "incumbent_2025_players": incumbent.height,
            "common_players": comparison.height,
        },
        "incumbent_component_reconstruction": {
            "formula": (
                "expected_mlb_pa / 600 * (batting_runs_per_600 + "
                "replacement_runs_per_600) / runs_per_win"
            ),
            "runs_per_win": rpw_min,
            "reason": (
                "remove baserunning, defense, and positional runs so both forecasts "
                "are scored against the same batting-plus-replacement outcome"
            ),
        },
        "overall": _metrics(comparison),
        "new_minus_incumbent": paired,
        "by_player_stage": by_stage,
        "by_actual_activity": by_activity,
        "sources": {
            "new": {"path": str(NEW_PATH), "sha256": sha256_file(NEW_PATH)},
            "incumbent": {
                "path": str(INCUMBENT_PATH),
                "sha256": sha256_file(INCUMBENT_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "This is one already-exposed development season, not fresh confirmation.",
            "The comparison covers only players present in both forecast universes.",
            "Defense, baserunning, and position are deliberately removed from the incumbent forecast.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
