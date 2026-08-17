#!/usr/bin/env python
"""Audit armstjc historical MiLB PBP for Challenger-2 terminal contact outcomes.

This is a source-feasibility audit only. It downloads one bandwidth-minimized
regular-season-capable asset for each 2021/2022 affiliated level, verifies that
result-producing physical contacts retain the structured ``events`` field, and
reports the observed event vocabulary against the frozen nine-group contact-
value proposal. It performs no player scoring and reads no 2023 data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.certification import download_file
from universal_baseball.event_types import KNOWN_EVENT_TYPES


YEARS = (2021, 2022)
LEVELS = ("aaa", "aa", "a+", "a", "rk")
REGULAR_GAME_TYPE = "R"
CONTACT_CODES = frozenset({"D", "E", "X"})

# This mapping is a source-audit proposal, not a promoted model contract. Any
# observed result-producing event outside it fails the feasibility gate and must
# be investigated before the event builder is implemented.
PROPOSED_EVENT_TO_GROUP = {
    "single": "1B",
    "double": "2B",
    "triple": "3B",
    "home_run": "HR",
    "field_error": "ROE",
    "fielders_choice": "FC_REACH",
    "force_out": "FC_REACH",
    "sac_fly": "SF",
    "double_play": "MULTI_OUT",
    "grounded_into_double_play": "MULTI_OUT",
    "triple_play": "MULTI_OUT",
    "grounded_into_triple_play": "MULTI_OUT",
    "sac_fly_double_play": "MULTI_OUT",
    "field_out": "OUT",
    "fielders_choice_out": "OUT",
}

REQUIRED_COLUMNS = (
    "game_pk",
    "game_date",
    "game_type",
    "batter",
    "at_bat_number",
    "pitch_number",
    "events",
    "type",
    "bb_type",
    "hit_location",
    "hc_x",
    "hc_y",
    "hit_distance_sc",
    "launch_speed",
    "launch_angle",
    "description",
    "des",
)


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-value-event-source/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _choose_asset(candidates: list[ArmstjcAsset], *, year: int, level: str) -> ArmstjcAsset:
    # Restrict to normal playing-season months. Rookie ball generally begins
    # later, so June-September is the comparable window there.
    months = {6, 7, 8, 9} if level == "rk" else {4, 5, 6, 7, 8, 9}
    eligible = [
        asset
        for asset in candidates
        if asset.year == year
        and asset.filename_level == level
        and asset.filename_period in months
    ]
    if not eligible:
        raise RuntimeError(f"no reusable PBP audit asset found for {year} {level}")
    return min(eligible, key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id))


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (pl.col(column).cast(pl.String).str.strip_chars() != "")


def _contact_evidence_expr() -> pl.Expr:
    return (
        pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase().is_in(sorted(CONTACT_CODES))
        | _nonblank("bb_type")
        | _nonblank("hit_location")
        | _nonblank("hc_x")
        | _nonblank("hc_y")
        | _nonblank("hit_distance_sc")
        | _nonblank("launch_speed")
        | _nonblank("launch_angle")
    )


def _event_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {}
    return {
        str(row["events"]): int(row["len"])
        for row in frame.group_by("events").len().sort("events").to_dicts()
    }


def _audit_asset(asset: ArmstjcAsset, *, root: Path) -> dict[str, Any]:
    path = root / asset.name
    download = download_file(asset.browser_download_url, path, attempts=4, timeout_seconds=240)
    schema = pl.scan_csv(path, infer_schema_length=1000).collect_schema()
    missing = sorted(set(REQUIRED_COLUMNS) - set(schema.names()))
    if missing:
        return {
            "asset": asset.as_record(),
            "download": download,
            "missing_required_columns": missing,
            "accepted": False,
        }

    frame = pl.read_csv(
        path,
        columns=list(REQUIRED_COLUMNS),
        infer_schema_length=10_000,
        null_values=[""],
        ignore_errors=False,
    ).with_columns(
        pl.col("game_type").cast(pl.String),
        pl.col("events").cast(pl.String),
        pl.col("type").cast(pl.String),
        pl.col("description").cast(pl.String),
        pl.col("des").cast(pl.String),
    )
    regular = frame.filter(pl.col("game_type") == REGULAR_GAME_TYPE)
    if regular.is_empty():
        return {
            "asset": asset.as_record(),
            "download": download,
            "missing_required_columns": [],
            "regular_row_count": 0,
            "accepted": False,
            "failure": "selected asset contains no regular-season rows",
        }

    contacts = regular.filter(_contact_evidence_expr())
    # Mirror the frozen model's non-bunt result-producing contact semantics for
    # source feasibility. Both source description spellings are checked because
    # the historical release carries both on many rows.
    bunt = (
        pl.coalesce([pl.col("description"), pl.lit("")])
        .cast(pl.String)
        .str.to_lowercase()
        .str.contains(r"\bbunt\b")
        | pl.coalesce([pl.col("des"), pl.lit("")])
        .cast(pl.String)
        .str.to_lowercase()
        .str.contains(r"\bbunt\b")
    )
    result_contacts = contacts.filter(_nonblank("events") & ~bunt).with_columns(
        pl.col("events").str.strip_chars().str.to_lowercase().alias("events")
    )
    blank_event_contacts = contacts.filter(~_nonblank("events") & ~bunt)

    unknown_mlb_events = sorted(
        event
        for event in result_contacts.get_column("events").unique().drop_nulls().to_list()
        if event not in KNOWN_EVENT_TYPES
    )
    unsupported_mapping = sorted(
        event
        for event in result_contacts.get_column("events").unique().drop_nulls().to_list()
        if event not in PROPOSED_EVENT_TO_GROUP
    )
    group_counts: dict[str, int] = {}
    for event, count in _event_counts(result_contacts).items():
        group = PROPOSED_EVENT_TO_GROUP.get(event)
        if group is not None:
            group_counts[group] = group_counts.get(group, 0) + count

    result_key = ["game_pk", "batter", "at_bat_number", "pitch_number"]
    duplicate_result_keys = (
        result_contacts.group_by(result_key).len().filter(pl.col("len") > 1).height
        if not result_contacts.is_empty()
        else 0
    )
    multi_result_pa = (
        result_contacts.group_by(["game_pk", "batter", "at_bat_number"])
        .len()
        .filter(pl.col("len") > 1)
        .height
        if not result_contacts.is_empty()
        else 0
    )

    return {
        "asset": asset.as_record(),
        "download": download,
        "missing_required_columns": [],
        "regular_row_count": regular.height,
        "regular_game_count": regular.get_column("game_pk").n_unique(),
        "physical_contact_evidence_count": contacts.height,
        "non_bunt_result_contact_count": result_contacts.height,
        "non_bunt_contact_with_blank_events_count": blank_event_contacts.height,
        "event_counts": _event_counts(result_contacts),
        "proposed_group_counts": dict(sorted(group_counts.items())),
        "unknown_current_mlb_event_types": unknown_mlb_events,
        "unsupported_proposed_mapping_event_types": unsupported_mapping,
        "duplicate_result_pitch_key_count": duplicate_result_keys,
        "multiple_result_contact_same_player_pa_count": multi_result_pa,
        "accepted": (
            result_contacts.height > 0
            and not unknown_mlb_events
            and not unsupported_mapping
            and duplicate_result_keys == 0
            and multi_result_pa == 0
        ),
    }


def main() -> int:
    work_root = Path("data/quarantine/current-talent-contact-value-event-source")
    report_root = Path("reports/generated/current-talent-contact-value-event-source")
    work_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    selected = [
        _choose_asset(inventory, year=year, level=level)
        for year in YEARS
        for level in LEVELS
    ]
    reports = [_audit_asset(asset, root=work_root) for asset in selected]
    accepted = all(bool(report.get("accepted")) for report in reports)
    payload = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_reusable_terminal_event_source",
        "years": list(YEARS),
        "levels": list(LEVELS),
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "source_semantics": "armstjc_structured_play_event_details_eventType_on_physical_pitch_v1",
        "proposed_event_to_group": PROPOSED_EVENT_TO_GROUP,
        "assets": reports,
        "accepted": accepted,
    }
    (report_root / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Current Talent contact-value reusable terminal-event source audit",
        "",
        f"- Accepted: **{accepted}**",
        "- Model scoring performed: **false**",
        "- 2023 accessed: **false**",
        "",
    ]
    for report in reports:
        asset = report["asset"]
        lines.extend(
            [
                f"## {asset['year']} {asset['filename_level']} — `{asset['name']}`",
                "",
                f"- Accepted: {report.get('accepted', False)}",
                f"- Regular rows: {report.get('regular_row_count')}",
                f"- Physical contact evidence: {report.get('physical_contact_evidence_count')}",
                f"- Non-bunt result contacts: {report.get('non_bunt_result_contact_count')}",
                f"- Blank `events` among non-bunt physical contacts: {report.get('non_bunt_contact_with_blank_events_count')}",
                f"- Event counts: `{report.get('event_counts', {})}`",
                f"- Proposed groups: `{report.get('proposed_group_counts', {})}`",
                f"- Unknown current MLB event types: `{report.get('unknown_current_mlb_event_types', [])}`",
                f"- Unsupported proposed mapping: `{report.get('unsupported_proposed_mapping_event_types', [])}`",
                f"- Duplicate result pitch keys: {report.get('duplicate_result_pitch_key_count')}",
                f"- Multiple result contacts in same player PA: {report.get('multiple_result_contact_same_player_pa_count')}",
                "",
            ]
        )
    (report_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
