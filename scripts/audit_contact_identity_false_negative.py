#!/usr/bin/env python
"""Test whether player-game contact controls miss hidden batter-ID errors.

The certified 2024 AAA localization policy flags games whose reusable PBP
player/contact counts disagree with reusable player-game boxscore counts.  That
catches the known armstjc pinch-runner batter overwrite, but in principle two
wrong attributions could cancel within a game and leave all player counts exact.

This audit samples games that the reusable control *does not* flag, fetches
current official PBP for that deterministic sample, and compares both physical
contact keys and official matchup-batter identity.  It is a certification gate,
not a production all-season official replay.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_official_contact_exceptions import (
    _load_player_games,
    _load_source_contacts,
    _official_contacts,
    _outer_contact_comparison,
)
from universal_baseball.official import fetch_official_game_evidence


REPORT_DIR = Path("reports/generated/contact-identity-false-negative")
SAMPLE_GAME_COUNT = 120


def _evenly_spaced_sample(values: list[int], n: int) -> list[int]:
    ordered = sorted(set(int(value) for value in values))
    if n <= 0 or not ordered:
        return []
    if len(ordered) <= n:
        return ordered
    if n == 1:
        return [ordered[len(ordered) // 2]]

    # Deterministic coverage across the entire season rather than the first N
    # game IDs.  The rounded indices are unique when n <= len(ordered).
    indices = [round(i * (len(ordered) - 1) / (n - 1)) for i in range(n)]
    return [ordered[index] for index in indices]


def _compare_contacts(
    source_contacts: pl.DataFrame,
    official_contacts: pl.DataFrame,
) -> pl.DataFrame:
    key = ["game_id", "at_bat_index", "pitch_number"]
    source = source_contacts.select(
        pl.col("game_pk").cast(pl.Int64).alias("game_id"),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("source_batter_id").cast(pl.Int64, strict=False),
    ).with_columns(pl.lit(True).alias("source_present"))
    official = official_contacts.select(
        pl.col("game_id").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("official_batter_id").cast(pl.Int64, strict=False),
    ).with_columns(pl.lit(True).alias("official_present"))

    return (
        source.join(official, on=key, how="full", coalesce=True)
        .with_columns(
            pl.col("source_present").fill_null(False),
            pl.col("official_present").fill_null(False),
        )
        .with_columns(
            pl.when(pl.col("source_present") & pl.col("official_present"))
            .then(pl.lit("both"))
            .when(pl.col("source_present"))
            .then(pl.lit("source_only"))
            .otherwise(pl.lit("official_only"))
            .alias("key_presence"),
            (
                pl.col("source_present")
                & pl.col("official_present")
                & (pl.col("source_batter_id") != pl.col("official_batter_id"))
            ).alias("batter_mismatch"),
        )
        .sort(key)
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    contacts, source_metrics = _load_source_contacts()
    player_games, player_game_metrics = _load_player_games()
    if source_metrics["contact_status_conflict_key_count"]:
        raise RuntimeError("source contact-status conflicts block false-negative audit")
    if source_metrics["unresolved_contact_batter_count"]:
        raise RuntimeError("unresolved source contact batter blocks false-negative audit")
    if player_game_metrics["unresolved_expected_contact_player_game_count"]:
        raise RuntimeError("unresolved player-game counts block false-negative audit")

    observed = (
        contacts.select(
            pl.col("game_pk").alias("game_id"),
            pl.col("source_batter_id").alias("player_id"),
        )
        .group_by(["game_id", "player_id"])
        .len(name="source_contact_count")
    )
    expected = player_games.select(
        "game_id", "player_id", "expected_contact_count"
    ).filter(pl.col("expected_contact_count").is_not_null())
    comparison = _outer_contact_comparison(observed, expected)

    flagged_games = set(
        int(value)
        for value in comparison.filter(pl.col("difference") != 0)
        .get_column("game_id")
        .unique()
        .to_list()
    )
    all_contact_games = sorted(
        int(value) for value in contacts.get_column("game_pk").unique().to_list()
    )
    unflagged_games = [game for game in all_contact_games if game not in flagged_games]
    sample_games = _evenly_spaced_sample(unflagged_games, SAMPLE_GAME_COUNT)
    if not sample_games:
        raise RuntimeError("no unflagged games available for false-negative audit")

    official_pa, official_pitch = fetch_official_game_evidence(sample_games)
    official_contacts = _official_contacts(official_pa, official_pitch)
    fetched_games = sorted(
        int(value)
        for value in official_pa.get_column("game_pk").cast(pl.Int64).unique().to_list()
    )

    source_sample = contacts.filter(pl.col("game_pk").is_in(sample_games))
    key_comparison = _compare_contacts(source_sample, official_contacts)
    source_only = key_comparison.filter(pl.col("key_presence") == "source_only")
    official_only = key_comparison.filter(pl.col("key_presence") == "official_only")
    batter_mismatches = key_comparison.filter(pl.col("batter_mismatch") == True)  # noqa: E712

    flagged_rows = key_comparison.filter(
        (pl.col("key_presence") != "both")
        | (pl.col("batter_mismatch") == True)  # noqa: E712
    )
    flagged_rows.write_csv(REPORT_DIR / "unexpected_contact_differences.csv")

    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "level": "aaa",
        "sample_design": "deterministic evenly spaced unflagged games",
        "requested_sample_game_count": SAMPLE_GAME_COUNT,
        "source_contact_game_count": len(all_contact_games),
        "reusable_control_flagged_game_count": len(flagged_games),
        "unflagged_game_count": len(unflagged_games),
        "sample_game_count": len(sample_games),
        "sample_game_ids": sample_games,
        "official_fetched_game_count": len(fetched_games),
        "source_sample_contact_count": source_sample.height,
        "official_sample_contact_count": official_contacts.height,
        "matched_physical_contact_key_count": key_comparison.filter(
            pl.col("key_presence") == "both"
        ).height,
        "source_only_physical_contact_key_count": source_only.height,
        "official_only_physical_contact_key_count": official_only.height,
        "matched_key_batter_mismatch_count": batter_mismatches.height,
        "batter_mismatch_game_count": batter_mismatches.get_column("game_id").n_unique(),
        "interpretation": (
            "A zero-mismatch result supports player-game residuals as a high-recall "
            "trigger for targeted official participant overlays. It does not prove a "
            "mathematical impossibility of cancelling attribution errors outside the sample."
        ),
    }
    (REPORT_DIR / "contact_identity_false_negative.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Contact identity false-negative audit — 2024 AAA",
        "",
        f"- Source contact games: {len(all_contact_games):,}",
        f"- Games flagged by reusable player-game residuals: {len(flagged_games):,}",
        f"- Unflagged games: {len(unflagged_games):,}",
        f"- Deterministic unflagged sample: {len(sample_games):,}",
        f"- Official PBP returned: {len(fetched_games):,}/{len(sample_games):,}",
        f"- Source / official contacts: {source_sample.height:,} / {official_contacts.height:,}",
        f"- Source-only / official-only physical keys: {source_only.height:,} / {official_only.height:,}",
        f"- Matched contact keys with batter mismatch: {batter_mismatches.height:,}",
        f"- Batter-mismatch games: {batter_mismatches.get_column('game_id').n_unique():,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "contact_identity_false_negative.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)

    if fetched_games != sample_games:
        raise RuntimeError("official PBP did not return every sampled unflagged game")
    if source_only.height or official_only.height:
        raise RuntimeError("physical contact-key mismatch in unflagged sample")
    if batter_mismatches.height:
        raise RuntimeError("hidden batter-attribution mismatch found in unflagged sample")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
