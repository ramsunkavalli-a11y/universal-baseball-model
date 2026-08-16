#!/usr/bin/env python
"""Full-season 2024 MLB Performance source reconciliation.

This gate promotes the sampled Savant certification into a completed-season
source proof without yet assigning contextual RE24/bin values.

Evidence roles:
- Baseball Savant CSV: reusable pitch/contact/profile and true-PA terminal rows;
- MLB Stats API bulk AL/NL season stats: standard PA/BB/HBP/K/count backbone;
- MLB team metadata: batting-team -> actual AL/NL environment authority.

Savant is fetched in non-overlapping four-day chunks to stay comfortably below
large-query limits. Exact response bytes are cached in quarantine and represented
by SHA-256 in the report. The gate requires exact player×league reconciliation
for PA, BB, HBP, and SO. Broad contact differences are reported rather than
synthetically repaired because `isInPlay` and AB-SO+SH+SF are not guaranteed to
be identical definitions.
"""

from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.mlb_performance import (
    assign_savant_actual_league,
    summarize_savant_contacts,
    summarize_savant_terminal_outcomes,
)
from universal_baseball.mlb_season_stats import (
    capture_manifest,
    fetch_mlb_hitting_backbone,
    fetch_mlb_team_leagues,
)
from universal_baseball.savant import (
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
START_DATE = date(2024, 3, 20)
END_DATE = date(2024, 9, 30)
CHUNK_DAYS = 4
WORK_DIR = Path("data/quarantine/mlb-full-season-performance-source")
REPORT_DIR = Path("reports/generated/mlb-full-season-performance-source")
TABLE_DIR = REPORT_DIR / "tables"


def _date_chunks(start: date, end: date, days: int) -> list[tuple[date, date]]:
    if days <= 0:
        raise ValueError("chunk days must be positive")
    chunks: list[tuple[date, date]] = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=days - 1), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _load_savant_season() -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    raw_dir = WORK_DIR / "savant"
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, Any]] = []
    for chunk_start, chunk_end in _date_chunks(START_DATE, END_DATE, CHUNK_DAYS):
        filename = f"savant_{chunk_start}_{chunk_end}.csv"
        path = raw_dir / filename
        if path.exists() and path.stat().st_size > 0:
            content = path.read_bytes()
            retrieved_url = "quarantine-cache"
            request_path = None
            status_code = None
        else:
            capture = fetch_savant_csv(chunk_start, chunk_end, timeout_seconds=180)
            content = capture.response_bytes
            path.write_bytes(content)
            retrieved_url = capture.retrieved_url
            request_path = capture.request_path
            status_code = capture.status_code
        raw = read_savant_csv_bytes(content)
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        frames.append(projected)
        captures.append(
            {
                "start_date": str(chunk_start),
                "end_date": str(chunk_end),
                "file_name": filename,
                "response_sha256": sha256(content).hexdigest(),
                "response_byte_count": len(content),
                "raw_row_count": raw.height,
                "regular_season_projected_row_count": projected.height,
                "request_path": request_path,
                "retrieved_url": retrieved_url,
                "status_code": status_code,
            }
        )
    combined = pl.concat(frames, how="vertical_relaxed")
    if combined.is_empty():
        raise RuntimeError("full-season Savant projection is empty")
    return combined.sort(["game_date", "game_pk", "at_bat_index", "pitch_number"]), captures


def _compare_outcomes(
    savant_outcomes: pl.DataFrame,
    backbone: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    expected = backbone.select(
        "season",
        "league_id",
        "player_id",
        pl.col("batting_plate_appearances").alias("backbone_plate_appearances"),
        pl.col("batting_base_on_balls").alias("backbone_base_on_balls"),
        pl.col("batting_hit_by_pitch").alias("backbone_hit_by_pitch"),
        pl.col("batting_strike_outs").alias("backbone_strike_outs"),
        pl.col("batting_balls_in_play").alias("backbone_contact_count"),
    )
    comparison = savant_outcomes.join(
        expected,
        on=["season", "league_id", "player_id"],
        how="full",
        coalesce=True,
    ).with_columns(
        pl.col("savant_plate_appearances").fill_null(0).cast(pl.Int64),
        pl.col("savant_base_on_balls").fill_null(0).cast(pl.Int64),
        pl.col("savant_hit_by_pitch").fill_null(0).cast(pl.Int64),
        pl.col("savant_strike_outs").fill_null(0).cast(pl.Int64),
        pl.col("backbone_plate_appearances").fill_null(0).cast(pl.Int64),
        pl.col("backbone_base_on_balls").fill_null(0).cast(pl.Int64),
        pl.col("backbone_hit_by_pitch").fill_null(0).cast(pl.Int64),
        pl.col("backbone_strike_outs").fill_null(0).cast(pl.Int64),
        pl.col("backbone_contact_count").fill_null(0).cast(pl.Int64),
    )
    fields = (
        ("plate_appearances", "savant_plate_appearances", "backbone_plate_appearances"),
        ("base_on_balls", "savant_base_on_balls", "backbone_base_on_balls"),
        ("hit_by_pitch", "savant_hit_by_pitch", "backbone_hit_by_pitch"),
        ("strike_outs", "savant_strike_outs", "backbone_strike_outs"),
    )
    comparison = comparison.with_columns(
        *[
            (pl.col(source) - pl.col(target)).alias(f"difference_{label}")
            for label, source, target in fields
        ]
    )
    mismatches = comparison.filter(
        pl.any_horizontal(
            [pl.col(f"difference_{label}") != 0 for label, _, _ in fields]
        )
    )
    return comparison.sort(["league_id", "player_id"]), mismatches.sort(
        ["league_id", "player_id"]
    )


def _classify_contacts(savant: pl.DataFrame) -> pl.DataFrame:
    contacts = savant.filter(pl.col("is_contact"))
    input_frame = contacts.select(
        pl.col("game_year").cast(pl.Int64).alias("season"),
        pl.col("league_id").cast(pl.Int64),
        "game_pk",
        "at_bat_index",
        "pitch_number",
        pl.col("batter_mlbam_id"),
        pl.lit("savant_official").alias("participant_authority"),
        pl.lit("savant_official").alias("result_description_authority"),
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    )
    classified = classify_contact_profile_events(input_frame)
    if classified.height != contacts.height:
        raise RuntimeError(
            f"MLB contact classifier lost rows: {classified.height:,} vs {contacts.height:,}"
        )
    return classified


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    savant, savant_captures = _load_savant_season()
    duplicate_pitch_keys = (
        savant.group_by(["game_pk", "at_bat_index", "pitch_number"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_pitch_keys.is_empty():
        duplicate_pitch_keys.write_csv(REPORT_DIR / "duplicate_savant_pitch_keys.csv")
        raise RuntimeError("full-season Savant has duplicate canonical pitch keys")

    team_leagues, team_response = fetch_mlb_team_leagues(SEASON)
    savant = assign_savant_actual_league(savant, team_leagues)
    backbone, backbone_captures = fetch_mlb_hitting_backbone(SEASON)

    terminal = summarize_savant_terminal_outcomes(savant)
    outcome_comparison, outcome_mismatches = _compare_outcomes(terminal, backbone)
    contacts_by_player = summarize_savant_contacts(savant)
    contact_comparison = (
        contacts_by_player.join(
            backbone.select(
                "season",
                "league_id",
                "player_id",
                pl.col("batting_balls_in_play").alias("backbone_contact_count"),
            ),
            on=["season", "league_id", "player_id"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            pl.col("savant_contact_count").fill_null(0).cast(pl.Int64),
            pl.col("backbone_contact_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (pl.col("savant_contact_count") - pl.col("backbone_contact_count")).alias(
                "contact_count_difference"
            )
        )
        .sort(["league_id", "player_id"])
    )

    classified = _classify_contacts(savant)
    contact_status_counts = (
        classified.group_by("contact_profile_status")
        .len()
        .sort("len", descending=True)
        .to_dicts()
    )
    unknown_contacts = classified.filter(
        pl.col("contact_profile_status").str.starts_with("unknown_")
    )

    outcome_comparison.write_csv(REPORT_DIR / "outcome_reconciliation.csv")
    outcome_mismatches.write_csv(REPORT_DIR / "outcome_reconciliation_mismatches.csv")
    contact_comparison.filter(pl.col("contact_count_difference") != 0).write_csv(
        REPORT_DIR / "contact_count_residuals.csv"
    )
    unknown_contacts.write_csv(REPORT_DIR / "unknown_contact_rows.csv")

    terminal_path = TABLE_DIR / "mlb_savant_terminal_outcomes_2024.parquet"
    contact_path = TABLE_DIR / "mlb_contact_profile_2024.parquet"
    backbone_path = TABLE_DIR / "mlb_batting_backbone_2024.parquet"
    terminal_artifact = write_canonical_parquet(
        terminal, terminal_path, table_name="mlb_savant_terminal_outcomes"
    )
    contact_artifact = write_canonical_parquet(
        classified, contact_path, table_name="mlb_contact_profile"
    )
    backbone_artifact = write_canonical_parquet(
        backbone, backbone_path, table_name="mlb_batting_backbone"
    )

    pa_total_savant = int(terminal.get_column("savant_plate_appearances").sum() or 0)
    pa_total_backbone = int(backbone.get_column("batting_plate_appearances").sum() or 0)
    contact_total = classified.height
    backbone_contact_total = int(backbone.get_column("batting_balls_in_play").sum() or 0)
    contact_residual = contact_total - backbone_contact_total
    true_pa_terminal_rows = savant.filter(pl.col("is_plate_appearance_terminal")).height
    truncated_rows = savant.filter(pl.col("events") == "truncated_pa").height

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "date_range": {"start": str(START_DATE), "end": str(END_DATE)},
        "savant": {
            "chunk_days": CHUNK_DAYS,
            "chunk_count": len(savant_captures),
            "captures": savant_captures,
            "projected_pitch_row_count": savant.height,
            "game_count": savant.get_column("game_pk").n_unique(),
            "duplicate_pitch_key_count": duplicate_pitch_keys.height,
            "true_pa_terminal_row_count": true_pa_terminal_rows,
            "truncated_pa_row_count": truncated_rows,
            "contact_row_count": contact_total,
            "contact_profile_status_counts": contact_status_counts,
            "unknown_contact_count": unknown_contacts.height,
        },
        "team_league_authority": {
            "team_count": len(team_leagues),
            "response_sha256": sha256(team_response).hexdigest(),
            "observed_batting_team_count": savant.get_column("batting_team").n_unique(),
            "observed_league_ids": sorted(
                int(value) for value in savant.get_column("league_id").unique().to_list()
            ),
        },
        "outcome_backbone": {
            "player_league_row_count": backbone.height,
            "capture_manifest": json.loads(capture_manifest(backbone_captures)),
            "savant_pa_total": pa_total_savant,
            "backbone_pa_total": pa_total_backbone,
            "player_league_outcome_mismatch_count": outcome_mismatches.height,
        },
        "contact_reconciliation": {
            "savant_contact_total": contact_total,
            "backbone_broad_contact_total": backbone_contact_total,
            "net_contact_residual": contact_residual,
            "absolute_player_league_residual_mass": int(
                contact_comparison.get_column("contact_count_difference").abs().sum() or 0
            ),
            "player_league_nonzero_residual_count": contact_comparison.filter(
                pl.col("contact_count_difference") != 0
            ).height,
        },
        "storage": {
            "terminal": terminal_artifact.as_record(),
            "contact_profile": contact_artifact.as_record(),
            "backbone": backbone_artifact.as_record(),
        },
        "interpretation": (
            "Exact PA/BB/HBP/K reconciliation certifies Savant + bulk Stats API as the "
            "MLB Performance source backbone. Broad-contact residuals remain explicit "
            "definition/coverage evidence and are not synthetically repaired. Contextual "
            "RE24/bin values are intentionally a separate next gate."
        ),
    }
    (REPORT_DIR / "mlb_full_season_performance_source.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB full-season Performance source reconciliation — 2024",
        "",
        f"- Savant chunks / games / pitch rows: {len(savant_captures):,} / {savant.get_column('game_pk').n_unique():,} / {savant.height:,}",
        f"- True-PA terminal rows / truncated_pa markers: {true_pa_terminal_rows:,} / {truncated_rows:,}",
        f"- Savant / backbone PA: {pa_total_savant:,} / {pa_total_backbone:,}",
        f"- Player-league PA/BB/HBP/K mismatches: {outcome_mismatches.height:,}",
        f"- Savant / backbone broad contacts: {contact_total:,} / {backbone_contact_total:,}",
        f"- Net broad-contact residual: {contact_residual:+,}",
        f"- Player-league rows with contact residual: {contact_comparison.filter(pl.col('contact_count_difference') != 0).height:,}",
        f"- Classified contacts / unknown contacts: {classified.height:,} / {unknown_contacts.height:,}",
        f"- Batting teams / actual leagues: {savant.get_column('batting_team').n_unique():,} / {savant.get_column('league_id').n_unique():,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_full_season_performance_source.md").write_text(summary, encoding="utf-8")
    print(summary)

    if outcome_mismatches.height:
        raise RuntimeError("Savant terminal outcomes do not reconcile to MLB bulk backbone")
    if pa_total_savant != pa_total_backbone:
        raise RuntimeError("Savant and bulk backbone total PA differ")
    if classified.height != contact_total:
        raise RuntimeError("MLB contact classifier failed complete contact accounting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
