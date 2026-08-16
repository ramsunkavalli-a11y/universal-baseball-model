#!/usr/bin/env python
"""Certify play-sequence-grain official participant authority for 2024 AA/Rookie.

The stricter current-official ``isInPlay`` pitch-key overlay fails on a handful
of AA/Rookie games because current official contact coding can differ from the
historical reusable source. Participant identity does not require that equality:
the authoritative batter is the top-level matchup batter for the play sequence.

This audit asks the narrower production question: for every reusable contact
sequence in every player-game-residual exception game, does current official
allPlays evidence contain exactly one unambiguous matchup batter at the same
``game_pk + at_bat_index`` key?
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
    project_official_sequence_authority,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_level_config import performance_level_spec_2024
from universal_baseball.player_game_controls import resolve_player_game_contact_controls


base.resolve_player_game_batting = resolve_player_game_contact_controls
REPORT_ROOT = Path("reports/generated/contact-sequence-authority")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, choices=("aa", "rk"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = performance_level_spec_2024(args.level)
    slug = args.level.replace("+", "plus")
    work_dir = Path("data/quarantine/contact-sequence-authority") / slug
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
        raise RuntimeError("sequence-authority audit expected exception games")

    pa, _pitch = fetch_official_game_evidence(exception_games)
    authority = project_official_sequence_authority(pa)

    source_contacts = contacts.filter(pl.col("game_pk").is_in(exception_games))
    source_sequences = source_contacts.select("game_pk", "at_bat_index").unique()
    authority_for_games = authority.filter(pl.col("game_pk").is_in(exception_games))
    joined_sequences = source_sequences.join(
        authority_for_games,
        on=["game_pk", "at_bat_index"],
        how="left",
    )
    missing_authority = joined_sequences.filter(pl.col("official_batter_id").is_null())

    contact_identity = source_contacts.join(
        authority_for_games,
        on=["game_pk", "at_bat_index"],
        how="left",
    ).with_columns(
        (
            pl.col("source_batter_id").cast(pl.Int64)
            != pl.col("official_batter_id").cast(pl.Int64)
        ).alias("source_batter_differs")
    )
    batter_drift = contact_identity.filter(pl.col("source_batter_differs"))

    official_game_ids = sorted(
        int(value)
        for value in authority_for_games.get_column("game_pk").unique().to_list()
    )
    missing_games = sorted(set(exception_games) - set(official_game_ids))

    missing_authority.write_csv(report_dir / "source_contact_sequences_without_authority.csv")
    batter_drift.select(
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "source_batter_id",
        "official_batter_id",
    ).write_csv(report_dir / "source_contact_batter_drift.csv")

    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "league_ids": sorted(spec.league_ids),
        "source_metrics": source_metrics,
        "player_game_metrics": player_game_metrics,
        "exception_game_count": len(exception_games),
        "official_authority_game_count": len(official_game_ids),
        "missing_official_authority_game_count": len(missing_games),
        "missing_official_authority_game_ids": missing_games,
        "source_exception_contact_count": source_contacts.height,
        "source_exception_sequence_count": source_sequences.height,
        "official_allplay_sequence_count_in_exception_games": authority_for_games.height,
        "covered_source_contact_sequence_count": joined_sequences.filter(
            pl.col("official_batter_id").is_not_null()
        ).height,
        "missing_source_contact_sequence_count": missing_authority.height,
        "source_contact_rows_with_batter_drift": batter_drift.height,
        "source_contact_batter_drift_game_count": batter_drift.get_column("game_pk").n_unique(),
        "authority_grain": "game_pk + at_bat_index",
        "interpretation": (
            "Participant overlay is valid if every reusable source contact sequence in "
            "every residual-triggered game maps to one official top-level matchup batter. "
            "Current official isInPlay pitch identity is not required to reproduce the "
            "historical source contact row."
        ),
    }
    (report_dir / "contact_sequence_authority.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        f"# Contact sequence authority — 2024 {spec.display_name}",
        "",
        f"- Exception games: {len(exception_games):,}",
        f"- Official authority games: {len(official_game_ids):,}",
        f"- Source contact rows / distinct sequences: {source_contacts.height:,} / {source_sequences.height:,}",
        f"- Source contact sequences covered by official matchup authority: {joined_sequences.filter(pl.col('official_batter_id').is_not_null()).height:,}/{source_sequences.height:,}",
        f"- Missing source contact sequence authority: {missing_authority.height:,}",
        f"- Source contact rows whose batter changes under authority: {batter_drift.height:,}",
        f"- Batter-drift games: {batter_drift.get_column('game_pk').n_unique():,}",
    ]
    summary = "\n".join(lines)
    (report_dir / "contact_sequence_authority.md").write_text(summary, encoding="utf-8")
    print(summary)

    if missing_games:
        raise RuntimeError("official allPlays authority missing exception games")
    if missing_authority.height:
        raise RuntimeError("official matchup authority misses reusable contact sequences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
