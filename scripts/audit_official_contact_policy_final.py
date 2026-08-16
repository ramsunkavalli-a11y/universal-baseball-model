#!/usr/bin/env python
"""Final 2024 AAA gate for an exception-only official contact overlay.

The preceding discovery work showed that player-game boxscore controls can
localize sparse PBP batter-attribution defects, but a seemingly unambiguous
+1/-1 source-only reassignment was wrong in 1 of 182 cases. This gate therefore
certifies the safer production policy rather than attempting another heuristic:

1. build the reusable-source contact set and player-game controls;
2. flag every game with any player-game contact residual;
3. fetch official PBP only for that flagged game set;
4. verify physical contact-key coverage across the entire flagged set;
5. treat official matchup batter as participant authority for those games; and
6. isolate residual differences between official ``isInPlay`` semantics and
   boxscore-style AB-SO+SF+SH contact accounting instead of forcing equality.

This is a certification script, not a permanent all-season official backfill.
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
from universal_baseball.official import (
    fetch_official_game_evidence,
    fetch_official_team_batting,
)
from universal_baseball.player_game_stats import (
    identify_unambiguous_contact_reassignments,
)


REPORT_DIR = Path("reports/generated/official-contact-policy-final")


def _physical_key_comparison(
    source_contacts: pl.DataFrame,
    official_contacts: pl.DataFrame,
) -> pl.DataFrame:
    key = ["game_id", "at_bat_index", "pitch_number"]
    source = (
        source_contacts.select(
            pl.col("game_pk").alias("game_id"),
            "at_bat_index",
            "pitch_number",
            "source_batter_id",
        )
        .with_columns(pl.lit(True).alias("source_present"))
    )
    official = (
        official_contacts.select(
            key + ["official_batter_id", "pa_event_type", "pitch_event_type"]
        )
        .with_columns(pl.lit(True).alias("official_present"))
    )
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
            ).alias("source_batter_mismatch"),
        )
        .sort(key)
    )


def _official_player_game_comparison(
    official_contacts: pl.DataFrame,
    expected: pl.DataFrame,
) -> pl.DataFrame:
    official_by_player = (
        official_contacts.group_by(["game_id", "official_batter_id"])
        .len(name="official_contact_count")
        .rename({"official_batter_id": "player_id"})
    )
    return _outer_contact_comparison(
        official_by_player,
        expected,
        observed_column="official_contact_count",
    )


def _edge_case_pa_rows(
    pa_frame: pl.DataFrame,
    official_contacts: pl.DataFrame,
    residuals: pl.DataFrame,
) -> pl.DataFrame:
    """Return scalar-only diagnostic rows for player-game count residuals.

    The earlier version retained a nested list of pitch-event types. That is
    useful interactively but invalid for CSV output, and in all-null groups
    Polars infers ``list[null]`` which cannot be safely joined as strings. The
    diagnostic only needs to know whether a PA has an official in-play pitch;
    physical-key details are already written separately.
    """

    residual_pairs = residuals.select("game_id", "player_id", "difference")
    contact_by_pa = official_contacts.group_by(["game_id", "at_bat_index"]).agg(
        pl.len().alias("official_in_play_pitch_count")
    )
    return (
        pa_frame.select(
            pl.col("game_pk").cast(pl.Int64, strict=False).alias("game_id"),
            pl.col("at_bat_number").cast(pl.Int64, strict=False).alias("at_bat_index"),
            pl.col("batter_id").alias("player_id"),
            "event_type",
            "event",
            "description",
            "official_pitch_count",
        )
        .drop_nulls(["game_id", "at_bat_index", "player_id"])
        .join(contact_by_pa, on=["game_id", "at_bat_index"], how="left")
        .with_columns(
            pl.col("official_in_play_pitch_count").fill_null(0),
            (pl.col("official_in_play_pitch_count").fill_null(0) > 0).alias(
                "has_official_in_play_pitch"
            ),
        )
        .join(residual_pairs, on=["game_id", "player_id"], how="inner")
        .sort(["game_id", "player_id", "at_bat_index"])
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    contacts, source_metrics = _load_source_contacts()
    player_games, player_game_metrics = _load_player_games()
    if source_metrics["contact_status_conflict_key_count"]:
        raise RuntimeError("source contact-status conflicts block final policy audit")
    if source_metrics["unresolved_contact_batter_count"]:
        raise RuntimeError("source contact batter consensus unresolved")
    if player_game_metrics["unresolved_expected_contact_player_game_count"]:
        raise RuntimeError("player-game expected contacts unresolved")

    source_by_game_player = (
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
    source_comparison = _outer_contact_comparison(source_by_game_player, expected)
    flagged_games = sorted(
        int(v)
        for v in source_comparison.filter(pl.col("difference") != 0)
        .get_column("game_id")
        .unique()
        .to_list()
    )

    # Retain the earlier heuristic only as evidence about why it is not safe
    # enough to mutate production data automatically.
    heuristic_repairs = identify_unambiguous_contact_reassignments(source_comparison)

    official_pa, official_pitch = fetch_official_game_evidence(flagged_games)
    official_contacts = _official_contacts(official_pa, official_pitch)
    fetched_games = sorted(
        int(v)
        for v in official_pa.get_column("game_pk").cast(pl.Int64).unique().to_list()
    )

    source_flagged = contacts.filter(pl.col("game_pk").is_in(flagged_games))
    key_comparison = _physical_key_comparison(source_flagged, official_contacts)
    source_only = key_comparison.filter(pl.col("key_presence") == "source_only")
    official_only = key_comparison.filter(pl.col("key_presence") == "official_only")
    both = key_comparison.filter(pl.col("key_presence") == "both")
    batter_mismatches = both.filter(pl.col("source_batter_mismatch") == True)  # noqa: E712

    expected_flagged = expected.filter(pl.col("game_id").is_in(flagged_games))
    official_vs_player_game = _official_player_game_comparison(
        official_contacts, expected_flagged
    )
    residuals = official_vs_player_game.filter(pl.col("difference") != 0).sort(
        ["game_id", "player_id"]
    )
    edge_pa_rows = _edge_case_pa_rows(official_pa, official_contacts, residuals)

    official_boxscore = fetch_official_team_batting(flagged_games)
    boxscore_contacts = (
        official_boxscore.with_columns(
            (
                pl.col("at_bats")
                - pl.col("strikeouts")
                + pl.col("sac_bunts")
                + pl.col("sac_flies")
            ).alias("boxscore_contact_count")
        )
        .group_by("game_pk")
        .agg(pl.col("boxscore_contact_count").sum())
        .with_columns(pl.col("game_pk").cast(pl.Int64).alias("game_id"))
        .drop("game_pk")
    )
    pbp_contacts_by_game = official_contacts.group_by("game_id").len(
        name="official_pbp_contact_count"
    )
    definition_by_game = (
        pbp_contacts_by_game.join(
            boxscore_contacts, on="game_id", how="full", coalesce=True
        )
        .with_columns(
            pl.col("official_pbp_contact_count").fill_null(0),
            pl.col("boxscore_contact_count").fill_null(0),
        )
        .with_columns(
            (
                pl.col("official_pbp_contact_count")
                - pl.col("boxscore_contact_count")
            ).alias("difference")
        )
        .sort("game_id")
    )
    definition_residuals = definition_by_game.filter(pl.col("difference") != 0)

    edge_summary = (
        edge_pa_rows.group_by(
            ["difference", "event_type", "has_official_in_play_pitch"]
        )
        .agg(pl.len().alias("pa_count"))
        .sort(["difference", "pa_count"], descending=[False, True])
    )

    key_comparison.filter(
        (pl.col("key_presence") != "both")
        | (pl.col("source_batter_mismatch") == True)  # noqa: E712
    ).write_csv(REPORT_DIR / "flagged_source_vs_official_contact_keys.csv")
    residuals.write_csv(REPORT_DIR / "official_vs_player_game_residuals.csv")
    edge_pa_rows.write_csv(REPORT_DIR / "contact_definition_residual_player_pas.csv")
    edge_summary.write_csv(REPORT_DIR / "contact_definition_residual_event_summary.csv")
    definition_residuals.write_csv(
        REPORT_DIR / "official_pbp_vs_boxscore_contact_definition.csv"
    )

    source_flagged_total = source_flagged.height
    official_total = official_contacts.height
    boxscore_total = int(boxscore_contacts.get_column("boxscore_contact_count").sum() or 0)
    positive_residual = int(
        residuals.select(
            pl.when(pl.col("difference") > 0)
            .then(pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )
    negative_residual = int(
        residuals.select(
            pl.when(pl.col("difference") < 0)
            .then(-pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )

    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "level": "aaa",
        "game_type": "R",
        "source": source_metrics,
        "player_game": player_game_metrics,
        "flagging": {
            "source_player_game_residual_game_count": len(flagged_games),
            "source_player_game_residual_game_ids": flagged_games,
            "diagnostic_strict_reassignment_count": heuristic_repairs.height,
            "production_automatic_source_reassignment": False,
            "reason": (
                "Independent official certification contradicted 1 of 182 otherwise "
                "strict +1/-1 source-only reassignment candidates."
            ),
        },
        "official_exception_overlay": {
            "target_game_count": len(flagged_games),
            "fetched_game_count": len(fetched_games),
            "source_contact_count": source_flagged_total,
            "official_contact_count": official_total,
            "net_source_minus_official": source_flagged_total - official_total,
            "matched_physical_contact_key_count": both.height,
            "source_only_physical_contact_key_count": source_only.height,
            "official_only_physical_contact_key_count": official_only.height,
            "matched_key_source_batter_mismatch_count": batter_mismatches.height,
        },
        "official_vs_reusable_player_game_after_overlay": {
            "nonzero_player_game_count": residuals.height,
            "mismatch_game_count": residuals.get_column("game_id").n_unique(),
            "positive_residual_mass": positive_residual,
            "negative_residual_mass": negative_residual,
            "net_residual_mass": positive_residual - negative_residual,
            "absolute_residual_mass": positive_residual + negative_residual,
        },
        "official_contact_definition": {
            "official_pbp_contact_total": official_total,
            "official_boxscore_contact_total": boxscore_total,
            "pbp_minus_boxscore_total": official_total - boxscore_total,
            "mismatch_game_count": definition_residuals.height,
        },
        "production_policy": (
            "For contact-profile participant identity, use certified reusable PBP by "
            "default. Resolve player-game boxscore snapshots conservatively and compare "
            "source player-game contact counts against them. If any player residual exists "
            "in a game, fetch official PBP for that game and overlay the official matchup "
            "batter on the matching physical contact keys. Do not auto-apply inferred "
            "+1/-1 player reassignments. Preserve official PBP-vs-boxscore semantic "
            "differences instead of forcing AB-SO+SF+SH equality."
        ),
    }
    (REPORT_DIR / "official_contact_policy_final.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Final exception-only contact policy audit — 2024 AAA",
        "",
        f"- Games flagged by reusable player-game control: {len(flagged_games):,}",
        f"- Official PBP returned: {len(fetched_games):,}/{len(flagged_games):,}",
        f"- Source contacts in flagged games: {source_flagged_total:,}",
        f"- Official contacts in flagged games: {official_total:,}",
        f"- Source-only physical contact keys: {source_only.height:,}",
        f"- Official-only physical contact keys: {official_only.height:,}",
        f"- Matched keys with source batter mismatch: {batter_mismatches.height:,}",
        "",
        "## After official participant overlay",
        "",
        f"- Remaining player-game residual rows: {residuals.height:,}",
        f"- Remaining residual games: {residuals.get_column('game_id').n_unique():,}",
        f"- Positive/negative residual mass: +{positive_residual:,}/-{negative_residual:,}",
        "",
        "## Contact-definition semantics",
        "",
        f"- Official PBP in-play contacts: {official_total:,}",
        f"- Official boxscore AB-SO+SF+SH contacts: {boxscore_total:,}",
        f"- PBP minus boxscore: {official_total - boxscore_total:+,}",
        f"- Games with semantic count difference: {definition_residuals.height:,}",
        "",
        "The 181/182 repair heuristic is diagnostic only. Production flags the game and uses official participant identity rather than guessing the recipient.",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "official_contact_policy_final.md").write_text(summary, encoding="utf-8")
    print(summary)

    if fetched_games != flagged_games:
        raise RuntimeError("official PBP did not return every flagged game")
    if source_only.height or official_only.height:
        raise RuntimeError(
            "reusable and official physical contact-key sets differ in flagged games"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
