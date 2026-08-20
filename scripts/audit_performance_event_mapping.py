#!/usr/bin/env python
"""Audit the minimum Performance event mapper on real affiliated games."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.canonical_adapters import (
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
)
from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import capture_official_json
from universal_baseball.performance_events import build_performance_events
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.resolution import resolve_pitch_observations_within_snapshot
from universal_baseball.source_comparison import select_diverse_game_ids


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aaa-asset", default="2025_4_aaa_pbp.csv")
    parser.add_argument("--rookie-asset", default="2024_6_rk_pbp.csv")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/performance-event-audit"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/performance-event-audit"),
    )
    return parser.parse_args()


def _snapshot_id(asset: str, sha256: str) -> str:
    return make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=sha256,
        upstream_version=asset,
    )


def _normalization(snapshot_id: str) -> NormalizationDefinition:
    return NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_armstjc_pitch_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )


def _numeric_game_ids(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("game_pk").cast(pl.Int64, strict=False).alias("__game_pk_int")
    ).filter(pl.col("__game_pk_int").is_not_null())


def _select_rookie_games(frame: pl.DataFrame) -> list[tuple[str, int]]:
    """Select one game from each Rookie league represented in the asset."""

    if "league_name" not in frame.columns:
        raise ValueError("Rookie audit asset lacks league_name")
    working = _numeric_game_ids(frame)
    rows = (
        working.select(["league_name", "__game_pk_int", "game_date"])
        .drop_nulls(["league_name", "__game_pk_int"])
        .unique()
        .sort(["league_name", "game_date", "__game_pk_int"])
    )
    selected: list[tuple[str, int]] = []
    for league, group in rows.group_by("league_name", maintain_order=True):
        label = str(league[0] if isinstance(league, tuple) else league)
        game_id = int(group.get_column("__game_pk_int")[0])
        selected.append((label, game_id))
    return selected


def _asset_games(frame: pl.DataFrame, *, rookie: bool) -> list[tuple[str, int]]:
    if rookie:
        return _select_rookie_games(frame)
    working = _numeric_game_ids(frame)
    sample_frame = working.rename({"__game_pk_int": "game_pk_numeric"})
    sample_input = sample_frame.select(
        pl.col("game_pk_numeric").alias("game_pk"), "game_date"
    )
    return [("AAA", game_id) for game_id in select_diverse_game_ids(sample_input, limit=3)]


def _filter_game(frame: pl.DataFrame, game_id: int) -> pl.DataFrame:
    return frame.filter(pl.col("game_pk").cast(pl.Int64, strict=False) == game_id)


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["len"])
        for row in frame.group_by(column).len().sort(["len", column], descending=[True, False]).to_dicts()
    }


def _audit_asset(asset: str, *, rookie: bool, work_dir: Path) -> dict[str, Any]:
    path = work_dir / asset
    metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=180)
    source = read_quarantined_csv(path)
    snapshot_id = _snapshot_id(asset, str(metadata["sha256"]))
    normalization = _normalization(snapshot_id)

    game_reports: list[dict[str, Any]] = []
    all_events: list[pl.DataFrame] = []
    for league_label, game_id in _asset_games(source, rookie=rookie):
        source_game = _filter_game(source, game_id)
        observations = normalize_armstjc_pitch_observations(
            source_game,
            source_snapshot_id=snapshot_id,
            normalization_id=normalization.normalization_id,
        )
        pitch_consensus = resolve_pitch_observations_within_snapshot(observations)

        capture = capture_official_json(f"game/{game_id}/playByPlay")
        if not isinstance(capture.data, dict):
            raise RuntimeError(f"official game {game_id} PBP is not a JSON object")
        official_snapshot_id = make_source_snapshot_id(
            source_name="mlb_stats_api",
            content_sha256=capture.content_sha256,
            upstream_version=capture.endpoint,
        )
        official_normalization = NormalizationDefinition.build(
            source_snapshot_id=official_snapshot_id,
            normalizer_name="normalize_official_play_sequence_observations",
            normalizer_version="1",
            canonical_schema_version=CANONICAL_SCHEMA_VERSION,
        )
        sequences = normalize_official_play_sequence_observations(
            game_id,
            capture.data,
            source_snapshot_id=official_snapshot_id,
            normalization_id=official_normalization.normalization_id,
        )
        events = build_performance_events(sequences, pitch_consensus)
        all_events.append(events.with_columns(pl.lit(league_label).alias("audit_league")))

        status_counts = _counts(events, "evidence_status")
        game_reports.append(
            {
                "league": league_label,
                "game_pk": game_id,
                "true_pa_count": events.height,
                "core_eligible_count_pre_foul_screen": int(
                    events.get_column("core_profile_eligible_pre_foul_screen").sum()
                ),
                "evidence_status_counts": status_counts,
                "unexpected_in_play_non_bip_count": status_counts.get(
                    "unexpected_in_play_non_bip", 0
                ),
                "missing_in_play_pitch_count": status_counts.get(
                    "missing_in_play_pitch", 0
                ),
                "multiple_in_play_pitches_count": status_counts.get(
                    "multiple_in_play_pitches", 0
                ),
                "conflicted_in_play_flag_count": status_counts.get(
                    "conflicted_in_play_flag", 0
                ),
            }
        )

    combined = pl.concat(all_events, how="vertical_relaxed")
    status_counts = _counts(combined, "evidence_status")
    core_counts = _counts(
        combined.filter(pl.col("fabio_core_bin_pre_foul_screen").is_not_null()),
        "fabio_core_bin_pre_foul_screen",
    )
    trajectory_counts = _counts(combined, "trajectory_family")

    structural_problem_count = sum(
        status_counts.get(code, 0)
        for code in (
            "unexpected_in_play_non_bip",
            "missing_in_play_pitch",
            "multiple_in_play_pitches",
            "conflicted_in_play_flag",
        )
    )
    return {
        "asset": asset,
        "source_sha256": metadata["sha256"],
        "sampled_game_count": len(game_reports),
        "true_pa_count": combined.height,
        "core_eligible_count_pre_foul_screen": int(
            combined.get_column("core_profile_eligible_pre_foul_screen").sum()
        ),
        "core_eligible_rate_pre_foul_screen": (
            float(combined.get_column("core_profile_eligible_pre_foul_screen").mean())
            if combined.height
            else None
        ),
        "evidence_status_counts": status_counts,
        "fabio_core_bin_counts_pre_foul_screen": core_counts,
        "trajectory_family_counts": trajectory_counts,
        "structural_problem_count": structural_problem_count,
        "games": game_reports,
    }


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    reports = [
        _audit_asset(args.aaa_asset, rookie=False, work_dir=args.work_dir),
        _audit_asset(args.rookie_asset, rookie=True, work_dir=args.work_dir),
    ]
    payload = {"report_schema_version": 1, "assets": reports}
    (args.report_dir / "performance_event_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = ["# Performance event mapping audit", ""]
    for report in reports:
        lines.extend(
            [
                f"## `{report['asset']}`",
                "",
                f"- Sampled games: {report['sampled_game_count']}",
                f"- Official true PAs: {report['true_pa_count']:,}",
                f"- Core eligible before foul-air screen: {report['core_eligible_count_pre_foul_screen']:,} "
                f"({report['core_eligible_rate_pre_foul_screen']:.2%})",
                f"- Structural source/PA mapping problems: {report['structural_problem_count']:,}",
                f"- Evidence statuses: `{report['evidence_status_counts']}`",
                f"- Trajectory families: `{report['trajectory_family_counts']}`",
                "",
            ]
        )
        for game in report["games"]:
            lines.append(
                f"- {game['league']} game `{game['game_pk']}`: {game['true_pa_count']} PAs; "
                f"statuses `{game['evidence_status_counts']}`"
            )
        lines.append("")

    summary = "\n".join(lines)
    (args.report_dir / "performance_event_audit.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
