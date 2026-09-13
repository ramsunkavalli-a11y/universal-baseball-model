#!/usr/bin/env python3
"""Build retrospective post-debut service-pattern evidence from official MLB events."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.control_events import (
    classify_control_transactions,
    materialize_control_stints,
)
from universal_baseball.control_season_source import (
    fetch_season_windows,
    project_season_window,
)
from universal_baseball.historical_replay_inputs import MLB_TEAM_ID_BY_ABBREVIATION
from universal_baseball.people_control_source import (
    PeopleControlEvidence,
    fetch_people_control_evidence,
    project_people_control_payload,
)
from universal_baseball.roster_entry_source import build_opening_control_states
from universal_baseball.source_capture import (
    load_parsed_json_captures,
    persist_parsed_json_captures,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet
from universal_baseball.team_control import calculate_control_years


START_DEBUT_YEAR = 2009
END_DEBUT_YEAR = 2019
LAST_OBSERVED_SEASON = 2024
PATH_YEARS = 6
AS_OF_DATE = date(2024, 12, 31)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-historical-service-paths-2009-2019"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-historical-service-paths-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-historical-service-paths-result.md"),
    )
    return parser.parse_args()


def _project_people_captures(root: Path) -> PeopleControlEvidence:
    captures = load_parsed_json_captures(root)
    batches = [
        project_people_control_payload(
            capture["payload"],
            as_of_date=AS_OF_DATE,
            source_snapshot_id=str(capture["source_snapshot_id"]),
        )
        for name, capture in sorted(captures.items())
        if name.startswith("people-")
    ]
    if not batches:
        raise ValueError("historical service capture set contains no people batches")
    return PeopleControlEvidence(
        people=pl.concat([item.people for item in batches]),
        roster_entries=pl.concat(
            [item.roster_entries for item in batches], how="vertical_relaxed"
        ),
        transactions=pl.concat(
            [item.transactions for item in batches], how="vertical_relaxed"
        ),
        captures=[],
    )


def _deduplicate(frame: pl.DataFrame, kind: str) -> pl.DataFrame:
    if kind == "people":
        return frame.unique("player_id", keep="first").sort("player_id")
    if kind == "roster_entries":
        return frame.unique(
            ["player_id", "team_id", "status_code", "start_date", "end_date"],
            keep="first",
        ).sort(["player_id", "start_date", "team_id"])
    return frame.unique(["player_id", "transaction_id"], keep="first").sort(
        ["player_id", "effective_date", "transaction_id"]
    )


def _season_windows(root: Path) -> pl.DataFrame:
    capture_root = root / "season-window-captures"
    if capture_root.is_dir():
        captures = load_parsed_json_captures(capture_root)
        frames = [
            project_season_window(capture["payload"], season=int(name[7:11]))
            for name, capture in sorted(captures.items())
            if name.startswith("season-")
        ]
        return pl.concat(frames).sort("season")
    windows, captures = fetch_season_windows(
        range(START_DEBUT_YEAR, LAST_OBSERVED_SEASON + 1)
    )
    persist_parsed_json_captures(
        (
            (f"season-{int(capture['season'])}.json", capture)
            for capture in captures
        ),
        capture_root,
    )
    return windows


def _activity() -> pl.DataFrame:
    root = Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables")
    batting = pl.read_parquet(root / "mlb_batting_2009_2025.parquet").select(
        "player_id", "season", pl.col("batting_pa").alias("workload")
    )
    pitching = pl.read_parquet(root / "mlb_pitching_2009_2025.parquet").select(
        "player_id", "season", pl.col("pitching_bf").alias("workload")
    )
    return (
        pl.concat([batting, pitching])
        .group_by("player_id", "season")
        .agg(pl.col("workload").sum())
        .filter(pl.col("season") <= LAST_OBSERVED_SEASON)
    )


def main() -> int:
    args = _args()
    outcome_root = Path(
        "reports/generated/career-mlb-outcome-inventory-2009-2025/tables"
    )
    debut_path = outcome_root / "people-debut-dates.parquet"
    retained_root = Path("reports/generated/historical-people-control/2025-10-15/tables")
    fg_path = Path(
        "reports/generated/fangraphs-opening-day-control/2025/"
        "opening-day-control-baseline.parquet"
    )
    cohort = (
        pl.read_parquet(debut_path)
        .filter(
            pl.col("mlb_debut_date")
            .dt.year()
            .is_between(START_DEBUT_YEAR, END_DEBUT_YEAR)
        )
        .with_columns(pl.col("mlb_debut_date").dt.year().alias("debut_year"))
        .sort("player_id")
    )
    cohort_ids = set(cohort.get_column("player_id").to_list())
    retained_people = pl.read_parquet(retained_root / "people.parquet")
    retained_ids = set(retained_people.get_column("player_id").to_list())
    missing_ids = sorted(cohort_ids - retained_ids)
    supplement_root = args.output_root / "people-captures"
    if supplement_root.is_dir():
        supplement = _project_people_captures(supplement_root)
        acquisition = "official_statsapi_capture_hash_verified"
    elif missing_ids:
        supplement = fetch_people_control_evidence(
            missing_ids, as_of_date=AS_OF_DATE, batch_size=50
        )
        persist_parsed_json_captures(
            (
                (f"people-{index:03d}.json", capture)
                for index, capture in enumerate(supplement.captures, start=1)
            ),
            supplement_root,
        )
        acquisition = "official_statsapi_capture_hash_verified"
    else:
        supplement = PeopleControlEvidence(
            people=retained_people.head(0),
            roster_entries=pl.read_parquet(retained_root / "roster-entries.parquet").head(0),
            transactions=pl.read_parquet(retained_root / "transactions.parquet").head(0),
            captures=[],
        )
        acquisition = "existing_retained_evidence_complete"

    people = _deduplicate(
        pl.concat(
            [retained_people, supplement.people], how="vertical_relaxed"
        ).filter(pl.col("player_id").is_in(sorted(cohort_ids))),
        "people",
    )
    roster_entries = _deduplicate(
        pl.concat(
            [
                pl.read_parquet(retained_root / "roster-entries.parquet"),
                supplement.roster_entries,
            ],
            how="vertical_relaxed",
        ).filter(
            pl.col("player_id").is_in(sorted(cohort_ids))
            & (pl.col("start_date").dt.year() <= LAST_OBSERVED_SEASON)
        ),
        "roster_entries",
    )
    transactions = _deduplicate(
        pl.concat(
            [
                pl.read_parquet(retained_root / "transactions.parquet"),
                supplement.transactions,
            ],
            how="vertical_relaxed",
        ).filter(
            pl.col("player_id").is_in(sorted(cohort_ids))
            & (pl.col("effective_date").dt.year() <= LAST_OBSERVED_SEASON)
        ),
        "transactions",
    )
    if set(people.get_column("player_id")) != cohort_ids:
        raise RuntimeError("official people evidence does not cover the debut cohort")

    windows = _season_windows(args.output_root)
    mlb_team_ids = set(MLB_TEAM_ID_BY_ABBREVIATION.values())
    openings = build_opening_control_states(
        roster_entries, windows, mlb_team_ids=mlb_team_ids
    )
    events = classify_control_transactions(
        transactions, mlb_team_ids=mlb_team_ids
    ).filter(
        pl.col("season").is_between(START_DEBUT_YEAR, LAST_OBSERVED_SEASON)
    )
    materialized = materialize_control_stints(
        openings.opening_states, events, windows, as_of_date=AS_OF_DATE
    )
    control = calculate_control_years(
        materialized.stints, windows, as_of_date=AS_OF_DATE
    )

    path_grid = pl.concat(
        [
            cohort.select("player_id", "debut_year").with_columns(
                (pl.col("debut_year") + offset).alias("season"),
                pl.lit(offset + 1).alias("path_year"),
            )
            for offset in range(PATH_YEARS)
        ]
    ).sort(["player_id", "season"])
    window_days = windows.with_columns(
        ((pl.col("end_date") - pl.col("start_date")).dt.total_days() + 1).alias(
            "season_calendar_days"
        )
    ).select("season", "season_calendar_days")
    activity = _activity().filter(pl.col("player_id").is_in(sorted(cohort_ids)))
    review_pairs = pl.concat(
        [
            openings.review_players.select("player_id", "season"),
            materialized.review_events.select("player_id", "season"),
        ]
    ).unique().with_columns(pl.lit(True).alias("state_review"))
    paths = (
        path_grid.join(control, on=["player_id", "season"], how="left")
        .join(activity, on=["player_id", "season"], how="left")
        .join(review_pairs, on=["player_id", "season"], how="left")
        .join(window_days, on="season", how="left", validate="m:1")
        .with_columns(
            pl.col("service_days").fill_null(0),
            pl.col("workload").fill_null(0),
            pl.col("state_review").fill_null(False),
        )
        .with_columns(
            pl.when(pl.col("season") == 2020)
            .then(
                (pl.col("service_days") * 172 / pl.col("season_calendar_days"))
                .round()
                .clip(0, 172)
                .cast(pl.Int64)
            )
            .otherwise(pl.col("service_days"))
            .alias("standardized_service_days"),
            ((pl.col("workload") > 0) & (pl.col("service_days") == 0)).alias(
                "active_without_service_evidence"
            ),
        )
        .select(
            "player_id", "debut_year", "season", "path_year", "workload",
            "service_days", "standardized_service_days", "optioned_days",
            "option_year_used", "state_review", "active_without_service_evidence",
        )
        .sort(["player_id", "path_year"])
    )
    path_summary = paths.group_by("player_id").agg(
        pl.col("standardized_service_days").sum().alias("six_year_service_days"),
        pl.col("service_days").first().alias("first_year_service_days"),
        pl.col("active_without_service_evidence").sum().alias(
            "active_years_without_service_evidence"
        ),
        pl.col("state_review").sum().alias("reviewed_player_years"),
    )

    full_control = (
        control.join(window_days, on="season", how="left", validate="m:1")
        .with_columns(
            pl.when(pl.col("season") == 2020)
            .then(
                (pl.col("service_days") * 172 / pl.col("season_calendar_days"))
                .round()
                .clip(0, 172)
                .cast(pl.Int64)
            )
            .otherwise(pl.col("service_days"))
            .alias("standardized_service_days")
        )
        .group_by("player_id")
        .agg(pl.col("standardized_service_days").sum().alias("reconstructed_service_days"))
    )
    fg = pl.read_parquet(fg_path).select(
        "player_id", pl.col("service_days").alias("fangraphs_service_days")
    )
    validation = (
        cohort.select("player_id")
        .join(full_control, on="player_id", how="left")
        .join(fg, on="player_id", how="inner")
        .with_columns(pl.col("reconstructed_service_days").fill_null(0))
        .with_columns(
            (pl.col("reconstructed_service_days") - pl.col("fangraphs_service_days"))
            .abs()
            .alias("absolute_error_days")
        )
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    storage = {
        "annual_paths": write_canonical_parquet(
            paths,
            args.output_root / "annual-service-paths.parquet",
            table_name="prospect_historical_annual_service_paths",
        ).as_record(),
        "path_summary": write_canonical_parquet(
            path_summary,
            args.output_root / "service-path-summary.parquet",
            table_name="prospect_historical_service_path_summary",
        ).as_record(),
        "opening_reviews": write_canonical_parquet(
            openings.review_players,
            args.output_root / "opening-state-reviews.parquet",
            table_name="prospect_historical_opening_state_reviews",
        ).as_record(),
        "event_reviews": write_canonical_parquet(
            materialized.review_events,
            args.output_root / "transaction-state-reviews.parquet",
            table_name="prospect_historical_transaction_state_reviews",
        ).as_record(),
        "fangraphs_validation": write_canonical_parquet(
            validation,
            args.output_root / "fangraphs-service-validation.parquet",
            table_name="prospect_historical_fangraphs_service_validation",
        ).as_record(),
    }
    first_year = path_summary.get_column("first_year_service_days")
    report = {
        "status": "historical_service_path_evidence_not_yet_promoted",
        "cohort": {
            "debut_years": [START_DEBUT_YEAR, END_DEBUT_YEAR],
            "players": cohort.height,
            "six_year_path_rows": paths.height,
        },
        "acquisition": acquisition,
        "official_people_coverage": people.height,
        "roster_entry_rows": roster_entries.height,
        "transaction_rows": transactions.height,
        "classified_transaction_rows": events.height,
        "opening_state_review_rows": openings.review_players.height,
        "transaction_state_review_rows": materialized.review_events.height,
        "active_years_without_service_evidence": int(
            paths.get_column("active_without_service_evidence").sum()
        ),
        "first_year_service": {
            "median_days": float(first_year.median()),
            "share_below_172": float((first_year < 172).mean()),
            "share_below_100": float((first_year < 100).mean()),
        },
        "fangraphs_2025_opening_validation": {
            "players": validation.height,
            "exact_share": float(
                (validation.get_column("absolute_error_days") == 0).mean()
            ) if validation.height else None,
            "within_15_days_share": float(
                (validation.get_column("absolute_error_days") <= 15).mean()
            ) if validation.height else None,
            "mean_absolute_error_days": float(
                validation.get_column("absolute_error_days").mean()
            ) if validation.height else None,
            "median_absolute_error_days": float(
                validation.get_column("absolute_error_days").median()
            ) if validation.height else None,
        },
        "decision_rule": (
            "Promote service-pattern donors only if active-season coverage is complete "
            "and opening-service validation is accurate enough for control-year timing."
        ),
        "boundaries": {
            "statsapi_roster_and_transaction_evidence": True,
            "later_retrieval_not_vintage_snapshot": True,
            "outside_fv_used": False,
            "first_active_season_not_assumed_full_service": True,
            "2020_normalized_to_172_day_scale": True,
            "super_two_not_assigned_here": True,
            "salary_or_value_not_assigned_here": True,
        },
        "source_files": {
            debut_path.as_posix(): sha256_file(debut_path),
            fg_path.as_posix(): sha256_file(fg_path),
        },
        "storage": storage,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    validation_result = report["fangraphs_2025_opening_validation"]
    args.output_md.write_text(
        "\n".join(
            [
                "# Historical prospect service-path result",
                "",
                "**Status:** historical evidence; not yet used in player value.",
                "",
                f"The official-event cohort contains {cohort.height:,} players who debuted "
                f"from {START_DEBUT_YEAR} through {END_DEBUT_YEAR}. The old value simulator's "
                "one-active-season-equals-one-service-year shortcut is not retained.",
                "",
                f"Median first-year reconstructed service is {report['first_year_service']['median_days']:.0f} days; "
                f"{report['first_year_service']['share_below_172']:.1%} are below a full 172-day year.",
                "",
                f"Against {validation_result['players']:,} FanGraphs 2025 opening balances, "
                f"the median absolute error is {validation_result['median_absolute_error_days']:.1f} days "
                f"and {validation_result['within_15_days_share']:.1%} are within 15 days.",
                "",
                "Promotion requires complete active-season coverage and accurate enough service timing. "
                "This artifact does not assign FV, controlled WAR, salary or dollar value.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
