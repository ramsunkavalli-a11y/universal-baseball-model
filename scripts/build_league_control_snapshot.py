#!/usr/bin/env python
"""Build the dated league control, payroll, future-path and Super Two tables."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re

import polars as pl

from universal_baseball.chadwick import (
    build_fangraphs_mlbam_crosswalk,
    read_chadwick_people_archive,
)
from universal_baseball.contract_overlay import build_contract_overlay
from universal_baseball.contract_terms import (
    normalize_fangraphs_payroll,
    read_fangraphs_payroll_xlsx,
)
from universal_baseball.control_baseline import build_control_baselines
from universal_baseball.control_events import (
    classify_control_transactions,
    materialize_control_stints,
)
from universal_baseball.control_path import project_future_control_path
from universal_baseball.control_season_source import fetch_season_windows
from universal_baseball.control_validation import (
    confirm_name_matches_with_current_roster_entries,
    match_control_reference_players,
)
from universal_baseball.depth_chart_reference import (
    normalize_fangraphs_depth_chart,
    read_fangraphs_depth_chart_xlsx,
)
from universal_baseball.people_control_source import fetch_people_control_evidence
from universal_baseball.playing_time_roster_source import (
    fetch_mlb_teams,
    fetch_team_40man_membership_as_of,
    fetch_team_full_roster_candidates_as_of,
)
from universal_baseball.roster_entry_source import build_opening_control_states
from universal_baseball.team_control import (
    CONTROL_PLAYER_SCHEMA,
    SERVICE_DAYS_PER_YEAR,
    build_super_two_pool,
    build_team_control_summary,
    calculate_control_years,
)


TEAM_IDS = {
    "Angels": 108, "Astros": 117, "Athletics": 133, "Blue Jays": 141,
    "Braves": 144, "Brewers": 158, "Cardinals": 138, "Cubs": 112,
    "Diamondbacks": 109, "Dodgers": 119, "Giants": 137, "Guardians": 114,
    "Mariners": 136, "Marlins": 146, "Mets": 121, "Nationals": 120,
    "Orioles": 110, "Padres": 135, "Phillies": 143, "Pirates": 134,
    "Rangers": 140, "Rays": 139, "Red Sox": 111, "Reds": 113,
    "Rockies": 115, "Royals": 118, "Tigers": 116, "Twins": 142,
    "White Sox": 145, "Yankees": 147,
}
ACCEPTED_BASELINES = {
    "accepted_stable_identity",
    "accepted_official_roster_confirmed_identity",
    "accepted_stable_identity_outside_expected_team",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth-chart-dir", type=Path, required=True)
    parser.add_argument("--payroll-dir", type=Path, required=True)
    parser.add_argument("--chadwick-archive", type=Path, required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--through-year", type=int, default=2032)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _depth_file_team(path: Path) -> str:
    match = re.fullmatch(r"\d{4}-(.+)-Depth-Charts(?:\(\d+\))?", path.stem)
    if match is None:
        raise ValueError(f"unexpected depth-chart filename: {path.name}")
    return match.group(1)


def _payroll_file_team(path: Path) -> str:
    match = re.fullmatch(r"(.+)-Payroll-\d{4}(?:\(\d+\))?", path.stem)
    if match is None:
        raise ValueError(f"unexpected payroll filename: {path.name}")
    return match.group(1)


def _consolidate_baselines(baselines: pl.DataFrame) -> pl.DataFrame:
    rows = []
    accepted = baselines.filter(pl.col("baseline_status").is_in(sorted(ACCEPTED_BASELINES)))
    for group in accepted.partition_by("player_id", maintain_order=True):
        player_id = int(group.item(0, "player_id"))
        service = sorted(set(group.get_column("service_days").drop_nulls().to_list()))
        options = sorted(set(group.get_column("options_remaining").drop_nulls().to_list()))
        conflicts = []
        if len(service) > 1:
            conflicts.append("service_conflict")
        if len(options) > 1:
            conflicts.append("options_conflict")
        rows.append(
            {
                "player_id": player_id,
                "baseline_service_days": service[0] if len(service) == 1 else None,
                "baseline_options_remaining": options[0] if len(options) == 1 else None,
                "baseline_status": "review_" + ",".join(conflicts) if conflicts else "available",
                "baseline_source_snapshot_ids": ",".join(
                    sorted(set(group.get_column("source_snapshot_id").to_list()))
                ),
            }
        )
    return pl.DataFrame(
        rows,
        schema={
            "player_id": pl.Int64,
            "baseline_service_days": pl.Int64,
            "baseline_options_remaining": pl.Int64,
            "baseline_status": pl.String,
            "baseline_source_snapshot_ids": pl.String,
        },
    ).sort("player_id")


def main() -> int:
    args = parse_args()
    if set(TEAM_IDS) != {_depth_file_team(path) for path in args.depth_chart_dir.glob("*.xlsx")}:
        raise ValueError("depth-chart directory must contain exactly the 30 expected teams")
    if set(TEAM_IDS) != {_payroll_file_team(path) for path in args.payroll_dir.glob("*.xlsx")}:
        raise ValueError("payroll directory must contain exactly the 30 expected teams")

    official_teams, _ = fetch_mlb_teams(args.as_of.year)
    mlb_team_ids = set(official_teams.get_column("team_id").to_list())
    window, _ = fetch_season_windows([args.as_of.year])
    baseline_date = window.item(0, "start_date") - timedelta(days=1)
    roster_by_team = {}
    roster_frames = []
    forty_frames = []
    for team_name, team_id in TEAM_IDS.items():
        roster, _ = fetch_team_full_roster_candidates_as_of(
            team_id, season=args.as_of.year, as_of_date=args.as_of
        )
        forty, _ = fetch_team_40man_membership_as_of(
            team_id, season=args.as_of.year, as_of_date=args.as_of
        )
        roster_by_team[team_name] = roster
        roster_frames.append(roster)
        forty_frames.append(forty)
    rosters = pl.concat(roster_frames, how="vertical_relaxed")
    forty = pl.concat(forty_frames, how="vertical_relaxed")
    candidate_ids = rosters.get_column("player_id").unique().sort()
    people = fetch_people_control_evidence(
        candidate_ids, as_of_date=args.as_of, batch_size=50
    )

    register = read_chadwick_people_archive(args.chadwick_archive)
    baseline_frames = []
    payroll_players = []
    payroll_years = []
    payroll_payments = []
    identity_rows = []
    service_reference_total = 0
    service_reference_resolved = 0

    for path in sorted(args.depth_chart_dir.glob("*.xlsx")):
        team_name = _depth_file_team(path)
        source_id = f"fangraphs:depth:{args.as_of}:{team_name}:{_hash(path)}"
        references = normalize_fangraphs_depth_chart(
            read_fangraphs_depth_chart_xlsx(path),
            team_name=team_name,
            season=args.as_of.year,
            source_snapshot_id=source_id,
        )
        crosswalk = build_fangraphs_mlbam_crosswalk(
            register, references.get_column("fangraphs_id").to_list()
        )
        matches = match_control_reference_players(
            references, roster_by_team[team_name], crosswalk
        )
        matches = confirm_name_matches_with_current_roster_entries(
            matches,
            people.roster_entries,
            expected_team_id=TEAM_IDS[team_name],
            as_of_date=args.as_of,
        )
        identity_rows.append(
            matches.with_columns(
                pl.lit(team_name).alias("reference_team_name"),
                pl.lit(TEAM_IDS[team_name]).alias("reference_team_id"),
                pl.lit("depth_chart").alias("reference_type"),
            )
        )
        # A 0.000 reference carries no prior MLB service into the Super Two pool.
        # Unresolved zero-service minor leaguers therefore do not make that pool incomplete.
        service_references = references.filter(
            ~pl.col("reference_service_time").is_in(["", "0.000"])
        )
        service_reference_total += service_references.height
        service_reference_resolved += (
            service_references.join(
                matches.select("fangraphs_id", "reference_player_name", "match_status"),
                left_on=["fangraphs_id", "player_name"],
                right_on=["fangraphs_id", "reference_player_name"],
                how="left",
            )
            .filter(
                pl.col("match_status").is_in(
                    [
                        "matched_stable_id",
                        "stable_id_outside_statsapi_candidates",
                        "matched_official_roster_confirmed_name",
                    ]
                )
            )
            .height
        )
        baseline_frames.append(
            build_control_baselines(
                references, matches, baseline_as_of_date=baseline_date
            )
        )

    for path in sorted(args.payroll_dir.glob("*.xlsx")):
        team_name = _payroll_file_team(path)
        source_id = f"fangraphs:payroll:{args.as_of}:{team_name}:{_hash(path)}"
        payroll = normalize_fangraphs_payroll(
            read_fangraphs_payroll_xlsx(path),
            team_name=team_name,
            season=args.as_of.year,
            source_snapshot_id=source_id,
        )
        crosswalk = build_fangraphs_mlbam_crosswalk(
            register, payroll.players.get_column("fangraphs_id").to_list()
        )
        matches = match_control_reference_players(
            payroll.players.select("fangraphs_id", "player_name"),
            roster_by_team[team_name],
            crosswalk,
        )
        matches = confirm_name_matches_with_current_roster_entries(
            matches,
            people.roster_entries,
            expected_team_id=TEAM_IDS[team_name],
            as_of_date=args.as_of,
        )
        identity_rows.append(
            matches.with_columns(
                pl.lit(team_name).alias("reference_team_name"),
                pl.lit(TEAM_IDS[team_name]).alias("reference_team_id"),
                pl.lit("payroll").alias("reference_type"),
            )
        )
        overlay = build_contract_overlay(payroll, matches)
        payroll_players.append(overlay.players)
        payroll_years.append(overlay.year_terms)
        payroll_payments.append(payroll.other_payments)

    baselines = _consolidate_baselines(pl.concat(baseline_frames, how="vertical_relaxed"))
    identities = pl.concat(identity_rows, how="vertical_relaxed")
    contract_players = pl.concat(payroll_players, how="vertical_relaxed").with_columns(
        pl.col("team_name").replace_strict(TEAM_IDS).cast(pl.Int64).alias("organization_id")
    )
    contract_years = pl.concat(payroll_years, how="vertical_relaxed").with_columns(
        pl.col("team_name").replace_strict(TEAM_IDS).cast(pl.Int64).alias("organization_id")
    )
    other_payments = pl.concat(payroll_payments, how="vertical_relaxed").with_columns(
        pl.col("team_name").replace_strict(TEAM_IDS).cast(pl.Int64).alias("organization_id")
    )

    organizations = (
        rosters.group_by("player_id")
        .agg(
            pl.col("player_name").first(),
            pl.col("candidate_organization_id").n_unique().alias("organization_count"),
            pl.col("candidate_organization_id").unique().sort().alias("organization_ids"),
        )
        .with_columns(
            pl.when(pl.col("organization_count") == 1)
            .then(pl.col("organization_ids").list.first())
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("organization_id"),
            pl.when(pl.col("organization_count") == 1)
            .then(pl.lit("provisional_unique_full_roster"))
            .otherwise(pl.lit("review_multiple_full_roster_organizations"))
            .alias("organization_status"),
        )
        .drop("organization_ids")
    )
    on_40man = forty.select("player_id").unique().with_columns(pl.lit(True).alias("on_40man"))

    openings = build_opening_control_states(
        people.roster_entries, window, mlb_team_ids=mlb_team_ids
    )
    events = classify_control_transactions(
        people.transactions, mlb_team_ids=mlb_team_ids
    ).filter(pl.col("season") == args.as_of.year)
    materialized = materialize_control_stints(
        openings.opening_states, events, window, as_of_date=args.as_of
    )
    current_years = calculate_control_years(
        materialized.stints, window, as_of_date=args.as_of
    ).select(
        "player_id",
        pl.col("service_days").alias("current_service_days"),
        pl.col("option_year_used").alias("current_option_year_used"),
    )

    rule5_players = (
        people.people.select(
            "player_id", "player_name", "birth_date", "first_pro_contract_date", "source_snapshot_id"
        )
        .join(on_40man, on="player_id", how="left")
        .with_columns(
            pl.col("on_40man").fill_null(False),
            pl.lit(0, dtype=pl.Int64).alias("service_days_before_window"),
            pl.lit(0, dtype=pl.Int64).alias("option_years_used_before_window"),
            pl.lit(0, dtype=pl.Int64).alias("full_pro_seasons_before_window"),
            pl.lit(False).alias("history_complete"),
            pl.col("source_snapshot_id").alias("source_snapshot_ids"),
        )
        .select(list(CONTROL_PLAYER_SCHEMA))
        .cast(CONTROL_PLAYER_SCHEMA, strict=True)
    )
    empty_years = calculate_control_years(
        materialized.stints.head(0), window, as_of_date=args.as_of
    )
    rule5 = build_team_control_summary(
        rule5_players, empty_years, as_of_date=args.as_of
    ).select("player_id", "rule5_eligibility_year", "rule5_status")

    unified = (
        organizations.join(on_40man, on="player_id", how="left")
        .join(baselines, on="player_id", how="left")
        .join(current_years, on="player_id", how="left")
        .join(rule5, on="player_id", how="left")
        .with_columns(
            pl.col("on_40man").fill_null(False),
            pl.col("current_service_days").fill_null(0),
            pl.col("current_option_year_used").fill_null(False),
            pl.when(pl.col("baseline_service_days").is_not_null())
            .then(pl.col("baseline_service_days") + pl.col("current_service_days"))
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("service_days"),
            pl.when(pl.col("baseline_options_remaining").is_not_null())
            .then(
                pl.max_horizontal(
                    pl.col("baseline_options_remaining")
                    - pl.col("current_option_year_used").cast(pl.Int64),
                    pl.lit(0),
                )
            )
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("options_remaining"),
            pl.lit(args.as_of).cast(pl.Date).alias("as_of_date"),
        )
    ).with_columns(
            pl.when(pl.col("service_days").is_not_null())
            .then(
                (pl.col("service_days") // SERVICE_DAYS_PER_YEAR).cast(pl.String)
                + pl.lit(".")
                + (pl.col("service_days") % SERVICE_DAYS_PER_YEAR)
                .cast(pl.String)
                .str.pad_start(3, "0")
            )
            .otherwise(pl.lit(""))
            .alias("service_time"),
    )

    baseline_conflicts = baselines.filter(pl.col("baseline_status") != "available").height
    service_reference_unresolved = service_reference_total - service_reference_resolved
    pool_complete = (
        baseline_conflicts == 0
        and service_reference_total > 0
        and service_reference_unresolved == 0
    )
    super_two = build_super_two_pool(
        unified.filter(pl.col("service_days").is_not_null()).select(
            "player_id", "service_days", "current_service_days"
        ),
        as_of_date=args.as_of,
        pool_complete=pool_complete,
    )
    unified = unified.join(
        super_two.select("player_id", pl.col("selected").alias("super_two_selected")),
        on="player_id",
        how="left",
    ).with_columns(pl.col("super_two_selected").fill_null(False))

    current_contracts = contract_players.filter(
        pl.col("overlay_status") == "accepted_contract_overlay"
    ).select(
        "player_id", "organization_id", "contract_text", "aav_dollars"
    )
    unified = unified.join(
        current_contracts,
        on=["player_id", "organization_id"],
        how="left",
    )
    path_terms = contract_years.filter(
        pl.col("overlay_status") == "accepted_contract_overlay"
    ).select(
        "player_id",
        "organization_id",
        "payroll_year",
        "amount_dollars",
        "term_label",
        "clause_types",
    )
    future = project_future_control_path(
        unified.select(
            "player_id",
            "organization_id",
            "service_days",
            "current_service_days",
            "super_two_selected",
        ),
        path_terms,
        as_of_date=args.as_of,
        through_year=args.through_year,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    unified.write_parquet(args.output_dir / "league-control-snapshot.parquet")
    future.write_parquet(args.output_dir / "future-control-path.parquet")
    contract_years.write_parquet(args.output_dir / "contract-year-liabilities.parquet")
    other_payments.write_parquet(args.output_dir / "payroll-other-payments.parquet")
    identities.write_parquet(args.output_dir / "identity-audit.parquet")
    super_two.write_parquet(args.output_dir / "super-two-pool.parquet")
    summary = {
        "as_of_date": args.as_of.isoformat(),
        "players": unified.height,
        "unique_organization_players": unified.filter(pl.col("organization_id").is_not_null()).height,
        "multiple_organization_reviews": unified.filter(pl.col("organization_id").is_null()).height,
        "service_baselines": unified.filter(pl.col("baseline_service_days").is_not_null()).height,
        "baseline_as_of_date": baseline_date.isoformat(),
        "baseline_conflicts": baseline_conflicts,
        "service_references": service_reference_total,
        "service_references_resolved": service_reference_resolved,
        "service_references_unresolved": service_reference_unresolved,
        "payroll_players": contract_players.height,
        "payroll_identity_reviews": contract_players.filter(
            pl.col("overlay_status") != "accepted_contract_overlay"
        ).height,
        "future_path_rows": future.height,
        "super_two_pool_players": super_two.height,
        "super_two_selected": super_two.filter(pl.col("selected")).height,
        "super_two_cutoff_days": super_two.item(0, "cutoff_days") if super_two.height else None,
        "super_two_cutoff_tie": super_two.item(0, "cutoff_tie") if super_two.height else None,
        "opening_state_reviews": openings.review_players.height,
        "transaction_reviews": materialized.review_events.height,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
