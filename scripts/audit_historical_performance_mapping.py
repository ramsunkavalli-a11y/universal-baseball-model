#!/usr/bin/env python
"""Exercise the universal Performance event mapper in older MiLB eras."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

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
ASSETS = ("2005_9_aaa_pbp.csv", "2015_9_aaa_pbp.csv")
STRUCTURAL_FAILURE_STATUSES = {
    "unexpected_in_play_non_bip",
    "missing_in_play_pitch",
    "multiple_in_play_pitches",
    "conflicted_in_play_flag",
}


def _source_snapshot(asset: str, sha256: str) -> tuple[str, NormalizationDefinition]:
    snapshot_id = make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=sha256,
        upstream_version=asset,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_armstjc_pitch_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    return snapshot_id, normalization


def _official_sequences(game_id: int) -> pl.DataFrame:
    capture = capture_official_json(f"game/{game_id}/playByPlay")
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official game {game_id} PBP is not an object")
    snapshot_id = make_source_snapshot_id(
        source_name="mlb_stats_api",
        content_sha256=capture.content_sha256,
        upstream_version=capture.endpoint,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_official_play_sequence_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    return normalize_official_play_sequence_observations(
        game_id,
        capture.data,
        source_snapshot_id=snapshot_id,
        normalization_id=normalization.normalization_id,
    )


def _sample_games(frame: pl.DataFrame, limit: int = 2) -> list[int]:
    sample = frame.select(
        pl.col("game_pk").cast(pl.Int64, strict=False).alias("game_pk"),
        "game_date",
    ).drop_nulls(["game_pk"])
    return select_diverse_game_ids(sample, limit=limit)


def _status_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {}
    return {
        str(row["evidence_status"]): int(row["len"])
        for row in (
            frame.group_by("evidence_status")
            .len()
            .sort(["len", "evidence_status"], descending=[True, False])
            .to_dicts()
        )
    }


def main() -> int:
    work_dir = Path("data/quarantine/historical-performance-audit")
    report_dir = Path("reports/generated/historical-performance-audit")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    asset_reports: list[dict[str, Any]] = []
    total_structural_failures = 0

    for asset in ASSETS:
        path = work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=180)
        source = read_quarantined_csv(path)
        snapshot_id, normalization = _source_snapshot(asset, str(metadata["sha256"]))
        game_reports: list[dict[str, Any]] = []

        for game_id in _sample_games(source):
            source_game = source.filter(
                pl.col("game_pk").cast(pl.Int64, strict=False) == game_id
            )
            observations = normalize_armstjc_pitch_observations(
                source_game,
                source_snapshot_id=snapshot_id,
                normalization_id=normalization.normalization_id,
            )
            pitch_consensus = resolve_pitch_observations_within_snapshot(observations)
            sequences = _official_sequences(game_id)
            events = build_performance_events(sequences, pitch_consensus)
            statuses = _status_counts(events)
            structural_failures = sum(
                statuses.get(status, 0) for status in STRUCTURAL_FAILURE_STATUSES
            )
            total_structural_failures += structural_failures
            core_count = int(events.get_column("core_profile_eligible_pre_foul_screen").sum())
            game_reports.append(
                {
                    "game_pk": game_id,
                    "true_pa_count": events.height,
                    "core_eligible_pre_foul_screen_count": core_count,
                    "core_eligible_pre_foul_screen_rate": core_count / events.height if events.height else None,
                    "evidence_status_counts": statuses,
                    "structural_failure_count": structural_failures,
                    "source_pitch_consensus_count": pitch_consensus.height,
                    "source_pitch_conflict_count": int(
                        pitch_consensus.filter(pl.col("conflict_field_count") > 0).height
                    ),
                }
            )

        aggregate_statuses: Counter[str] = Counter()
        for game in game_reports:
            aggregate_statuses.update(game["evidence_status_counts"])
        total_pa = sum(game["true_pa_count"] for game in game_reports)
        total_core = sum(game["core_eligible_pre_foul_screen_count"] for game in game_reports)
        asset_reports.append(
            {
                "asset": asset,
                "source_sha256": metadata["sha256"],
                "sampled_game_count": len(game_reports),
                "true_pa_count": total_pa,
                "core_eligible_pre_foul_screen_count": total_core,
                "core_eligible_pre_foul_screen_rate": total_core / total_pa if total_pa else None,
                "evidence_status_counts": dict(sorted(aggregate_statuses.items())),
                "structural_failure_count": sum(game["structural_failure_count"] for game in game_reports),
                "games": game_reports,
            }
        )

    payload = {
        "report_schema_version": 1,
        "assets": asset_reports,
        "total_structural_failure_count": total_structural_failures,
    }
    (report_dir / "historical_performance_mapping.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = ["# Historical Performance mapping audit", ""]
    for report in asset_reports:
        lines.extend(
            [
                f"## `{report['asset']}`",
                "",
                f"- Sampled games: {report['sampled_game_count']}",
                f"- Official true PAs: {report['true_pa_count']:,}",
                f"- Core eligible before foul-air screen: {report['core_eligible_pre_foul_screen_count']:,} "
                f"({report['core_eligible_pre_foul_screen_rate']:.2%})",
                f"- Structural mapping failures: {report['structural_failure_count']:,}",
                f"- Evidence statuses: `{report['evidence_status_counts']}`",
                "",
            ]
        )
        for game in report["games"]:
            lines.append(
                f"- Game `{game['game_pk']}`: {game['true_pa_count']} PAs; "
                f"core {game['core_eligible_pre_foul_screen_rate']:.2%}; "
                f"statuses `{game['evidence_status_counts']}`; "
                f"source pitch conflicts {game['source_pitch_conflict_count']}"
            )
        lines.append("")

    summary = "\n".join(lines)
    (report_dir / "historical_performance_mapping.md").write_text(summary, encoding="utf-8")
    print(summary)

    if total_structural_failures:
        raise RuntimeError(
            f"historical Performance audit found {total_structural_failures} structural mapping failures"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
