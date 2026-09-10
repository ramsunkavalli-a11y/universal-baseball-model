#!/usr/bin/env python3
"""Freeze pre-MLB pitcher linked-path confirmation inputs without 2026 outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file, write_canonical_parquet


ROOT = Path("model_artifacts")
OUTPUT = ROOT / "prospect-pitcher-linked-2026-confirmation-forecast-2026-09-10"
OPPORTUNITY = ROOT / "opportunity-v2-2026-confirmation-forecast-2026-09-09/pitcher-selected.parquet"
INCUMBENT = ROOT / "pitcher-aging-2026-confirmation-forecast-2026-09-10/tango-aging.parquet"
DEBUT = Path(
    "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
)
PATHS = Path(
    "reports/generated/prospect-outcome-quality-2009-2025/post-debut-pitcher-performance-paths.parquet"
)
SNAPSHOTS = Path(
    "reports/generated/opportunity-history-sources-v2/tables/pitcher_snapshots.parquet"
)
CONTRACT = Path("docs/prospect-pitcher-linked-2026-confirmation-contract.md")
ENVIRONMENT = Path("docs/prospect-component-uncertainty-result.json")


def main() -> int:
    opportunity = pl.read_parquet(OPPORTUNITY)
    incumbent = pl.read_parquet(INCUMBENT).filter(pl.col("season") == 2026)
    debut = pl.read_parquet(DEBUT)
    environment = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    runs_per_win = float(environment["runs_per_win"])
    if runs_per_win <= 0:
        raise ValueError("runs per win must be positive")
    if debut.get_column("mlb_debut_date").max().year > 2025:
        raise ValueError("forecast freeze refuses any 2026 debut outcome")
    snapshot = pl.read_parquet(SNAPSHOTS).filter(pl.col("snapshot_year") == 2025)
    prospects = (
        opportunity.join(
            snapshot.select("player_id", "age_years", "as_of_level_group", "as_of_role"),
            on="player_id",
            how="inner",
            validate="1:1",
        )
        .join(debut, on="player_id", how="left", validate="1:1")
        .filter(pl.col("mlb_debut_date").is_null())
        .drop("mlb_debut_date")
        .join(
            incumbent.select(
                "player_id",
                "conditional_mlb_bf",
                "conditional_mlb_bf_variance",
                "conditional_war_per_800_bf",
                "event_run_variance",
                "posterior_run_rate_variance",
                "expected_war",
                "aging_source",
                "talent_model_id",
            ),
            on="player_id",
            how="inner",
            validate="1:1",
        )
        .sort("player_id")
    )
    if prospects.height == 0 or prospects.get_column("player_id").n_unique() != prospects.height:
        raise ValueError("prospect confirmation universe is empty or duplicated")
    path_source = pl.read_parquet(PATHS)
    if int(path_source.get_column("window_end_year").max()) > 2025:
        raise ValueError("linked path source crosses the 2025 outcome boundary")
    candidate = (
        path_source.filter(
            (pl.col("path_year") == 1) & (pl.col("adjusted_workload") > 0)
        )
        .select(
            "path_player_id",
            "debut_year",
            "outcome_tier_v2",
            "career_role",
            "adjusted_workload",
            "observed_component_war",
        )
        .sort("path_player_id")
    )
    if candidate.height < 1000 or not candidate.get_column(
        "observed_component_war"
    ).is_finite().all():
        raise ValueError("linked first-year path pool is insufficient")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = {
        "prospects": write_canonical_parquet(
            prospects,
            OUTPUT / "prospect-forecast-inputs.parquet",
            table_name="prospect_pitcher_linked_2026_forecast_inputs",
        ).as_record(),
        "linked_positive_paths": write_canonical_parquet(
            candidate,
            OUTPUT / "linked-positive-paths.parquet",
            table_name="prospect_pitcher_linked_2026_positive_paths",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "status": "frozen_before_final_2026_outcomes",
        "target_season": 2026,
        "prospect_pitchers": prospects.height,
        "linked_positive_paths": candidate.height,
        "linked_positive_path_mean_war": float(
            candidate.get_column("observed_component_war").mean()
        ),
        "runs_per_win": runs_per_win,
        "2026_outcomes_read": False,
        "contract_path": CONTRACT.as_posix(),
        "contract_sha256": sha256_file(CONTRACT),
        "runner_path": Path(__file__).relative_to(Path.cwd()).as_posix(),
        "runner_sha256": sha256_file(Path(__file__)),
        "sources": {
            path.as_posix(): sha256_file(path)
            for path in (OPPORTUNITY, INCUMBENT, DEBUT, PATHS, ENVIRONMENT, SNAPSHOTS)
        },
        "storage": storage,
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
