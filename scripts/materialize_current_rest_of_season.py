#!/usr/bin/env python3
"""Materialize current-season remaining WAR and base-salary evidence."""

from __future__ import annotations

import argparse
from datetime import date
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re

import polars as pl
import requests

from universal_baseball.current_availability import (
    apply_current_availability_sensitivity,
    project_current_affiliated_status_payload,
)
from universal_baseball.playing_time_roster_source import STATS_API_BASE
from universal_baseball.remaining_rights import (
    REMAINING_RIGHTS_INPUT_SCHEMA,
    build_remaining_rights_inputs,
)
from universal_baseball.rest_of_season import (
    build_hitter_ros_paths,
    build_pitcher_ros_paths,
    build_remaining_base_salary,
    project_team_schedule_calendar,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--current-source-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--current-capture-root", type=Path,
        default=Path(
            "reports/generated/opportunity-current-source-2026-09-08/captures/2026"
        ),
    )
    parser.add_argument(
        "--mlb-skill-root", type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--opportunity-root", type=Path,
        default=Path("reports/generated/current-opportunity-paths"),
    )
    parser.add_argument(
        "--war-root", type=Path,
        default=Path("reports/generated/current-conditional-war-paths"),
    )
    parser.add_argument(
        "--control-root", type=Path,
        default=Path("reports/generated/league-control"),
    )
    parser.add_argument(
        "--future-economics-root", type=Path,
        default=Path("reports/generated/current-contract-economics-inputs"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-rest-of-season"),
    )
    return parser.parse_args()


def _schedule(as_of_date: date, output_root: Path) -> tuple[pl.DataFrame, int, int, dict]:
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-rest-of-season/0.1"
        response = session.get(
            f"{STATS_API_BASE}/schedule",
            params={"sportId": 1, "season": as_of_date.year, "gameType": "R"},
            timeout=120,
        )
        response.raise_for_status()
    output_root.mkdir(parents=True, exist_ok=True)
    raw_path = output_root / "official-mlb-schedule.json"
    raw_path.write_bytes(response.content)
    digest = sha256(response.content).hexdigest()
    if sha256(raw_path.read_bytes()).hexdigest() != digest:
        raise RuntimeError("persisted schedule source hash mismatch")
    payload = response.json()
    calendar, completed, scheduled = project_team_schedule_calendar(
        payload, season=as_of_date.year, as_of_date=as_of_date
    )
    return calendar, completed, scheduled, {
        "requested_url": response.url,
        "response_bytes": len(response.content),
        "response_sha256": digest,
        "raw_path": raw_path.as_posix(),
    }


def _availability_statuses(capture_root: Path, as_of_date: date) -> pl.DataFrame:
    frames = []
    for path in sorted(capture_root.glob("full-roster-*.json.gz")):
        match = re.fullmatch(r"full-roster-(\d+)\.json\.gz", path.name)
        if match is None:
            raise ValueError(f"unexpected full-roster capture name: {path.name}")
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            capture = json.load(handle)
        payload = capture.get("payload", capture)
        frames.append(
            project_current_affiliated_status_payload(
                payload,
                organization_id=int(match.group(1)),
                as_of_date=as_of_date,
            )
        )
    if len(frames) != 30:
        raise ValueError(f"current availability requires 30 team captures, got {len(frames)}")
    return pl.concat(frames).sort(["organization_id", "player_id"])


def main() -> int:
    args = _args()
    output_root = args.output_root / args.as_of_date.isoformat()
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    calendar, completed, scheduled, schedule_capture = _schedule(
        args.as_of_date, output_root
    )
    dated_skill = args.mlb_skill_root / args.as_of_date.isoformat() / "tables"
    dated_opportunity = args.opportunity_root / args.as_of_date.isoformat() / "tables"
    dated_war = args.war_root / args.as_of_date.isoformat() / "tables"
    dated_control = args.control_root / args.as_of_date.isoformat()
    hitter_opportunity = pl.read_parquet(
        dated_opportunity / "hitter_opportunity_paths.parquet"
    ).filter(pl.col("season") == args.as_of_date.year + 1)
    pitcher_opportunity = pl.read_parquet(
        dated_opportunity / "pitcher_opportunity_paths.parquet"
    ).filter(pl.col("season") == args.as_of_date.year + 1)
    hitter_players = hitter_opportunity.select("player_id")
    pitcher_players = pitcher_opportunity.select("player_id")
    hitter_ros = build_hitter_ros_paths(
        hitter_players,
        pl.read_parquet(dated_skill / "mlb_hitting_components.parquet").filter(
            pl.col("season") == args.as_of_date.year
        ),
        hitter_opportunity,
        pl.read_parquet(dated_war / "hitter_conditional_war_rates.parquet").filter(
            pl.col("season") == args.as_of_date.year + 1
        ),
        as_of_date=args.as_of_date,
        completed_league_games=completed,
        scheduled_league_games=scheduled,
    )
    pitcher_ros = build_pitcher_ros_paths(
        pitcher_players,
        pl.read_parquet(dated_skill / "mlb_pitching_components.parquet").filter(
            pl.col("season") == args.as_of_date.year
        ),
        pitcher_opportunity,
        pl.read_parquet(dated_war / "pitcher_conditional_war_rates.parquet").filter(
            pl.col("season") == args.as_of_date.year + 1
        ),
        as_of_date=args.as_of_date,
        completed_league_games=completed,
        scheduled_league_games=scheduled,
    )
    whole_player_unadjusted = pl.concat(
        [
            hitter_ros.select("player_id", "projected_remaining_war"),
            pitcher_ros.select("player_id", "projected_remaining_war"),
        ]
    ).group_by("player_id").agg(
        pl.col("projected_remaining_war").sum().alias("projected_remaining_war_mean")
    ).join(
        pl.read_parquet(dated_control / "league-control-snapshot.parquet").select(
            "player_id", "organization_id", "organization_status"
        ),
        on="player_id", how="left", validate="1:1",
    ).with_columns(
        pl.lit(args.as_of_date).alias("as_of_date"),
        pl.lit(args.as_of_date.year).alias("season"),
        pl.lit("hitter_plus_pitcher_ros_v1").alias("projection_source_id"),
    ).select(
        "as_of_date", "season", "player_id", "organization_id",
        "organization_status", "projected_remaining_war_mean", "projection_source_id",
    ).sort("player_id")
    availability = _availability_statuses(
        args.current_capture_root, args.as_of_date
    )
    whole_player = apply_current_availability_sensitivity(
        whole_player_unadjusted,
        availability,
    )
    salary = build_remaining_base_salary(
        pl.read_parquet(dated_control / "contract-year-liabilities.parquet"),
        calendar,
        as_of_date=args.as_of_date,
    )
    salary_reconciliation = salary.join(
        whole_player.select(
            "player_id",
            "organization_id",
            "projected_remaining_war_mean",
            "projected_remaining_war_lower",
            "projected_remaining_war_upper",
        ),
        on="player_id",
        how="left",
        suffix="_current",
        validate="m:1",
    ).with_columns(
        pl.when(pl.col("projected_remaining_war_mean").is_null())
        .then(pl.lit("missing_projection"))
        .when(pl.col("organization_id_current").is_null())
        .then(pl.lit("unresolved_current_organization"))
        .when(pl.col("organization_id") != pl.col("organization_id_current"))
        .then(pl.lit("payroll_current_organization_mismatch"))
        .otherwise(pl.lit("matched_current_rights"))
        .alias("rights_join_status")
    )
    rights_source = salary_reconciliation.filter(
        pl.col("rights_join_status") == "matched_current_rights"
    ).select(
        "as_of_date",
        "player_id",
        "organization_id",
        "season",
        pl.lit("remaining_current_season").alias("forecast_scope"),
        pl.lit(None, dtype=pl.Float64).alias("realized_war_to_date"),
        "projected_remaining_war_mean",
        "projected_remaining_war_lower",
        "projected_remaining_war_upper",
        pl.lit("current_season_committed").alias("control_status"),
        pl.col("remaining_base_salary_dollars").alias(
            "salary_obligation_dollars"
        ),
        pl.lit(None, dtype=pl.Int64).alias("buyout_dollars"),
        pl.lit(None, dtype=pl.Int64).alias("arbitration_class"),
        pl.lit(None, dtype=pl.Float64).alias("arbitration_salary_basis_war"),
        pl.lit("").alias("arbitration_salary_basis_source"),
        pl.lit("hitter_plus_pitcher_ros_v1").alias("projection_source_id"),
        pl.col("source_snapshot_id").alias("contract_source_id"),
    ).select(
        list(REMAINING_RIGHTS_INPUT_SCHEMA)
    ).cast(REMAINING_RIGHTS_INPUT_SCHEMA, strict=True)
    rights = build_remaining_rights_inputs(rights_source)
    future_inputs = pl.read_parquet(
        args.future_economics_root
        / args.as_of_date.isoformat()
        / "annual-contract-economics-inputs.parquet"
    )
    combined_economics = pl.concat(
        [rights.economics_inputs, future_inputs], how="vertical"
    ).sort(["player_id", "organization_id", "season"])
    if combined_economics.group_by(
        ["player_id", "organization_id", "season"]
    ).len().filter(pl.col("len") != 1).height:
        raise ValueError("current-and-future economics violates annual grain")
    storage = {
        "team_calendar": write_canonical_parquet(
            calendar, tables / "team-championship-season-calendar.parquet",
            table_name="team_championship_season_calendar",
        ).as_record(),
        "hitter_ros": write_canonical_parquet(
            hitter_ros, tables / "hitter-rest-of-season-path.parquet",
            table_name="hitter_rest_of_season_path",
        ).as_record(),
        "pitcher_ros": write_canonical_parquet(
            pitcher_ros, tables / "pitcher-rest-of-season-path.parquet",
            table_name="pitcher_rest_of_season_path",
        ).as_record(),
        "whole_player_ros": write_canonical_parquet(
            whole_player, tables / "whole-player-rest-of-season-war.parquet",
            table_name="whole_player_rest_of_season_war",
        ).as_record(),
        "current_availability": write_canonical_parquet(
            availability,
            tables / "current-availability-status.parquet",
            table_name="current_availability_status",
        ).as_record(),
        "remaining_base_salary": write_canonical_parquet(
            salary, tables / "remaining-base-salary.parquet",
            table_name="remaining_base_salary",
        ).as_record(),
        "salary_rights_reconciliation": write_canonical_parquet(
            salary_reconciliation,
            tables / "salary-rights-reconciliation.parquet",
            table_name="salary_rights_reconciliation",
        ).as_record(),
        "remaining_rights_timeline": write_canonical_parquet(
            rights.timeline, tables / "remaining-rights-timeline.parquet",
            table_name="remaining_rights_timeline",
        ).as_record(),
        "remaining_contract_economics_inputs": write_canonical_parquet(
            rights.economics_inputs,
            tables / "remaining-contract-economics-inputs.parquet",
            table_name="remaining_contract_economics_inputs",
        ).as_record(),
        "current_and_future_contract_economics_inputs": write_canonical_parquet(
            combined_economics,
            tables / "current-and-future-contract-economics-inputs.parquet",
            table_name="current_and_future_contract_economics_inputs",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_2026_rest_of_season_baseline",
        "as_of_date": args.as_of_date.isoformat(),
        "schedule": {
            "completed_league_games": completed,
            "scheduled_league_games": scheduled,
            "remaining_fraction": (scheduled - completed) / scheduled,
            "capture": schedule_capture,
        },
        "coverage": {
            "hitter_rows": hitter_ros.height,
            "pitcher_rows": pitcher_ros.height,
            "whole_player_rows": whole_player.height,
            "resolved_organization_rows": whole_player.filter(
                pl.col("organization_id").is_not_null()
            ).height,
            "remaining_base_salary_rows": salary.height,
            "salary_rows_joined_to_remaining_rights": rights.timeline.height,
            "salary_rows_without_projection_or_current_team": (
                salary.height - rights.timeline.height
            ),
            "current_and_future_economics_rows": combined_economics.height,
            "availability_status": whole_player.group_by(
                "availability_category"
            ).len().sort("availability_category").to_dicts(),
            "salary_rights_join_status": {
                str(row["rights_join_status"]): int(row["len"])
                for row in salary_reconciliation.group_by(
                    "rights_join_status"
                ).len().iter_rows(named=True)
            },
        },
        "war_method": (
            "season-to-date opportunity pace shrunk to the 2027 unconditional "
            "opportunity prior; 2027 conditional rate used as a short-horizon proxy"
        ),
        "totals": {
            "projected_remaining_hitter_pa": hitter_ros.get_column(
                "projected_remaining_opportunity"
            ).sum(),
            "projected_remaining_pitcher_bf": pitcher_ros.get_column(
                "projected_remaining_opportunity"
            ).sum(),
            "projected_remaining_hitter_war": hitter_ros.get_column(
                "projected_remaining_war"
            ).sum(),
            "projected_remaining_pitcher_war": pitcher_ros.get_column(
                "projected_remaining_war"
            ).sum(),
            "projected_remaining_whole_player_war": whole_player.get_column(
                "projected_remaining_war_mean"
            ).sum(),
            "unadjusted_projected_remaining_whole_player_war": (
                whole_player.get_column(
                    "unadjusted_projected_remaining_war"
                ).sum()
            ),
            "availability_lower_whole_player_war": whole_player.get_column(
                "projected_remaining_war_lower"
            ).sum(),
            "availability_upper_whole_player_war": whole_player.get_column(
                "projected_remaining_war_upper"
            ).sum(),
            "remaining_base_salary_dollars": salary.get_column(
                "remaining_base_salary_dollars"
            ).sum(),
            "matched_remaining_base_salary_dollars": rights.timeline.get_column(
                "salary_obligation_dollars"
            ).sum(),
            "matched_rights_projected_war_mean": rights.timeline.get_column(
                "projected_remaining_war_mean"
            ).sum(),
            "matched_rights_availability_lower_war": rights.timeline.get_column(
                "projected_remaining_war_lower"
            ).sum(),
            "matched_rights_availability_upper_war": rights.timeline.get_column(
                "projected_remaining_war_upper"
            ).sum(),
        },
        "team_depth_used": False,
        "salary_method": (
            "accepted 2026 base salary multiplied by team championship-season days "
            "after the as-of date divided by total championship-season days"
        ),
        "rights_accounting": (
            "only projected WAR and unpaid base salary enter current rights value; "
            "realized WAR is unavailable, disclosed as null, and excluded"
        ),
        "availability_policy": (
            "official full-season unavailability sets remaining WAR to zero; "
            "ordinary injured-list status leaves the point unchanged and creates "
            "a zero-to-baseline sensitivity bound"
        ),
        "remaining_limitations": [
            "realized 2026 WAR to date is not reported",
            "special payment covenants and deferred compensation",
            "retained salary and transaction cash",
            "bonuses and players without an accepted 2026 payroll amount",
        ],
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "schedule": report["schedule"], "coverage": report["coverage"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
