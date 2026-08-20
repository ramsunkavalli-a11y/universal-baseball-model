#!/usr/bin/env python3
"""Measure 2021-2024 batting position/role profile stability.

Consumes only the certified historical position-role source. It builds observed
player-season batting-role profiles and compares adjacent development seasons.
No future position model is fit and no 2025 source is accessed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

import polars as pl

from universal_baseball.position_role_profile import (
    BATTING_ROLE_POSITIONS,
    DEFENSIVE_ROLE_POSITIONS,
    build_batting_role_profiles,
)
from universal_baseball.storage import write_canonical_parquet


SOURCE_RESULT = Path("docs/position-role-historical-source-result.json")
TRANSITIONS = ((2021, 2022), (2022, 2023), (2023, 2024))
REPORT_ROOT = Path("reports/generated/position-role-batting-profile-stability")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    return parser.parse_args()


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {filename} below {root}, found {len(matches)}: {matches}")
    return matches[0]


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _profile_maps(profile: pl.DataFrame) -> tuple[
    dict[tuple[int, int], dict[str, float]],
    dict[tuple[int, int], dict[str, float]],
]:
    role: dict[tuple[int, int], dict[str, float]] = {}
    defensive: dict[tuple[int, int], dict[str, float]] = {}
    for row in profile.iter_rows(named=True):
        key = (int(row["season"]), int(row["player_id"]))
        position = str(row["position_abbreviation"])
        role.setdefault(key, {})[position] = float(row["role_probability"])
        defensive_probability = row["defensive_probability"]
        if position in DEFENSIVE_ROLE_POSITIONS and defensive_probability is not None:
            defensive.setdefault(key, {})[position] = float(defensive_probability)
    return role, defensive


def _tv(left: dict[str, float], right: dict[str, float], positions: tuple[str, ...]) -> float:
    return 0.5 * sum(abs(left.get(position, 0.0) - right.get(position, 0.0)) for position in positions)


def _season_summary(summary: pl.DataFrame, season: int) -> dict[str, Any]:
    frame = summary.filter(pl.col("season") == season)
    fallback = frame.filter(pl.col("role_evidence_mode") == "games_played_fallback")
    primary_counts = (
        frame.group_by("primary_position")
        .len()
        .sort("primary_position")
        .to_dicts()
    )
    shares = [float(value) for value in frame.get_column("primary_role_share").to_list()]
    return {
        "season": int(season),
        "player_count": int(frame.height),
        "games_started_mode_count": int(frame.height - fallback.height),
        "games_played_fallback_count": int(fallback.height),
        "games_played_fallback_rate": float(fallback.height / frame.height) if frame.height else None,
        "mean_primary_role_share": float(mean(shares)) if shares else None,
        "median_primary_role_share": float(median(shares)) if shares else None,
        "primary_position_counts": primary_counts,
    }


def _transition(
    summary_rows: dict[tuple[int, int], dict[str, Any]],
    role_profiles: dict[tuple[int, int], dict[str, float]],
    defensive_profiles: dict[tuple[int, int], dict[str, float]],
    *,
    current_season: int,
    next_season: int,
) -> tuple[dict[str, Any], list[dict[str, object]]]:
    current_ids = {player_id for season, player_id in summary_rows if season == current_season}
    next_ids = {player_id for season, player_id in summary_rows if season == next_season}
    paired_ids = sorted(current_ids & next_ids)

    tv_values: list[float] = []
    defensive_tv_values: list[float] = []
    exact: list[bool] = []
    concentrated_exact: list[bool] = []
    current_shares: list[float] = []
    transition_counts: Counter[tuple[str, str]] = Counter()
    mode_counts: Counter[tuple[str, str]] = Counter()
    rows: list[dict[str, object]] = []

    for player_id in paired_ids:
        current = summary_rows[(current_season, player_id)]
        future = summary_rows[(next_season, player_id)]
        role_tv = _tv(
            role_profiles[(current_season, player_id)],
            role_profiles[(next_season, player_id)],
            BATTING_ROLE_POSITIONS,
        )
        is_exact = str(current["primary_position"]) == str(future["primary_position"])
        current_share = float(current["primary_role_share"])
        if current_share >= 0.75:
            concentrated_exact.append(is_exact)
        exact.append(is_exact)
        current_shares.append(current_share)
        tv_values.append(role_tv)
        transition_counts[(str(current["primary_position"]), str(future["primary_position"]))] += 1
        mode_counts[(str(current["role_evidence_mode"]), str(future["role_evidence_mode"]))] += 1

        defensive_tv = None
        current_def = defensive_profiles.get((current_season, player_id))
        future_def = defensive_profiles.get((next_season, player_id))
        if current_def is not None and future_def is not None:
            defensive_tv = _tv(current_def, future_def, DEFENSIVE_ROLE_POSITIONS)
            defensive_tv_values.append(defensive_tv)

        rows.append(
            {
                "current_season": int(current_season),
                "next_season": int(next_season),
                "player_id": int(player_id),
                "current_primary_position": str(current["primary_position"]),
                "next_primary_position": str(future["primary_position"]),
                "primary_position_match": bool(is_exact),
                "current_primary_role_share": current_share,
                "next_primary_role_share": float(future["primary_role_share"]),
                "current_role_evidence_mode": str(current["role_evidence_mode"]),
                "next_role_evidence_mode": str(future["role_evidence_mode"]),
                "role_profile_tv_distance": float(role_tv),
                "defensive_profile_tv_distance": defensive_tv,
            }
        )

    transition_matrix = [
        {
            "current_primary_position": current,
            "next_primary_position": future,
            "player_count": count,
        }
        for (current, future), count in sorted(transition_counts.items())
    ]
    evidence_modes = [
        {
            "current_mode": current,
            "next_mode": future,
            "player_count": count,
        }
        for (current, future), count in sorted(mode_counts.items())
    ]
    report = {
        "current_season": int(current_season),
        "next_season": int(next_season),
        "paired_player_count": len(paired_ids),
        "exact_primary_position_match_rate": float(sum(exact) / len(exact)) if exact else None,
        "mean_role_profile_tv_distance": float(mean(tv_values)) if tv_values else None,
        "median_role_profile_tv_distance": float(median(tv_values)) if tv_values else None,
        "p75_role_profile_tv_distance": _percentile(tv_values, 0.75),
        "p90_role_profile_tv_distance": _percentile(tv_values, 0.90),
        "mean_current_primary_role_share": float(mean(current_shares)) if current_shares else None,
        "median_current_primary_role_share": float(median(current_shares)) if current_shares else None,
        "current_primary_share_ge_0_75_player_count": len(concentrated_exact),
        "exact_primary_match_rate_when_current_share_ge_0_75": (
            float(sum(concentrated_exact) / len(concentrated_exact))
            if concentrated_exact
            else None
        ),
        "defensive_profile_paired_player_count": len(defensive_tv_values),
        "mean_defensive_profile_tv_distance": (
            float(mean(defensive_tv_values)) if defensive_tv_values else None
        ),
        "median_defensive_profile_tv_distance": (
            float(median(defensive_tv_values)) if defensive_tv_values else None
        ),
        "evidence_mode_transitions": evidence_modes,
        "primary_position_transition_matrix": transition_matrix,
    }
    return report, rows


def main() -> int:
    args = _args()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    source_record = json.loads(SOURCE_RESULT.read_text(encoding="utf-8"))
    if not source_record.get("decision", {}).get("historical_position_role_source_certified"):
        raise RuntimeError("historical position-role source is not certified")
    if source_record.get("boundary", {}).get("2025_accessed"):
        raise RuntimeError("historical source unexpectedly claims 2025 access")

    source_path = _find_one(args.source_root, "historical_fielding_usage.parquet")
    expected_sha = str(source_record["storage"]["fielding_usage"]["file_sha256"])
    observed_sha = _file_sha256(source_path)
    if observed_sha != expected_sha:
        raise RuntimeError(
            f"historical fielding source hash changed: expected={expected_sha}, observed={observed_sha}"
        )
    fielding = pl.read_parquet(source_path)
    built = build_batting_role_profiles(fielding)

    profile_storage = write_canonical_parquet(
        built.profile,
        table_root / "batting_role_profiles_2021_2024.parquet",
        table_name="batting_role_profiles_2021_2024",
    ).as_record()
    summary_storage = write_canonical_parquet(
        built.player_season,
        table_root / "batting_role_player_season_2021_2024.parquet",
        table_name="batting_role_player_season_2021_2024",
    ).as_record()

    summary_rows = {
        (int(row["season"]), int(row["player_id"])): row
        for row in built.player_season.iter_rows(named=True)
    }
    role_profiles, defensive_profiles = _profile_maps(built.profile)

    transition_reports: list[dict[str, Any]] = []
    transition_rows: list[dict[str, object]] = []
    for current_season, next_season in TRANSITIONS:
        report, rows = _transition(
            summary_rows,
            role_profiles,
            defensive_profiles,
            current_season=current_season,
            next_season=next_season,
        )
        transition_reports.append(report)
        transition_rows.extend(rows)

    transition_frame = pl.DataFrame(transition_rows).sort(
        ["current_season", "player_id"]
    )
    transition_storage = write_canonical_parquet(
        transition_frame,
        table_root / "batting_role_adjacent_year_stability.parquet",
        table_name="batting_role_adjacent_year_stability_2021_2024",
    ).as_record()

    pooled_exact = transition_frame.get_column("primary_position_match").cast(pl.Float64)
    pooled_tv = transition_frame.get_column("role_profile_tv_distance")
    pooled_concentrated = transition_frame.filter(pl.col("current_primary_role_share") >= 0.75)
    pooled_defensive = transition_frame.filter(
        pl.col("defensive_profile_tv_distance").is_not_null()
    )
    pooled_report = {
        "player_transition_count": int(transition_frame.height),
        "exact_primary_position_match_rate": float(pooled_exact.mean()),
        "mean_role_profile_tv_distance": float(pooled_tv.mean()),
        "median_role_profile_tv_distance": float(pooled_tv.median()),
        "p75_role_profile_tv_distance": _percentile(
            [float(value) for value in pooled_tv.to_list()], 0.75
        ),
        "p90_role_profile_tv_distance": _percentile(
            [float(value) for value in pooled_tv.to_list()], 0.90
        ),
        "current_primary_share_ge_0_75_player_transition_count": int(
            pooled_concentrated.height
        ),
        "exact_primary_match_rate_when_current_share_ge_0_75": float(
            pooled_concentrated.get_column("primary_position_match")
            .cast(pl.Float64)
            .mean()
        )
        if pooled_concentrated.height
        else None,
        "defensive_profile_player_transition_count": int(pooled_defensive.height),
        "mean_defensive_profile_tv_distance": float(
            pooled_defensive.get_column("defensive_profile_tv_distance").mean()
        )
        if pooled_defensive.height
        else None,
        "median_defensive_profile_tv_distance": float(
            pooled_defensive.get_column("defensive_profile_tv_distance").median()
        )
        if pooled_defensive.height
        else None,
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "batting_position_role_profile_stability_development_only",
        "contract": "docs/position-role-batting-profile-stability-contract.md",
        "source_run_id": int(source_record["source_run_id"]),
        "source_fielding_sha256": observed_sha,
        "seasons": [2021, 2022, 2023, 2024],
        "batting_role_positions": list(BATTING_ROLE_POSITIONS),
        "season_summaries": [
            _season_summary(built.player_season, season) for season in (2021, 2022, 2023, 2024)
        ],
        "transitions": transition_reports,
        "pooled": pooled_report,
        "storage": {
            "role_profiles": profile_storage,
            "player_season": summary_storage,
            "adjacent_year_stability": transition_storage,
        },
        "decision": {
            "stability_audit_complete": True,
            "position_projection_method_selected": False,
            "position_model_authorized": False,
            "2025_confirmation_authorized": False,
            "team_allocator_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "model_fit": False,
            "future_position_projected": False,
            "playing_time_v1_modified": False,
            "pitcher_role_included_in_batting_profile": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Batting position / role profile stability — 2021–2024",
        "",
        f"- Pooled player-transitions: {transition_frame.height:,}",
        f"- Exact primary-position match: {pooled_report['exact_primary_position_match_rate']:.3f}",
        f"- Median full-profile TV distance: {pooled_report['median_role_profile_tv_distance']:.3f}",
        f"- Exact match when current primary share >= .75: "
        f"{pooled_report['exact_primary_match_rate_when_current_share_ge_0_75']:.3f}",
        f"- Median defensive-profile TV distance: "
        f"{pooled_report['median_defensive_profile_tv_distance']:.3f}",
        "- Position projection method selected: False",
        "- 2025 accessed: False",
        "",
    ]
    for row in transition_reports:
        lines.extend(
            [
                f"## {row['current_season']} -> {row['next_season']}",
                f"- Paired players: {row['paired_player_count']:,}",
                f"- Exact primary-position match: {row['exact_primary_position_match_rate']:.3f}",
                f"- Median role-profile TV: {row['median_role_profile_tv_distance']:.3f}",
                f"- Exact match at current primary share >= .75: "
                f"{row['exact_primary_match_rate_when_current_share_ge_0_75']:.3f}",
                f"- Median defensive-profile TV: {row['median_defensive_profile_tv_distance']:.3f}",
                "",
            ]
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
