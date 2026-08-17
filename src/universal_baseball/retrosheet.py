"""Thin adapters for Retrosheet parsed-season play CSVs.

Retrosheet is used as the independent event-account source for validating and
estimating the canonical 24-state run-expectancy matrix. This module promotes
only the small parsed-play surfaces consumed by deterministic project gates; it
is not a general Retrosheet parser.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
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

RETROSHEET_REGULAR_GAME_TYPES = frozenset({"regular", "playoff"})
RETROSHEET_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y%m%d",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%m/%d/%y",
)
RETROSHEET_CONTACT_VALUE_GROUPS = (
    "1B",
    "2B",
    "3B",
    "HR",
    "ROE",
    "FC_REACH",
    "SF",
    "MULTI_OUT",
    "OUT",
)


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


def _game_date_expr() -> pl.Expr:
    """Parse known Retrosheet CSV date encodings without format inference."""

    raw = pl.col("date").cast(pl.String).str.strip_chars()
    return pl.coalesce(
        [
            raw.str.strptime(pl.Date, format=date_format, strict=False)
            for date_format in RETROSHEET_DATE_FORMATS
        ]
    ).alias("game_date")


def _transition_projection(frame: pl.DataFrame) -> pl.DataFrame:
    frame = frame.with_columns(
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
            if column in frame.columns
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
    return frame.filter(candidate)


def load_plays_transitions(csv_path: Path | str) -> pl.DataFrame:
    """Project Retrosheet parsed plays to canonical state-event transitions."""

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
    )
    frame = _transition_projection(frame)
    return (
        frame.select(
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


def _flag(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Int64, strict=False).fill_null(0) == 1


def _terminal_group_expr() -> pl.Expr:
    """Map parsed Retrosheet PA flags to the frozen challenger-2 groups."""

    return (
        pl.when(_flag("gdp") | _flag("othdp") | _flag("tp"))
        .then(pl.lit("MULTI_OUT"))
        .when(_flag("single"))
        .then(pl.lit("1B"))
        .when(_flag("double"))
        .then(pl.lit("2B"))
        .when(_flag("triple"))
        .then(pl.lit("3B"))
        .when(_flag("hr"))
        .then(pl.lit("HR"))
        .when(_flag("roe"))
        .then(pl.lit("ROE"))
        .when(_flag("fc"))
        .then(pl.lit("FC_REACH"))
        .when(_flag("sf"))
        .then(pl.lit("SF"))
        .when(_flag("othout"))
        .then(pl.lit("OUT"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )


def load_plays_contact_value_transitions(
    csv_path: Path | str,
    *,
    cutoff_date: date,
) -> pl.DataFrame:
    """Load pre-cutoff regular-season transitions with contact-value metadata.

    Retrosheet's parsed play table already exposes game date/type and discrete PA
    outcome flags. All state-changing transitions are retained for RE estimation;
    ``contact_value_target_candidate`` marks non-bunt result-producing contact PAs
    (Retrosheet BIP plus home runs), and ``terminal_outcome_group`` is populated
    only when the frozen mapping supports the terminal result. Unsupported target
    candidates remain visible so callers can fail closed instead of silently
    dropping them.
    """

    columns = [
        "gid",
        "date",
        "gametype",
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
        "single",
        "double",
        "triple",
        "hr",
        "sh",
        "sf",
        "roe",
        "fc",
        "othout",
        "noout",
        "bip",
        "bunt",
        "gdp",
        "othdp",
        "tp",
    ]
    frame = pl.read_csv(
        csv_path,
        columns=columns,
        infer_schema_length=10_000,
        null_values=[""],
    ).with_columns(
        _game_date_expr(),
        pl.col("gametype").cast(pl.String).str.to_lowercase().alias("gametype"),
    )
    invalid_dates = frame.filter(pl.col("game_date").is_null())
    if not invalid_dates.is_empty():
        examples = (
            invalid_dates.select(pl.col("date").cast(pl.String).alias("raw_date"))
            .unique()
            .head(10)
            .get_column("raw_date")
            .to_list()
        )
        raise ValueError(f"Retrosheet parsed plays contain invalid game date examples={examples}")
    frame = frame.filter(
        (pl.col("game_date") < pl.lit(cutoff_date))
        & pl.col("gametype").is_in(sorted(RETROSHEET_REGULAR_GAME_TYPES))
    )
    if frame.is_empty():
        raise ValueError("no pre-cutoff regular-season Retrosheet plays available")
    frame = _transition_projection(frame).with_columns(
        (
            _flag("pa")
            & (_flag("bip") | _flag("hr"))
            & ~_flag("bunt")
            & ~_flag("sh")
        ).alias("contact_value_target_candidate"),
        _terminal_group_expr().alias("terminal_outcome_group"),
    ).with_columns(
        (
            pl.col("contact_value_target_candidate")
            & pl.col("terminal_outcome_group").is_not_null()
        ).alias("contact_value_mapping_supported")
    )
    return frame.select(
        pl.col("gid").cast(pl.String).alias("game_pk"),
        "game_date",
        "gametype",
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
        "contact_value_target_candidate",
        "contact_value_mapping_supported",
        "terminal_outcome_group",
    ).sort(["game_pk", "inning", "half_inning", "at_bat_index"])
