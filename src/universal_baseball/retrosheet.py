"""Thin adapter for Retrosheet's parsed season play CSVs.

Retrosheet is used as the independent event-account source for validating and
estimating the canonical 24-state run-expectancy matrix.  This module promotes
the already-certified play-table projection out of audit scripts so production
materialization can reproduce the same matrix without importing audit code.

It deliberately projects only the state-transition surface consumed by
``run_expectancy``; it is not a general Retrosheet parser.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import polars as pl


RETROSHEET_TRANSITION_SCHEMA: dict[str, pl.DataType] = {
    "game_pk": pl.String,
    "inning": pl.Int64,
    "half_inning": pl.String,
    "at_bat_index": pl.Int64,
    "transition_index": pl.Int64,
    "start_outs": pl.Int64,
    "end_outs": pl.Int64,
    "start_bases_code": pl.Int64,
    "end_bases_code": pl.Int64,
    "runs_scored": pl.Int64,
    "start_bat_score": pl.Int64,
    "end_bat_score": pl.Int64,
    "re24_state_event_candidate": pl.Boolean,
    "quality_flags_json": pl.String,
}


def find_plays_csv_member(names: Iterable[str]) -> str:
    """Choose the parsed play CSV member from a Retrosheet season archive."""

    members = [str(name) for name in names if str(name).lower().endswith(".csv")]
    if not members:
        raise ValueError("Retrosheet season archive contains no CSV member")
    return sorted(members, key=lambda name: ("play" not in name.lower(), name))[0]


def _base_code(prefix: str) -> pl.Expr:
    return (
        pl.when(pl.col(f"br1_{prefix}").fill_null("") != "").then(1).otherwise(0)
        + pl.when(pl.col(f"br2_{prefix}").fill_null("") != "").then(2).otherwise(0)
        + pl.when(pl.col(f"br3_{prefix}").fill_null("") != "").then(4).otherwise(0)
    )


def load_plays_transitions(csv_path: Path | str) -> pl.DataFrame:
    """Project Retrosheet parsed plays to canonical state-event transitions.

    Candidate rows are retained when they are plate appearances or when outs,
    base occupancy, or score changes.  This exactly matches the independently
    validated RE24 audit semantics.
    """

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
        *[
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
        (pl.col("start_bat_score") + pl.col("runs").fill_null(0)).alias("end_bat_score")
    )

    candidate = (
        (pl.col("pa") == 1)
        | (pl.col("outs_pre") != pl.col("outs_post"))
        | (pl.col("start_bases_code") != pl.col("end_bases_code"))
        | (pl.col("runs").fill_null(0) != 0)
    )
    return (
        frame.filter(candidate)
        .select(
            pl.col("gid").cast(pl.String).alias("game_pk"),
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
        .cast(RETROSHEET_TRANSITION_SCHEMA, strict=True)
        .sort(["game_pk", "inning", "half_inning", "at_bat_index"])
    )
