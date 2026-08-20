#!/usr/bin/env python
"""Materialize completed-2024 MLB batting Performance on the universal contract.

This is the MLB reporting-anchor build required before Current Talent can learn a
common MLB-through-DSL scale.  It intentionally reuses the certified source and
value components rather than creating an MLB-only metric:

- Baseball Savant: pitch/contact/profile evidence;
- bulk MLB Stats API: AL/NL player-season PA/BB/HBP/K/contact backbone;
- Retrosheet: independent full-season 24-state RE matrix;
- official MLB PBP: 45 deterministic intraleague calibration games per AL/NL;
- ADR 023: same-bin AL<->NL shrinkage, lambda=5;
- ``batting_performance_v1``: identical downstream output contract to MiLB.
"""

from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

import duckdb
import polars as pl
import requests

from universal_baseball.bin_value_calibration import (
    bin_calibration_coverage,
    summarize_direct_bin_values,
)
from universal_baseball.certification import download_file
from universal_baseball.mlb_bin_value_policy import estimate_certified_mlb_bin_values
from universal_baseball.mlb_calibration import (
    calibration_events_from_official_payload,
    intraleague_schedule_candidates,
    spread_sample,
)
from universal_baseball.mlb_performance import (
    assign_savant_actual_league,
    summarize_savant_contacts,
    summarize_savant_terminal_outcomes,
)
from universal_baseball.mlb_performance_materialization import (
    classify_mlb_savant_contacts,
)
from universal_baseball.mlb_season_stats import (
    capture_manifest,
    fetch_mlb_hitting_backbone,
    fetch_mlb_team_leagues,
)
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.performance_contract import validate_batting_performance_contract
from universal_baseball.performance_season import build_batting_performance_season
from universal_baseball.retrosheet import find_plays_csv_member, load_plays_transitions
from universal_baseball.run_expectancy import estimate_run_expectancy
from universal_baseball.savant import (
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
START_DATE = date(2024, 3, 20)
END_DATE = date(2024, 9, 30)
SAVANT_CHUNK_DAYS = 4
CALIBRATION_GAMES_PER_LEAGUE = 45
RETROSHEET_URL = f"https://www.retrosheet.org/downloads/plays/{SEASON}plays.zip"
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
WORK_DIR = Path("data/quarantine/mlb-batting-performance-2024")
REPORT_DIR = Path("reports/generated/mlb-batting-performance-2024")
TABLE_DIR = REPORT_DIR / "tables"


def _date_chunks(start: date, end: date, days: int) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=days - 1), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _load_savant_season() -> tuple[pl.DataFrame, list[dict[str, object]]]:
    raw_dir = WORK_DIR / "savant"
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    for chunk_start, chunk_end in _date_chunks(START_DATE, END_DATE, SAVANT_CHUNK_DAYS):
        path = raw_dir / f"savant_{chunk_start}_{chunk_end}.csv"
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
                "response_sha256": sha256(content).hexdigest(),
                "response_byte_count": len(content),
                "raw_row_count": raw.height,
                "projected_row_count": projected.height,
                "retrieved_url": retrieved_url,
                "request_path": request_path,
                "status_code": status_code,
            }
        )
    combined = pl.concat(frames, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index", "pitch_number"]
    )
    if combined.is_empty():
        raise RuntimeError("2024 MLB Savant Performance source is empty")
    duplicates = (
        combined.group_by(["game_pk", "at_bat_index", "pitch_number"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise RuntimeError("2024 MLB Savant source contains duplicate canonical pitch keys")
    return combined, captures


def _load_retrosheet_matrix() -> tuple[pl.DataFrame, dict[str, object]]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = WORK_DIR / f"{SEASON}plays.zip"
    metadata = download_file(RETROSHEET_URL, archive_path, timeout_seconds=240)
    with ZipFile(archive_path) as archive:
        member = find_plays_csv_member(archive.namelist())
        csv_path = WORK_DIR / Path(member).name
        with archive.open(member) as source, csv_path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
    transitions = load_plays_transitions(csv_path)
    matrix = estimate_run_expectancy(transitions)
    if matrix.height != 24:
        raise RuntimeError(f"2024 Retrosheet matrix has {matrix.height} states instead of 24")
    return matrix, {
        "url": RETROSHEET_URL,
        "archive_sha256": metadata["sha256"],
        "game_count": transitions.get_column("game_pk").n_unique(),
        "transition_count": transitions.height,
        "state_count": matrix.height,
    }


def _reconcile_terminal_outcomes(terminal: pl.DataFrame, backbone: pl.DataFrame) -> dict[str, int]:
    source = terminal.select(
        "season",
        "league_id",
        "player_id",
        pl.col("savant_plate_appearances").alias("source_pa"),
        pl.col("savant_base_on_balls").alias("source_bb"),
        pl.col("savant_hit_by_pitch").alias("source_hbp"),
        pl.col("savant_strike_outs").alias("source_k"),
    )
    expected = backbone.select(
        "season",
        "league_id",
        "player_id",
        pl.col("batting_plate_appearances").alias("expected_pa"),
        pl.col("batting_base_on_balls").alias("expected_bb"),
        pl.col("batting_hit_by_pitch").alias("expected_hbp"),
        pl.col("batting_strike_outs").alias("expected_k"),
    )
    comparison = source.join(
        expected,
        on=["season", "league_id", "player_id"],
        how="full",
        coalesce=True,
    ).with_columns(
        *[
            pl.col(column).fill_null(0).cast(pl.Int64)
            for column in (
                "source_pa", "source_bb", "source_hbp", "source_k",
                "expected_pa", "expected_bb", "expected_hbp", "expected_k",
            )
        ]
    )
    mismatches = comparison.filter(
        (pl.col("source_pa") != pl.col("expected_pa"))
        | (pl.col("source_bb") != pl.col("expected_bb"))
        | (pl.col("source_hbp") != pl.col("expected_hbp"))
        | (pl.col("source_k") != pl.col("expected_k"))
    )
    if not mismatches.is_empty():
        mismatches.write_csv(REPORT_DIR / "outcome_reconciliation_mismatches.csv")
        raise RuntimeError(
            f"MLB source/backbone outcome reconciliation failed for {mismatches.height} player-league rows"
        )
    return {
        "player_league_row_count": comparison.height,
        "mismatch_row_count": mismatches.height,
        "plate_appearances": int(comparison.get_column("expected_pa").sum() or 0),
        "base_on_balls": int(comparison.get_column("expected_bb").sum() or 0),
        "hit_by_pitch": int(comparison.get_column("expected_hbp").sum() or 0),
        "strike_outs": int(comparison.get_column("expected_k").sum() or 0),
    }


def _build_calibration_events(
    matrix: pl.DataFrame,
    team_to_league: dict[int, int],
) -> tuple[pl.DataFrame, dict[str, object]]:
    response = requests.get(
        SCHEDULE_URL,
        params={"sportId": 1, "season": SEASON, "gameType": "R"},
        timeout=120,
    )
    response.raise_for_status()
    schedule_bytes = response.content
    candidates = intraleague_schedule_candidates(response.json(), team_to_league)
    selected = {
        league_id: spread_sample(rows, CALIBRATION_GAMES_PER_LEAGUE)
        for league_id, rows in candidates.items()
    }

    frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    session = new_official_session()
    try:
        for league_id in sorted(selected):
            for game in selected[league_id]:
                game_pk = int(game["game_pk"])
                capture = capture_official_json(f"game/{game_pk}/playByPlay", session=session)
                frames.append(
                    calibration_events_from_official_payload(
                        game_pk,
                        capture.data,
                        matrix,
                        season=SEASON,
                        league_id=int(league_id),
                        game_date=str(game["game_date"]),
                        source_snapshot_id=f"official:{capture.content_sha256}",
                    )
                )
                captures.append(
                    {
                        "game_pk": game_pk,
                        "league_id": int(league_id),
                        "game_date": str(game["game_date"]),
                        "response_sha256": capture.content_sha256,
                    }
                )
    finally:
        session.close()

    events = pl.concat(frames, how="vertical_relaxed").sort(
        ["league_id", "game_date", "game_pk", "at_bat_index"]
    )
    return events, {
        "schedule_sha256": sha256(schedule_bytes).hexdigest(),
        "candidate_counts": {str(k): len(v) for k, v in candidates.items()},
        "selected_game_count": sum(len(rows) for rows in selected.values()),
        "selected_games": {str(k): rows for k, rows in selected.items()},
        "official_capture_count": len(captures),
        "official_captures": captures,
    }


def _duckdb_validate(summary_path: Path, profile_path: Path, values_path: Path) -> dict[str, int]:
    connection = duckdb.connect()
    try:
        summary_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(summary_path)]).fetchone()[0])
        summary_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id FROM read_parquet(?))",
            [str(summary_path)],
        ).fetchone()[0])
        profile_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(profile_path)]).fetchone()[0])
        profile_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id, core_bin FROM read_parquet(?))",
            [str(profile_path)],
        ).fetchone()[0])
        value_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(values_path)]).fetchone()[0])
        value_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, core_bin FROM read_parquet(?))",
            [str(values_path)],
        ).fetchone()[0])
    finally:
        connection.close()
    if (summary_rows, profile_rows, value_rows) != (summary_unique, profile_unique, value_unique):
        raise RuntimeError("MLB Performance parquet violates canonical-grain uniqueness")
    return {
        "summary_rows": summary_rows,
        "summary_unique_keys": summary_unique,
        "profile_rows": profile_rows,
        "profile_unique_keys": profile_unique,
        "bin_value_rows": value_rows,
        "bin_value_unique_keys": value_unique,
    }


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    savant, savant_captures = _load_savant_season()
    teams, team_response_bytes = fetch_mlb_team_leagues(SEASON)
    savant = assign_savant_actual_league(savant, teams)
    team_to_league = {int(row.team_id): int(row.league_id) for row in teams}
    backbone, backbone_captures = fetch_mlb_hitting_backbone(SEASON)

    terminal = summarize_savant_terminal_outcomes(savant)
    reconciliation = _reconcile_terminal_outcomes(terminal, backbone)
    contacts_by_player = summarize_savant_contacts(savant)
    contact_total = int(contacts_by_player.get_column("savant_contact_count").sum() or 0)
    backbone_contact_total = int(backbone.get_column("batting_balls_in_play").sum() or 0)
    contact_residual = contact_total - backbone_contact_total

    classified_contacts = classify_mlb_savant_contacts(savant)

    matrix, retrosheet_meta = _load_retrosheet_matrix()
    calibration_events, calibration_meta = _build_calibration_events(matrix, team_to_league)
    coverage = bin_calibration_coverage(calibration_events)
    if coverage.filter(pl.col("re24_coverage_rate") < 1.0).height:
        raise RuntimeError("MLB calibration sample contains core bins without RE24 coverage")
    direct_values = summarize_direct_bin_values(calibration_events)
    bin_values = estimate_certified_mlb_bin_values(direct_values)
    if bin_values.filter(~pl.col("estimator_certified")).height:
        raise RuntimeError("MLB calibration failed to produce certified AL/NL bin values")

    summary, profile = build_batting_performance_season(
        backbone,
        classified_contacts,
        bin_values,
    )
    contract = validate_batting_performance_contract(
        summary,
        profile,
        bin_values,
        require_certified_values=True,
    )

    summary_path = TABLE_DIR / "batting_performance_summary_2024_mlb.parquet"
    profile_path = TABLE_DIR / "batting_performance_bins_2024_mlb.parquet"
    values_path = TABLE_DIR / "league_bin_values_2024_mlb.parquet"
    summary_artifact = write_canonical_parquet(summary, summary_path, table_name="batting_performance_summary_mlb")
    profile_artifact = write_canonical_parquet(profile, profile_path, table_name="batting_performance_bins_mlb")
    values_artifact = write_canonical_parquet(bin_values, values_path, table_name="league_performance_bin_values_mlb")
    duckdb_metrics = _duckdb_validate(summary_path, profile_path, values_path)

    unknown_contacts = int(summary.get_column("unknown_contact_count").sum() or 0)
    total_contacts = int(summary.get_column("contact_event_count").sum() or 0)
    payload = {
        "report_schema_version": 1,
        "scope": {
            "season": SEASON,
            "coverage": "completed MLB regular season at actual AL/NL grain",
            "performance_contract": contract["contract_version"],
        },
        "source": {
            "savant_chunk_count": len(savant_captures),
            "savant_captures": savant_captures,
            "team_authority_sha256": sha256(team_response_bytes).hexdigest(),
            "bulk_stats_manifest": json.loads(capture_manifest(backbone_captures)),
            "outcome_reconciliation": reconciliation,
            "savant_contact_count": contact_total,
            "aggregate_contact_count": backbone_contact_total,
            "net_contact_residual": contact_residual,
        },
        "run_value": {
            "retrosheet": retrosheet_meta,
            "calibration": calibration_meta,
            "direct_bin_row_count": direct_values.height,
            "certified_bin_row_count": bin_values.height,
            "prior_strength": 5,
            "policy": "same-bin AL<->NL peer pooling; ADR 023",
        },
        "performance_contract": contract,
        "contact_quality": {
            "unknown_contact_count": unknown_contacts,
            "unknown_contact_rate": unknown_contacts / total_contacts if total_contacts else None,
        },
        "storage": {
            "summary": summary_artifact.as_record(),
            "profile": profile_artifact.as_record(),
            "bin_values": values_artifact.as_record(),
            "duckdb": duckdb_metrics,
        },
        "interpretation": (
            "Observed 2024 batting Performance at actual AL/NL grain. This is the MLB "
            "reporting anchor for later Current Talent translation; it is not a latent "
            "talent estimate, projection, playing-time forecast, WAR value, or ranking."
        ),
    }
    (REPORT_DIR / "mlb_batting_performance_2024.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB batting Performance materialization — 2024",
        "",
        f"- Player × actual-league × season rows: {contract['summary_row_count']:,}",
        f"- Plate appearances: {contract['total_plate_appearances']:,}",
        f"- Classified contact events: {contract['total_contact_events']:,}",
        f"- Screened core Performance events: {contract['total_core_profile_events']:,}",
        f"- Core-profile coverage: {contract['core_profile_coverage_rate']:.2%}",
        f"- Unknown contacts: {unknown_contacts:,} ({unknown_contacts / total_contacts if total_contacts else 0:.3%})",
        f"- Net Savant contact residual vs aggregate: {contact_residual:+,}",
        f"- AL/NL certified bin-value rows: {bin_values.height:,}",
        "- Contextual peer prior strength: 5 prior-equivalent occurrences",
        f"- Outcome reconciliation mismatches: {reconciliation['mismatch_row_count']:,}",
        f"- DuckDB unique summary keys: {duckdb_metrics['summary_unique_keys']:,}/{duckdb_metrics['summary_rows']:,}",
        "",
        "This table satisfies the same batting_performance_v1 output contract as affiliated MiLB and supplies the MLB anchor required before common-scale Current Talent fitting.",
    ]
    text = "\n".join(lines) + "\n"
    (REPORT_DIR / "mlb_batting_performance_2024.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
