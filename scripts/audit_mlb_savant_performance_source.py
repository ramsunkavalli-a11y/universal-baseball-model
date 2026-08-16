#!/usr/bin/env python
"""Certify Baseball Savant as the reusable MLB Performance contact source.

The affiliated MiLB Performance layer uses armstjc history plus targeted official
authority. MLB has a simpler public source: Baseball Savant's official Statcast
CSV export already exposes the required pitch/contact surface. This gate samples
three regular-season dates spanning 2024 and reconciles Savant against the
project's tolerant Stats API projection.

The gate deliberately separates source semantics:

- contact *existence/profile* is certified at play-sequence grain because the
  current Stats API can revise the pitch number assigned to an otherwise
  identical historical contact;
- pitch-number drift is retained as revision evidence rather than used as a
  participant/profile tiebreaker;
- canonical bunt trajectory is reconstructed from Savant's explicit PA
  narrative because the public ``bb_type`` collapses bunts;
- ``truncated_pa`` is retained as a source terminal marker but is not a true PA;
- standard PA/outcome totals remain a separate backbone so pitch-level exports
  never need to invent zero-pitch PAs.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_events import FOUL_TERRITORY_REGEX
from universal_baseball.savant import (
    SAVANT_NON_PA_TERMINAL_EVENTS,
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)


REPORT_DIR = Path("reports/generated/mlb-savant-performance-source")
AUDIT_DATES = (date(2024, 4, 15), date(2024, 6, 15), date(2024, 9, 15))
GAMES_PER_DATE = 4
SEQUENCE_KEY = ["game_pk", "at_bat_index"]
CONTACT_KEY = ["game_pk", "at_bat_index", "pitch_number"]


def _normalized_text_expr(column: str) -> pl.Expr:
    return (
        pl.col(column)
        .cast(pl.String)
        .str.to_lowercase()
        .str.replace_all(r"[^a-z0-9]+", " ")
        .str.strip_chars()
    )


def _official_contacts(
    official_pa: pl.DataFrame,
    official_pitch: pl.DataFrame,
) -> pl.DataFrame:
    pa = official_pa.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
        pl.col("batter_id").cast(pl.Int64).alias("official_batter_id"),
        pl.col("description").cast(pl.String).alias("official_result_description"),
    )
    return (
        official_pitch.filter(pl.col("is_in_play") == True)  # noqa: E712
        .select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
            pl.col("pitch_number").cast(pl.Int64).alias("official_pitch_number"),
            pl.col("batter_side").cast(pl.String).alias("official_batter_side"),
            pl.col("hit_trajectory").cast(pl.String).alias("official_bb_type"),
            pl.col("hit_coord_x").cast(pl.Float64).alias("official_hc_x"),
            pl.col("hit_coord_y").cast(pl.Float64).alias("official_hc_y"),
        )
        .join(pa, on=SEQUENCE_KEY, how="left")
        .sort([*SEQUENCE_KEY, "official_pitch_number"])
    )


def _contact_sequence_counts(
    savant_contacts: pl.DataFrame,
    official_contacts: pl.DataFrame,
) -> pl.DataFrame:
    source = (
        savant_contacts.group_by(SEQUENCE_KEY)
        .len(name="savant_contact_count")
        .with_columns(pl.lit(True).alias("savant_sequence_present"))
    )
    official = (
        official_contacts.group_by(SEQUENCE_KEY)
        .len(name="official_contact_count")
        .with_columns(pl.lit(True).alias("official_sequence_present"))
    )
    return (
        source.join(official, on=SEQUENCE_KEY, how="full", coalesce=True)
        .with_columns(
            pl.col("savant_sequence_present").fill_null(False),
            pl.col("official_sequence_present").fill_null(False),
            pl.col("savant_contact_count").fill_null(0).cast(pl.Int64),
            pl.col("official_contact_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (
                pl.col("savant_contact_count") - pl.col("official_contact_count")
            ).alias("contact_count_difference")
        )
        .sort(SEQUENCE_KEY)
    )


def _rank_contacts_within_sequence(
    frame: pl.DataFrame,
    *,
    pitch_column: str,
) -> pl.DataFrame:
    return (
        frame.sort([*SEQUENCE_KEY, pitch_column])
        .with_columns(
            pl.col(pitch_column)
            .rank(method="ordinal")
            .over(SEQUENCE_KEY)
            .cast(pl.Int64)
            .alias("contact_rank")
        )
    )


def _paired_contact_comparison(
    savant: pl.DataFrame,
    official_pa: pl.DataFrame,
    official_pitch: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    savant_contacts = (
        savant.filter(pl.col("is_contact"))
        .select(
            *SEQUENCE_KEY,
            pl.col("pitch_number").cast(pl.Int64).alias("savant_pitch_number"),
            "batter_mlbam_id",
            "batter_side",
            "source_bb_type",
            "bb_type",
            "hc_x",
            "hc_y",
            "result_description",
        )
        .sort([*SEQUENCE_KEY, "savant_pitch_number"])
    )
    official_contacts = _official_contacts(official_pa, official_pitch)
    sequence_counts = _contact_sequence_counts(savant_contacts, official_contacts)

    source_ranked = _rank_contacts_within_sequence(
        savant_contacts,
        pitch_column="savant_pitch_number",
    )
    official_ranked = _rank_contacts_within_sequence(
        official_contacts,
        pitch_column="official_pitch_number",
    )
    comparison = (
        source_ranked.join(
            official_ranked,
            on=[*SEQUENCE_KEY, "contact_rank"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            (
                pl.col("savant_pitch_number") - pl.col("official_pitch_number")
            ).alias("pitch_number_delta"),
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
            _normalized_text_expr("official_result_description").alias(
                "official_result_norm"
            ),
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
        .sort([*SEQUENCE_KEY, "contact_rank"])
    )
    return comparison, sequence_counts


def _terminal_comparison(
    savant: pl.DataFrame,
    official_pa: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    savant_pa = (
        savant.filter(pl.col("is_plate_appearance_terminal"))
        .select(
            *SEQUENCE_KEY,
            "events",
            "batter_mlbam_id",
            "result_description",
        )
        .unique(subset=SEQUENCE_KEY, keep="any")
        .with_columns(pl.lit(True).alias("savant_pa_present"))
    )
    truncated = (
        savant.filter(pl.col("events").is_in(sorted(SAVANT_NON_PA_TERMINAL_EVENTS)))
        .select(*SEQUENCE_KEY, "events", "batter_mlbam_id", "pitch_number")
        .unique(subset=SEQUENCE_KEY, keep="any")
        .sort(SEQUENCE_KEY)
    )
    official = (
        official_pa.select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("at_bat_number").cast(pl.Int64).alias("at_bat_index"),
            pl.col("event_type").cast(pl.String).alias("official_event_type"),
            pl.col("batter_id").cast(pl.Int64).alias("official_batter_id"),
            pl.col("official_pitch_count").cast(pl.Int64),
            pl.col("description").cast(pl.String).alias("official_result_description"),
        )
        .with_columns(pl.lit(True).alias("official_pa_present"))
    )
    comparison = (
        savant_pa.join(official, on=SEQUENCE_KEY, how="full", coalesce=True)
        .with_columns(
            pl.col("savant_pa_present").fill_null(False),
            pl.col("official_pa_present").fill_null(False),
        )
        .with_columns(
            (
                pl.col("events").is_not_null()
                & pl.col("official_event_type").is_not_null()
                & (pl.col("events") == pl.col("official_event_type"))
            ).alias("event_type_match"),
            (
                pl.col("batter_mlbam_id").is_not_null()
                & pl.col("official_batter_id").is_not_null()
                & (pl.col("batter_mlbam_id") == pl.col("official_batter_id"))
            ).alias("batter_match"),
        )
        .sort(SEQUENCE_KEY)
    )
    return comparison, truncated


def _match_rate(
    frame: pl.DataFrame,
    field: str,
    availability: pl.Expr,
) -> dict[str, int | float | None]:
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
        games = sorted(
            int(value) for value in projected.get_column("game_pk").unique().to_list()
        )
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

    contact, sequence_counts = _paired_contact_comparison(
        savant,
        official_pa,
        official_pitch,
    )
    sequence_count_mismatches = sequence_counts.filter(
        pl.col("contact_count_difference") != 0
    )
    multi_contact_sequences = sequence_counts.filter(
        (pl.col("savant_contact_count") > 1) | (pl.col("official_contact_count") > 1)
    )
    pitch_drift = contact.filter(pl.col("pitch_number_delta") != 0)

    batter = _match_rate(
        contact,
        "batter_match",
        pl.col("batter_mlbam_id").is_not_null()
        & pl.col("official_batter_id").is_not_null(),
    )
    side = _match_rate(
        contact,
        "batter_side_match",
        pl.col("batter_side").is_not_null()
        & pl.col("official_batter_side").is_not_null(),
    )
    trajectory = _match_rate(
        contact,
        "trajectory_match_when_both",
        pl.col("bb_type").is_not_null() & pl.col("official_bb_type").is_not_null(),
    )
    hc_x = _match_rate(
        contact,
        "hc_x_match_when_both",
        pl.col("hc_x").is_not_null() & pl.col("official_hc_x").is_not_null(),
    )
    hc_y = _match_rate(
        contact,
        "hc_y_match_when_both",
        pl.col("hc_y").is_not_null() & pl.col("official_hc_y").is_not_null(),
    )
    description = _match_rate(
        contact,
        "result_description_match_when_both",
        pl.col("result_description").is_not_null()
        & pl.col("official_result_description").is_not_null(),
    )
    foul_disagreement = contact.filter(
        pl.col("savant_foul_territory") != pl.col("official_foul_territory")
    )

    terminal, truncated = _terminal_comparison(savant, official_pa)
    missing_savant_pa = terminal.filter(
        pl.col("official_pa_present") & ~pl.col("savant_pa_present")
    )
    extra_savant_pa = terminal.filter(
        pl.col("savant_pa_present") & ~pl.col("official_pa_present")
    )
    nonzero_pitch_missing = missing_savant_pa.filter(
        pl.col("official_pitch_count").fill_null(0) > 0
    )
    zero_pitch_missing = missing_savant_pa.filter(
        pl.col("official_pitch_count").fill_null(-1) == 0
    )
    paired_pa = terminal.filter(
        pl.col("savant_pa_present") & pl.col("official_pa_present")
    )
    terminal_event_mismatch = paired_pa.filter(~pl.col("event_type_match"))
    terminal_batter_mismatch = paired_pa.filter(~pl.col("batter_match"))

    sequence_count_mismatches.write_csv(
        REPORT_DIR / "contact_sequence_count_differences.csv"
    )
    pitch_drift.select(
        *SEQUENCE_KEY,
        "contact_rank",
        "savant_pitch_number",
        "official_pitch_number",
        "pitch_number_delta",
        "batter_mlbam_id",
        "official_batter_id",
        "bb_type",
        "official_bb_type",
        "hc_x",
        "official_hc_x",
        "hc_y",
        "official_hc_y",
        "result_description",
        "official_result_description",
    ).write_csv(REPORT_DIR / "contact_pitch_number_drift.csv")
    contact.filter(
        (~pl.col("batter_match").fill_null(True))
        | (~pl.col("trajectory_match_when_both").fill_null(True))
        | (~pl.col("hc_x_match_when_both").fill_null(True))
        | (~pl.col("hc_y_match_when_both").fill_null(True))
        | (~pl.col("result_description_match_when_both").fill_null(True))
        | (pl.col("savant_foul_territory") != pl.col("official_foul_territory"))
    ).write_csv(REPORT_DIR / "contact_field_differences.csv")
    missing_savant_pa.write_csv(REPORT_DIR / "official_pas_without_savant_pa_terminal.csv")
    extra_savant_pa.write_csv(REPORT_DIR / "savant_pa_terminal_without_official_pa.csv")
    truncated.write_csv(REPORT_DIR / "savant_truncated_pa_sequences.csv")

    savant_contact_count = savant.filter(pl.col("is_contact")).height
    official_contact_count = official_pitch.filter(pl.col("is_in_play") == True).height  # noqa: E712
    payload = {
        "report_schema_version": 2,
        "season": 2024,
        "source": "Baseball Savant Statcast CSV",
        "sample": {
            "dates": [str(value) for value in AUDIT_DATES],
            "games_per_date": GAMES_PER_DATE,
            "game_count": len(selected_games),
            "game_ids": selected_games,
            "captures": captures,
        },
        "contact_surface": {
            "savant_contact_rows": savant_contact_count,
            "official_contact_rows": official_contact_count,
            "savant_contact_sequence_count": sequence_counts.filter(
                pl.col("savant_sequence_present")
            ).height,
            "official_contact_sequence_count": sequence_counts.filter(
                pl.col("official_sequence_present")
            ).height,
            "sequence_count_mismatch_count": sequence_count_mismatches.height,
            "multi_contact_sequence_count": multi_contact_sequences.height,
            "paired_contact_row_count": contact.height,
            "pitch_number_drift_count": pitch_drift.height,
            "pitch_number_delta_counts": {
                str(row["pitch_number_delta"]): int(row["len"])
                for row in pitch_drift.group_by("pitch_number_delta")
                .len()
                .sort("pitch_number_delta")
                .to_dicts()
            },
        },
        "contact_fields": {
            "batter": batter,
            "batter_side": side,
            "canonical_trajectory": trajectory,
            "hc_x": hc_x,
            "hc_y": hc_y,
            "result_description": description,
            "foul_territory_disagreement_count": foul_disagreement.height,
        },
        "terminal_pa_surface": {
            "savant_true_pa_terminal_count": terminal.filter(
                pl.col("savant_pa_present")
            ).height,
            "official_true_pa_count": terminal.filter(pl.col("official_pa_present")).height,
            "official_pa_missing_savant_terminal_count": missing_savant_pa.height,
            "missing_savant_terminal_zero_pitch_pa_count": zero_pitch_missing.height,
            "missing_savant_terminal_nonzero_pitch_pa_count": nonzero_pitch_missing.height,
            "savant_pa_terminal_without_official_pa_count": extra_savant_pa.height,
            "paired_pa_event_type_mismatch_count": terminal_event_mismatch.height,
            "paired_pa_batter_mismatch_count": terminal_batter_mismatch.height,
            "savant_truncated_pa_count": truncated.height,
        },
        "interpretation": (
            "Baseball Savant is certified here at play-sequence/contact-profile grain. "
            "Its source pitch number is preserved even when current Stats API numbering "
            "has drifted. Savant's raw bunt-collapsed bb_type and truncated_pa marker are "
            "normalized explicitly. Standard season PA/outcome totals remain a separate "
            "backbone rather than being reconstructed from pitch rows."
        ),
    }
    (REPORT_DIR / "mlb_savant_performance_source.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB Savant Performance source audit — 2024",
        "",
        f"- Dates / games: {len(AUDIT_DATES)} / {len(selected_games)}",
        f"- Savant / official contact rows: {savant_contact_count:,} / {official_contact_count:,}",
        f"- Contact-sequence count mismatches: {sequence_count_mismatches.height:,}",
        f"- Multi-contact sequences: {multi_contact_sequences.height:,}",
        f"- Paired contact rows: {contact.height:,}",
        f"- Pitch-number drift rows: {pitch_drift.height:,}",
        f"- Batter match: {batter['matched']:,}/{batter['compared']:,}",
        f"- Canonical trajectory match when both present: {trajectory['matched']:,}/{trajectory['compared']:,}",
        f"- hc_x / hc_y match when both present: {hc_x['matched']:,}/{hc_x['compared']:,} / {hc_y['matched']:,}/{hc_y['compared']:,}",
        f"- Result narrative match when both present: {description['matched']:,}/{description['compared']:,}",
        f"- Foul-territory classification disagreements: {foul_disagreement.height:,}",
        f"- Official true PAs without Savant true-PA terminal: {missing_savant_pa.height:,}",
        f"- Missing with nonzero / zero official pitches: {nonzero_pitch_missing.height:,} / {zero_pitch_missing.height:,}",
        f"- Savant true-PA terminals without official true PA: {extra_savant_pa.height:,}",
        f"- Paired PA event/batter mismatches: {terminal_event_mismatch.height:,} / {terminal_batter_mismatch.height:,}",
        f"- Savant truncated_pa non-PA markers: {truncated.height:,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_savant_performance_source.md").write_text(summary, encoding="utf-8")
    print(summary)

    if sequence_count_mismatches.height:
        raise RuntimeError("Savant contact sequence counts do not reconcile to official sample")
    if contact.height != savant_contact_count or contact.height != official_contact_count:
        raise RuntimeError("paired contact rows do not account for both sources")
    for label, result in (
        ("batter", batter),
        ("batter side", side),
        ("canonical trajectory", trajectory),
        ("hc_x", hc_x),
        ("hc_y", hc_y),
        ("result description", description),
    ):
        if result["mismatched"]:
            raise RuntimeError(f"Savant {label} differs from official sample")
    if foul_disagreement.height:
        raise RuntimeError("Savant foul-territory classification differs from official")
    if nonzero_pitch_missing.height:
        raise RuntimeError("Savant misses official nonzero-pitch true PAs")
    if extra_savant_pa.height:
        raise RuntimeError("Savant true-PA terminals include non-PA official sequences")
    if terminal_event_mismatch.height or terminal_batter_mismatch.height:
        raise RuntimeError("Savant PA terminal semantics differ from official sample")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
