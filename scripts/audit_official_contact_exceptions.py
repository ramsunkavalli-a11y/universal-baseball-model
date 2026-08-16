#!/usr/bin/env python
"""Adjudicate sparse 2024 AAA contact-identity exceptions with official PBP.

This gate runs *after* reusable-source localization.  It deliberately avoids an
all-season official replay:

* armstjc PBP and player-game release files identify the sparse candidate set;
* deterministic +1/-1 zero-contact reassignments are derived source-side;
* official MLB PBP is fetched only for candidate exception games plus the games
  containing those deterministic repairs, so the repair rule itself is
  independently certified once;
* current official team boxscores are fetched only for unresolved exception
  games to distinguish participant drift from contact-definition drift.

Production policy can therefore remain reuse-first: apply a certified local
repair when the source-only rule is mathematically unique, and reserve official
PBP for the remaining exception queue.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official import (
    fetch_official_game_evidence,
    fetch_official_team_batting,
)
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    identify_unambiguous_contact_reassignments,
    project_player_game_batting,
    resolve_player_game_batting,
)


SEASON = 2024
LEVEL = "aaa"
GAME_TYPE = "R"
IN_PLAY_CODES = ("D", "E", "X")
PITCH_KEY = ["game_pk", "at_bat_index", "pitch_number"]
LOCALIZATION_WORK_DIR = Path("data/quarantine/player-game-contact-localization")
REPORT_DIR = Path("reports/generated/official-contact-exceptions")


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def _project_pbp_asset(frame: pl.DataFrame, asset_name: str) -> pl.DataFrame:
    required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "batter",
        "game_date",
        "game_type",
        "type",
        "bb_type",
        "hit_location",
        "hc_x",
        "hc_y",
        "hit_distance_sc",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{asset_name} missing contact-localization fields: {missing}")

    contact_evidence = (
        pl.col("type").cast(pl.String).str.strip_chars().is_in(IN_PLAY_CODES)
        | _nonblank("bb_type")
        | _nonblank("hit_location")
        | _nonblank("hc_x")
        | _nonblank("hc_y")
        | _nonblank("hit_distance_sc")
        | _nonblank("launch_speed")
        | _nonblank("launch_angle")
    )
    return (
        frame.select(
            _int_expr("game_pk"),
            _int_expr("at_bat_number", "at_bat_index"),
            _int_expr("pitch_number"),
            _int_expr("batter", "source_batter_id"),
            pl.col("game_date").cast(pl.String),
            pl.col("game_type").cast(pl.String),
            contact_evidence.alias("source_is_in_play"),
            pl.lit(asset_name).alias("source_asset"),
        )
        .drop_nulls(PITCH_KEY)
        .filter(
            (pl.col("game_type") == GAME_TYPE)
            & pl.col("game_date").str.starts_with(f"{SEASON}-")
        )
    )


def _resolve_pbp_contacts(observations: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, int]]:
    resolved = (
        observations.group_by(PITCH_KEY)
        .agg(
            pl.col("source_batter_id")
            .drop_nulls()
            .n_unique()
            .alias("batter_value_count"),
            pl.when(pl.col("source_batter_id").drop_nulls().n_unique() <= 1)
            .then(pl.col("source_batter_id").drop_nulls().first())
            .otherwise(None)
            .alias("source_batter_id"),
            pl.col("source_is_in_play").n_unique().alias("in_play_value_count"),
            pl.when(pl.col("source_is_in_play").n_unique() <= 1)
            .then(pl.col("source_is_in_play").first())
            .otherwise(None)
            .alias("source_is_in_play"),
            pl.col("source_asset").n_unique().alias("source_snapshot_count"),
        )
        .sort(PITCH_KEY)
    )
    contact_status_conflicts = resolved.filter(pl.col("in_play_value_count") > 1).height
    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    unresolved_batter = contacts.filter(pl.col("source_batter_id").is_null()).height
    return contacts, {
        "resolved_pitch_key_count": resolved.height,
        "source_contact_count": contacts.height,
        "contact_status_conflict_key_count": contact_status_conflicts,
        "unresolved_contact_batter_count": unresolved_batter,
    }


def _load_source_contacts() -> tuple[pl.DataFrame, dict[str, Any]]:
    LOCALIZATION_WORK_DIR.mkdir(parents=True, exist_ok=True)
    assets = [
        asset
        for asset in fetch_pbp_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    frames: list[pl.DataFrame] = []
    downloaded = 0
    reused = 0
    for asset in assets:
        path = LOCALIZATION_WORK_DIR / asset.name
        if path.exists() and path.stat().st_size > 0:
            reused += 1
        else:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
            downloaded += 1
        raw = read_quarantined_csv(path)
        frames.append(_project_pbp_asset(raw, asset.name))
        del raw
    observations = pl.concat(frames, how="vertical_relaxed")
    contacts, metrics = _resolve_pbp_contacts(observations)
    return contacts, {
        "asset_count": len(assets),
        "reused_local_asset_count": reused,
        "downloaded_asset_count": downloaded,
        "raw_projected_observation_count": observations.height,
        **metrics,
    }


def _load_player_games() -> tuple[pl.DataFrame, dict[str, int]]:
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = LOCALIZATION_WORK_DIR / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        frames.append(
            project_player_game_batting(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type=GAME_TYPE,
            )
        )
        del raw
    observations = pl.concat(frames, how="vertical_relaxed")
    return resolve_player_game_batting(observations)


def _outer_contact_comparison(
    observed_by_game_player: pl.DataFrame,
    expected_by_game_player: pl.DataFrame,
    *,
    observed_column: str = "source_contact_count",
) -> pl.DataFrame:
    return (
        observed_by_game_player.join(
            expected_by_game_player,
            on=["game_id", "player_id"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            pl.col(observed_column).fill_null(0).cast(pl.Int64),
            pl.col("expected_contact_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (pl.col(observed_column) - pl.col("expected_contact_count")).alias(
                "difference"
            )
        )
        .filter(
            (pl.col(observed_column) > 0) | (pl.col("expected_contact_count") > 0)
        )
        .sort(["game_id", "difference", "player_id"], descending=[False, True, False])
    )


def _residual_metrics(comparison: pl.DataFrame) -> dict[str, Any]:
    nonzero = comparison.filter(pl.col("difference") != 0)
    positive = int(
        comparison.select(
            pl.when(pl.col("difference") > 0)
            .then(pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )
    negative = int(
        comparison.select(
            pl.when(pl.col("difference") < 0)
            .then(-pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )
    return {
        "active_player_game_count": comparison.height,
        "nonzero_player_game_count": nonzero.height,
        "mismatch_game_count": nonzero.get_column("game_id").n_unique(),
        "positive_residual_mass": positive,
        "negative_residual_mass": negative,
        "absolute_discrepancy_mass": positive + negative,
        "residual_mass_imbalance": positive - negative,
        "difference_distribution": dict(
            sorted(Counter(int(v) for v in nonzero.get_column("difference")).items())
        ),
    }


def _official_contacts(
    pa_frame: pl.DataFrame,
    pitch_frame: pl.DataFrame,
) -> pl.DataFrame:
    pa_keys = (
        pa_frame.select(
            _int_expr("game_pk", "game_id"),
            _int_expr("at_bat_number", "at_bat_index"),
            pl.col("batter_id").cast(pl.Int64, strict=False).alias("official_batter_id"),
            pl.col("event_type").alias("pa_event_type"),
        )
        .drop_nulls(["game_id", "at_bat_index"])
        .unique(subset=["game_id", "at_bat_index"], keep="any")
    )
    contacts = (
        pitch_frame.filter(pl.col("is_in_play") == True)  # noqa: E712
        .select(
            _int_expr("game_pk", "game_id"),
            _int_expr("at_bat_number", "at_bat_index"),
            pl.col("pitch_number").cast(pl.Int64, strict=False),
            pl.col("event_type").alias("pitch_event_type"),
        )
        .drop_nulls(["game_id", "at_bat_index", "pitch_number"])
        .join(pa_keys, on=["game_id", "at_bat_index"], how="left")
    )
    return contacts.sort(["game_id", "at_bat_index", "pitch_number"])


def _key_comparison(source_contacts: pl.DataFrame, official_contacts: pl.DataFrame) -> pl.DataFrame:
    key = ["game_id", "at_bat_index", "pitch_number"]
    source = source_contacts.select(
        key
        + [
            "source_batter_id",
            "effective_batter_id",
        ]
    ).with_columns(pl.lit(True).alias("source_present"))
    official = official_contacts.select(
        key + ["official_batter_id", "pa_event_type"]
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
                & (pl.col("effective_batter_id") != pl.col("official_batter_id"))
            ).alias("batter_mismatch"),
        )
        .sort(key)
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    contacts, source_metrics = _load_source_contacts()
    player_games, player_game_metrics = _load_player_games()
    if source_metrics["contact_status_conflict_key_count"]:
        raise RuntimeError("source contact-status conflicts block official exception audit")
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
    expected_by_game_player = player_games.select(
        "game_id", "player_id", "expected_contact_count"
    ).filter(pl.col("expected_contact_count").is_not_null())

    source_comparison = _outer_contact_comparison(
        source_by_game_player, expected_by_game_player
    )
    repairs = identify_unambiguous_contact_reassignments(source_comparison)
    repair_contact_keys = (
        contacts.select(
            pl.col("game_pk").alias("game_id"),
            "at_bat_index",
            "pitch_number",
            "source_batter_id",
        )
        .join(repairs, on=["game_id", "source_batter_id"], how="inner")
        .sort(["game_id", "at_bat_index", "pitch_number"])
    )
    if repair_contact_keys.height != repairs.height:
        raise RuntimeError("strict repair does not map one-to-one to source contact keys")

    repaired_contacts = (
        contacts.select(
            pl.col("game_pk").alias("game_id"),
            "at_bat_index",
            "pitch_number",
            "source_batter_id",
        )
        .join(repairs, on=["game_id", "source_batter_id"], how="left")
        .with_columns(
            pl.coalesce(["reassigned_batter_id", "source_batter_id"]).alias(
                "effective_batter_id"
            )
        )
    )
    repaired_by_game_player = (
        repaired_contacts.group_by(["game_id", "effective_batter_id"])
        .len(name="source_contact_count")
        .rename({"effective_batter_id": "player_id"})
    )
    repaired_comparison = _outer_contact_comparison(
        repaired_by_game_player, expected_by_game_player
    )
    exception_games = sorted(
        int(v)
        for v in repaired_comparison.filter(pl.col("difference") != 0)
        .get_column("game_id")
        .unique()
        .to_list()
    )
    repair_games = sorted(int(v) for v in repairs.get_column("game_id").unique().to_list())
    audit_games = sorted(set(exception_games) | set(repair_games))

    # One-time certification fetch: every deterministic repair game + every
    # unresolved game. Production only needs official PBP for exception_games.
    official_pa, official_pitch = fetch_official_game_evidence(audit_games)
    official_contacts = _official_contacts(official_pa, official_pitch)
    fetched_games = sorted(
        int(v) for v in official_pa.get_column("game_pk").cast(pl.Int64).unique().to_list()
    )

    duplicate_official_contact_keys = (
        official_contacts.group_by(["game_id", "at_bat_index", "pitch_number"])
        .len()
        .filter(pl.col("len") > 1)
    )
    unmapped_official_batters = official_contacts.filter(
        pl.col("official_batter_id").is_null()
    )

    # Independently confirm the source-only deterministic repair rule.
    repair_confirmation = (
        repair_contact_keys.join(
            official_contacts.select(
                "game_id",
                "at_bat_index",
                "pitch_number",
                "official_batter_id",
                "pa_event_type",
            ),
            on=["game_id", "at_bat_index", "pitch_number"],
            how="left",
        )
        .with_columns(
            (pl.col("official_batter_id") == pl.col("reassigned_batter_id")).alias(
                "official_confirms_reassignment"
            )
        )
    )
    confirmed_repairs = repair_confirmation.filter(
        pl.col("official_confirms_reassignment") == True  # noqa: E712
    ).height
    missing_repair_official_key = repair_confirmation.filter(
        pl.col("official_batter_id").is_null()
    ).height
    disproved_repairs = repair_confirmation.filter(
        pl.col("official_batter_id").is_not_null()
        & (pl.col("official_confirms_reassignment") == False)  # noqa: E712
    ).height

    # Compare only the remaining production exception queue to current official.
    source_exception_contacts = repaired_contacts.filter(
        pl.col("game_id").is_in(exception_games)
    )
    official_exception_contacts = official_contacts.filter(
        pl.col("game_id").is_in(exception_games)
    )
    key_comparison = _key_comparison(
        source_exception_contacts, official_exception_contacts
    )

    source_only_keys = key_comparison.filter(pl.col("key_presence") == "source_only")
    official_only_keys = key_comparison.filter(pl.col("key_presence") == "official_only")
    matched_keys = key_comparison.filter(pl.col("key_presence") == "both")
    batter_mismatches = matched_keys.filter(pl.col("batter_mismatch") == True)  # noqa: E712

    official_by_game_player = (
        official_exception_contacts.group_by(["game_id", "official_batter_id"])
        .len(name="official_contact_count")
        .rename({"official_batter_id": "player_id"})
    )
    expected_exception = expected_by_game_player.filter(
        pl.col("game_id").is_in(exception_games)
    )
    official_player_game_comparison = _outer_contact_comparison(
        official_by_game_player,
        expected_exception,
        observed_column="official_contact_count",
    )
    official_player_game_metrics = _residual_metrics(official_player_game_comparison)

    official_boxscore = fetch_official_team_batting(exception_games)
    official_boxscore_contacts = (
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
    official_pbp_game_contacts = (
        official_exception_contacts.group_by("game_id")
        .len(name="official_pbp_contact_count")
    )
    official_contact_definition = (
        official_pbp_game_contacts.join(
            official_boxscore_contacts, on="game_id", how="full", coalesce=True
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

    # Persist exact exception evidence.
    repairs.write_csv(REPORT_DIR / "source_only_repair_map.csv")
    repair_confirmation.write_csv(REPORT_DIR / "source_only_repair_official_confirmation.csv")
    key_comparison.filter(
        (pl.col("key_presence") != "both") | (pl.col("batter_mismatch") == True)  # noqa: E712
    ).write_csv(REPORT_DIR / "exception_source_vs_official_contact_keys.csv")
    official_player_game_comparison.filter(pl.col("difference") != 0).write_csv(
        REPORT_DIR / "official_vs_player_game_residuals.csv"
    )
    official_contact_definition.filter(pl.col("difference") != 0).write_csv(
        REPORT_DIR / "official_pbp_vs_boxscore_contact_definition.csv"
    )

    source_exception_total = source_exception_contacts.height
    official_exception_total = official_exception_contacts.height
    boxscore_exception_total = int(
        official_contact_definition.get_column("boxscore_contact_count").sum() or 0
    )
    pbp_vs_box_nonzero_games = official_contact_definition.filter(
        pl.col("difference") != 0
    ).height

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "level": LEVEL,
        "game_type": GAME_TYPE,
        "source": source_metrics,
        "player_game": player_game_metrics,
        "source_only_stage": {
            "strict_reassignment_count": repairs.height,
            "strict_reassignment_game_count": len(repair_games),
            "remaining_exception_game_count": len(exception_games),
            "remaining_exception_game_ids": exception_games,
            "after_repair_residuals": _residual_metrics(repaired_comparison),
        },
        "official_certification_fetch": {
            "audit_game_count": len(audit_games),
            "fetched_game_count": len(fetched_games),
            "strict_repair_game_count": len(repair_games),
            "production_exception_game_count": len(exception_games),
            "duplicate_official_contact_key_count": duplicate_official_contact_keys.height,
            "unmapped_official_contact_batter_count": unmapped_official_batters.height,
        },
        "strict_repair_confirmation": {
            "repair_count": repairs.height,
            "official_confirmed_count": confirmed_repairs,
            "official_missing_contact_key_count": missing_repair_official_key,
            "official_disproved_count": disproved_repairs,
        },
        "exception_source_vs_official": {
            "source_contact_count": source_exception_total,
            "official_contact_count": official_exception_total,
            "net_source_minus_official": source_exception_total - official_exception_total,
            "matched_contact_key_count": matched_keys.height,
            "source_only_contact_key_count": source_only_keys.height,
            "official_only_contact_key_count": official_only_keys.height,
            "matched_key_batter_mismatch_count": batter_mismatches.height,
        },
        "official_vs_reusable_player_game": official_player_game_metrics,
        "official_contact_definition": {
            "official_pbp_contact_total": official_exception_total,
            "official_boxscore_contact_total": boxscore_exception_total,
            "pbp_minus_boxscore_total": official_exception_total - boxscore_exception_total,
            "mismatch_game_count": pbp_vs_box_nonzero_games,
        },
        "production_policy_candidate": (
            "Use reusable PBP plus the certified strict source-only reassignment rule. "
            "For games still in the residual queue, replace contact identity/status from "
            "current official PBP rather than guessing from season residuals."
        ),
    }
    (REPORT_DIR / "official_contact_exceptions.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Targeted official contact exception audit — 2024 AAA",
        "",
        "## Reuse-first localization",
        "",
        f"- Deterministic source-only repairs: {repairs.height:,} across {len(repair_games):,} games",
        f"- Remaining production exception games: {len(exception_games):,}",
        "",
        "## One-time official certification",
        "",
        f"- Official PBP games fetched: {len(fetched_games):,}/{len(audit_games):,}",
        f"- Source-only repairs confirmed by official batter: {confirmed_repairs:,}/{repairs.height:,}",
        f"- Repair keys missing from current official contact PBP: {missing_repair_official_key:,}",
        f"- Source-only repairs contradicted by official batter: {disproved_repairs:,}",
        "",
        "## Remaining exception queue",
        "",
        f"- Reusable-source contacts in exception games: {source_exception_total:,}",
        f"- Current official PBP contacts: {official_exception_total:,}",
        f"- Source-only contact keys: {source_only_keys.height:,}",
        f"- Official-only contact keys: {official_only_keys.height:,}",
        f"- Matched contact keys with batter mismatch: {batter_mismatches.height:,}",
        f"- Official-vs-player-game mismatch games: {official_player_game_metrics['mismatch_game_count']:,}",
        f"- Official-vs-player-game absolute discrepancy mass: {official_player_game_metrics['absolute_discrepancy_mass']:,}",
        "",
        "## Contact-definition check",
        "",
        f"- Official PBP contact total: {official_exception_total:,}",
        f"- Current official boxscore AB-SO+SF+SH total: {boxscore_exception_total:,}",
        f"- Difference: {official_exception_total - boxscore_exception_total:+,}",
        f"- Games with a PBP-vs-boxscore contact-count difference: {pbp_vs_box_nonzero_games:,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "official_contact_exceptions.md").write_text(summary, encoding="utf-8")
    print(summary)

    # Structural failures only. Ordinary current-source discrepancies are the
    # evidence this audit is designed to measure and therefore do not fail it.
    if len(fetched_games) != len(audit_games):
        raise RuntimeError("official PBP did not return every targeted audit game")
    if duplicate_official_contact_keys.height:
        raise RuntimeError("official PBP produced duplicate physical contact keys")
    if unmapped_official_batters.height:
        raise RuntimeError("official contact pitch could not be mapped to a PA batter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
