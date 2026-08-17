#!/usr/bin/env python
"""Materialize source-only 2021/2022 MiLB target contacts for Challenger 2.

This gate deliberately reuses the existing historical Current Talent source
loader rather than rebuilding public-source cleanup.  It stops before terminal
values, baseline fitting, richer residual fitting, or any model scoring.

For one season/level slice it:

1. reuses player-game controls and unique same-game actual-league authority;
2. reuses the historical physical-contact resolver and participant overlay;
3. reuses the frozen shared contact-profile classifier;
4. projects exactly one terminal pitch/result description per PA from the same
   downloaded reusable PBP assets;
5. applies the source-reconciled nine-group terminal narrative contract; and
6. materializes exact terminal physical contacts eligible for the frozen target.

Only 2021 and 2022 are permitted.  No 2023 evidence is read and no player/model
performance is calculated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

import materialize_current_talent_historical_milb_game_evidence as historical
from universal_baseball.certification import read_quarantined_csv
from universal_baseball.current_talent_contact_value_materialization import (
    materialize_contact_value_target_contacts,
)
from universal_baseball.current_talent_contact_value_source import (
    SUPPORTED_TERMINAL_GROUPS,
    attach_narrative_terminal_groups,
    project_terminal_pa_descriptions,
)
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_milb_source import (
    classify_milb_current_talent_contacts,
    validate_expected_actual_leagues,
)
from universal_baseball.storage import write_canonical_parquet


ALLOWED_SEASONS = (2021, 2022)
LEVELS = historical.LEVELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, choices=ALLOWED_SEASONS, required=True)
    parser.add_argument("--level", choices=LEVELS, required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-contact-value-source-materialization"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-source-materialization"),
    )
    return parser.parse_args()


def _count_table(frame: pl.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    if frame.is_empty():
        return []
    return frame.group_by(columns).len(name="event_count").sort(columns).to_dicts()


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def main() -> int:
    args = parse_args()
    if args.season not in ALLOWED_SEASONS:
        raise RuntimeError("contact-value source materialization is restricted to 2021/2022")

    spec = current_talent_level_spec(args.season, args.level)
    slug = args.level.replace("+", "plus")
    work_dir = args.work_root / str(args.season) / slug
    report_dir = args.report_root / str(args.season) / slug
    table_dir = report_dir / "tables"
    for path in (work_dir, report_dir, table_dir):
        path.mkdir(parents=True, exist_ok=True)

    session = historical._github_session()
    try:
        game_league_map, controls, _source_outcomes, player_game_metrics = (
            historical._load_player_game_sources(
                season=args.season,
                level=args.level,
                league_ids=spec.league_ids,
                work_dir=work_dir,
                session=session,
            )
        )
        contacts, contact_metrics = historical._load_contacts(
            season=args.season,
            level=args.level,
            league_ids=spec.league_ids,
            game_league_map=game_league_map,
            work_dir=work_dir,
            session=session,
        )
    finally:
        session.close()

    authorized_contacts, participant_metrics = historical._apply_participant_authority(
        contacts,
        controls,
    )
    classified_contacts = classify_milb_current_talent_contacts(authorized_contacts)
    classified_coverage = validate_expected_actual_leagues(
        classified_contacts,
        league_column="league_id",
        expected_league_ids=spec.league_ids,
        label=f"{args.season} {args.level} classified contact-value source contacts",
    )

    raw_pbp_frames = [
        read_quarantined_csv(work_dir / "pbp" / str(asset_name))
        for asset_name in contact_metrics["asset_names"]
    ]
    if not raw_pbp_frames:
        raise RuntimeError(f"{args.season} {args.level} has no downloaded PBP source frames")
    raw_pbp = pl.concat(raw_pbp_frames, how="diagonal_relaxed")
    terminal_pas = attach_narrative_terminal_groups(
        project_terminal_pa_descriptions(raw_pbp, game_type=historical.GAME_TYPE)
    )

    targets, target_metrics = materialize_contact_value_target_contacts(
        authorized_contacts,
        classified_contacts,
        terminal_pas,
    )
    if targets.is_empty():
        raise RuntimeError(f"{args.season} {args.level} produced zero supported target contacts")

    target_seasons = set(targets.get_column("event_date").dt.year().unique().to_list())
    if target_seasons != {int(args.season)}:
        raise RuntimeError(
            f"{args.season} {args.level} target contacts span wrong seasons: {sorted(target_seasons)}"
        )
    unknown_groups = sorted(
        set(targets.get_column("terminal_outcome_group").unique().to_list())
        - set(SUPPORTED_TERMINAL_GROUPS)
    )
    if unknown_groups:
        raise RuntimeError(f"materialized target contains unsupported groups: {unknown_groups}")

    # Source-coverage diagnostics at the exact terminal core-contact grain.  These
    # rows are diagnostics only; unsupported/special/ambiguous outcomes remain
    # outside the frozen target rather than being guessed into a group.
    terminal_diag = (
        classified_contacts.select(
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "league_id",
            "batter_mlbam_id",
            "core_profile_eligible",
            "core_bin",
        )
        .join(
            terminal_pas.select(
                "game_pk",
                "at_bat_index",
                "terminal_pitch_number",
                "pa_description",
                "terminal_outcome_group",
                "terminal_outcome_status",
            ),
            on=["game_pk", "at_bat_index"],
            how="left",
            validate="m:1",
        )
        .filter(
            pl.col("core_profile_eligible")
            & (pl.col("pitch_number") == pl.col("terminal_pitch_number"))
        )
    )
    if terminal_diag.height != target_metrics["core_terminal_contact_count"]:
        raise RuntimeError("terminal core-contact diagnostic count disagrees with materializer")

    supported_diag = terminal_diag.filter(
        pl.col("terminal_outcome_group").is_in(sorted(SUPPORTED_TERMINAL_GROUPS))
    )
    if supported_diag.height != targets.height:
        raise RuntimeError("supported terminal diagnostic count disagrees with target table")

    unsupported_diag = terminal_diag.filter(
        ~pl.col("terminal_outcome_group")
        .is_in(sorted(SUPPORTED_TERMINAL_GROUPS))
        .fill_null(False)
    )
    ambiguous_count = int(
        unsupported_diag.filter(pl.col("terminal_outcome_status") == "ambiguous_narrative_groups").height
    )

    target_storage = write_canonical_parquet(
        targets,
        table_dir / f"contact_value_target_contacts_{args.season}_{slug}.parquet",
        table_name=f"contact_value_target_contacts_{args.season}_{slug}",
    ).as_record()
    terminal_pas.write_parquet(table_dir / f"terminal_pas_{args.season}_{slug}.parquet")

    status_table = (
        terminal_diag.group_by(["terminal_outcome_status", "terminal_outcome_group"])
        .len(name="event_count")
        .sort(["terminal_outcome_status", "terminal_outcome_group"])
    )
    status_table.write_csv(report_dir / "terminal_core_contact_outcome_coverage.csv")
    targets.group_by("terminal_outcome_group").len(name="event_count").sort(
        "terminal_outcome_group"
    ).write_csv(report_dir / "target_by_terminal_group.csv")
    targets.group_by("contact_bin").len(name="event_count").sort("contact_bin").write_csv(
        report_dir / "target_by_contact_bin.csv"
    )
    targets.group_by(["league_id", "level_group"]).len(name="event_count").sort(
        ["league_id", "level_group"]
    ).write_csv(report_dir / "target_by_actual_league.csv")
    targets.group_by("participant_authority").len(name="event_count").sort(
        "participant_authority"
    ).write_csv(report_dir / "target_by_participant_authority.csv")
    if not unsupported_diag.is_empty():
        unsupported_diag.select(
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "league_id",
            "batter_mlbam_id",
            "core_bin",
            "pa_description",
            "terminal_outcome_status",
        ).head(200).write_csv(report_dir / "unsupported_terminal_core_contact_sample.csv")

    event_min = targets.get_column("event_date").min()
    event_max = targets.get_column("event_date").max()
    supported_rate = targets.height / terminal_diag.height if terminal_diag.height else None
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_source_materialization",
        "season": int(args.season),
        "filename_level": args.level,
        "level_group": spec.level_group,
        "actual_league_ids": sorted(int(value) for value in spec.league_ids),
        "boundaries": {
            "model_scoring": False,
            "accessed_2023": False,
            "terminal_values_attached": False,
            "baseline_fitted": False,
            "richer_residual_fitted": False,
        },
        "player_game_source": player_game_metrics,
        "contact_source": contact_metrics,
        "participant_authority": participant_metrics,
        "classified_contact_league_coverage": classified_coverage,
        "terminal_pa_source": {
            "raw_pbp_asset_count": len(raw_pbp_frames),
            "terminal_pa_count": int(terminal_pas.height),
            "terminal_outcome_status_counts": _count_table(
                terminal_pas, ["terminal_outcome_status"]
            ),
        },
        "target_materialization": {
            **target_metrics,
            "supported_target_rate_among_core_terminal_contacts": supported_rate,
            "ambiguous_terminal_core_contact_count": ambiguous_count,
            "terminal_core_contact_outcome_counts": status_table.to_dicts(),
            "event_date_min": _date_text(event_min),
            "event_date_max": _date_text(event_max),
            "player_count": int(targets.get_column("player_id").n_unique()),
            "game_count": int(targets.get_column("game_pk").n_unique()),
            "actual_league_count": int(targets.get_column("league_id").n_unique()),
            "terminal_group_counts": _count_table(targets, ["terminal_outcome_group"]),
            "contact_bin_counts": _count_table(targets, ["contact_bin"]),
            "actual_league_counts": _count_table(targets, ["league_id", "level_group"]),
            "participant_authority_counts": _count_table(targets, ["participant_authority"]),
        },
        "storage": {"target_contacts": target_storage},
        "accepted_source_materialization": True,
        "requires_coverage_review_before_model_scoring": True,
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
