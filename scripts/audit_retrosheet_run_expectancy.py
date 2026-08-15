#!/usr/bin/env python
"""Validate generic RE24 transforms on the full 2025 Retrosheet play table."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.run_expectancy import (
    attach_re24,
    estimate_run_expectancy,
    run_expectancy_coverage,
)


RETROSHEET_URL = "https://www.retrosheet.org/downloads/plays/2025plays.zip"


def _find_csv(archive: ZipFile) -> str:
    members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
    if not members:
        raise RuntimeError("Retrosheet season archive contains no CSV member")
    # The parsed-season download currently contains one plays CSV. Prefer a
    # member with 'play' in the filename while remaining robust to naming drift.
    return sorted(members, key=lambda name: ("play" not in name.lower(), name))[0]


def _base_code(prefix: str) -> pl.Expr:
    return (
        pl.when(pl.col(f"br1_{prefix}").fill_null("") != "").then(1).otherwise(0)
        + pl.when(pl.col(f"br2_{prefix}").fill_null("") != "").then(2).otherwise(0)
        + pl.when(pl.col(f"br3_{prefix}").fill_null("") != "").then(4).otherwise(0)
    )


def _load_transitions(csv_path: Path) -> pl.DataFrame:
    columns = [
        "gid",
        "inning",
        "top_bot",
        "pn",
        "pa",
        "outs_pre",
        "outs_post",
        "br1_pre",
        "br2_pre",
        "br3_pre",
        "br1_post",
        "br2_post",
        "br3_post",
        "runs",
        "score_v",
        "score_h",
    ]
    frame = pl.read_csv(
        csv_path,
        columns=columns,
        infer_schema_length=10_000,
        null_values=[""],
    ).with_columns(
        [
            pl.col(column).cast(pl.Int64, strict=False)
            for column in (
                "inning",
                "top_bot",
                "pn",
                "pa",
                "outs_pre",
                "outs_post",
                "runs",
                "score_v",
                "score_h",
            )
        ]
    )
    frame = frame.with_columns(
        _base_code("pre").cast(pl.Int64).alias("start_bases_code"),
        _base_code("post").cast(pl.Int64).alias("end_bases_code"),
        pl.when(pl.col("top_bot") == 0)
        .then(pl.lit("top"))
        .otherwise(pl.lit("bottom"))
        .alias("half_inning"),
        pl.when(pl.col("top_bot") == 0)
        .then(pl.col("score_v"))
        .otherwise(pl.col("score_h"))
        .alias("start_bat_score"),
    ).with_columns(
        (pl.col("start_bat_score") + pl.col("runs")).alias("end_bat_score")
    )

    candidate = (
        (pl.col("pa") == 1)
        | (pl.col("outs_pre") != pl.col("outs_post"))
        | (pl.col("start_bases_code") != pl.col("end_bases_code"))
        | (pl.col("runs") != 0)
    )
    return (
        frame.filter(candidate)
        .select(
            pl.col("gid").alias("game_pk"),
            "inning",
            "half_inning",
            pl.col("pn").alias("at_bat_index"),
            pl.lit(0, dtype=pl.Int64).alias("transition_index"),
            pl.col("outs_pre").alias("start_outs"),
            pl.col("outs_post").alias("end_outs"),
            "start_bases_code",
            "end_bases_code",
            pl.col("runs").fill_null(0).alias("runs_scored"),
            "start_bat_score",
            "end_bat_score",
            pl.lit(True).alias("re24_state_event_candidate"),
            pl.lit("[]").alias("quality_flags_json"),
        )
        .sort(["game_pk", "inning", "half_inning", "at_bat_index"])
    )


def main() -> int:
    work_dir = Path("data/quarantine/retrosheet-re24")
    report_dir = Path("reports/generated/retrosheet-re24")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    zip_path = work_dir / "2025plays.zip"
    metadata = download_file(RETROSHEET_URL, zip_path, timeout_seconds=240)
    with ZipFile(zip_path) as archive:
        member = _find_csv(archive)
        csv_path = work_dir / Path(member).name
        with archive.open(member) as source, csv_path.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)

    transitions = _load_transitions(csv_path)
    matrix = estimate_run_expectancy(transitions)
    re24 = attach_re24(transitions, matrix)
    coverage = run_expectancy_coverage(re24)

    state_count = matrix.height
    if state_count != 24:
        raise RuntimeError(f"expected all 24 base/out states in full 2025 MLB; got {state_count}")

    complete_halves = (
        re24.filter(pl.col("half_completed_three_outs"))
        .select(["game_pk", "inning", "half_inning"])
        .unique()
        .height
    )
    incomplete_halves = (
        re24.filter(~pl.col("half_completed_three_outs"))
        .select(["game_pk", "inning", "half_inning"])
        .unique()
        .height
    )

    matrix_rows = matrix.sort(["start_outs", "start_bases_code"]).to_dicts()
    no_runner = {
        str(row["start_outs"]): row["run_expectancy"]
        for row in matrix_rows
        if row["start_bases_code"] == 0
    }
    bases_loaded = {
        str(row["start_outs"]): row["run_expectancy"]
        for row in matrix_rows
        if row["start_bases_code"] == 7
    }

    monotonic_empty_bases = (
        no_runner["0"] >= no_runner["1"] >= no_runner["2"]
    )
    monotonic_loaded_bases = (
        bases_loaded["0"] >= bases_loaded["1"] >= bases_loaded["2"]
    )

    payload = {
        "report_schema_version": 1,
        "retrosheet_url": RETROSHEET_URL,
        "retrosheet_archive_sha256": metadata["sha256"],
        "candidate_transition_count": transitions.height,
        "game_count": transitions.get_column("game_pk").n_unique(),
        "completed_three_out_half_count": complete_halves,
        "incomplete_half_count": incomplete_halves,
        "observed_base_out_state_count": state_count,
        "coverage": coverage,
        "empty_bases_run_expectancy_by_outs": no_runner,
        "bases_loaded_run_expectancy_by_outs": bases_loaded,
        "empty_bases_monotonic_by_outs": monotonic_empty_bases,
        "bases_loaded_monotonic_by_outs": monotonic_loaded_bases,
        "matrix": matrix_rows,
        "method": (
            "Each candidate state-event in a half inning completed with three outs contributes "
            "final_half_batting_score - start_bat_score to its start base/out state. "
            "RE24 is runs + RE(after) - RE(before); final transitions in any half receive RE(after)=0."
        ),
    }
    (report_dir / "retrosheet_re24.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# 2025 Retrosheet run-expectancy validation",
        "",
        f"- Candidate state transitions: {transitions.height:,}",
        f"- Games: {payload['game_count']:,}",
        f"- Three-out completed half-innings used for estimation: {complete_halves:,}",
        f"- Incomplete/walkoff half-innings excluded from estimation: {incomplete_halves:,}",
        f"- Observed base/out states: {state_count}/24",
        f"- RE24 coverage: {coverage['re24_available_count']:,}/{coverage['transition_count']:,} "
        f"({coverage['re24_coverage_rate']:.2%})",
        f"- Empty bases RE by outs: `{no_runner}`",
        f"- Bases loaded RE by outs: `{bases_loaded}`",
        f"- Empty-bases RE monotonic with outs: {monotonic_empty_bases}",
        f"- Bases-loaded RE monotonic with outs: {monotonic_loaded_bases}",
        "",
        "The full matrix is stored in the JSON artifact. This validates deterministic RE24 mechanics on an independent complete MLB event source; it does not define the eventual MiLB pooling/shrinkage strategy.",
        "",
        "Retrosheet attribution: The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at 20 Sunset Rd., Newark, DE 19711.",
        "",
    ]
    summary = "\n".join(lines)
    (report_dir / "retrosheet_re24.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
