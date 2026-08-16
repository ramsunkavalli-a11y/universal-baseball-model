#!/usr/bin/env python
"""Diagnose exact contact-key mismatches in 2024 AA / Rookie exception games.

High-A and Single-A pass the strict ADR 020 pitch-key overlay unchanged. AA and
Rookie/complex do not. This audit asks whether the discrepancy is only
``pitch_number`` drift while the lossless play-sequence contact key
``game_pk + at_bat_index`` remains exact.

No production join is changed here. The audit fails loudly on duplicate in-play
contacts within a sequence or any sequence-level source/official coverage gap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

import build_batting_performance_level_poc as base
from universal_baseball.contact_identity_overlay import (
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_contact_authority,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_level_config import performance_level_spec_2024
from universal_baseball.player_game_controls import resolve_player_game_contact_controls


base.resolve_player_game_batting = resolve_player_game_contact_controls
REPORT_ROOT = Path("reports/generated/contact-key-alignment")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, choices=("aa", "rk"))
    return parser.parse_args()


def _duplicate_sequence_count(frame: pl.DataFrame) -> int:
    return frame.group_by(["game_pk", "at_bat_index"]).len().filter(
        pl.col("len") > 1
    ).height


def main() -> int:
    args = parse_args()
    spec = performance_level_spec_2024(args.level)
    slug = args.level.replace("+", "plus")
    work_dir = Path("data/quarantine/contact-key-alignment") / slug
    report_dir = REPORT_ROOT / slug
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    contacts, source_metrics = base._load_reusable_contacts(
        spec.filename_level, spec.league_ids, work_dir
    )
    player_games, player_game_metrics = base._load_player_game_controls(
        spec.filename_level, spec.league_ids, work_dir
    )
    residuals = contact_identity_residuals(contacts, player_games)
    exception_games = exception_games_from_residuals(residuals)
    if not exception_games:
        raise RuntimeError("diagnostic expected at least one exception game")

    pa, pitch = fetch_official_game_evidence(exception_games)
    official = project_official_contact_authority(pa, pitch)
    source = contacts.filter(pl.col("game_pk").is_in(exception_games)).select(
        "game_pk", "at_bat_index", "pitch_number", "source_batter_id"
    )

    source_duplicate_sequences = _duplicate_sequence_count(source)
    official_duplicate_sequences = _duplicate_sequence_count(official)

    exact_key = ["game_pk", "at_bat_index", "pitch_number"]
    sequence_key = ["game_pk", "at_bat_index"]
    source_only_exact = source.join(
        official.select(exact_key), on=exact_key, how="anti"
    )
    official_only_exact = official.join(
        source.select(exact_key), on=exact_key, how="anti"
    )

    source_sequences = source.select(sequence_key).unique()
    official_sequences = official.select(sequence_key).unique()
    source_only_sequence = source_sequences.join(
        official_sequences, on=sequence_key, how="anti"
    )
    official_only_sequence = official_sequences.join(
        source_sequences, on=sequence_key, how="anti"
    )

    sequence_matches = source.join(
        official,
        on=sequence_key,
        how="inner",
        suffix="_official",
    ).with_columns(
        (pl.col("pitch_number") != pl.col("pitch_number_official")).alias(
            "pitch_number_differs"
        ),
        (
            pl.col("source_batter_id") != pl.col("official_batter_id")
        ).alias("batter_differs"),
        (pl.col("pitch_number") - pl.col("pitch_number_official")).alias(
            "pitch_number_delta"
        ),
    )

    pitch_number_drift = sequence_matches.filter(pl.col("pitch_number_differs"))
    batter_drift = sequence_matches.filter(pl.col("batter_differs"))
    exact_mismatch_games = sorted(
        set(int(v) for v in source_only_exact.get_column("game_pk").to_list())
        | set(int(v) for v in official_only_exact.get_column("game_pk").to_list())
    )
    sequence_mismatch_games = sorted(
        set(int(v) for v in source_only_sequence.get_column("game_pk").to_list())
        | set(int(v) for v in official_only_sequence.get_column("game_pk").to_list())
    )

    mismatch_rows = sequence_matches.filter(
        pl.col("pitch_number_differs") | pl.col("batter_differs")
    ).sort(["game_pk", "at_bat_index"])
    mismatch_rows.write_csv(report_dir / "sequence_matched_differences.csv")
    source_only_exact.write_csv(report_dir / "source_only_exact_pitch_keys.csv")
    official_only_exact.write_csv(report_dir / "official_only_exact_pitch_keys.csv")
    source_only_sequence.write_csv(report_dir / "source_only_sequence_keys.csv")
    official_only_sequence.write_csv(report_dir / "official_only_sequence_keys.csv")

    delta_distribution = {
        str(int(row["pitch_number_delta"])): int(row["len"])
        for row in pitch_number_drift.group_by("pitch_number_delta")
        .len()
        .sort("pitch_number_delta")
        .to_dicts()
    }
    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "league_ids": sorted(spec.league_ids),
        "source_metrics": source_metrics,
        "player_game_metrics": player_game_metrics,
        "exception_game_count": len(exception_games),
        "source_exception_contact_count": source.height,
        "official_exception_contact_count": official.height,
        "source_duplicate_contact_sequence_count": source_duplicate_sequences,
        "official_duplicate_contact_sequence_count": official_duplicate_sequences,
        "source_only_exact_pitch_key_count": source_only_exact.height,
        "official_only_exact_pitch_key_count": official_only_exact.height,
        "exact_pitch_key_mismatch_game_count": len(exact_mismatch_games),
        "exact_pitch_key_mismatch_game_ids": exact_mismatch_games,
        "source_only_sequence_key_count": source_only_sequence.height,
        "official_only_sequence_key_count": official_only_sequence.height,
        "sequence_key_mismatch_game_count": len(sequence_mismatch_games),
        "sequence_key_mismatch_game_ids": sequence_mismatch_games,
        "sequence_matched_contact_count": sequence_matches.height,
        "sequence_matches_with_pitch_number_drift": pitch_number_drift.height,
        "pitch_number_delta_distribution": delta_distribution,
        "sequence_matches_with_batter_drift": batter_drift.height,
        "interpretation": (
            "Sequence-grain overlay is eligible for consideration only if both sources "
            "have at most one in-play contact per sequence and source/official sequence "
            "sets are exactly equal across every exception game."
        ),
    }
    (report_dir / "contact_key_alignment.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        f"# Contact key alignment — 2024 {spec.display_name}",
        "",
        f"- Exception games: {len(exception_games):,}",
        f"- Source / official contacts: {source.height:,} / {official.height:,}",
        f"- Duplicate contact sequences source / official: {source_duplicate_sequences:,} / {official_duplicate_sequences:,}",
        f"- Source-only / official-only exact pitch keys: {source_only_exact.height:,} / {official_only_exact.height:,}",
        f"- Exact-key mismatch games: {len(exact_mismatch_games):,}",
        f"- Source-only / official-only sequence keys: {source_only_sequence.height:,} / {official_only_sequence.height:,}",
        f"- Sequence-key mismatch games: {len(sequence_mismatch_games):,}",
        f"- Sequence matches with pitch-number drift: {pitch_number_drift.height:,}",
        f"- Sequence matches with batter drift: {batter_drift.height:,}",
        f"- Pitch-number delta distribution: {delta_distribution}",
    ]
    summary = "\n".join(lines)
    (report_dir / "contact_key_alignment.md").write_text(summary, encoding="utf-8")
    print(summary)

    if source_duplicate_sequences or official_duplicate_sequences:
        raise RuntimeError("multiple in-play contacts found within a play sequence")
    if source_only_sequence.height or official_only_sequence.height:
        raise RuntimeError("source and official contact sequence sets differ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
