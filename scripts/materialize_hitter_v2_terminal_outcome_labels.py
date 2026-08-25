#!/usr/bin/env python3
"""Materialize and reconcile source-only Hitter v2 terminal-PA labels."""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

import polars as pl

import materialize_hitter_v2_stage1_mlb as stage1_mlb
from universal_baseball.current_talent_contact_value_source import (
    attach_narrative_terminal_groups,
    project_terminal_pa_descriptions,
)
from universal_baseball.current_talent_mlb_evidence import (
    _with_official_outcome_batter,
)
from universal_baseball.hitter_v2_event_labels import (
    attach_structured_terminal_event,
    attach_terminal_pa_labels,
    reconcile_terminal_pa_labels,
)
from universal_baseball.hitter_v2_outcomes import TERMINAL_OUTCOMES
from universal_baseball.storage import write_canonical_parquet


SEASONS = (2021, 2022, 2023, 2024)
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-milb-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/pbp"),
    )
    parser.add_argument(
        "--milb-2024-root",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-2024-milb/"
            "reconstructed-terminal-source/2024"
        ),
    )
    parser.add_argument(
        "--contact-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/artifacts"),
    )
    parser.add_argument(
        "--mlb-2021-2023-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1-mlb/artifacts"),
    )
    parser.add_argument(
        "--mlb-2024-artifact-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage2-2024-mlb/artifacts"),
    )
    parser.add_argument(
        "--matchup-sidecar",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-matchup-context-sidecar/tables/"
            "hitter_v2_matchup_context_sidecar_2021_2024.parquet"
        ),
    )
    parser.add_argument(
        "--player-game-2021-2023",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--player-game-2024",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-2024-universal/tables/"
            "hitter_v2_player_game_outcomes_2024.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-terminal-outcome-label-sidecar"),
    )
    return parser.parse_args()


def _contact_archive(root: Path, season: int, level: str) -> Path:
    slug = level.replace("+", "plus")
    pattern = (
        f"*-current-talent-contact-value-source-{season}-{slug}.zip"
        if season in (2021, 2022)
        else "*-current-talent-contact-value-confirmation-source-v2.zip"
    )
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise ValueError(f"expected one contact archive matching {pattern}: {paths}")
    return paths[0]


def _read_terminal_archive(path: Path, season: int, level: str) -> pl.DataFrame:
    slug = level.replace("+", "plus")
    suffix = f"terminal_pas_{season}_{slug}.parquet"
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise ValueError(f"expected one {suffix} in {path.name}: {names}")
        return pl.read_parquet(io.BytesIO(archive.read(names[0])))


def _load_raw(files: list[Path]) -> pl.DataFrame:
    if not files:
        raise ValueError("terminal label source has no PBP files")
    frames = [
        pl.scan_csv(
            path,
            infer_schema=False,
            null_values=["", "NA", "NaN", "null", "None"],
            truncate_ragged_lines=False,
        )
        .select(
            "game_pk",
            "at_bat_number",
            "pitch_number",
            "game_type",
            "events",
            "des",
            "description",
        )
        .collect()
        for path in files
    ]
    return pl.concat(frames, how="vertical_relaxed")


def _milb_labels(
    *,
    season: int,
    level: str,
    raw_root: Path,
    contact_root: Path,
) -> tuple[pl.DataFrame, dict[str, object]]:
    directory = level.replace("+", "plus")
    if season == 2024:
        files = sorted((raw_root / directory / "pbp").glob("*_pbp.csv"))
    else:
        files = sorted((raw_root / str(season) / directory).glob("*_pbp.csv"))
    raw = _load_raw(files)
    if season == 2024:
        terminal = attach_narrative_terminal_groups(
            project_terminal_pa_descriptions(raw)
        )
        source_method = "reconstructed_terminal_narrative_with_structured_event_priority"
        source_container = None
    else:
        archive = _contact_archive(contact_root, season, level)
        terminal = _read_terminal_archive(archive, season, level)
        source_method = "retained_terminal_projection_with_structured_event_priority"
        source_container = archive.name
    terminal = attach_structured_terminal_event(raw, terminal)
    labels = attach_terminal_pa_labels(
        terminal,
        event_column="structured_event",
        description_column="pa_description",
    ).select(
        "game_pk",
        "at_bat_index",
        "canonical_outcome",
        "label_status",
        "label_authority",
        "structured_event_conflict",
    )
    return labels, {
        "season": season,
        "level_group": level,
        "source_system": "ARMSTJC_PBP",
        "source_files": len(files),
        "source_size_bytes": sum(path.stat().st_size for path in files),
        "source_container": source_container,
        "terminal_pa": labels.height,
        "direct_labeled_pa": int(labels["canonical_outcome"].is_not_null().sum()),
        "structured_event_conflict_pa": int(labels["structured_event_conflict"].sum()),
        "source_method": source_method,
    }


def _mlb_labels(
    *, season: int, artifact_root: Path
) -> tuple[pl.DataFrame, dict[str, object]]:
    paths = sorted(artifact_root.glob(f"*-current-talent-historical-mlb-{season}.zip"))
    if len(paths) != 1:
        raise ValueError(f"expected one MLB {season} artifact: {paths}")
    with zipfile.ZipFile(paths[0]) as archive:
        savant, chunks = stage1_mlb._savant(archive, season)
    terminal = _with_official_outcome_batter(savant).filter(
        pl.col("is_plate_appearance_terminal")
    ).select(
        "game_pk",
        "at_bat_index",
        pl.col("events").alias("structured_event"),
        pl.col("result_description").alias("pa_description"),
    )
    labels = attach_terminal_pa_labels(
        terminal,
        event_column="structured_event",
        description_column="pa_description",
    ).select(
        "game_pk",
        "at_bat_index",
        "canonical_outcome",
        "label_status",
        "label_authority",
    ).with_columns(pl.lit(False).alias("structured_event_conflict"))
    return labels, {
        "season": season,
        "level_group": "MLB",
        "source_system": "BASEBALL_SAVANT",
        "source_container": paths[0].name,
        "source_files": len(chunks),
        "source_size_bytes": sum(int(row["size_bytes"]) for row in chunks),
        "terminal_pa": labels.height,
        "direct_labeled_pa": int(labels["canonical_outcome"].is_not_null().sum()),
        "structured_event_conflict_pa": 0,
        "source_method": "structured_savant_true_pa_terminal_event",
    }


def _coverage(frame: pl.DataFrame) -> list[dict[str, object]]:
    return (
        frame.group_by(["season", "level_group"])
        .agg(
            pl.len().alias("sidecar_pa"),
            pl.col("canonical_outcome").is_not_null().sum().alias("direct_labeled_pa"),
            pl.col("context_label_ready").sum().alias("context_label_ready_pa"),
            pl.col("matchup_ready").sum().alias("matchup_ready_pa"),
        )
        .with_columns(
            (pl.col("direct_labeled_pa") / pl.col("sidecar_pa")).alias(
                "direct_label_rate"
            ),
            (pl.col("context_label_ready_pa") / pl.col("sidecar_pa")).alias(
                "context_label_ready_rate"
            ),
        )
        .sort(["season", "level_group"])
        .to_dicts()
    )


def _gate(coverage: list[dict[str, object]]) -> tuple[bool, list[dict[str, object]]]:
    failures: list[dict[str, object]] = []
    total_pa = sum(int(row["sidecar_pa"]) for row in coverage)
    total_ready = sum(int(row["context_label_ready_pa"]) for row in coverage)
    overall_rate = total_ready / total_pa
    if overall_rate < 0.90:
        failures.append({"scope": "overall", "rate": overall_rate, "minimum": 0.90})
    for row in coverage:
        minimum = 0.85 if row["level_group"] == "rk" else 0.90
        rate = float(row["context_label_ready_rate"])
        if rate < minimum:
            failures.append(
                {
                    "scope": f"{row['season']}_{row['level_group']}",
                    "rate": rate,
                    "minimum": minimum,
                }
            )
    return not failures, failures


def main() -> int:
    args = _parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    matchup = pl.read_parquet(args.matchup_sidecar)
    player_games = pl.concat(
        [
            pl.read_parquet(args.player_game_2021_2023),
            pl.read_parquet(args.player_game_2024),
        ],
        how="vertical_relaxed",
    )
    label_frames: list[pl.DataFrame] = []
    provenance: list[dict[str, object]] = []
    for season in SEASONS:
        for level in LEVELS:
            frame, record = _milb_labels(
                season=season,
                level=level,
                raw_root=(
                    args.milb_2024_root if season == 2024 else args.historical_milb_root
                ),
                contact_root=args.contact_artifact_root,
            )
            label_frames.append(
                frame.with_columns(
                    pl.lit(season).alias("season"),
                    pl.lit(level).alias("level_group"),
                    pl.lit("ARMSTJC_PBP").alias("label_source_system"),
                )
            )
            provenance.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
        root = (
            args.mlb_2024_artifact_root
            if season == 2024
            else args.mlb_2021_2023_artifact_root
        )
        frame, record = _mlb_labels(season=season, artifact_root=root)
        label_frames.append(
            frame.with_columns(
                pl.lit(season).alias("season"),
                pl.lit("MLB").alias("level_group"),
                pl.lit("BASEBALL_SAVANT").alias("label_source_system"),
            )
        )
        provenance.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)

    labels = pl.concat(label_frames, how="vertical_relaxed")
    duplicate = labels.group_by(["season", "game_pk", "at_bat_index"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise RuntimeError("terminal labels are not globally unique at PA grain")
    labeled = matchup.join(
        labels.drop("level_group"),
        on=["season", "game_pk", "at_bat_index"],
        how="left",
        validate="1:1",
    )
    labeled, reconciliation = reconcile_terminal_pa_labels(labeled, player_games)
    if labeled.height != matchup.height:
        raise RuntimeError("terminal label join changed matchup-sidecar membership")
    if labeled.filter(pl.col("season") >= 2025).height:
        raise RuntimeError("terminal label sidecar crossed the 2021-2024 boundary")
    if labeled.filter(pl.col("context_label_ready") & pl.col("canonical_outcome").is_null()).height:
        raise RuntimeError("context-ready terminal label is null")

    coverage = _coverage(labeled)
    gate_passed, gate_failures = _gate(coverage)
    sidecar_artifact = write_canonical_parquet(
        labeled,
        args.report_root / "tables" / "hitter_v2_terminal_outcome_label_sidecar_2021_2024.parquet",
        table_name="hitter_v2_terminal_outcome_label_sidecar",
    ).as_record()
    reconciliation_artifact = write_canonical_parquet(
        reconciliation,
        args.report_root / "tables" / "hitter_v2_terminal_outcome_label_reconciliation_2021_2024.parquet",
        table_name="hitter_v2_terminal_outcome_label_reconciliation",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "gate": "source_only_terminal_outcome_label_sidecar_materialization_and_reconciliation",
        "accepted": gate_passed,
        "contract_sha256": sha256(
            Path("docs/hitter-v2-stage2d-development-contract.json").read_bytes()
        ).hexdigest(),
        "source_seasons": list(SEASONS),
        "taxonomy": list(TERMINAL_OUTCOMES),
        "forecast_targets_loaded": False,
        "candidate_implemented": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "source_provenance": provenance,
        "coverage_by_season_level": coverage,
        "gate_failures": gate_failures,
        "totals": {
            "sidecar_pa": labeled.height,
            "direct_labeled_pa": int(labeled["canonical_outcome"].is_not_null().sum()),
            "context_label_ready_pa": int(labeled["context_label_ready"].sum()),
            "exact_direct_label_player_games": reconciliation.filter(
                pl.col("context_label_reconciliation_status") == "exact_direct_labels"
            ).height,
            "failed_closed_player_games": reconciliation.filter(
                pl.col("context_label_reconciliation_status") != "exact_direct_labels"
            ).height,
        },
        "label_status_counts": (
            labeled.group_by(["label_status", "canonical_outcome"])
            .len(name="pa")
            .sort(["label_status", "canonical_outcome"])
            .to_dicts()
        ),
        "reconciliation_status": (
            reconciliation.group_by("context_label_reconciliation_status")
            .agg(
                pl.len().alias("player_games"),
                pl.col("sidecar_pa").fill_null(0).sum().alias("sidecar_pa"),
            )
            .sort("context_label_reconciliation_status")
            .to_dicts()
        ),
        "storage": {
            "sidecar": sidecar_artifact,
            "reconciliation": reconciliation_artifact,
        },
        "next_gate": (
            "review_label_gate_then_authorize_J0_implementation_only"
            if gate_passed
            else "stop_source_gate_failed_no_candidate_implementation"
        ),
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(report_path),
                "sha256": sha256(report_path.read_bytes()).hexdigest(),
                "accepted": gate_passed,
                "totals": report["totals"],
                "gate_failures": gate_failures,
            },
            indent=2,
        )
    )
    return 0 if gate_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
