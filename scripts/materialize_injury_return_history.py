#!/usr/bin/env python3
"""Materialize historical injured-list return evidence from official MLB sources."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.injury_return import (
    build_injury_return_cohort,
    fit_injury_return_references,
    normalize_injury_transaction_payload,
)
from universal_baseball.playing_time_roster_source import STATS_API_BASE
from universal_baseball.rest_of_season import project_team_schedule_calendar
from universal_baseball.rights_transactions import project_transaction_payload
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", default="2021,2022,2023,2024,2025")
    parser.add_argument(
        "--fit-start-season",
        type=int,
        default=2022,
        help=(
            "First season used to fit the production reference. Earlier requested "
            "seasons remain in the cohort as sensitivity evidence."
        ),
    )
    parser.add_argument("--cutoff-month", type=int, default=9)
    parser.add_argument("--cutoff-day", type=int, default=8)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/injury-return-history"),
    )
    return parser.parse_args()


def _capture(
    session: requests.Session, url: str, params: dict[str, object], path: Path
) -> dict:
    response = session.get(url, params=params, timeout=120)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return response.json()


def main() -> int:
    args = _args()
    seasons = tuple(sorted({int(value) for value in args.seasons.split(",")}))
    captures = args.output_root / "captures"
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    cohorts: list[pl.DataFrame] = []
    source_records: list[dict[str, object]] = []
    transaction_normalization: list[dict[str, object]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-injury-return/0.1"
        for season in seasons:
            cutoff = date(season, args.cutoff_month, args.cutoff_day)
            transaction_path = captures / f"transactions-{season}.json"
            transaction_payload = _capture(
                session,
                f"{STATS_API_BASE}/transactions",
                {
                    "sportId": 1,
                    "startDate": f"01/01/{season}",
                    "endDate": f"12/31/{season}",
                },
                transaction_path,
            )
            schedule_path = captures / f"schedule-{season}.json"
            schedule_payload = _capture(
                session,
                f"{STATS_API_BASE}/schedule",
                {"sportId": 1, "season": season, "gameType": "R"},
                schedule_path,
            )
            calendar, _, _ = project_team_schedule_calendar(
                schedule_payload, season=season, as_of_date=cutoff
            )
            season_end = calendar.get_column("championship_season_end").max()
            assert isinstance(season_end, date)
            transaction_payload, normalization = (
                normalize_injury_transaction_payload(
                    transaction_payload, season=season
                )
            )
            transaction_normalization.append({"season": season, **normalization})
            transactions = project_transaction_payload(
                transaction_payload,
                as_of_date=date(season, 12, 31),
                source_snapshot_id=f"statsapi:transactions:mlb:{season}",
            )
            cohorts.append(
                build_injury_return_cohort(
                    transactions,
                    cutoff_date=cutoff,
                    season_end_date=season_end,
                )
            )
            source_records.extend(
                {
                    "season": season,
                    "kind": kind,
                    "path": path.as_posix(),
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                }
                for kind, path in (
                    ("transactions", transaction_path),
                    ("schedule", schedule_path),
                )
            )
    cohort = pl.concat(cohorts, how="vertical")
    fit_cohort = cohort.filter(pl.col("season") >= args.fit_start_season)
    if fit_cohort.is_empty():
        raise ValueError("fit-start-season excludes the full historical cohort")
    fit = fit_injury_return_references(fit_cohort)
    annual = (
        cohort.group_by("season")
        .agg(
            pl.len().alias("cohort_players"),
            pl.col("returned_by_season_end").sum().alias("returned_players"),
            pl.col("returned_by_season_end").mean().alias("raw_return_rate"),
            pl.col("remaining_season_availability_fraction")
            .mean()
            .alias("raw_mean_remaining_availability_fraction"),
        )
        .sort("season")
        .to_dicts()
    )
    storage = {
        "cohort": write_canonical_parquet(
            cohort,
            tables / "injury-return-cohort.parquet",
            table_name="historical_injury_return_cohort",
        ).as_record(),
        "references": write_canonical_parquet(
            fit.references,
            tables / "injury-return-references.parquet",
            table_name="historical_injury_return_references",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_injury_return_source_baseline",
        "status": "production_reference_with_historical_sensitivity",
        "seasons": list(seasons),
        "fit_seasons": sorted(fit_cohort.get_column("season").unique().to_list()),
        "fit_start_season": args.fit_start_season,
        "cutoff_month_day": f"{args.cutoff_month:02d}-{args.cutoff_day:02d}",
        "cohort_players": cohort.height,
        "returned_players": int(cohort.get_column("returned_by_season_end").sum()),
        "raw_return_rate": float(cohort.get_column("returned_by_season_end").mean()),
        "raw_mean_remaining_availability_fraction": float(
            cohort.get_column("remaining_season_availability_fraction").mean()
        ),
        "fit_cohort_players": fit_cohort.height,
        "fit_returned_players": int(
            fit_cohort.get_column("returned_by_season_end").sum()
        ),
        "fit_raw_return_rate": float(
            fit_cohort.get_column("returned_by_season_end").mean()
        ),
        "fit_raw_mean_remaining_availability_fraction": float(
            fit_cohort.get_column("remaining_season_availability_fraction").mean()
        ),
        "annual_sensitivity": annual,
        "transaction_normalization": transaction_normalization,
        "source_records": source_records,
        "storage": storage,
        "boundary": (
            "placement/transfer/activation text is used only to reconstruct injured-list "
            "state and activation timing; age, injury diagnosis and current-team depth "
            "are not inferred"
        ),
        "fit_boundary": (
            "2021 remains visible as sensitivity evidence but is excluded from the "
            "production fit because MLB restored the 15-day injured list for pitchers "
            "and two-way players during 2022; 2022-2025 better matches the current "
            "injured-list structure"
        ),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "gate", "status", "cohort_players", "returned_players",
        "raw_return_rate", "raw_mean_remaining_availability_fraction",
        "fit_cohort_players", "fit_returned_players", "fit_raw_return_rate",
        "fit_raw_mean_remaining_availability_fraction",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
