#!/usr/bin/env python3
"""Inventory raw official fielding statistics across certified 2021-2024 captures.

Source inventory only: this script does not score defensive skill or choose a
Defense v1 fallback/model.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from typing import Any, Mapping


SEASONS = {2021, 2022, 2023, 2024}
LEVEL_BY_LEAGUE = {
    103: "MLB",
    104: "MLB",
    112: "AAA",
    117: "AAA",
    109: "AA",
    111: "AA",
    113: "AA",
    116: "HIGH_A",
    118: "HIGH_A",
    126: "HIGH_A",
    110: "SINGLE_A",
    122: "SINGLE_A",
    123: "SINGLE_A",
    121: "ROOKIE_COMPLEX",
    124: "ROOKIE_COMPLEX",
    130: "ROOKIE_COMPLEX",
}
EXPECTED_PAIRS = {(season, league_id) for season in SEASONS for league_id in LEVEL_BY_LEAGUE}
REPORT_ROOT = Path("reports/generated/defense-universal-fielding-source-audit")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonblank(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _numeric(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False
    if not isinstance(value, str):
        return False
    text = value.strip().replace(",", "")
    if not text:
        return False
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return math.isfinite(float(text))
    except ValueError:
        return False


def _infer_context(path: Path) -> tuple[int, int]:
    """Infer season/league from retained quarantine path, robust to artifact prefix."""
    parts = list(path.parts)
    for index, part in enumerate(parts[:-1]):
        try:
            season = int(part)
        except ValueError:
            continue
        if season not in SEASONS or index + 1 >= len(parts):
            continue
        try:
            league_id = int(parts[index + 1])
        except ValueError:
            continue
        if league_id in LEVEL_BY_LEAGUE:
            return season, league_id
    raise RuntimeError(f"cannot infer season/league from capture path: {path}")


def _field_record() -> dict[str, Any]:
    return {
        "rows_key_exists": 0,
        "nonblank_count": 0,
        "numeric_parseable_count": 0,
        "pairs": set(),
        "levels": set(),
        "positions": set(),
        "seasons": set(),
        "leagues": set(),
        "value_types": defaultdict(int),
    }


def _value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Mapping):
        return "mapping"
    if isinstance(value, list):
        return "list"
    return type(value).__name__


def _update_record(
    record: dict[str, Any],
    *,
    value: Any,
    season: int,
    league_id: int,
    position: str,
) -> None:
    record["rows_key_exists"] += 1
    if _nonblank(value):
        record["nonblank_count"] += 1
    if _numeric(value):
        record["numeric_parseable_count"] += 1
    record["pairs"].add((season, league_id))
    record["levels"].add(LEVEL_BY_LEAGUE[league_id])
    record["positions"].add(position or "UNKNOWN")
    record["seasons"].add(season)
    record["leagues"].add(league_id)
    record["value_types"][_value_type(value)] += 1


def _finalize_field(key: str, record: dict[str, Any], *, catcher: bool) -> dict[str, Any]:
    exists = int(record["rows_key_exists"])
    nonblank = int(record["nonblank_count"])
    numeric = int(record["numeric_parseable_count"])
    pair_count = len(record["pairs"])
    completeness = float(nonblank / exists) if exists else 0.0
    numeric_rate = float(numeric / nonblank) if nonblank else 0.0
    candidate = bool(pair_count == len(EXPECTED_PAIRS) and completeness >= 0.95)
    return {
        "stat_key": key,
        "rows_key_exists": exists,
        "nonblank_count": nonblank,
        "nonblank_rate_where_defined": completeness,
        "numeric_parseable_count": numeric,
        "numeric_parseable_rate_among_nonblank": numeric_rate,
        "season_league_pair_count": pair_count,
        "seasons": sorted(record["seasons"]),
        "league_ids": sorted(record["leagues"]),
        "level_groups": sorted(record["levels"]),
        "positions": sorted(record["positions"]),
        "value_types": dict(sorted(record["value_types"].items())),
        ("broad_catcher_source_candidate" if catcher else "broad_universal_source_candidate"): candidate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()

    capture_paths = sorted(args.source_root.rglob("fielding_offset_*.json"))
    if not capture_paths:
        raise RuntimeError(f"no retained fielding capture pages found under {args.source_root}")

    fields: dict[str, dict[str, Any]] = defaultdict(_field_record)
    catcher_fields: dict[str, dict[str, Any]] = defaultdict(_field_record)
    observed_pairs: set[tuple[int, int]] = set()
    pair_page_counts: dict[tuple[int, int], int] = defaultdict(int)
    pair_split_counts: dict[tuple[int, int], int] = defaultdict(int)
    total_splits = 0
    catcher_splits = 0

    for path in capture_paths:
        season, league_id = _infer_context(path)
        pair = (season, league_id)
        observed_pairs.add(pair)
        pair_page_counts[pair] += 1

        payload = json.loads(path.read_text(encoding="utf-8"))
        groups = payload.get("stats") or []
        if len(groups) != 1 or not isinstance(groups[0], Mapping):
            raise RuntimeError(f"expected one Stats API stats group in {path}, observed={len(groups)}")
        splits = groups[0].get("splits") or []
        if not isinstance(splits, list):
            raise RuntimeError(f"invalid splits payload in {path}")

        for split in splits:
            if not isinstance(split, Mapping):
                raise RuntimeError(f"non-mapping split in {path}")
            stat = _mapping(split.get("stat"))
            position = str(_mapping(split.get("position")).get("abbreviation") or "").strip()
            total_splits += 1
            pair_split_counts[pair] += 1
            is_catcher = position == "C"
            if is_catcher:
                catcher_splits += 1
            for key, value in stat.items():
                _update_record(
                    fields[str(key)],
                    value=value,
                    season=season,
                    league_id=league_id,
                    position=position,
                )
                if is_catcher:
                    _update_record(
                        catcher_fields[str(key)],
                        value=value,
                        season=season,
                        league_id=league_id,
                        position=position,
                    )

    missing_pairs = sorted(EXPECTED_PAIRS - observed_pairs)
    unexpected_pairs = sorted(observed_pairs - EXPECTED_PAIRS)
    if missing_pairs or unexpected_pairs:
        raise RuntimeError(
            "certified raw fielding capture pair mismatch: "
            f"missing={missing_pairs}, unexpected={unexpected_pairs}"
        )

    general_rows = sorted(
        (_finalize_field(key, record, catcher=False) for key, record in fields.items()),
        key=lambda row: (-row["season_league_pair_count"], row["stat_key"]),
    )
    catcher_rows = sorted(
        (_finalize_field(key, record, catcher=True) for key, record in catcher_fields.items()),
        key=lambda row: (-row["season_league_pair_count"], row["stat_key"]),
    )
    general_candidates = [
        row["stat_key"] for row in general_rows if row["broad_universal_source_candidate"]
    ]
    catcher_candidates = [
        row["stat_key"] for row in catcher_rows if row["broad_catcher_source_candidate"]
    ]

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_universal_official_fielding_source_audit",
        "contract": "docs/defense-universal-fielding-source-audit-contract.md",
        "source": {
            "historical_source_run_id": 32148467330,
            "artifact_name": "position-role-historical-source-2021-2024",
            "seasons": sorted(SEASONS),
            "expected_season_league_pair_count": len(EXPECTED_PAIRS),
            "observed_season_league_pair_count": len(observed_pairs),
            "fielding_capture_page_count": len(capture_paths),
            "fielding_split_count": total_splits,
            "catcher_split_count": catcher_splits,
            "pair_page_counts": [
                {
                    "season": season,
                    "league_id": league_id,
                    "level_group": LEVEL_BY_LEAGUE[league_id],
                    "page_count": pair_page_counts[(season, league_id)],
                    "split_count": pair_split_counts[(season, league_id)],
                }
                for season, league_id in sorted(observed_pairs)
            ],
        },
        "general_fielding_stat_keys": general_rows,
        "catcher_fielding_stat_keys": catcher_rows,
        "decision": {
            "general_broad_source_candidate_keys": general_candidates,
            "catcher_broad_source_candidate_keys": catcher_candidates,
            "predictive_defensive_signal_established": False,
            "tier_c_defense_fallback_frozen": False,
            "defense_projection_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "source_refetched": False,
            "defensive_skill_model_fit": False,
            "traditional_fielding_stat_weight_selected": False,
            "untracked_player_defense_imputed": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Universal official fielding source audit",
        "",
        f"- certified season x league pairs: {len(observed_pairs)}/{len(EXPECTED_PAIRS)}",
        f"- raw fielding capture pages: {len(capture_paths):,}",
        f"- raw fielding splits: {total_splits:,}",
        f"- catcher splits: {catcher_splits:,}",
        f"- distinct general stat keys: {len(general_rows)}",
        f"- broad general source candidates: {len(general_candidates)}",
        f"- distinct catcher stat keys: {len(catcher_rows)}",
        f"- broad catcher source candidates: {len(catcher_candidates)}",
        "",
        "## Broad general source candidates",
    ]
    lines.extend(f"- `{key}`" for key in general_candidates) or lines.append("- none")
    lines.extend(["", "## Broad catcher source candidates"])
    lines.extend(f"- `{key}`" for key in catcher_candidates) or lines.append("- none")
    lines.extend(
        [
            "",
            "- Predictive defensive signal established: False",
            "- Tier-C fallback frozen: False",
            "- WAR/value authorized: False",
            "",
        ]
    )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
