#!/usr/bin/env python3
"""Build complete historical donor paths for the annually linked simulator."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_mlb_progression import (
    SIMULATED_STATE_CODES,
    add_observed_annual_career_states,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ANNUAL = Path(
    "reports/generated/prospect-outcome-quality-2009-2025/"
    "post-debut-annual-workload-paths.parquet"
)
DEMOGRAPHICS = Path(
    "reports/generated/player-demographics/tables/player-demographics.parquet"
)
MLB_ROOT = Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables")
OUTPUT = Path("model_artifacts/prospect-linked-career-state-paths-2009-2025")
RUNNER = Path("scripts/materialize_linked_career_state_paths.py")


def _environments() -> pl.DataFrame:
    rows = []
    for player_type, filename, workload in (
        ("hitter", "mlb_batting_2009_2025.parquet", "batting_pa"),
        ("pitcher", "mlb_pitching_2009_2025.parquet", "pitching_bf"),
    ):
        frame = pl.read_parquet(MLB_ROOT / filename)
        rows.append(
            frame.filter(pl.col(workload) > 0)
            .group_by("season")
            .agg(pl.col(workload).mean().alias("active_mean_raw_workload"))
            .with_columns(pl.lit(player_type).alias("player_type"))
            .rename({"season": "source_season"})
        )
    return pl.concat(rows, how="vertical").sort("player_type", "source_season")


def main() -> int:
    sources = [
        ANNUAL,
        DEMOGRAPHICS,
        MLB_ROOT / "mlb_batting_2009_2025.parquet",
        MLB_ROOT / "mlb_pitching_2009_2025.parquet",
    ]
    if missing := [path for path in sources if not path.exists()]:
        raise FileNotFoundError(f"linked career-state sources missing: {missing}")
    annual = add_observed_annual_career_states(pl.read_parquet(ANNUAL))
    demographics = pl.read_parquet(DEMOGRAPHICS).select(
        pl.col("player_id").alias("path_player_id"), "birth_date"
    )
    paths = (
        annual.join(demographics, on="path_player_id", how="left", validate="m:1")
        .join(
            _environments(),
            on=["player_type", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("adjusted_workload") / pl.col("shortened_2020_scale"))
            .otherwise(pl.col("adjusted_workload"))
            .alias("raw_workload"),
            (
                (
                    pl.date(pl.col("source_season"), 7, 1)
                    - pl.col("birth_date")
                ).dt.total_days()
                / 365.2425
            ).alias("season_age_years"),
            pl.col("birth_date").is_not_null().alias("age_evidence_available"),
        )
        .sort("path_player_id", "player_type", "path_year")
        .with_columns(
            pl.col("raw_workload")
            .shift(1)
            .over("path_player_id", "player_type")
            .fill_null(0.0)
            .alias("prior_raw_workload"),
            pl.col("active_mean_raw_workload")
            .shift(1)
            .over("path_player_id", "player_type")
            .alias("prior_active_mean_raw_workload"),
            pl.col("observed_career_state")
            .shift(1)
            .over("path_player_id", "player_type")
            .fill_null("NO_MLB")
            .alias("from_state"),
        )
        .with_columns(
            pl.when(pl.col("path_year") == 1)
            .then(0.0)
            .otherwise(
                pl.col("prior_raw_workload")
                / pl.col("prior_active_mean_raw_workload")
            )
            .alias("prior_workload_vs_active_mean"),
            pl.col("observed_career_state").alias("to_state"),
        )
    )
    if paths.filter(
        pl.col("active_mean_raw_workload").is_null()
        | pl.col("prior_workload_vs_active_mean").is_null()
        | ~pl.col("prior_workload_vs_active_mean").is_finite()
    ).height:
        raise ValueError("linked career-state paths have missing age or environment")
    if paths.group_by("path_player_id", "player_type").len().filter(
        pl.col("len") != 6
    ).height:
        raise ValueError("linked career-state donor path is not six complete years")
    if paths.with_columns(
        pl.col("from_state").replace_strict(SIMULATED_STATE_CODES).alias("_from"),
        pl.col("to_state").replace_strict(SIMULATED_STATE_CODES).alias("_to"),
    ).filter(pl.col("_to") < pl.col("_from")).height:
        raise ValueError("linked donor state moves backward")
    terminal = paths.filter(pl.col("path_year") == 6).with_columns(
        pl.col("outcome_tier_v2")
        .replace_strict(
            {
                "fringe": "FRINGE_MLB",
                "meaningful_only": "MEANINGFUL_MLB",
                "established": "ESTABLISHED_MLB",
            }
        )
        .alias("expected_terminal_state")
    )
    terminal_mismatches = terminal.filter(
        pl.col("observed_career_state") != pl.col("expected_terminal_state")
    ).height
    if terminal_mismatches:
        raise ValueError("annual states do not reproduce frozen terminal career tiers")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        paths,
        OUTPUT / "annual-state-paths.parquet",
        table_name="prospect_linked_annual_career_state_paths_2009_2025",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "historical_linked_state_path_source_ready_not_promoted",
        "created_on": date.today().isoformat(),
        "players": paths.select("path_player_id", "player_type").unique().height,
        "players_with_age_evidence": paths.filter(
            pl.col("age_evidence_available")
        ).select("path_player_id", "player_type").unique().height,
        "players_without_age_evidence": paths.filter(
            ~pl.col("age_evidence_available")
        ).select("path_player_id", "player_type").unique().height,
        "annual_rows": paths.height,
        "minimum_debut_year": int(paths["debut_year"].min()),
        "maximum_window_end_year": int(paths["window_end_year"].max()),
        "current_2026_used": False,
        "whole_six_year_paths_retained": True,
        "terminal_state_mismatches": terminal_mismatches,
        "missing_age_paths_retained_for_explicit_fallback": True,
        "shortened_2020_state_uses_full_season_equivalent": True,
        "shortened_2020_relative_workload_uses_raw_scale": True,
        "production_changed": False,
        "runner_path": RUNNER.as_posix(),
        "runner_sha256": sha256_file(RUNNER),
        "sources": {path.as_posix(): sha256_file(path) for path in sources},
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
