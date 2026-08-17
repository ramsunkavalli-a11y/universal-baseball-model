#!/usr/bin/env python
"""Audit reusable MiLB terminal PA descriptions for Challenger-2 outcomes.

Exploratory source audit only. It does not score players and does not read 2023.
The historical armstjc release retains PA-level result descriptions even when its
per-pitch ``events`` field is blank. This audit asks whether the *terminal pitch*
of a physical, non-bunt PA can recover the frozen nine contact-value groups.

Only source semantics are being refined here. No 2022 model score or promotion
criterion is inspected.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.certification import download_file

YEARS = (2021, 2022)
LEVELS = ("aaa", "aa", "a+", "a", "rk")
CONTACT_CODES = frozenset({"D", "E", "X"})
REGULAR_GAME_TYPE = "R"

# Conservative PA-result phrases. These additions are direct lexical variants
# observed in the source audit, not model-performance-driven feature choices.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("HR", re.compile(r"\b(homers|home run|grand slam)\b", re.I)),
    ("3B", re.compile(r"\btriples\b", re.I)),
    ("2B", re.compile(r"\b(doubles|ground-rule double)\b", re.I)),
    ("1B", re.compile(r"\bsingles\b", re.I)),
    ("MULTI_OUT", re.compile(r"\b(double play|triple play)\b", re.I)),
    ("SF", re.compile(r"\bsacrifice fly\b", re.I)),
    ("ROE", re.compile(r"\breaches(?: first base)? on (?:a |an )?[^.]{0,60}\berror\b", re.I)),
    ("FC_REACH", re.compile(r"\b(?:grounds|flies|lines|pops)?\s*into a force out\b|\breaches(?: first base)? on (?:a )?fielder'?s choice\b", re.I)),
    ("OUT", re.compile(r"\b(grounds out|flies out|flyout|lines out|lineout|pops out|pop out|fouls out|foul out)\b", re.I)),
)

REQUIRED_COLUMNS = (
    "game_pk", "game_date", "game_type", "batter", "at_bat_number", "pitch_number",
    "type", "bb_type", "hit_location", "hc_x", "hc_y", "hit_distance_sc",
    "launch_speed", "launch_angle", "description", "des",
)


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-value-description-source/0.2"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _choose_asset(inventory: list[ArmstjcAsset], *, year: int, level: str) -> ArmstjcAsset:
    months = {6, 7, 8} if level == "rk" else {4, 5, 6, 7, 8, 9}
    eligible = [
        asset
        for asset in inventory
        if asset.year == year
        and asset.filename_level == level
        and asset.filename_period in months
    ]
    if not eligible:
        raise RuntimeError(f"no audit asset for {year} {level}")
    return min(eligible, key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id))


def _nonblank(name: str) -> pl.Expr:
    return pl.col(name).is_not_null() & (pl.col(name).cast(pl.String).str.strip_chars() != "")


def _contact_expr() -> pl.Expr:
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


def _classify(text: str) -> tuple[str | None, list[str]]:
    matches = [group for group, pattern in PATTERNS if pattern.search(text)]
    return (matches[0] if len(matches) == 1 else None), matches


def _audit(asset: ArmstjcAsset, root: Path) -> dict[str, Any]:
    path = root / asset.name
    meta = download_file(asset.browser_download_url, path, attempts=4, timeout_seconds=240)
    schema = pl.scan_csv(path, infer_schema_length=1000).collect_schema()
    missing = sorted(set(REQUIRED_COLUMNS) - set(schema.names()))
    if missing:
        return {"asset": asset.as_record(), "download": meta, "missing_required_columns": missing}

    frame = pl.read_csv(
        path,
        columns=list(REQUIRED_COLUMNS),
        infer_schema_length=10_000,
        null_values=[""],
        ignore_errors=False,
    ).with_columns(
        pl.col("game_pk").cast(pl.Int64, strict=False),
        pl.col("batter").cast(pl.Int64, strict=False),
        pl.col("at_bat_number").cast(pl.Int64, strict=False),
        pl.col("pitch_number").cast(pl.Int64, strict=False),
        pl.col("game_type").cast(pl.String),
    )
    regular = frame.filter(pl.col("game_type") == REGULAR_GAME_TYPE)

    # PA result descriptions are repeated across pitch rows. Restrict to exactly
    # the final pitch in each game/PA before asking whether that PA ended on
    # physical contact. Otherwise an earlier foul can inherit the later result.
    terminal = regular.with_columns(
        pl.col("pitch_number")
        .max()
        .over(["game_pk", "at_bat_number"])
        .alias("_terminal_pitch_number")
    ).filter(pl.col("pitch_number") == pl.col("_terminal_pitch_number"))

    duplicate_terminal_pa = (
        terminal.group_by(["game_pk", "at_bat_number"])
        .len()
        .filter(pl.col("len") > 1)
        .height
    )

    contacts = terminal.filter(_contact_expr()).with_columns(
        pl.coalesce([
            pl.when(_nonblank("des")).then(pl.col("des").cast(pl.String)).otherwise(None),
            pl.when(_nonblank("description")).then(pl.col("description").cast(pl.String)).otherwise(None),
        ]).alias("pa_description")
    )
    contacts = contacts.filter(
        ~pl.coalesce([pl.col("pa_description"), pl.lit("")])
        .str.to_lowercase()
        .str.contains(r"\bbunt\b")
    )

    rows: list[dict[str, Any]] = []
    for row in contacts.select(
        "game_pk", "batter", "at_bat_number", "pitch_number", "pa_description"
    ).to_dicts():
        text = str(row["pa_description"]).strip() if row["pa_description"] is not None else ""
        group, matches = _classify(text) if text else (None, [])
        rows.append({
            **row,
            "terminal_group": group,
            "pattern_matches": matches,
            "description_text": text,
        })

    total = len(rows)
    nonblank = sum(bool(row["description_text"]) for row in rows)
    classified = sum(row["terminal_group"] is not None for row in rows)
    ambiguous = sum(len(row["pattern_matches"]) > 1 for row in rows)
    group_counts: dict[str, int] = {}
    unmatched_counts: dict[str, int] = {}
    for row in rows:
        group = row["terminal_group"]
        if group is not None:
            group_counts[group] = group_counts.get(group, 0) + 1
        elif row["description_text"]:
            text = row["description_text"]
            unmatched_counts[text] = unmatched_counts.get(text, 0) + 1

    top_unmatched = sorted(unmatched_counts.items(), key=lambda item: (-item[1], item[0]))[:30]
    return {
        "asset": asset.as_record(),
        "download": meta,
        "missing_required_columns": [],
        "regular_row_count": int(regular.height),
        "terminal_pa_count": int(terminal.height),
        "duplicate_terminal_pa_count": int(duplicate_terminal_pa),
        "terminal_non_bunt_contact_count": total,
        "nonblank_pa_description_count": nonblank,
        "nonblank_pa_description_share": (nonblank / total if total else None),
        "classified_count": classified,
        "classified_share": (classified / total if total else None),
        "ambiguous_pattern_count": ambiguous,
        "group_counts": dict(sorted(group_counts.items())),
        "top_unmatched_descriptions": [
            {"description": text, "count": count} for text, count in top_unmatched
        ],
    }


def main() -> int:
    work = Path("data/quarantine/current-talent-contact-value-description-source")
    reports = Path("reports/generated/current-talent-contact-value-description-source")
    work.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [
        _choose_asset(inventory, year=year, level=level)
        for year in YEARS
        for level in LEVELS
    ]
    audited = [_audit(asset, work) for asset in assets]
    payload = {
        "report_schema_version": "0.2",
        "gate": "current_talent_contact_value_terminal_pa_description_source_exploration",
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "accepted": False,
        "note": "Exploratory terminal-pitch-only source audit; inspect residual unmatched narratives before freezing a parser.",
        "assets": audited,
    }
    (reports / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Current Talent terminal-PA description source exploration",
        "",
        "- Model scoring: **false**",
        "- 2023 accessed: **false**",
        "- Gate accepted: **false (exploratory)**",
        "",
    ]
    for report in audited:
        asset = report["asset"]
        lines += [
            f"## {asset['year']} {asset['filename_level']} — `{asset['name']}`",
            "",
            f"- Terminal PAs: {report.get('terminal_pa_count')}",
            f"- Duplicate terminal PA rows: {report.get('duplicate_terminal_pa_count')}",
            f"- Terminal non-bunt contacts: {report.get('terminal_non_bunt_contact_count')}",
            f"- Nonblank PA description: {report.get('nonblank_pa_description_count')} ({report.get('nonblank_pa_description_share')})",
            f"- Conservatively classified: {report.get('classified_count')} ({report.get('classified_share')})",
            f"- Ambiguous pattern matches: {report.get('ambiguous_pattern_count')}",
            f"- Group counts: `{report.get('group_counts', {})}`",
            f"- Top unmatched: `{report.get('top_unmatched_descriptions', [])[:8]}`",
            "",
        ]
    text = "\n".join(lines)
    (reports / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
