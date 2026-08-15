"""Generic 24-state run expectancy and RE24 transforms.

The formulas follow standard public RE24 implementations such as baseballr:

    RE24 = runs_scored + RE(after) - RE(before)

The estimator deliberately learns only from *completed half-innings* whose last
state transition reaches three outs. That is more portable than hard-coding a
regulation inning cutoff and automatically excludes walkoff/truncated halves
from the run-expectancy sample.

This module is environment-agnostic. Callers may supply grouping columns such
as league/competition + season. Pooling/shrinkage across sparse environments is
a later calibration layer, not hidden inside these deterministic transforms.
"""

from __future__ import annotations

from collections.abc import Sequence

import polars as pl


RUN_EXPECTANCY_REQUIRED_COLUMNS = {
    "game_pk",
    "inning",
    "half_inning",
    "at_bat_index",
    "transition_index",
    "start_outs",
    "end_outs",
    "start_bases_code",
    "end_bases_code",
    "runs_scored",
    "start_bat_score",
    "end_bat_score",
    "re24_state_event_candidate",
    "quality_flags_json",
}


def _validate_state_bounds(frame: pl.DataFrame) -> None:
    invalid = frame.filter(
        (pl.col("start_outs") < 0)
        | (pl.col("start_outs") > 2)
        | (pl.col("end_outs") < 0)
        | (pl.col("end_outs") > 3)
        | (pl.col("start_bases_code") < 0)
        | (pl.col("start_bases_code") > 7)
        | (pl.col("end_bases_code") < 0)
        | (pl.col("end_bases_code") > 7)
    )
    if not invalid.is_empty():
        raise ValueError("state transition contains invalid base/out state")
    inning_end_with_bases = frame.filter(
        (pl.col("end_outs") == 3) & (pl.col("end_bases_code") != 0)
    )
    if not inning_end_with_bases.is_empty():
        raise ValueError("three-out transition must have empty end-base state")


def _validated_candidates(transitions: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(RUN_EXPECTANCY_REQUIRED_COLUMNS - set(transitions.columns))
    if missing:
        raise ValueError(f"state transitions missing RE24 columns: {missing}")
    candidates = transitions.filter(pl.col("re24_state_event_candidate"))
    if candidates.is_empty():
        raise ValueError("no RE24 state-event candidates available")
    dirty = candidates.filter(pl.col("quality_flags_json") != "[]")
    if not dirty.is_empty():
        raise ValueError(
            "RE24 input contains replay quality flags; resolve or exclude them before estimation"
        )
    _validate_state_bounds(candidates)
    return candidates.sort(
        ["game_pk", "inning", "half_inning", "at_bat_index", "transition_index"]
    )


def _validate_group_columns(frame: pl.DataFrame, group_columns: Sequence[str]) -> list[str]:
    columns = list(group_columns)
    if len(columns) != len(set(columns)):
        raise ValueError("run-expectancy grouping columns must be unique")
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"run-expectancy grouping columns are missing: {missing}")
    forbidden = {
        "start_outs",
        "end_outs",
        "start_bases_code",
        "end_bases_code",
        "runs_scored",
    }
    overlap = sorted(set(columns) & forbidden)
    if overlap:
        raise ValueError(f"state fields cannot be environment grouping columns: {overlap}")
    return columns


def _half_keys() -> list[str]:
    return ["game_pk", "inning", "half_inning"]


def add_half_inning_boundaries(transitions: pl.DataFrame) -> pl.DataFrame:
    """Add deterministic completed/terminal-half metadata to clean candidates."""

    working = _validated_candidates(transitions)
    keys = _half_keys()
    summaries = (
        working.group_by(keys, maintain_order=True)
        .agg(
            pl.col("end_outs").last().alias("half_final_outs"),
            pl.col("end_bat_score").last().alias("half_final_bat_score"),
            pl.len().alias("half_transition_count"),
        )
        .with_columns((pl.col("half_final_outs") == 3).alias("half_completed_three_outs"))
    )
    result = working.join(summaries, on=keys, how="left")

    # Mark the final candidate transition within each half. Using a per-half
    # ordinal avoids relying on atBatIndex alone when a PA contains preterminal
    # runner transitions.
    result = result.with_columns(
        pl.int_range(pl.len()).over(keys).alias("__half_ordinal")
    ).with_columns(
        (pl.col("__half_ordinal") == pl.col("half_transition_count") - 1).alias(
            "is_half_terminal_transition"
        )
    ).drop("__half_ordinal")
    return result


def estimate_run_expectancy(
    transitions: pl.DataFrame,
    *,
    group_columns: Sequence[str] = (),
) -> pl.DataFrame:
    """Estimate mean runs remaining for observed 24 base/out states.

    Only start states from half-innings completed by three outs contribute to
    the estimator. Each state-event visit contributes one observation:

        runs_remaining = final batting-team score in half - score at state start

    The result contains only observed states. Sparse-state pooling/fallback is a
    separate model-calibration decision.
    """

    working = add_half_inning_boundaries(transitions)
    groups = _validate_group_columns(working, group_columns)
    sample = working.filter(pl.col("half_completed_three_outs")).with_columns(
        (pl.col("half_final_bat_score") - pl.col("start_bat_score"))
        .cast(pl.Int64)
        .alias("runs_remaining")
    )
    if sample.is_empty():
        raise ValueError("no completed three-out half-innings available for RE estimation")
    negative = sample.filter(pl.col("runs_remaining") < 0)
    if not negative.is_empty():
        raise ValueError("completed half-inning has negative runs remaining")

    state_keys = [*groups, "start_outs", "start_bases_code"]
    return (
        sample.group_by(state_keys)
        .agg(
            pl.col("runs_remaining").mean().alias("run_expectancy"),
            pl.len().alias("state_sample_size"),
            pl.col("game_pk").n_unique().alias("state_game_count"),
        )
        .sort(state_keys)
    )


def attach_re24(
    transitions: pl.DataFrame,
    run_expectancy: pl.DataFrame,
    *,
    group_columns: Sequence[str] = (),
) -> pl.DataFrame:
    """Attach RE before/after and contextual RE24 to state transitions.

    The final transition of any half-inning receives RE(after)=0. This includes
    three-out endings and walkoff/truncated halves. Nonterminal end states must
    be present in the supplied run-expectancy table or the result remains null
    and ``re24_available`` is false.
    """

    working = add_half_inning_boundaries(transitions)
    groups = _validate_group_columns(working, group_columns)
    matrix_required = {*groups, "start_outs", "start_bases_code", "run_expectancy"}
    missing_matrix = sorted(matrix_required - set(run_expectancy.columns))
    if missing_matrix:
        raise ValueError(f"run-expectancy table missing columns: {missing_matrix}")

    duplicate_matrix = (
        run_expectancy.group_by([*groups, "start_outs", "start_bases_code"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_matrix.is_empty():
        raise ValueError("run-expectancy table has duplicate environment/state rows")

    before_lookup = run_expectancy.select(
        [
            *groups,
            "start_outs",
            "start_bases_code",
            pl.col("run_expectancy").alias("run_expectancy_before"),
        ]
    )
    after_lookup = run_expectancy.select(
        [
            *groups,
            pl.col("start_outs").alias("end_outs"),
            pl.col("start_bases_code").alias("end_bases_code"),
            pl.col("run_expectancy").alias("__matrix_re_after"),
        ]
    )

    result = (
        working.join(
            before_lookup,
            on=[*groups, "start_outs", "start_bases_code"],
            how="left",
        )
        .join(
            after_lookup,
            on=[*groups, "end_outs", "end_bases_code"],
            how="left",
        )
        .with_columns(
            pl.when(pl.col("is_half_terminal_transition"))
            .then(pl.lit(0.0))
            .otherwise(pl.col("__matrix_re_after"))
            .alias("run_expectancy_after")
        )
        .with_columns(
            (
                pl.col("run_expectancy_before").is_not_null()
                & pl.col("run_expectancy_after").is_not_null()
            ).alias("re24_available")
        )
        .with_columns(
            pl.when(pl.col("re24_available"))
            .then(
                pl.col("runs_scored").cast(pl.Float64)
                + pl.col("run_expectancy_after")
                - pl.col("run_expectancy_before")
            )
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("re24")
        )
        .drop("__matrix_re_after")
    )
    return result


def run_expectancy_coverage(re24_frame: pl.DataFrame) -> dict[str, int | float]:
    """Summarize matrix coverage without silently dropping unavailable events."""

    required = {"re24_available", "re24"}
    missing = sorted(required - set(re24_frame.columns))
    if missing:
        raise ValueError(f"RE24 frame missing coverage columns: {missing}")
    total = re24_frame.height
    available = int(re24_frame.get_column("re24_available").sum()) if total else 0
    return {
        "transition_count": total,
        "re24_available_count": available,
        "re24_missing_count": total - available,
        "re24_coverage_rate": available / total if total else 0.0,
    }
