#!/usr/bin/env python3
"""Independently audit the frozen Defense v1 Tier-B tracked-range cohort.

This is a diagnostic only. It does not score, refit, retune, or modify any
Defense-v1 model component. It reconstructs the 2023 MiLB -> 2024 MLB OAA
transfer eligibility path and records where candidate rows are lost.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import polars as pl

from develop_defense_v1_universal import (
    _fit_general_normalizer,
    _general_matrix,
    _general_targets,
    _load_profiles,
)


GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}
TRANSFER_INPUT_YEAR = 2023
TRANSFER_TARGET_YEAR = 2024
TRANSFER_LEVELS = {"AAA", "TRACKED_NON_AAA"}


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} under {root}, observed={matches}")
    return matches[0]


def _person_names(player_ids: list[int]) -> dict[int, str]:
    """Best-effort MLB Stats API name lookup; diagnostic must not depend on it."""
    if not player_ids:
        return {}
    names: dict[int, str] = {}
    for start in range(0, len(player_ids), 100):
        batch = player_ids[start : start + 100]
        query = urlencode({"personIds": ",".join(str(v) for v in batch)})
        request = Request(
            f"https://statsapi.mlb.com/api/v1/people?{query}",
            headers={"User-Agent": "universal-baseball-model-defense-tier-b-audit/0.1"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
            for person in payload.get("people") or []:
                if person.get("id") is not None:
                    names[int(person["id"])] = str(person.get("fullName") or "")
        except Exception as exc:  # noqa: BLE001 - names are non-binding decoration
            print(f"warning: name lookup failed for batch starting {start}: {exc}")
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--tracked-root", type=Path, required=True)
    parser.add_argument("--binding-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    binding = json.loads(args.binding_result.read_text(encoding="utf-8"))
    binding_transfer = binding["general_tracked_range"]["tier_b_transfer"]
    if binding["general_tracked_range"]["tier_a_gate"]["passed"] is not True:
        raise RuntimeError("binding result does not have Tier-A range pass")
    if binding_transfer["attempted"] is not True:
        raise RuntimeError("binding result says Tier-B transfer was not attempted")

    profiles, profile_diag = _load_profiles(args.source_root)
    targets = _general_targets()

    # Recreate the exact 2024 U1 held-set universe without calling the frozen
    # scorer's _range_subset transfer function.
    normalizer = _fit_general_normalizer(profiles, {2021, 2022})
    _, _, meta = _general_matrix(profiles, targets, {TRANSFER_TARGET_YEAR}, normalizer, "U1")
    profile_index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in profiles.iter_rows(named=True)
    }

    range_path = _find_one(args.tracked_root, "tracked_range_proxy_2021_2023.parquet")
    tracked = pl.read_parquet(range_path)
    raw_milb = tracked.filter(
        (pl.col("season") == TRANSFER_INPUT_YEAR)
        & pl.col("level_group").is_in(sorted(TRANSFER_LEVELS))
        & pl.col("position_abbreviation").is_in(sorted(GENERAL_POSITIONS))
    )
    eligible = raw_milb.filter(
        (pl.col("opportunities") >= 100)
        & pl.col("tracked_oaa_per_100").is_not_null()
    )
    moments = eligible.group_by(["level_group", "position_abbreviation"]).agg(
        pl.col("tracked_oaa_per_100").mean().alias("mean"),
        pl.col("tracked_oaa_per_100").std(ddof=0).alias("sd"),
        pl.len().alias("n"),
    )
    scored = (
        eligible.join(moments, on=["level_group", "position_abbreviation"], how="left")
        .filter((pl.col("n") >= 20) & pl.col("sd").is_not_null() & (pl.col("sd") > 1e-12))
        .with_columns(((pl.col("tracked_oaa_per_100") - pl.col("mean")) / pl.col("sd")).alias("tracked_z"))
    )

    raw_any = {(int(r["player_id"]), str(r["position_abbreviation"])) for r in raw_milb.iter_rows(named=True)}
    raw_players = {pid for pid, _ in raw_any}
    eligible_exact = {(int(r["player_id"]), str(r["position_abbreviation"])) for r in eligible.iter_rows(named=True)}
    scored_exact = {
        (int(r["player_id"]), str(r["position_abbreviation"]))
        for r in scored.iter_rows(named=True)
        if r["tracked_z"] is not None and math.isfinite(float(r["tracked_z"]))
    }

    rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    for item in meta:
        player_id = int(item["player_id"])
        profile = profile_index[(TRANSFER_INPUT_YEAR, player_id)]
        position = str(profile["position"])
        level = str(profile["current_level_group"])
        exact = (player_id, position)

        has_raw_player = player_id in raw_players
        has_raw_exact = exact in raw_any
        has_eligible_exact = exact in eligible_exact
        has_scored_exact = exact in scored_exact

        if level == "MLB":
            reason = "excluded_already_mlb_2023"
        elif not has_raw_player:
            reason = "non_mlb_no_tracked_milb_row"
        elif not has_raw_exact:
            reason = "non_mlb_tracked_only_other_position"
        elif not has_eligible_exact:
            reason = "non_mlb_exact_position_below_raw_eligibility"
        elif not has_scored_exact:
            reason = "non_mlb_exact_position_z_cell_ineligible"
        else:
            reason = "qualifies_transfer"
        reason_counts[reason] += 1
        rows.append(
            {
                "player_id": player_id,
                "position": position,
                "current_level_group_2023": level,
                "has_raw_tracked_milb_any_position": has_raw_player,
                "has_raw_tracked_milb_exact_position": has_raw_exact,
                "has_eligible_tracked_milb_exact_position": has_eligible_exact,
                "has_scored_tracked_milb_exact_position": has_scored_exact,
                "disposition": reason,
            }
        )

    ids = sorted({row["player_id"] for row in rows})
    names = _person_names(ids)
    for row in rows:
        row["player_name"] = names.get(row["player_id"])

    non_mlb_rows = [row for row in rows if row["current_level_group_2023"] != "MLB"]
    counts = {
        "u1_eligible_2023_with_matching_2024_mlb_oaa_target": len(rows),
        "of_those_non_mlb_in_2023": len(non_mlb_rows),
        "non_mlb_with_any_raw_2023_tracked_milb_row": sum(r["has_raw_tracked_milb_any_position"] for r in non_mlb_rows),
        "non_mlb_with_raw_2023_tracked_milb_at_exact_u1_position": sum(r["has_raw_tracked_milb_exact_position"] for r in non_mlb_rows),
        "non_mlb_with_raw_eligible_exact_position_opportunities_ge_100": sum(r["has_eligible_tracked_milb_exact_position"] for r in non_mlb_rows),
        "non_mlb_with_scored_tracked_z_exact_position": sum(r["has_scored_tracked_milb_exact_position"] for r in non_mlb_rows),
        "qualifying_transfer_players": reason_counts["qualifies_transfer"],
    }

    cell_diagnostics = []
    for row in moments.sort(["level_group", "position_abbreviation"]).iter_rows(named=True):
        n = int(row["n"])
        sd = None if row["sd"] is None else float(row["sd"])
        cell_diagnostics.append(
            {
                "level_group": str(row["level_group"]),
                "position": str(row["position_abbreviation"]),
                "eligible_player_count": n,
                "sd": sd,
                "z_cell_eligible": bool(n >= 20 and sd is not None and sd > 1e-12),
            }
        )

    report = {
        "report_schema_version": "0.1",
        "audit": "defense_v1_tier_b_tracked_range_cohort",
        "diagnostic_only": True,
        "input_year": TRANSFER_INPUT_YEAR,
        "target_year": TRANSFER_TARGET_YEAR,
        "binding_scoring_run_id": binding.get("scoring_run_id"),
        "binding_scoring_sha": binding.get("scoring_sha"),
        "binding_transfer_player_count": int(binding_transfer["player_count"]),
        "binding_transfer_status": binding_transfer["status"],
        "independent_reproduction_matches_binding_count": int(binding_transfer["player_count"]) == counts["qualifying_transfer_players"],
        "counts": counts,
        "disposition_counts": dict(sorted(reason_counts.items())),
        "tracked_z_cell_diagnostics": cell_diagnostics,
        "candidate_rows": sorted(rows, key=lambda r: (r["disposition"], r["player_id"])),
        "source_profile_diagnostics": profile_diag,
        "boundary": {
            "2025_defensive_targets_accessed": False,
            "model_scoring_performed": False,
            "model_parameters_modified": False,
            "war_value_performed": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"counts": counts, "disposition_counts": report["disposition_counts"]}, indent=2))

    if not report["independent_reproduction_matches_binding_count"]:
        raise RuntimeError(
            "independent Tier-B cohort count does not match binding scorer: "
            f"audit={counts['qualifying_transfer_players']} binding={binding_transfer['player_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
