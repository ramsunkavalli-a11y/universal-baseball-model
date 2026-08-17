#!/usr/bin/env python
"""Audit reusable MiLB PA result descriptions for Challenger-2 terminal groups.

Exploratory source audit only. It does not score players and does not read 2023.
The armstjc parser writes the PA-level result description to both ``description``
and ``des`` on exported pitch rows even when the exported ``events`` field is
blank. This audit measures whether those descriptions can deterministically
recover the frozen nine terminal contact-value groups.
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

# Deliberately conservative lexical proposal. Ambiguous/unmatched descriptions
# remain unclassified and are surfaced for inspection rather than guessed.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("HR", re.compile(r"\b(homers|home run)\b", re.I)),
    ("3B", re.compile(r"\btriples\b", re.I)),
    ("2B", re.compile(r"\bdoubles\b", re.I)),
    ("1B", re.compile(r"\bsingles\b", re.I)),
    ("MULTI_OUT", re.compile(r"\b(double play|triple play)\b", re.I)),
    ("SF", re.compile(r"\bsacrifice fly\b", re.I)),
    ("ROE", re.compile(r"\breaches(?: first base)? on (?:a |an )?(?:fielding |throwing )?error\b", re.I)),
    ("FC_REACH", re.compile(r"\breaches(?: first base)? on (?:a )?fielder'?s choice\b", re.I)),
    ("OUT", re.compile(r"\b(grounds out|flies out|flyout|lines out|lineout|pops out|pop out|fouls out|foul out)\b", re.I)),
)

REQUIRED_COLUMNS = (
    "game_pk", "game_date", "game_type", "batter", "at_bat_number", "pitch_number",
    "type", "bb_type", "hit_location", "hc_x", "hc_y", "hit_distance_sc",
    "launch_speed", "launch_angle", "description", "des",
)


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-value-description-source/0.1"
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


def _nonblank(name: str) -> pl.Expr:
    return pl.col(name).is_not_null() & (pl.col(name).cast(pl.String).str.strip_chars() != "")


def _contact_expr() -> pl.Expr:
    return (
        pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase().is_in(sorted(CONTACT_CODES))
        | _nonblank("bb_type") | _nonblank("hit_location") | _nonblank("hc_x") | _nonblank("hc_y")
        | _nonblank("hit_distance_sc") | _nonblank("launch_speed") | _nonblank("launch_angle")
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

    frame = pl.read_csv(path, columns=list(REQUIRED_COLUMNS), infer_schema_length=10000, null_values=[""], ignore_errors=False)
    regular = frame.filter(pl.col("game_type").cast(pl.String) == REGULAR_GAME_TYPE)
    contacts = regular.filter(_contact_expr()).with_columns(
        pl.coalesce([
            pl.when(_nonblank("des")).then(pl.col("des").cast(pl.String)).otherwise(None),
            pl.when(_nonblank("description")).then(pl.col("description").cast(pl.String)).otherwise(None),
        ]).alias("pa_description")
    )
    contacts = contacts.filter(
        ~pl.coalesce([pl.col("pa_description"), pl.lit("")]).str.to_lowercase().str.contains(r"\bbunt\b")
    )

    rows: list[dict[str, Any]] = []
    for row in contacts.select("game_pk", "batter", "at_bat_number", "pitch_number", "pa_description").to_dicts():
        text = str(row["pa_description"]).strip() if row["pa_description"] is not None else ""
        group, matches = _classify(text) if text else (None, [])
        rows.append({**row, "terminal_group": group, "pattern_matches": matches, "description_text": text})

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

    top_unmatched = sorted(unmatched_counts.items(), key=lambda x: (-x[1], x[0]))[:30]
    return {
        "asset": asset.as_record(),
        "download": meta,
        "missing_required_columns": [],
        "regular_row_count": int(regular.height),
        "contact_count": total,
        "nonblank_pa_description_count": nonblank,
        "nonblank_pa_description_share": (nonblank / total if total else None),
        "classified_count": classified,
        "classified_share": (classified / total if total else None),
        "ambiguous_pattern_count": ambiguous,
        "group_counts": dict(sorted(group_counts.items())),
        "top_unmatched_descriptions": [{"description": text, "count": count} for text, count in top_unmatched],
    }


def main() -> int:
    work = Path("data/quarantine/current-talent-contact-value-description-source")
    reports = Path("reports/generated/current-talent-contact-value-description-source")
    work.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [_choose_asset(inventory, year=year, level=level) for year in YEARS for level in LEVELS]
    audited = [_audit(asset, work) for asset in assets]
    payload = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_pa_description_source_exploration",
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "accepted": False,
        "note": "Exploratory only; inspect coverage and unmatched narratives before freezing any parser.",
        "assets": audited,
    }
    (reports / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    lines = ["# Current Talent contact-value PA-description source exploration", "", "- Model scoring: **false**", "- 2023 accessed: **false**", "- Gate accepted: **false (exploratory)**", ""]
    for r in audited:
        a = r["asset"]
        lines += [
            f"## {a['year']} {a['filename_level']} — `{a['name']}`", "",
            f"- Contacts: {r.get('contact_count')}",
            f"- Nonblank PA description: {r.get('nonblank_pa_description_count')} ({r.get('nonblank_pa_description_share')})",
            f"- Conservatively classified: {r.get('classified_count')} ({r.get('classified_share')})",
            f"- Ambiguous pattern matches: {r.get('ambiguous_pattern_count')}",
            f"- Group counts: `{r.get('group_counts', {})}`",
            f"- Top unmatched: `{r.get('top_unmatched_descriptions', [])[:8]}`", "",
        ]
    text = "\n".join(lines)
    (reports / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
