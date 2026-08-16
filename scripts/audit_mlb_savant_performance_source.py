#!/usr/bin/env python
"""Certify Baseball Savant as the reusable MLB Performance contact source.

The affiliated MiLB Performance layer uses armstjc history plus targeted official
authority. MLB has a simpler public source: Baseball Savant's official Statcast
CSV export already exposes the required pitch/contact surface. This gate samples
three regular-season dates spanning 2024 and reconciles Savant against the
project's tolerant Stats API projection.

The audit deliberately separates:
- physical contact-key coverage;
- participant identity;
- trajectory / Gameday coordinates;
- PA narrative / foul-territory classification; and
- terminal-event coverage (which may legitimately omit zero-pitch PAs).
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re

import polars as pl

from universal_baseball.contact_identity_overlay import project_official_contact_authority
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_events import FOUL_TERRITORY_REGEX
from universal_baseball.savant import (
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)


REPORT_DIR = Path("reports/generated/mlb-savant-performance-source")
AUDIT_DATES = (date(2024, 4, 15), date(2024, 6, 15), date(2024, 9, 15))
GAMES_PER_DATE = 4


def _normalized_text_expr(column: str) -> pl.Expr:
    return (
        pl.col(column)
        .cast(pl.String)
        .str.to_lowercase()
        .str.replace_all(r"[^a-z0-9]+", " ")
        .str.strip_chars()
    )


def _contact_comparison(
    savant: pl.DataFrame,
    official_pa: pl.DataFrame,
    official_pitch: pl.DataFrame,
) -> pl.DataFrame:
    key = ["game_pk", "at_bat_index", "pitch_number"]
    savant_contacts = savant.filter(pl.col("is_contact")).select(
        *key,
        "batter_mlbam_id",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    ).with_columns(pl.lit(True).alias("savant_present"))

    pa_authority = official_pa.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("batter_id").cast(pl.Int64).alias("official_batter_id"),
        pl.col("description").alias("official_result_description"),
    )
    official_contacts = (
        official_pitch.filter(pl.col("is_in_play") == True)  # noqa: E712
        .select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
            pl.col("pitch_number").cast(pl.Int64),
            pl.col("batter_side").alias("official_batter_side"),
            pl.col("hit_trajectory").alias("official_bb_type"),
            pl.col("hit_coord_x").alias("official_hc_x"),
            pl.col("hit_coord_y").alias("official_hc_y"),
        )
        .join(pa_authority, on=["game_pk", "at_bat_index"], how="left")
        .with_columns(pl.lit(True).alias("official_present"))
    )

    return (
        savant_contacts.join(official_contacts, on=key, how="full", coalesce=True)
        .with_columns(
            pl.col("savant_present").fill_null(False),
            pl.col("official_present").fill_null(False),
        )
        .with_columns(
            pl.when(pl.col("savant_present") & pl.col("official_present"))
            .then(pl.lit("both"))
            .when(pl.col("savant_present"))
            .then(pl.lit("savant_only"))
            .otherwise(pl.lit("official_only"))
            .alias("key_presence"),
            (
                pl.col("batter_mlbam_id").is_not_null()
                & pl.col("official_batter_id").is_not_null()
                & (pl.col("batter_mlbam_id") == pl.col("official_batter_id"))
            ).alias("batter_match"),
            (
                pl.col("batter_side").is_not_null()
                & pl.col("official_batter_side").is_not_null()
                & (pl.col("batter_side") == pl.col("official_batter_side"))
            ).alias("batter_side_match"),
            (
                pl.col("bb_type").is_not_null()
                & pl.col("official_bb_type").is_not_null()
                & (pl.col("bb_type") == pl.col("official_bb_type"))
            ).alias("trajectory_match_when_both"),
            (
                pl.col("hc_x").is_not_null()
                & pl.col("official_hc_x").is_not_null()
                & ((pl.col("hc_x") - pl.col("official_hc_x")).abs() < 1e-9)
            ).alias("hc_x_match_when_both"),
            (
                pl.col("hc_y").is_not_null()
                & pl.col("official_hc_y").is_not_null()
                & ((pl.col("hc_y") - pl.col("official_hc_y")).abs() < 1e-9)
            ).alias("hc_y_match_when_both"),
            _normalized_text_expr("result_description").alias("savant_result_norm"),
            _normalized_text_expr("official_result_description").alias("official_result_norm"),
        )
        .with_columns(
            (
                pl.col("savant_result_norm").is_not_null()
                & pl.col("official_result_norm").is_not_null()
                & (pl.col("savant_result_norm") == pl.col("official_result_norm"))
            ).alias("result_description_match_when_both"),
            pl.col("result_description")
            .cast(pl.String)
            .str.contains(FOUL_TERRITORY_REGEX)
            .fill_null(False)
            .alias("savant_foul_territory"),
            pl.col("official_result_description")
            .cast(pl.String)
            .str.contains(FOUL_TERRITORY_REGEX)
            .fill_null(False)
            .alias("official_foul_territory"),
        )
        .sort(key)
    )


def _terminal_comparison(savant: pl.DataFrame, official_pa: pl.DataFrame) -> pl.DataFrame:
    savant_terminal = (
        savant.filter(pl.col("is_terminal_event"))
        .select(
            "game_pk",
            "at_bat_index",
            "events",
            "batter_mlbam_id",
        )
        .unique(subset=["game_pk", "at_bat_index"], keep="any")
        .with_columns(pl.lit(True).alias("savant_terminal_present"))
    )
    official = official_pa.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("event_type").alias("official_event_type"),
        pl.col("batter_id").cast(pl.Int64).alias("official_batter_id"),
        pl.col("official_pitch_count").cast(pl.Int64),
    ).with_columns(pl.lit(True).alias("official_pa_present"))
    return (
        savant_terminal.join(
            official,
            on=["game_pk", "at_bat_index"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            pl.col("savant_terminal_present").fill_null(False),
            pl.col("official_pa_present").fill_null(False),
        )
        .sort(["game_pk", "at_bat_index"])
    )


def _match_rate(frame: pl.DataFrame, field: str, availability: pl.Expr) -> dict[str, int | float | None]:
    available = frame.filter(availability)
    matched = available.filter(pl.col(field) == True)  # noqa: E712
    return {
        "compared": available.height,
        "matched": matched.height,
        "mismatched": available.height - matched.height,
        "match_rate": matched.height / available.height if available.height else None,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    date_frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    selected_games: list[int] = []

    for audit_date in AUDIT_DATES:
        capture = fetch_savant_csv(audit_date, audit_date)
        raw = read_savant_csv_bytes(capture.response_bytes)
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        games = sorted(int(value) for value in projected.get_column("game_pk").unique().to_list())
        chosen = games[:GAMES_PER_DATE]
        if len(chosen) != GAMES_PER_DATE:
            raise RuntimeError(
                f"Savant returned only {len(chosen)} regular-season games on {audit_date}"
            )
        selected_games.extend(chosen)
        date_frames.append(projected.filter(pl.col("game_pk").is_in(chosen)))
        captures.append(
            {
                "date": str(audit_date),
                "request_path": capture.request_path,
                "response_sha256": sha256(capture.response_bytes).hexdigest(),
                "response_byte_count": len(capture.response_bytes),
                "projected_regular_season_row_count": projected.height,
                "regular_season_game_count": len(games),
                "selected_game_ids": chosen,
            }
        )

    savant = pl.concat(date_frames, how="vertical_relaxed")
    selected_games = sorted(set(selected_games))
    official_pa, official_pitch = fetch_official_game_evidence(selected_games)

    contact = _contact_comparison(savant, official_pa, official_pitch)
    terminal = _terminal_comparison(savant, official_pa)
    both_contacts = contact.filter(pl.col("key_presence") == "both")
    savant_only = contact.filter(pl.col("key_presence") == "savant_only")
    official_only = contact.filter(pl.col("key_presence") == "official_only")

    batter = _match_rate(
        both_contacts,
        "batter_match",
        pl.col("batter_mlbam_id").is_not_null() & pl.col("official_batter_id").is_not_null(),
    )
    side = _match_rate(
        both_contacts,
        "batter_side_match",
        pl.col("batter_side").is_not_null() & pl.col("official_batter_side").is_not_null(),
    )
    trajectory = _match_rate(
        both_contacts,
        "trajectory_match_when_both",
        pl.col("bb_type").is_not_null() & pl.col("official_bb_type").is_not_null(),
    )
    hc_x = _match_rate(
        both_contacts,
        "hc_x_match_when_both",
        pl.col("hc_x").is_not_null() & pl.col("official_hc_x").is_not_null(),
    )
    hc_y = _match_rate(
        both_contacts,
        "hc_y_match_when_both",
        pl.col("hc_y").is_not_null() & pl.col("official_hc_y").is_not_null(),
    )
    description = _match_rate(
        both_contacts,
        "result_description_match_when_both",
        pl.col("result_description").is_not_null()
        & pl.col("official_result_description").is_not_null(),
    )
    foul_disagreement = both_contacts.filter(
        pl.col("savant_foul_territory") != pl.col("official_foul_territory")
    )

    missing_savant_terminal = terminal.filter(
        pl.col("official_pa_present") & ~pl.col("savant_terminal_present")
    )
    extra_savant_terminal = terminal.filter(
        pl.col("savant_terminal_present") & ~pl.col("official_pa_present")
    )
    zero_pitch_missing = missing_savant_terminal.filter(pl.col("official_pitch_count") == 0)

    contact.filter(pl.col("key_presence") != "both").write_csv(
        REPORT_DIR / "contact_key_differences.csv"
    )
    both_contacts.filter(
        (~pl.col("batter_match").fill_null(True))
        | (~pl.col("trajectory_match_when_both").fill_null(True))
        | (~pl.col("hc_x_match_when_both").fill_null(True))
        | (~pl.col("hc_y_match_when_both").fill_null(True))
        | (pl.col("savant_foul_territory") != pl.col("official_foul_territory"))
    ).write_csv(REPORT_DIR / "contact_field_differences.csv")
    missing_savant_terminal.write_csv(REPORT_DIR / "official_pas_without_savant_terminal.csv")
    extra_savant_terminal.write_csv(REPORT_DIR / "savant_terminal_without_official_pa.csv")

    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "source": "Baseball Savant Statcast CSV",
        "sample": {
            "dates": [str(value) for value in AUDIT_DATES],
            "games_per_date": GAMES_PER_DATE,
            "game_count": len(selected_games),
            "game_ids": selected_games,
            "captures": captures,
        },
        "rows": {
            "savant_pitch_rows": savant.height,
            "savant_contact_rows": savant.filter(pl.col("is_contact")).height,
            "official_contact_rows": official_pitch.filter(pl.col("is_in_play") == True).height,  # noqa: E712
            "matched_contact_keys": both_contacts.height,
            "savant_only_contact_keys": savant_only.height,
            "official_only_contact_keys": official_only.height,
        },
        "contact_fields": {
            "batter": batter,
            "batter_side": side,
            "trajectory": trajectory,
            "hc_x": hc_x,
            "hc_y": hc_y,
            "result_description": description,
            "foul_territory_disagreement_count": foul_disagreement.height,
        },
        "terminal_pa_surface": {
            "savant_terminal_sequence_count": terminal.filter(
                pl.col("savant_terminal_present")
            ).height,
            "official_true_pa_count": terminal.filter(pl.col("official_pa_present")).height,
            "official_pa_missing_savant_terminal_count": missing_savant_terminal.height,
            "missing_savant_terminal_zero_pitch_pa_count": zero_pitch_missing.height,
            "savant_terminal_without_official_pa_count": extra_savant_terminal.height,
        },
        "interpretation": (
            "Savant can serve as the reusable MLB contact/profile source if physical "
            "contact keys and certified profile fields reconcile to Stats API. Standard "
            "PA/outcome totals should remain a separate aggregate backbone because a "
            "pitch-level export need not represent zero-pitch PAs."
        ),
    }
    (REPORT_DIR / "mlb_savant_performance_source.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB Savant Performance source audit — 2024",
        "",
        f"- Dates / games: {len(AUDIT_DATES)} / {len(selected_games)}",
        f"- Savant / official contact rows: {savant.filter(pl.col('is_contact')).height:,} / {official_pitch.filter(pl.col('is_in_play') == True).height:,}",  # noqa: E712
        f"- Matched contact keys: {both_contacts.height:,}",
        f"- Savant-only / official-only contact keys: {savant_only.height:,} / {official_only.height:,}",
        f"- Batter match: {batter['matched']:,}/{batter['compared']:,}",
        f"- Trajectory match when both present: {trajectory['matched']:,}/{trajectory['compared']:,}",
        f"- hc_x / hc_y match when both present: {hc_x['matched']:,}/{hc_x['compared']:,} / {hc_y['matched']:,}/{hc_y['compared']:,}",
        f"- Foul-territory classification disagreements: {foul_disagreement.height:,}",
        f"- Official true PAs without Savant terminal row: {missing_savant_terminal.height:,}",
        f"- Of those, zero-pitch official PAs: {zero_pitch_missing.height:,}",
        f"- Savant terminal rows without official true PA: {extra_savant_terminal.height:,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_savant_performance_source.md").write_text(summary, encoding="utf-8")
    print(summary)

    if savant_only.height or official_only.height:
        raise RuntimeError("Savant physical contact keys do not reconcile to official sample")
    for label, result in (
        ("batter", batter),
        ("batter side", side),
        ("trajectory", trajectory),
        ("hc_x", hc_x),
        ("hc_y", hc_y),
    ):
        if result["mismatched"]:
            raise RuntimeError(f"Savant {label} differs from official sample")
    if foul_disagreement.height:
        raise RuntimeError("Savant foul-territory narrative classification differs from official")
    if extra_savant_terminal.height:
        raise RuntimeError("Savant terminal rows include non-PA official sequences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
