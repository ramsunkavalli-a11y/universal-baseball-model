#!/usr/bin/env python
"""Audit duplicate historical MiLB pitch rows through the existing resolver.

Source-feasibility only: no player scoring and no 2023 access.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.armstjc_contacts import (
    CONTACT_NATURAL_KEY,
    project_armstjc_contact_observations,
    resolve_armstjc_contact_observations,
)
from universal_baseball.certification import download_file

YEARS = (2021, 2022)
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-value-duplicate-audit/0.2"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _choose_asset(inventory: list[ArmstjcAsset], *, year: int, level: str) -> ArmstjcAsset:
    months = {6, 7, 8} if level == "rk" else {4, 5, 6, 7, 8, 9}
    eligible = [a for a in inventory if a.year == year and a.filename_level == level and a.filename_period in months]
    if not eligible:
        raise RuntimeError(f"no audit asset for {year} {level}")
    return min(eligible, key=lambda a: (a.size_bytes, a.filename_period, a.asset_id))


def _audit(asset: ArmstjcAsset, root: Path) -> dict[str, object]:
    path = root / asset.name
    meta = download_file(asset.browser_download_url, path, attempts=4, timeout_seconds=240)
    frame = pl.read_csv(path, infer_schema_length=10_000, null_values=[""], ignore_errors=False)

    # Some historical release snapshots predate the parser's league_id export.
    # league_id is not part of the natural physical-pitch key and this audit is
    # only asking whether repeated rows collapse or conflict. Preserve the
    # metadata as explicitly unknown rather than inventing a league identifier.
    if "league_id" not in frame.columns:
        frame = frame.with_columns(pl.lit(None, dtype=pl.Int64).alias("league_id"))

    observations = project_armstjc_contact_observations(
        frame,
        source_asset=asset.name,
        season=asset.year,
        game_type="R",
    )
    resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)

    raw_key_counts = observations.group_by(list(CONTACT_NATURAL_KEY)).len(name="raw_rows")
    duplicate_keys = raw_key_counts.filter(pl.col("raw_rows") > 1)
    duplicate_key_count = int(duplicate_keys.height)
    duplicate_raw_surplus = int((duplicate_keys.get_column("raw_rows") - 1).sum()) if duplicate_key_count else 0

    exact_duplicate_keys = resolved.filter(
        (pl.col("raw_source_row_count") > 1)
        & (pl.col("observation_variant_count") == 1)
    )
    variant_duplicate_keys = resolved.filter(
        (pl.col("raw_source_row_count") > 1)
        & (pl.col("observation_variant_count") > 1)
    )
    conflict_keys = resolved.filter(pl.col("conflict_field_count") > 0)
    contact_status_conflicts = conflict_keys.filter(
        pl.col("conflict_fields_json").str.contains("source_is_in_play", literal=True)
    )
    description_conflicts = conflict_keys.filter(
        pl.col("conflict_fields_json").str.contains("result_description", literal=True)
    )

    return {
        "asset": asset.as_record(),
        "download": meta,
        "league_id_present_in_raw": "league_id" in pl.scan_csv(path, infer_schema_length=1000).collect_schema().names(),
        "raw_observation_count": int(observations.height),
        "resolved_pitch_key_count": int(resolved.height),
        "duplicate_pitch_key_count": duplicate_key_count,
        "duplicate_raw_row_surplus": duplicate_raw_surplus,
        "exact_duplicate_pitch_key_count": int(exact_duplicate_keys.height),
        "variant_duplicate_pitch_key_count": int(variant_duplicate_keys.height),
        "conflicting_pitch_key_count": int(conflict_keys.height),
        "contact_status_conflict_count": int(contact_status_conflicts.height),
        "result_description_conflict_count": int(description_conflicts.height),
        "max_raw_rows_per_pitch_key": int(raw_key_counts.get_column("raw_rows").max() or 0),
        "max_observation_variants_per_pitch_key": int(resolved.get_column("observation_variant_count").max() or 0),
    }


def main() -> int:
    work = Path("data/quarantine/current-talent-contact-value-duplicate-resolution")
    reports = Path("reports/generated/current-talent-contact-value-duplicate-resolution")
    work.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [_choose_asset(inventory, year=year, level=level) for year in YEARS for level in LEVELS]
    audited = [_audit(asset, work) for asset in assets]
    payload = {
        "report_schema_version": "0.2",
        "gate": "current_talent_contact_value_duplicate_resolution_exploration",
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "accepted": False,
        "assets": audited,
    }
    (reports / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")

    lines = [
        "# Current Talent contact-value duplicate-resolution exploration",
        "",
        "- Model scoring: **false**",
        "- 2023 accessed: **false**",
        "- Gate accepted: **false (exploratory)**",
        "",
    ]
    for r in audited:
        a = r["asset"]
        lines += [
            f"## {a['year']} {a['filename_level']} — `{a['name']}`",
            "",
            f"- Raw league_id present: {r['league_id_present_in_raw']}",
            f"- Raw observations: {r['raw_observation_count']}",
            f"- Resolved pitch keys: {r['resolved_pitch_key_count']}",
            f"- Duplicate pitch keys: {r['duplicate_pitch_key_count']}",
            f"- Exact duplicate keys: {r['exact_duplicate_pitch_key_count']}",
            f"- Variant duplicate keys: {r['variant_duplicate_pitch_key_count']}",
            f"- Any field conflicts: {r['conflicting_pitch_key_count']}",
            f"- Contact-status conflicts: {r['contact_status_conflict_count']}",
            f"- Result-description conflicts: {r['result_description_conflict_count']}",
            f"- Max raw rows/key: {r['max_raw_rows_per_pitch_key']}",
            f"- Max variants/key: {r['max_observation_variants_per_pitch_key']}",
            "",
        ]
    text = "\n".join(lines)
    (reports / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
