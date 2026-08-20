#!/usr/bin/env python
"""Audit the structural signature behind the one uncovered 2021 Rookie contact.

Diagnostic only. The target sequence is classified as contact today because the
raw source has ``type=X`` and ``hit_location=1`` even though it has no pitch,
no event code, no batted-ball geometry, and a caught-stealing narrative. This
script scans every 2021 Rookie PBP snapshot for the same evidence pattern before
any production eligibility rule is changed.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import requests

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.certification import download_file, read_quarantined_csv


SEASON = 2021
LEVEL = "rk"
TARGET_GAME_PK = 657792
TARGET_AT_BAT_NUMBER = 54
CONTACT_CODES = {"D", "E", "X"}
HIT_DATA_FIELDS = (
    "bb_type",
    "hc_x",
    "hc_y",
    "hit_distance_sc",
    "launch_speed",
    "launch_angle",
)


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-false-positive-audit/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _narrative_class(text: str) -> str:
    lowered = text.lower()
    patterns = (
        ("caught_stealing", "caught stealing"),
        ("pickoff", "pickoff"),
        ("stolen_base", "stole "),
        ("wild_pitch", "wild pitch"),
        ("passed_ball", "passed ball"),
        ("balk", "balk"),
        ("defensive_indifference", "defensive indifference"),
        ("runner_out", "runner out"),
        ("runner_advances", "advances"),
    )
    for label, needle in patterns:
        if needle in lowered:
            return label
    return "other"


def main() -> int:
    work_dir = Path("data/quarantine/current-talent-2021-rk-raw-sequence")
    report_dir = Path("reports/generated/current-talent-2021-rk-contact-sequence-diagnostic")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    session = _session()
    suspect_rows: list[dict[str, Any]] = []
    asset_counts: Counter[str] = Counter()
    try:
        assets = [
            asset
            for asset in fetch_pbp_asset_inventory(session=session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        if not assets:
            raise RuntimeError("no reusable 2021 Rookie PBP assets found")
        for asset in assets:
            path = work_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=300)
            raw = read_quarantined_csv(path)
            required = {
                "game_pk",
                "at_bat_number",
                "pitch_number",
                "type",
                "events",
                "description",
                "pitch_type",
                "hit_location",
                *HIT_DATA_FIELDS,
            }
            missing = sorted(required - set(raw.columns))
            if missing:
                raise RuntimeError(f"{asset.name} missing signature-audit fields: {missing}")

            for row in raw.select(sorted(required)).iter_rows(named=True):
                type_code = str(row.get("type") or "").strip().upper()
                hit_location_present = _present(row.get("hit_location"))
                current_trigger = type_code in CONTACT_CODES or hit_location_present or any(
                    _present(row.get(field)) for field in HIT_DATA_FIELDS
                )
                if not current_trigger:
                    continue
                no_event = not _present(row.get("events"))
                no_pitch_type = not _present(row.get("pitch_type"))
                no_hit_data = not any(_present(row.get(field)) for field in HIT_DATA_FIELDS)
                if not (no_event and no_pitch_type and no_hit_data):
                    continue

                description = str(row.get("description") or "").strip()
                record = {
                    "source_asset": asset.name,
                    "game_pk": _int(row.get("game_pk")),
                    "at_bat_number": _int(row.get("at_bat_number")),
                    "pitch_number": _int(row.get("pitch_number")),
                    "type": type_code or None,
                    "hit_location": row.get("hit_location"),
                    "events": row.get("events"),
                    "pitch_type": row.get("pitch_type"),
                    **{field: row.get(field) for field in HIT_DATA_FIELDS},
                    "description": description,
                    "narrative_class": _narrative_class(description),
                    "target_sequence": (
                        _int(row.get("game_pk")) == TARGET_GAME_PK
                        and _int(row.get("at_bat_number")) == TARGET_AT_BAT_NUMBER
                    ),
                    "trigger_type_code": type_code in CONTACT_CODES,
                    "trigger_hit_location": hit_location_present,
                }
                suspect_rows.append(record)
                asset_counts[asset.name] += 1
    finally:
        session.close()

    narrative_counts = Counter(row["narrative_class"] for row in suspect_rows)
    type_counts = Counter(str(row.get("type")) for row in suspect_rows)
    trigger_counts = Counter(
        (
            bool(row["trigger_type_code"]),
            bool(row["trigger_hit_location"]),
        )
        for row in suspect_rows
    )
    target_rows = [row for row in suspect_rows if row["target_sequence"]]
    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "level": LEVEL,
        "signature": {
            "current_contact_trigger_present": True,
            "events_blank": True,
            "pitch_type_blank": True,
            "all_hit_data_fields_blank": list(HIT_DATA_FIELDS),
            "note": (
                "hit_location is intentionally not treated as strong hit data in this audit because "
                "the target caught-stealing row uses hit_location=1 for the fielding play."
            ),
        },
        "suspect_row_count": len(suspect_rows),
        "unique_game_sequence_count": len(
            {
                (row["game_pk"], row["at_bat_number"], row["pitch_number"])
                for row in suspect_rows
            }
        ),
        "asset_counts": dict(sorted(asset_counts.items())),
        "narrative_class_counts": dict(sorted(narrative_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
        "trigger_counts": {
            f"type={key[0]},hit_location={key[1]}": value
            for key, value in sorted(trigger_counts.items())
        },
        "target_sequence_rows": target_rows,
        "all_suspect_rows": suspect_rows,
        "accepted": False,
        "interpretation": (
            "Diagnostic only. The signature is safe for a class-level source-quality exclusion only "
            "if its rows are demonstrated to be non-batted-ball events; narrative labels are evidence "
            "for audit, not themselves a production parser rule."
        ),
    }
    (report_dir / "contact_false_positive_signature_audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "suspect_row_count": len(suspect_rows),
                "narrative_class_counts": report["narrative_class_counts"],
                "type_counts": report["type_counts"],
                "trigger_counts": report["trigger_counts"],
                "target_sequence_rows": target_rows,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
