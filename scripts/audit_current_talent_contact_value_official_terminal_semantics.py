#!/usr/bin/env python
"""Reconcile historical MiLB terminal descriptions to official PA event types.

Source-semantics gate only.  This script deliberately performs no player scoring,
no residual fitting, and no 2023 access.  It uses a deterministic sample from
representative 2021-22 affiliated PBP release assets and joins the historical
terminal PA by ``game_pk + atBatIndex`` to the repo's existing MLB Stats API
projection.

The primary unresolved question is whether the reusable narrative phrase
``force out`` can safely inherit the frozen structured ``force_out -> OUT``
contract.  Explicit fielder's-choice and ordinary field-out narratives are
included as positive controls.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.certification import download_file
from universal_baseball.current_talent_contact_value_source import (
    attach_narrative_terminal_groups,
    project_terminal_pa_descriptions,
    terminal_group_from_structured_event_type,
)
from universal_baseball.official import fetch_official_game_evidence

YEARS = (2021, 2022)
LEVELS = ("aaa", "aa", "a+", "a", "rk")
FORCE_OUT_SAMPLE_PER_SLICE = 20
CONTROL_SAMPLE_PER_SLICE = 8
MIN_TOTAL_OFFICIAL_MATCHES = 180
MIN_OFFICIAL_MATCH_SHARE = 0.98


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-contact-value-terminal-semantics/0.1"
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
        raise RuntimeError(f"no terminal-semantics audit asset for {year} {level}")
    return min(
        eligible,
        key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id),
    )


def _stable_sample(frame: pl.DataFrame, count: int) -> list[dict[str, Any]]:
    ranked: list[tuple[str, dict[str, Any]]] = []
    for row in frame.iter_rows(named=True):
        key = f"{int(row['game_pk'])}:{int(row['at_bat_index'])}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        ranked.append((digest, row))
    ranked.sort(key=lambda item: (item[0], int(item[1]["game_pk"]), int(item[1]["at_bat_index"])))
    return [row for _, row in ranked[:count]]


def _audit_asset(asset: ArmstjcAsset, work: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = work / asset.name
    download = download_file(asset.browser_download_url, path, attempts=4, timeout_seconds=240)
    raw = pl.read_csv(path, infer_schema_length=10_000, null_values=[""], ignore_errors=False)
    terminal = attach_narrative_terminal_groups(project_terminal_pa_descriptions(raw))

    force = terminal.filter(pl.col("terminal_outcome_status") == "unresolved_force_out_description")
    fielder_choice = terminal.filter(
        (pl.col("terminal_outcome_group") == "FC_REACH")
        & (pl.col("terminal_outcome_status") == "supported_narrative_fallback")
    )
    ordinary_out = terminal.filter(
        (pl.col("terminal_outcome_group") == "OUT")
        & (pl.col("terminal_outcome_status") == "supported_narrative_fallback")
    )

    selected: list[dict[str, Any]] = []
    for category, frame, limit, expected_group in (
        ("force_out_phrase", force, FORCE_OUT_SAMPLE_PER_SLICE, "OUT"),
        ("explicit_fielder_choice", fielder_choice, CONTROL_SAMPLE_PER_SLICE, "FC_REACH"),
        ("ordinary_field_out", ordinary_out, CONTROL_SAMPLE_PER_SLICE, "OUT"),
    ):
        for row in _stable_sample(frame, limit):
            selected.append(
                {
                    "season": int(asset.year),
                    "filename_level": str(asset.filename_level),
                    "source_asset": str(asset.name),
                    "category": category,
                    "expected_group": expected_group,
                    "game_pk": int(row["game_pk"]),
                    "at_bat_index": int(row["at_bat_index"]),
                    "pa_description": row.get("pa_description"),
                }
            )

    return selected, {
        "asset": asset.as_record(),
        "download": download,
        "terminal_pa_count": int(terminal.height),
        "force_out_phrase_count": int(force.height),
        "explicit_fielder_choice_count": int(fielder_choice.height),
        "ordinary_field_out_count": int(ordinary_out.height),
        "selected_count": len(selected),
    }


def main() -> int:
    work = Path("data/quarantine/current-talent-contact-value-official-terminal-semantics")
    reports = Path("reports/generated/current-talent-contact-value-official-terminal-semantics")
    work.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [
        _choose_asset(inventory, year=year, level=level)
        for year in YEARS
        for level in LEVELS
    ]

    selected: list[dict[str, Any]] = []
    asset_reports: list[dict[str, Any]] = []
    for asset in assets:
        rows, report = _audit_asset(asset, work)
        selected.extend(rows)
        asset_reports.append(report)

    game_ids = sorted({int(row["game_pk"]) for row in selected})
    official_pa, _ = fetch_official_game_evidence(game_ids)
    official = official_pa.select(
        pl.col("game_pk").cast(pl.Int64, strict=False),
        pl.col("at_bat_number").cast(pl.Int64, strict=False).alias("at_bat_index"),
        pl.col("event_type").cast(pl.String).alias("official_event_type"),
        pl.col("description").cast(pl.String).alias("official_description"),
    ).drop_nulls(["game_pk", "at_bat_index"])
    duplicates = official.group_by(["game_pk", "at_bat_index"]).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError("official PA projection is not unique by game_pk + at_bat_index")

    sample = pl.DataFrame(selected).join(
        official,
        on=["game_pk", "at_bat_index"],
        how="left",
        validate="m:1",
    )

    rows: list[dict[str, Any]] = []
    event_type_counts: dict[str, Counter[str]] = defaultdict(Counter)
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    category_matched: Counter[str] = Counter()
    category_agree: Counter[str] = Counter()
    for row in sample.iter_rows(named=True):
        event_type = row.get("official_event_type")
        official_group = terminal_group_from_structured_event_type(event_type)
        matched = event_type is not None
        agrees = matched and official_group == row["expected_group"]
        category = str(row["category"])
        if matched:
            category_matched[category] += 1
            event_type_counts[category][str(event_type)] += 1
            group_counts[category][str(official_group)] += 1
            if agrees:
                category_agree[category] += 1
        rows.append(
            {
                **row,
                "official_terminal_group": official_group,
                "official_match": matched,
                "expected_group_agreement": bool(agrees),
            }
        )

    total_selected = len(rows)
    total_matched = sum(category_matched.values())
    total_agree = sum(category_agree.values())
    match_share = total_matched / total_selected if total_selected else 0.0
    agreement_share = total_agree / total_matched if total_matched else 0.0
    force_matched = category_matched["force_out_phrase"]
    force_agree = category_agree["force_out_phrase"]
    force_agreement_share = force_agree / force_matched if force_matched else 0.0

    accepted = (
        total_matched >= MIN_TOTAL_OFFICIAL_MATCHES
        and match_share >= MIN_OFFICIAL_MATCH_SHARE
        and agreement_share == 1.0
        and force_matched > 0
        and force_agreement_share == 1.0
    )

    payload = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_official_terminal_semantics",
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "years": list(YEARS),
        "levels": list(LEVELS),
        "force_out_sample_per_slice": FORCE_OUT_SAMPLE_PER_SLICE,
        "control_sample_per_slice": CONTROL_SAMPLE_PER_SLICE,
        "selected_pa_count": total_selected,
        "official_matched_pa_count": total_matched,
        "official_match_share": match_share,
        "expected_group_agreement_count": total_agree,
        "expected_group_agreement_share": agreement_share,
        "force_out_official_match_count": force_matched,
        "force_out_expected_out_count": force_agree,
        "force_out_expected_out_share": force_agreement_share,
        "category_official_event_type_counts": {
            category: dict(sorted(counts.items()))
            for category, counts in sorted(event_type_counts.items())
        },
        "category_official_group_counts": {
            category: dict(sorted(counts.items()))
            for category, counts in sorted(group_counts.items())
        },
        "accepted": accepted,
        "acceptance_contract": {
            "minimum_official_matches": MIN_TOTAL_OFFICIAL_MATCHES,
            "minimum_official_match_share": MIN_OFFICIAL_MATCH_SHARE,
            "all_matched_controls_and_force_out_must_agree_with_frozen_group": True,
            "force_out_phrase_must_map_exclusively_to_OUT": True,
        },
        "assets": asset_reports,
        "sample_rows": rows,
    }
    (reports / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Current Talent contact-value official terminal semantics",
        "",
        "- Model scoring: **false**",
        "- 2023 accessed: **false**",
        f"- Selected PAs: **{total_selected}**",
        f"- Official matches: **{total_matched} ({match_share:.4%})**",
        f"- Frozen-group agreement: **{total_agree}/{total_matched} ({agreement_share:.4%})**",
        f"- Force-out phrase -> OUT: **{force_agree}/{force_matched} ({force_agreement_share:.4%})**",
        f"- Gate accepted: **{str(accepted).lower()}**",
        "",
        "## Official event types by narrative category",
        "",
    ]
    for category, counts in sorted(event_type_counts.items()):
        lines.append(f"- `{category}`: `{dict(sorted(counts.items()))}`")
    text = "\n".join(lines) + "\n"
    (reports / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
