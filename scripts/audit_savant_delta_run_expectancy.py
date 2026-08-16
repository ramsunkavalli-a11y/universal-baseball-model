#!/usr/bin/env python
"""Audit whether Savant ``delta_run_exp`` can replace MLB state replay for value.

This is deliberately a *decision audit*, not an acceptance test with a tuned
numeric threshold. Baseball Savant documents ``delta_run_exp`` as the change in
run expectancy across a pitch, which sounds like the terminal-transition RE24
quantity used by the Performance layer. We verify that claim against the
project's independently validated state-transition machinery rather than
assuming equivalence from the field name.

Design:

1. fetch the same three 2024 Savant audit dates used by source certification;
2. take four deterministic regular-season games per date;
3. retain Savant's terminal true-PA pitch and ``delta_run_exp``;
4. replay official Stats API state transitions for those games;
5. estimate a full-2024 MLB 24-state matrix from independent Retrosheet plays;
6. attach that matrix to the official terminal transitions;
7. compare Savant vs Retrosheet-matrix RE24 event by event, by transition
   signature, and by the universal Performance bins.

The two value systems are not assumed to use the identical RE matrix. A stable
state-transition signature and close bin-level values can still justify Savant
as the reusable MLB contextual-value source; material disagreement rejects that
shortcut and leaves official/Retrosheet replay as the value path.
"""

from __future__ import annotations

from datetime import date
import json
import math
from pathlib import Path
from typing import Any, Mapping
from zipfile import ZipFile

import polars as pl

from audit_retrosheet_run_expectancy import _find_csv, _load_transitions
from universal_baseball.certification import download_file
from universal_baseball.official_capture import capture_official_json
from universal_baseball.performance_events import (
    FOUL_AIR_TRAJECTORY_FAMILIES,
    FOUL_TERRITORY_REGEX,
    TRAJECTORY_FAMILY,
)
from universal_baseball.batted_ball_direction import (
    batted_ball_direction_expr,
    field_spray_angle_expr,
)
from universal_baseball.run_expectancy import attach_re24, estimate_run_expectancy
from universal_baseball.savant import (
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


REPORT_DIR = Path("reports/generated/savant-delta-run-expectancy")
WORK_DIR = Path("data/quarantine/savant-delta-run-expectancy")
RETROSHEET_URL = "https://www.retrosheet.org/downloads/plays/2024plays.zip"
AUDIT_DATES = (date(2024, 4, 15), date(2024, 6, 15), date(2024, 9, 15))
GAMES_PER_DATE = 4


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _pearson(frame: pl.DataFrame, left: str, right: str) -> float | None:
    if frame.height < 2:
        return None
    value = frame.select(pl.corr(left, right)).item()
    return float(value) if value is not None and math.isfinite(float(value)) else None


def _error_metrics(frame: pl.DataFrame, left: str, right: str) -> dict[str, float | int | None]:
    if frame.is_empty():
        return {
            "count": 0,
            "mean_left": None,
            "mean_right": None,
            "mean_difference": None,
            "mae": None,
            "rmse": None,
            "pearson": None,
        }
    diff = pl.col(left) - pl.col(right)
    row = frame.select(
        pl.len().alias("count"),
        pl.col(left).mean().alias("mean_left"),
        pl.col(right).mean().alias("mean_right"),
        diff.mean().alias("mean_difference"),
        diff.abs().mean().alias("mae"),
        (diff.pow(2).mean().sqrt()).alias("rmse"),
    ).to_dicts()[0]
    return {
        **row,
        "pearson": _pearson(frame, left, right),
    }


def _load_retrosheet_matrix() -> tuple[pl.DataFrame, dict[str, Any]]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = WORK_DIR / "2024plays.zip"
    metadata = download_file(RETROSHEET_URL, archive_path, timeout_seconds=240)
    with ZipFile(archive_path) as archive:
        member = _find_csv(archive)
        csv_path = WORK_DIR / Path(member).name
        with archive.open(member) as source, csv_path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
    transitions = _load_transitions(csv_path)
    matrix = estimate_run_expectancy(transitions)
    if matrix.height != 24:
        raise RuntimeError(f"2024 Retrosheet matrix has {matrix.height} states instead of 24")
    return matrix, {
        "url": RETROSHEET_URL,
        "archive_sha256": metadata["sha256"],
        "game_count": transitions.get_column("game_pk").n_unique(),
        "candidate_transition_count": transitions.height,
        "state_count": matrix.height,
    }


def _load_savant_sample() -> tuple[pl.DataFrame, list[int], list[dict[str, Any]]]:
    frames: list[pl.DataFrame] = []
    games: list[int] = []
    captures: list[dict[str, Any]] = []
    for audit_date in AUDIT_DATES:
        capture = fetch_savant_csv(audit_date, audit_date)
        raw = read_savant_csv_bytes(capture.response_bytes)
        if "delta_run_exp" not in raw.columns:
            raise RuntimeError("Savant CSV does not expose delta_run_exp")
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        delta = raw.select(
            pl.col("game_pk").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
            pl.col("at_bat_number").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
            pl.col("pitch_number").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
            pl.col("delta_run_exp").cast(pl.Float64, strict=False).alias("savant_delta_run_exp"),
        ).with_columns(
            (pl.col("at_bat_number") - 1).alias("at_bat_index")
        ).drop("at_bat_number")
        projected = projected.join(
            delta,
            on=["game_pk", "at_bat_index", "pitch_number"],
            how="left",
        )
        available_games = sorted(
            int(value) for value in projected.get_column("game_pk").unique().to_list()
        )
        chosen = available_games[:GAMES_PER_DATE]
        if len(chosen) != GAMES_PER_DATE:
            raise RuntimeError(f"insufficient Savant games on {audit_date}: {len(chosen)}")
        games.extend(chosen)
        frames.append(projected.filter(pl.col("game_pk").is_in(chosen)))
        captures.append(
            {
                "date": str(audit_date),
                "selected_game_ids": chosen,
                "projected_row_count": projected.height,
                "delta_non_null_count": projected.get_column("savant_delta_run_exp").is_not_null().sum(),
            }
        )
    return pl.concat(frames, how="vertical_relaxed"), sorted(set(games)), captures


def _official_terminal_values(game_ids: list[int], matrix: pl.DataFrame) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for game_id in game_ids:
        capture = capture_official_json(f"game/{game_id}/playByPlay")
        if not isinstance(capture.data, Mapping):
            raise RuntimeError(f"official game {game_id} playByPlay is not an object")
        transitions = build_official_state_transitions_v2(
            game_id,
            capture.data,
            source_snapshot_id=f"audit:{capture.content_sha256}",
            normalization_id="audit:savant-delta-run-exp-v1",
        )
        valued = attach_re24(transitions, matrix)
        terminal = valued.filter(
            pl.col("is_plate_appearance_result") & pl.col("re24_available")
        ).select(
            "game_pk",
            "at_bat_index",
            "event_type",
            "start_outs",
            "start_bases_code",
            "end_outs",
            "end_bases_code",
            "runs_scored",
            pl.col("re24").alias("retrosheet_matrix_re24"),
        )
        frames.append(terminal)
    return pl.concat(frames, how="vertical_relaxed")


def _trajectory_expr() -> pl.Expr:
    expression = pl.lit("UNKNOWN")
    for source_value, family in TRAJECTORY_FAMILY.items():
        expression = pl.when(pl.col("bb_type") == source_value).then(
            pl.lit(family)
        ).otherwise(expression)
    return expression


def _performance_bins(savant: pl.DataFrame) -> pl.DataFrame:
    terminal = savant.filter(pl.col("is_plate_appearance_terminal")).with_columns(
        _trajectory_expr().alias("trajectory_family"),
        field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle"),
        batted_ball_direction_expr(
            pl.col("hc_x"), pl.col("hc_y"), pl.col("batter_side")
        ).alias("direction"),
    )
    candidate_foul_air = pl.col("trajectory_family").is_in(
        sorted(FOUL_AIR_TRAJECTORY_FAMILIES)
    )
    narrative_present = pl.col("result_description").is_not_null() & (
        pl.col("result_description").str.strip_chars().str.len_chars() > 0
    )
    foul_territory = (
        candidate_foul_air
        & narrative_present
        & pl.col("result_description").str.contains(FOUL_TERRITORY_REGEX)
    )
    direction = pl.col("direction")
    trajectory = pl.col("trajectory_family")
    contact_bin = (
        pl.when(trajectory == "IFFB")
        .then(pl.lit("IFFB"))
        .when((trajectory == "OFFB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("OFFB")], separator="_"))
        .when((trajectory == "LD") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("LD")], separator="_"))
        .when((trajectory == "GB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("GB")], separator="_"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )
    outcome = pl.col("events")
    core_bin = (
        pl.when(outcome.is_in(["walk", "hit_by_pitch", "intent_walk"]))
        .then(pl.lit("BB_HBP"))
        .when(outcome.is_in(["strikeout", "strikeout_double_play"]))
        .then(pl.lit("K"))
        .when(
            contact_bin.is_not_null()
            & (~candidate_foul_air | (~foul_territory & narrative_present))
        )
        .then(contact_bin)
        .otherwise(pl.lit(None, dtype=pl.String))
    )
    return terminal.with_columns(core_bin.alias("core_bin")).select(
        "game_pk",
        "at_bat_index",
        "core_bin",
        "savant_delta_run_exp",
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    matrix, retrosheet_meta = _load_retrosheet_matrix()
    savant, games, captures = _load_savant_sample()
    official = _official_terminal_values(games, matrix)
    bins = _performance_bins(savant)

    terminal = savant.filter(pl.col("is_plate_appearance_terminal")).select(
        "game_pk",
        "at_bat_index",
        "events",
        "pitch_number",
        "savant_delta_run_exp",
    )
    comparison = terminal.join(
        official,
        on=["game_pk", "at_bat_index"],
        how="full",
        coalesce=True,
    ).with_columns(
        (
            pl.col("savant_delta_run_exp") - pl.col("retrosheet_matrix_re24")
        ).alias("value_difference")
    )
    paired = comparison.filter(
        pl.col("savant_delta_run_exp").is_not_null()
        & pl.col("retrosheet_matrix_re24").is_not_null()
    )
    savant_missing = comparison.filter(
        pl.col("retrosheet_matrix_re24").is_not_null()
        & pl.col("savant_delta_run_exp").is_null()
    )
    official_missing = comparison.filter(
        pl.col("savant_delta_run_exp").is_not_null()
        & pl.col("retrosheet_matrix_re24").is_null()
    )

    signature_columns = [
        "start_outs",
        "start_bases_code",
        "end_outs",
        "end_bases_code",
        "runs_scored",
    ]
    signature = (
        paired.group_by(signature_columns)
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("savant_delta_run_exp").mean().alias("mean_savant_delta"),
            pl.col("savant_delta_run_exp").min().alias("min_savant_delta"),
            pl.col("savant_delta_run_exp").max().alias("max_savant_delta"),
            pl.col("retrosheet_matrix_re24").mean().alias("mean_retrosheet_re24"),
        )
        .with_columns(
            (pl.col("max_savant_delta") - pl.col("min_savant_delta")).alias(
                "savant_within_signature_range"
            ),
            (pl.col("mean_savant_delta") - pl.col("mean_retrosheet_re24")).alias(
                "mean_value_difference"
            ),
        )
        .sort("occurrence_count", descending=True)
    )

    bin_comparison = (
        bins.filter(pl.col("core_bin").is_not_null())
        .join(
            official.select(
                "game_pk", "at_bat_index", "retrosheet_matrix_re24"
            ),
            on=["game_pk", "at_bat_index"],
            how="inner",
        )
        .group_by("core_bin")
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("savant_delta_run_exp").mean().alias("mean_savant_delta"),
            pl.col("retrosheet_matrix_re24").mean().alias("mean_retrosheet_re24"),
        )
        .with_columns(
            (pl.col("mean_savant_delta") - pl.col("mean_retrosheet_re24")).alias(
                "mean_value_difference"
            )
        )
        .sort("core_bin")
    )

    event_metrics = _error_metrics(
        paired,
        "savant_delta_run_exp",
        "retrosheet_matrix_re24",
    )
    weighted_bin_mae = (
        bin_comparison.select(
            (
                (
                    pl.col("mean_value_difference").abs()
                    * pl.col("occurrence_count")
                ).sum()
                / pl.col("occurrence_count").sum()
            ).alias("weighted_bin_mae")
        ).item()
        if not bin_comparison.is_empty()
        else None
    )
    max_signature_range = (
        float(signature.get_column("savant_within_signature_range").max() or 0.0)
        if not signature.is_empty()
        else None
    )
    nonconstant_signatures = signature.filter(
        pl.col("savant_within_signature_range") > 1e-9
    )

    comparison.write_csv(REPORT_DIR / "terminal_event_value_comparison.csv")
    signature.write_csv(REPORT_DIR / "transition_signature_values.csv")
    bin_comparison.write_csv(REPORT_DIR / "performance_bin_value_comparison.csv")

    payload = {
        "report_schema_version": 1,
        "season": 2024,
        "sample": {
            "dates": [str(value) for value in AUDIT_DATES],
            "game_count": len(games),
            "game_ids": games,
            "captures": captures,
        },
        "retrosheet_matrix": retrosheet_meta,
        "coverage": {
            "savant_true_pa_terminal_count": terminal.height,
            "official_valued_pa_terminal_count": official.height,
            "paired_value_count": paired.height,
            "official_value_without_savant_delta_count": savant_missing.height,
            "savant_delta_without_official_value_count": official_missing.height,
        },
        "event_value_comparison": event_metrics,
        "transition_signature_diagnostic": {
            "signature_count": signature.height,
            "nonconstant_savant_signature_count": nonconstant_signatures.height,
            "max_savant_within_signature_range": max_signature_range,
        },
        "performance_bin_diagnostic": {
            "bin_count": bin_comparison.height,
            "weighted_absolute_mean_bin_difference": weighted_bin_mae,
            "bins": bin_comparison.to_dicts(),
        },
        "decision_rule": (
            "No acceptance threshold is preselected. Coverage, state-signature consistency, "
            "event error, and Performance-bin mean differences are reviewed together."
        ),
    }
    (REPORT_DIR / "savant_delta_run_expectancy.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Savant delta_run_exp reuse audit — 2024",
        "",
        f"- Games: {len(games):,}",
        f"- Savant / official valued PA terminals: {terminal.height:,} / {official.height:,}",
        f"- Paired values: {paired.height:,}",
        f"- Official values missing Savant delta: {savant_missing.height:,}",
        f"- Savant deltas missing official value: {official_missing.height:,}",
        f"- Event MAE / RMSE: {event_metrics['mae']:.5f} / {event_metrics['rmse']:.5f}",
        f"- Event mean bias (Savant - Retrosheet matrix): {event_metrics['mean_difference']:+.5f}",
        f"- Event Pearson correlation: {event_metrics['pearson']:.6f}",
        f"- Transition signatures: {signature.height:,}",
        f"- Signatures with nonconstant Savant value: {nonconstant_signatures.height:,}",
        f"- Max within-signature Savant range: {max_signature_range:.9f}",
        f"- Core Performance bins compared: {bin_comparison.height:,}",
        f"- Occurrence-weighted absolute bin-mean difference: {weighted_bin_mae:.5f}",
        "",
        "This audit intentionally does not auto-accept or reject Savant delta_run_exp from a tuned cutoff.",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "savant_delta_run_expectancy.md").write_text(summary, encoding="utf-8")
    print(summary)

    if terminal.height != official.height or paired.height != terminal.height:
        raise RuntimeError("Savant delta_run_exp does not cover every sampled official true PA terminal")
    if savant_missing.height or official_missing.height:
        raise RuntimeError("Savant/offical terminal value coverage mismatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
