#!/usr/bin/env python3
"""Materialize untouched 2025 position/role confirmation source evidence.

Source-only by contract: this script does not import, load, fit, or score any
position model or confirmation parameter artifact.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry
from universal_baseball.position_role_source import (
    project_fielding_usage_splits,
    project_hitting_player_ids,
)
from universal_baseball.storage import write_canonical_parquet


SEASON = 2025
LEAGUES: tuple[tuple[int, str], ...] = (
    (103, "MLB"),
    (104, "MLB"),
    (112, "AAA"),
    (117, "AAA"),
    (109, "AA"),
    (111, "AA"),
    (113, "AA"),
    (116, "HIGH_A"),
    (118, "HIGH_A"),
    (126, "HIGH_A"),
    (110, "SINGLE_A"),
    (122, "SINGLE_A"),
    (123, "SINGLE_A"),
    (121, "ROOKIE_COMPLEX"),
    (124, "ROOKIE_COMPLEX"),
    (130, "ROOKIE_COMPLEX"),
)
GROUPS = ("fielding", "hitting")
PAGE_LIMIT = 500
REPORT_ROOT = Path("reports/generated/position-role-2025-confirmation-source")
CAPTURE_ROOT = Path("data/quarantine/position-role-2025-confirmation-source")


def _capture_page(
    session: requests.Session,
    *,
    league_id: int,
    group: str,
    offset: int,
) -> tuple[list[Mapping[str, Any]], int | None, dict[str, Any]]:
    params = {
        "stats": "season",
        "group": group,
        "season": SEASON,
        "leagueId": int(league_id),
        "playerPool": "ALL",
        "gameType": "R",
        "limit": PAGE_LIMIT,
        "offset": int(offset),
    }
    response = _statsapi_get_with_retry(
        session,
        MLB_STATS_URL,
        params=params,
        timeout_seconds=120,
    )
    content = response.content
    payload = response.json()
    stats_groups = payload.get("stats") or []
    if len(stats_groups) != 1:
        raise RuntimeError(
            f"expected one stats group league={league_id} group={group}, "
            f"observed={len(stats_groups)}"
        )
    stats_group = stats_groups[0]
    splits = stats_group.get("splits") or []
    if not isinstance(splits, list) or any(not isinstance(row, Mapping) for row in splits):
        raise RuntimeError(
            f"invalid splits league={league_id} group={group} offset={offset}"
        )
    total = stats_group.get("totalSplits")
    total_int = int(total) if total is not None else None

    capture_path = CAPTURE_ROOT / str(league_id) / f"{group}_offset_{offset}.json"
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    capture_path.write_bytes(content)
    return list(splits), total_int, {
        "season": SEASON,
        "league_id": int(league_id),
        "group": group,
        "offset": int(offset),
        "requested_limit": PAGE_LIMIT,
        "requested_url": response.url,
        "status_code": int(response.status_code),
        "response_byte_count": len(content),
        "response_sha256": sha256(content).hexdigest(),
        "returned_split_count": len(splits),
        "reported_total_splits": total_int,
        "capture_path": str(capture_path),
    }


def _fetch_group(
    session: requests.Session,
    *,
    league_id: int,
    group: str,
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    all_splits: list[Mapping[str, Any]] = []
    captures: list[dict[str, Any]] = []
    offset = 0
    reported_total: int | None = None
    while True:
        splits, total, capture = _capture_page(
            session,
            league_id=league_id,
            group=group,
            offset=offset,
        )
        all_splits.extend(splits)
        captures.append(capture)
        if total is not None:
            if reported_total is None:
                reported_total = total
            elif total != reported_total:
                raise RuntimeError(
                    f"totalSplits changed league={league_id} group={group}: "
                    f"{reported_total} -> {total}"
                )
        if reported_total is not None and len(all_splits) >= reported_total:
            break
        if not splits or len(splits) < PAGE_LIMIT:
            break
        offset += len(splits)
        if offset > 10_000:
            raise RuntimeError(
                f"pagination safety bound exceeded league={league_id} group={group}"
            )
    if not all_splits:
        raise RuntimeError(f"empty source league={league_id} group={group}")
    if reported_total is not None and len(all_splits) != reported_total:
        raise RuntimeError(
            f"incomplete pagination league={league_id} group={group}: "
            f"observed={len(all_splits)}, reported={reported_total}"
        )
    return all_splits, captures


def _coverage(
    fielding: pl.DataFrame,
    hitting_ids: set[int],
    *,
    league_id: int,
    level_group: str,
) -> tuple[dict[str, Any], dict[str, object]]:
    fielding_ids = set(int(v) for v in fielding.get_column("player_id").unique().to_list())
    missing = sorted(hitting_ids - fielding_ids)
    hitter_usage = fielding.filter(pl.col("player_id").is_in(list(hitting_ids)))
    starts = (
        hitter_usage.group_by("player_id")
        .agg(pl.col("games_started").sum().alias("total_games_started"))
        if not hitter_usage.is_empty()
        else pl.DataFrame({"player_id": [], "total_games_started": []})
    )
    zero_start_ids = (
        starts.filter(pl.col("total_games_started") == 0).get_column("player_id").to_list()
        if not starts.is_empty()
        else []
    )
    report = {
        "season": SEASON,
        "league_id": int(league_id),
        "level_group": level_group,
        "fielding_row_count": int(fielding.height),
        "fielding_unique_player_count": len(fielding_ids),
        "hitting_unique_player_count": len(hitting_ids),
        "hitting_players_without_fielding_count": len(missing),
        "hitting_players_without_fielding_examples": missing[:25],
        "hitting_players_with_fielding_but_zero_games_started_count": len(zero_start_ids),
        "hitting_players_with_fielding_but_zero_games_started_examples": sorted(
            int(value) for value in zero_start_ids
        )[:25],
        "position_totals": (
            fielding.group_by("position_abbreviation")
            .agg(
                pl.len().alias("source_rows"),
                pl.col("games_started").sum().alias("games_started"),
                pl.col("fielding_outs").sum().alias("fielding_outs"),
            )
            .sort("position_abbreviation")
            .to_dicts()
        ),
    }
    table_row: dict[str, object] = {
        "season": SEASON,
        "league_id": int(league_id),
        "level_group": level_group,
        "fielding_rows": int(fielding.height),
        "fielding_players": len(fielding_ids),
        "hitting_players": len(hitting_ids),
        "hitting_players_missing_fielding": len(missing),
        "hitting_players_zero_starts": len(zero_start_ids),
    }
    return report, table_row


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-position-role-2025-source/0.1"
    fielding_frames: list[pl.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, object]] = []
    capture_records: list[dict[str, Any]] = []
    errors: list[dict[str, object]] = []
    try:
        for league_id, level_group in LEAGUES:
            try:
                fielding_splits, fielding_captures = _fetch_group(
                    session, league_id=league_id, group="fielding"
                )
                hitting_splits, hitting_captures = _fetch_group(
                    session, league_id=league_id, group="hitting"
                )
                capture_records.extend(fielding_captures)
                capture_records.extend(hitting_captures)
                fielding = project_fielding_usage_splits(
                    fielding_splits,
                    season=SEASON,
                    league_id=league_id,
                    level_group=level_group,
                )
                hitting_ids = project_hitting_player_ids(hitting_splits)
                coverage, table_row = _coverage(
                    fielding,
                    hitting_ids,
                    league_id=league_id,
                    level_group=level_group,
                )
                coverage.update(
                    {
                        "fielding_page_count": len(fielding_captures),
                        "hitting_page_count": len(hitting_captures),
                        "fielding_capture_sha256": [
                            row["response_sha256"] for row in fielding_captures
                        ],
                        "hitting_capture_sha256": [
                            row["response_sha256"] for row in hitting_captures
                        ],
                        "accepted": True,
                    }
                )
                audit_rows.append(coverage)
                coverage_rows.append(table_row)
                fielding_frames.append(fielding)
            except Exception as exc:
                errors.append(
                    {
                        "season": SEASON,
                        "league_id": int(league_id),
                        "level_group": level_group,
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }
                )
                audit_rows.append(
                    {
                        "season": SEASON,
                        "league_id": int(league_id),
                        "level_group": level_group,
                        "accepted": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    finally:
        session.close()

    expected_pairs = len(LEAGUES)
    accepted = bool(
        len(audit_rows) == expected_pairs
        and len(fielding_frames) == expected_pairs
        and not errors
        and all(bool(row.get("accepted")) for row in audit_rows)
    )

    storage: dict[str, Any] = {}
    if fielding_frames:
        combined = pl.concat(fielding_frames, how="vertical_relaxed").sort(
            ["season", "league_id", "team_id", "player_id", "position_code"]
        )
        key = ["season", "league_id", "team_id", "player_id", "position_code"]
        if combined.group_by(key).len().filter(pl.col("len") != 1).height:
            raise RuntimeError("combined 2025 fielding source violates canonical grain")
        storage["fielding_usage"] = write_canonical_parquet(
            combined,
            table_root / "position_role_2025_fielding_usage.parquet",
            table_name="position_role_2025_fielding_usage",
        ).as_record()
    if coverage_rows:
        coverage_frame = pl.DataFrame(coverage_rows).sort(["season", "league_id"])
        storage["coverage"] = write_canonical_parquet(
            coverage_frame,
            table_root / "position_role_2025_fielding_coverage.parquet",
            table_name="position_role_2025_fielding_coverage",
        ).as_record()

    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_2025_confirmation_source_materialization",
        "contract": "docs/position-role-2025-confirmation-source-contract.md",
        "source": "official_mlb_stats_api_stats_season",
        "season": SEASON,
        "league_map": [
            {"league_id": league_id, "level_group": level_group}
            for league_id, level_group in LEAGUES
        ],
        "expected_league_pairs": expected_pairs,
        "successful_league_pairs": len(fielding_frames),
        "audits": audit_rows,
        "source_errors": errors,
        "capture_record_count": len(capture_records),
        "capture_records": capture_records,
        "storage": storage,
        "decision": {
            "source_materialized": accepted,
            "confirmation_scoring_authorized_next": accepted,
        },
        "boundary": {
            "2025_position_source_accessed": True,
            "2025_position_outcomes_scored": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "2024_role_profiles_loaded": False,
            "team_allocator_fit": False,
            "defense_model_fit": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Position / Role 2025 confirmation source",
        "",
        f"- Materialized: {accepted}",
        f"- Successful league pairs: {len(fielding_frames)}/{expected_pairs}",
        f"- Raw capture pages: {len(capture_records)}",
        f"- Source errors: {len(errors)}",
        "- Model parameters loaded: False",
        "- Position outcomes scored: False",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not accepted:
        raise RuntimeError("2025 position-role confirmation source failed closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
