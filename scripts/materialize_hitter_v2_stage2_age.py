#!/usr/bin/env python3
"""Materialize immutable age features for pre-cutoff forecast populations."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.chadwick import (
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLD_TARGETS = {"V2022": 2022, "V2023": 2023, "V2024": 2024}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--register-archive",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-age/"
            f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    people = read_chadwick_people_archive(args.register_archive)
    fold_records = []
    for fold_id, target_season in FOLD_TARGETS.items():
        population_path = (
            args.prescore_root
            / fold_id.lower()
            / "forecast_population.parquet"
        )
        population = pl.read_parquet(population_path)
        ages = build_mlbam_age_as_of(
            people,
            population["player_id"].to_list(),
            as_of_date=date(target_season, 7, 1),
        )
        if ages.height != population.height:
            raise RuntimeError(f"{fold_id} age rows differ from forecast population")
        status = Counter(str(value) for value in ages["age_source_status"].to_list())
        exact = ages.filter(pl.col("age_source_status") == "exact_birth_date")
        artifact = write_canonical_parquet(
            ages,
            args.report_root / "tables" / fold_id.lower() / "forecast_player_ages.parquet",
            table_name=f"hitter_v2_{fold_id.lower()}_forecast_player_ages",
        ).as_record()
        fold_records.append(
            {
                "fold_id": fold_id,
                "target_season": target_season,
                "as_of_date": f"{target_season}-07-01",
                "forecast_players": population.height,
                "exact_birth_date_players": exact.height,
                "exact_birth_date_coverage_rate": exact.height / population.height,
                "status_counts": dict(sorted(status.items())),
                "forecast_population_sha256": sha256_file(population_path),
                "storage": artifact,
            }
        )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": "forecast_population_age_source_materialized",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "source": {
            "repository": "chadwickbureau/register",
            "snapshot_commit": CHADWICK_SNAPSHOT_SHA,
            "archive_path": args.register_archive.as_posix(),
            "archive_sha256": sha256_file(args.register_archive),
            "immutable_field": "birth_date",
        },
        "membership_policy": (
            "ages are derived only for forecast populations frozen from pre-cutoff "
            "evidence; target participant membership is not consulted"
        ),
        "missing_policy": "retain missing age and use the declared neutral age fallback",
        "folds": fold_records,
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
