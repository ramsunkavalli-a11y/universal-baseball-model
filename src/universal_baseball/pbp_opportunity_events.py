"""Shared historical MiLB play-by-play opportunities for defense and baserunning.

The reusable armstjc files repeat the plate-appearance result and post-play
base state on every pitch row.  This module collapses that representation to
one terminal play before constructing two deliberately conservative views:

* a fielder opportunity is a non-home-run batted ball with a known first-touch
  position and the player occupying that position; and
* a runner opportunity compares the previous terminal post-play base state
  with the current terminal post-play state.  Ambiguous disappearances are
  retained as unknown rather than guessed.

The event table keeps park, level, handedness, pitcher, batter, batted-ball and
fielder context.  Expected-out and expected-advancement models therefore can
adjust the *outcome environment* before assigning a residual to a player.
"""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value_source import (
    attach_narrative_terminal_groups,
)


TERMINAL_KEY = ("game_pk", "at_bat_index")
FIELDING_OUT_GROUPS = frozenset({"OUT", "SF", "MULTI_OUT"})
FIELDING_REACH_GROUPS = frozenset({"1B", "2B", "3B", "ROE"})
FIELDING_CORE_GROUPS = FIELDING_OUT_GROUPS | FIELDING_REACH_GROUPS
RUNNER_CONTACT_GROUPS = frozenset({"1B", "2B", "3B", "OUT", "SF"})

_FIELDER_COLUMNS = tuple(f"fielder_{position}" for position in range(2, 10))
_INT_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "league_id",
    "batter",
    "pitcher",
    "inning",
    "outs_when_up",
    "hit_location",
    "on_1b",
    "on_2b",
    "on_3b",
    "bat_score",
    "fld_score",
    "post_bat_score",
    "post_fld_score",
    *_FIELDER_COLUMNS,
)
_TEXT_COLUMNS = (
    "game_date",
    "game_type",
    "home_team",
    "away_team",
    "inning_top_bot",
    "stand",
    "p_throws",
    "type",
    "bb_type",
    "description",
    "des",
    "if_fielding_alignment",
    "of_fielding_alignment",
)
_FLOAT_COLUMNS = ("hc_x", "hc_y")
_CATCHER_PITCH_INT_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "league_id",
    "batter",
    "pitcher",
    "fielder_2",
    "balls",
    "strikes",
)
_CATCHER_PITCH_FLOAT_COLUMNS = ("plate_x", "plate_z", "sz_top", "sz_bot")
_CATCHER_PITCH_TEXT_COLUMNS = (
    "game_date",
    "game_type",
    "home_team",
    "away_team",
    "inning_top_bot",
    "stand",
    "p_throws",
    "type",
    "description",
    "des",
)


def required_source_columns() -> tuple[str, ...]:
    """Return the raw source columns needed by the opportunity foundation."""

    return (*_INT_COLUMNS, *_TEXT_COLUMNS, *_FLOAT_COLUMNS)


def required_catcher_pitch_source_columns() -> tuple[str, ...]:
    """Return raw columns for framing and blocking opportunity preservation."""

    return (
        *_CATCHER_PITCH_INT_COLUMNS,
        *_CATCHER_PITCH_FLOAT_COLUMNS,
        *_CATCHER_PITCH_TEXT_COLUMNS,
    )


def _int_expr(name: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(name).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or name)
    )


def _normal_text(name: str) -> pl.Expr:
    return pl.when(
        pl.col(name).is_not_null()
        & (pl.col(name).cast(pl.String).str.strip_chars() != "")
    ).then(pl.col(name).cast(pl.String).str.strip_chars()).otherwise(None).alias(name)


def _first_non_null(name: str) -> pl.Expr:
    return pl.col(name).drop_nulls().first().alias(name)


def _non_null_variants(name: str) -> pl.Expr:
    return pl.col(name).drop_nulls().n_unique().alias(f"{name}__variant_count")


def _empty_terminal_schema() -> dict[str, pl.DataType]:
    schema: dict[str, pl.DataType] = {
        "season": pl.Int64,
        "level": pl.String,
        "source_asset": pl.String,
        "game_pk": pl.Int64,
        "at_bat_index": pl.Int64,
        "terminal_pitch_number": pl.Int64,
        "raw_terminal_row_count": pl.Int64,
    }
    for name in _INT_COLUMNS:
        if name not in {"game_pk", "at_bat_number", "pitch_number"}:
            schema[name] = pl.Int64
    for name in _TEXT_COLUMNS:
        schema[name] = pl.String
    for name in _FLOAT_COLUMNS:
        schema[name] = pl.Float64
    schema.update(
        {
            "pa_description": pl.String,
            "terminal_outcome_group": pl.String,
            "terminal_outcome_status": pl.String,
            "terminal_outcome_matches": pl.String,
            "park_key": pl.String,
            "defense_team": pl.String,
            "is_batted_ball": pl.Boolean,
            "batted_ball_out": pl.Boolean,
            "responsible_position": pl.Int64,
            "responsible_fielder_id": pl.Int64,
        }
    )
    return schema


def project_terminal_play_observations(
    raw_pbp: pl.DataFrame,
    *,
    source_asset: str,
    season: int,
    level: str,
    game_type: str = "R",
) -> pl.DataFrame:
    """Collapse one raw PBP asset to one auditable terminal row per PA.

    All non-null terminal values must agree within the asset.  This catches
    source drift while tolerating exact repeated rows in the public files.
    """

    missing = sorted(set(required_source_columns()) - set(raw_pbp.columns))
    if missing:
        raise ValueError(f"{source_asset} missing opportunity fields: {missing}")

    selected = raw_pbp.select(
        *[_int_expr(name) for name in _INT_COLUMNS],
        *[_normal_text(name) for name in _TEXT_COLUMNS],
        *[pl.col(name).cast(pl.Float64, strict=False).alias(name) for name in _FLOAT_COLUMNS],
    ).filter(pl.col("game_type") == str(game_type))
    if selected.is_empty():
        return pl.DataFrame(schema=_empty_terminal_schema())

    selected = selected.drop_nulls(["game_pk", "at_bat_number", "pitch_number"])
    terminal = (
        selected.with_columns(
            pl.col("pitch_number")
            .max()
            .over(["game_pk", "at_bat_number"])
            .alias("terminal_pitch_number")
        )
        .filter(pl.col("pitch_number") == pl.col("terminal_pitch_number"))
        .rename({"at_bat_number": "at_bat_index"})
    )

    value_columns = [
        name
        for name in terminal.columns
        if name
        not in {
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "terminal_pitch_number",
        }
    ]
    compact = terminal.group_by(list(TERMINAL_KEY)).agg(
        pl.col("terminal_pitch_number").first(),
        pl.len().alias("raw_terminal_row_count"),
        *[_first_non_null(name) for name in value_columns],
        *[_non_null_variants(name) for name in value_columns],
    )
    conflict_columns = [f"{name}__variant_count" for name in value_columns]
    conflicts = compact.filter(
        pl.any_horizontal(pl.col(name) > 1 for name in conflict_columns)
    )
    if conflicts.height:
        sample = conflicts.select(
            "game_pk", "at_bat_index", *conflict_columns
        ).head(5).to_dicts()
        raise ValueError(
            f"{source_asset} has conflicting terminal values within PA: {sample}"
        )
    compact = compact.drop(conflict_columns)

    compact = compact.with_columns(
        pl.coalesce([pl.col("des"), pl.col("description")]).alias("pa_description")
    )
    compact = attach_narrative_terminal_groups(compact)
    compact = compact.with_columns(
        pl.lit(int(season), dtype=pl.Int64).alias("season"),
        pl.lit(str(level)).alias("level"),
        pl.lit(str(source_asset)).alias("source_asset"),
        pl.concat_str(
            [pl.lit(str(season)), pl.col("home_team")], separator=":"
        ).alias("park_key"),
        pl.when(pl.col("inning_top_bot").str.to_lowercase() == "top")
        .then(pl.col("home_team"))
        .when(pl.col("inning_top_bot").str.to_lowercase() == "bot")
        .then(pl.col("away_team"))
        .otherwise(None)
        .alias("defense_team"),
        pl.col("hit_location").alias("responsible_position"),
    )

    fielder_expr: pl.Expr = pl.lit(None, dtype=pl.Int64)
    for position in range(2, 10):
        fielder_expr = (
            pl.when(pl.col("responsible_position") == position)
            .then(pl.col(f"fielder_{position}"))
            .otherwise(fielder_expr)
        )
    compact = compact.with_columns(
        pl.col("terminal_outcome_group")
        .is_in(sorted(FIELDING_CORE_GROUPS | {"FC_REACH", "HR"}))
        .alias("is_batted_ball"),
        pl.col("terminal_outcome_group")
        .is_in(sorted(FIELDING_OUT_GROUPS))
        .alias("batted_ball_out"),
        fielder_expr.alias("responsible_fielder_id"),
    )
    return compact.select(
        "season",
        "level",
        "source_asset",
        "game_pk",
        "at_bat_index",
        "terminal_pitch_number",
        "raw_terminal_row_count",
        *[
            name
            for name in (*_INT_COLUMNS, *_TEXT_COLUMNS, *_FLOAT_COLUMNS)
            if name not in {"game_pk", "at_bat_number", "pitch_number"}
        ],
        "pa_description",
        "terminal_outcome_group",
        "terminal_outcome_status",
        "terminal_outcome_matches",
        "park_key",
        "defense_team",
        "is_batted_ball",
        "batted_ball_out",
        "responsible_position",
        "responsible_fielder_id",
    ).sort(list(TERMINAL_KEY))


def resolve_overlapping_terminal_plays(frames: Iterable[pl.DataFrame]) -> pl.DataFrame:
    """Resolve overlapping release assets without using upload order as truth.

    Exact repeats are collapsed.  A key with conflicting model-relevant values
    is excluded and reported in ``resolution_status`` rather than guessed.
    """

    rows = [frame for frame in frames if not frame.is_empty()]
    if not rows:
        return pl.DataFrame(schema=_empty_terminal_schema())
    combined = pl.concat(rows, how="diagonal_relaxed")
    compare = [
        "game_date",
        "league_id",
        "level",
        "batter",
        "pitcher",
        "stand",
        "p_throws",
        "inning",
        "inning_top_bot",
        "outs_when_up",
        "bb_type",
        "hit_location",
        "hc_x",
        "hc_y",
        "pa_description",
        "terminal_outcome_group",
        "on_1b",
        "on_2b",
        "on_3b",
        *_FIELDER_COLUMNS,
    ]
    diagnostics = combined.group_by(list(TERMINAL_KEY)).agg(
        pl.col("source_asset").n_unique().alias("source_snapshot_count"),
        *[_non_null_variants(name) for name in compare],
    )
    variants = [f"{name}__variant_count" for name in compare]
    diagnostics = diagnostics.with_columns(
        pl.any_horizontal(pl.col(name) > 1 for name in variants).alias(
            "has_source_conflict"
        )
    ).select(*TERMINAL_KEY, "source_snapshot_count", "has_source_conflict")
    resolved = (
        combined.sort([*TERMINAL_KEY, "source_asset"])
        .unique(subset=list(TERMINAL_KEY), keep="first", maintain_order=True)
        .join(diagnostics, on=list(TERMINAL_KEY), validate="1:1")
        .with_columns(
            pl.when(pl.col("has_source_conflict"))
            .then(pl.lit("excluded_source_conflict"))
            .otherwise(pl.lit("resolved_non_null_consensus"))
            .alias("resolution_status")
        )
    )
    return resolved.sort(list(TERMINAL_KEY))


def add_sequence_start_state(terminal_plays: pl.DataFrame) -> pl.DataFrame:
    """Attach the previous terminal post-state within each half inning."""

    required = {
        "game_pk",
        "inning",
        "inning_top_bot",
        "at_bat_index",
        "on_1b",
        "on_2b",
        "on_3b",
        "outs_when_up",
        "terminal_outcome_group",
    }
    missing = sorted(required - set(terminal_plays.columns))
    if missing:
        raise ValueError(f"terminal plays missing sequence fields: {missing}")
    group = ["game_pk", "inning", "inning_top_bot"]
    ordered = terminal_plays.sort([*group, "at_bat_index"])
    ordered = ordered.with_columns(
        *[
            pl.col(f"on_{base}b")
            .shift(1)
            .over(group)
            .alias(f"start_runner_{base}b")
            for base in (1, 2, 3)
        ],
        pl.col("at_bat_index")
        .shift(1)
        .over(group)
        .alias("previous_at_bat_index"),
        pl.col("outs_when_up")
        .shift(1)
        .over(group)
        .alias("previous_outs_before"),
        pl.col("terminal_outcome_group")
        .shift(1)
        .over(group)
        .alias("previous_outcome_group"),
    )
    expected_previous_outs = (
        pl.when(pl.col("previous_outcome_group").is_in(["OUT", "SF"]))
        .then(1)
        .when(pl.col("previous_outcome_group") == "MULTI_OUT")
        .then(2)
        .when(pl.col("previous_outcome_group") == "FC_REACH")
        .then(1)
        .otherwise(0)
    )
    first_in_half = pl.col("previous_at_bat_index").is_null()
    return ordered.with_columns(
        pl.when(first_in_half)
        .then(pl.lit("empty_half_inning_start"))
        .otherwise(pl.lit("prior_terminal_post_state"))
        .alias("start_state_source"),
        pl.when(first_in_half)
        .then(True)
        .otherwise(
            pl.col("outs_when_up")
            == pl.col("previous_outs_before") + expected_previous_outs
        )
        .alias("outs_continuity_ok"),
    )


def build_fielding_opportunities(terminal_plays: pl.DataFrame) -> pl.DataFrame:
    """Return clean Total-Zone-style first-touch opportunities.

    Home runs and fielder's choices are excluded from the first range target.
    They remain in the terminal foundation for later specialized models.
    """

    required = {
        "terminal_outcome_group",
        "responsible_position",
        "responsible_fielder_id",
        "bb_type",
        "hit_location",
    }
    missing = sorted(required - set(terminal_plays.columns))
    if missing:
        raise ValueError(f"terminal plays missing fielding fields: {missing}")
    return (
        terminal_plays.filter(
            pl.col("terminal_outcome_group").is_in(sorted(FIELDING_CORE_GROUPS))
            & pl.col("responsible_position").is_between(2, 9)
            & pl.col("responsible_fielder_id").is_not_null()
            & pl.col("bb_type").is_not_null()
        )
        .with_columns(
            pl.col("batted_ball_out").cast(pl.Int8).alias("conversion_out"),
            pl.when(pl.col("terminal_outcome_group") == "ROE")
            .then(pl.lit("error_reach"))
            .when(pl.col("batted_ball_out"))
            .then(pl.lit("out"))
            .otherwise(pl.lit("hit"))
            .alias("fielding_result"),
            pl.lit("first_touch_core_v1").alias("opportunity_definition"),
        )
        .sort(list(TERMINAL_KEY))
    )


def project_catcher_pitch_observations(
    raw_pbp: pl.DataFrame,
    *,
    source_asset: str,
    season: int,
    level: str,
    terminal_plays: pl.DataFrame | None = None,
    game_type: str = "R",
) -> pl.DataFrame:
    """Preserve one row per physical pitch for framing/blocking research.

    The public result narrative is PA-wide, so a wild-pitch or passed-ball label
    is assigned to a particular dirt-ball pitch only when exactly one ``*B``
    candidate exists in that PA.  Other failures stay explicitly ambiguous.
    """

    required = set(required_catcher_pitch_source_columns())
    missing = sorted(required - set(raw_pbp.columns))
    if missing:
        raise ValueError(f"{source_asset} missing catcher pitch fields: {missing}")
    selected = raw_pbp.select(
        *[_int_expr(name) for name in _CATCHER_PITCH_INT_COLUMNS],
        *[
            pl.col(name).cast(pl.Float64, strict=False).alias(name)
            for name in _CATCHER_PITCH_FLOAT_COLUMNS
        ],
        *[_normal_text(name) for name in _CATCHER_PITCH_TEXT_COLUMNS],
    ).filter(pl.col("game_type") == str(game_type))
    selected = selected.drop_nulls(["game_pk", "at_bat_number", "pitch_number"])
    value_columns = [
        name
        for name in selected.columns
        if name not in {"game_pk", "at_bat_number", "pitch_number"}
    ]
    compact = selected.group_by(
        "game_pk", "at_bat_number", "pitch_number"
    ).agg(
        pl.len().alias("raw_pitch_row_count"),
        *[_first_non_null(name) for name in value_columns],
        *[_non_null_variants(name) for name in value_columns],
    )
    conflicts = [f"{name}__variant_count" for name in value_columns]
    bad = compact.filter(pl.any_horizontal(pl.col(name) > 1 for name in conflicts))
    if bad.height:
        raise ValueError(
            f"{source_asset} has conflicting physical pitch rows: "
            f"{bad.select('game_pk', 'at_bat_number', 'pitch_number').head(5).to_dicts()}"
        )
    compact = compact.drop(conflicts).rename({"at_bat_number": "at_bat_index"})
    compact = compact.with_columns(
        pl.coalesce([pl.col("des"), pl.col("description")]).alias("pa_description"),
        pl.col("type").str.to_uppercase().alias("pitch_result_code"),
    ).with_columns(
        (pl.col("pitch_result_code") == "C").alias("called_strike"),
        pl.col("pitch_result_code").is_in(["B", "*B"]).alias("called_ball"),
        (pl.col("pitch_result_code") == "*B").alias("block_candidate"),
        pl.col("pa_description")
        .fill_null("")
        .str.contains(r"(?i)passed ball")
        .alias("pa_has_passed_ball"),
        pl.col("pa_description")
        .fill_null("")
        .str.contains(r"(?i)wild pitch")
        .alias("pa_has_wild_pitch"),
    ).with_columns(
        pl.col("block_candidate")
        .sum()
        .over(["game_pk", "at_bat_index"])
        .alias("pa_block_candidate_count")
    )
    if terminal_plays is not None and not terminal_plays.is_empty():
        start_columns = [
            "game_pk",
            "at_bat_index",
            "start_runner_1b",
            "start_runner_2b",
            "start_runner_3b",
            "outs_continuity_ok",
        ]
        missing_start = sorted(set(start_columns) - set(terminal_plays.columns))
        if missing_start:
            raise ValueError(f"terminal plays missing catcher pitch state: {missing_start}")
        compact = compact.join(
            terminal_plays.select(start_columns),
            on=["game_pk", "at_bat_index"],
            how="left",
            validate="m:1",
        ).with_columns(
            pl.sum_horizontal(
                [
                    pl.col(f"start_runner_{base}b").is_not_null().cast(pl.Int8)
                    for base in (1, 2, 3)
                ]
            ).alias("start_runner_count")
        )
    else:
        compact = compact.with_columns(
            pl.lit(None, dtype=pl.Int8).alias("start_runner_count"),
            pl.lit(None, dtype=pl.Boolean).alias("outs_continuity_ok"),
        )
    return compact.with_columns(
        pl.lit(int(season), dtype=pl.Int64).alias("season"),
        pl.lit(str(level)).alias("level"),
        pl.lit(str(source_asset)).alias("source_asset"),
        (
            pl.col("block_candidate")
            & (pl.col("pa_block_candidate_count") == 1)
            & (pl.col("start_runner_count") > 0)
            & pl.col("outs_continuity_ok").fill_null(False)
        ).alias("clean_block_opportunity"),
        pl.when(
            pl.col("block_candidate")
            & (pl.col("pa_block_candidate_count") == 1)
            & pl.col("pa_has_passed_ball")
        )
        .then(pl.lit("passed_ball"))
        .when(
            pl.col("block_candidate")
            & (pl.col("pa_block_candidate_count") == 1)
            & pl.col("pa_has_wild_pitch")
        )
        .then(pl.lit("wild_pitch"))
        .when(pl.col("block_candidate") & (pl.col("pa_block_candidate_count") == 1))
        .then(pl.lit("blocked"))
        .otherwise(None)
        .alias("block_result"),
    ).sort(["game_pk", "at_bat_index", "pitch_number"])


def _runner_destination_expr() -> pl.Expr:
    runner = pl.col("runner_id")
    present_after = (
        (runner == pl.col("on_1b"))
        | (runner == pl.col("on_2b"))
        | (runner == pl.col("on_3b"))
    ).fill_null(False)
    disappeared = ~present_after
    return (
        pl.when(runner == pl.col("on_1b"))
        .then(1)
        .when(runner == pl.col("on_2b"))
        .then(2)
        .when(runner == pl.col("on_3b"))
        .then(3)
        .when(disappeared & (pl.col("disappeared_runner_count") == pl.col("runs_scored")))
        .then(4)
        .when(disappeared & (pl.col("runs_scored") == 0))
        .then(0)
        .otherwise(None)
    )


def build_runner_advancement_opportunities(
    terminal_plays: pl.DataFrame,
) -> pl.DataFrame:
    """Return conservative non-steal runner movements on terminal contacts."""

    state = (
        terminal_plays
        if "start_runner_1b" in terminal_plays.columns
        else add_sequence_start_state(terminal_plays)
    )
    required = {
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
        "on_1b",
        "on_2b",
        "on_3b",
        "bat_score",
        "post_bat_score",
        "outs_continuity_ok",
        "terminal_outcome_group",
    }
    missing = sorted(required - set(state.columns))
    if missing:
        raise ValueError(f"terminal plays missing runner fields: {missing}")

    base_frames = []
    for origin in (1, 2, 3):
        base_frames.append(
            state.with_columns(
                pl.lit(origin, dtype=pl.Int8).alias("origin_base"),
                pl.col(f"start_runner_{origin}b").alias("runner_id"),
            )
        )
    runners = pl.concat(base_frames, how="vertical").filter(
        pl.col("runner_id").is_not_null()
        & pl.col("terminal_outcome_group").is_in(sorted(RUNNER_CONTACT_GROUPS))
        & pl.col("outs_continuity_ok")
        & ~(
            (pl.col("outs_when_up") >= 2)
            & pl.col("terminal_outcome_group").is_in(["OUT", "SF"])
        )
    )
    if runners.is_empty():
        return runners.with_columns(
            pl.lit(None, dtype=pl.Int8).alias("destination_base"),
            pl.lit(None, dtype=pl.String).alias("runner_result"),
            pl.lit(None, dtype=pl.String).alias("opportunity_type"),
            pl.lit(None, dtype=pl.Boolean).alias("outfield_arm_context"),
            pl.lit(None, dtype=pl.String).alias("runner_state_definition"),
        )

    runners = runners.with_columns(
        (pl.col("post_bat_score") - pl.col("bat_score"))
        .clip(lower_bound=0)
        .alias("runs_scored"),
        pl.sum_horizontal(
            [
                (
                    pl.col(f"start_runner_{base}b").is_not_null()
                    & ~(
                        (pl.col(f"start_runner_{base}b") == pl.col("on_1b"))
                        | (pl.col(f"start_runner_{base}b") == pl.col("on_2b"))
                        | (pl.col(f"start_runner_{base}b") == pl.col("on_3b"))
                    ).fill_null(False)
                ).cast(pl.Int8)
                for base in (1, 2, 3)
            ]
        ).alias("disappeared_runner_count"),
    ).with_columns(_runner_destination_expr().cast(pl.Int8).alias("destination_base"))

    opportunity_type = (
        pl.when((pl.col("origin_base") == 1) & (pl.col("terminal_outcome_group") == "1B"))
        .then(pl.lit("first_on_single"))
        .when((pl.col("origin_base") == 1) & (pl.col("terminal_outcome_group") == "2B"))
        .then(pl.lit("first_on_double"))
        .when((pl.col("origin_base") == 2) & (pl.col("terminal_outcome_group") == "1B"))
        .then(pl.lit("second_on_single"))
        .when(
            (pl.col("origin_base").is_in([2, 3]))
            & pl.col("terminal_outcome_group").is_in(["OUT", "SF"])
            & pl.col("bb_type").is_in(["fly_ball", "line_drive", "popup"])
        )
        .then(pl.lit("tag_on_air_out"))
        .when(
            (pl.col("origin_base") == 2)
            & (pl.col("terminal_outcome_group") == "OUT")
            & (pl.col("bb_type") == "ground_ball")
        )
        .then(pl.lit("second_on_ground_out"))
        .otherwise(None)
    )
    return (
        runners.with_columns(
            opportunity_type.alias("opportunity_type"),
            pl.when(pl.col("destination_base") == 0)
            .then(pl.lit("out"))
            .when(pl.col("destination_base") == 4)
            .then(pl.lit("scored"))
            .when(pl.col("destination_base") == pl.col("origin_base"))
            .then(pl.lit("held"))
            .when(pl.col("destination_base") > pl.col("origin_base"))
            .then(pl.lit("advanced"))
            .otherwise(None)
            .alias("runner_result"),
        )
        .filter(pl.col("opportunity_type").is_not_null())
        .with_columns(
            pl.col("responsible_position")
            .is_in([7, 8, 9])
            .alias("outfield_arm_context"),
            pl.lit("prior_terminal_state_conservative_v1").alias(
                "runner_state_definition"
            ),
        )
        .sort([*TERMINAL_KEY, "origin_base"])
    )


def summarize_opportunity_coverage(
    terminal: pl.DataFrame,
    fielding: pl.DataFrame,
    runners: pl.DataFrame,
) -> dict[str, Any]:
    """Return compact, JSON-safe source coverage diagnostics."""

    def counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
        if frame.is_empty() or column not in frame.columns:
            return {}
        return {
            str(row[column]): int(row["len"])
            for row in frame.group_by(column).len().sort(column).to_dicts()
        }

    return {
        "terminal_play_count": int(terminal.height),
        "game_count": int(terminal.get_column("game_pk").n_unique())
        if terminal.height
        else 0,
        "supported_terminal_count": int(
            terminal.get_column("terminal_outcome_group").is_not_null().sum()
        )
        if terminal.height
        else 0,
        "terminal_outcome_counts": counts(terminal, "terminal_outcome_group"),
        "fielding_opportunity_count": int(fielding.height),
        "fielding_position_counts": counts(fielding, "responsible_position"),
        "runner_opportunity_count": int(runners.height),
        "runner_type_counts": counts(runners, "opportunity_type"),
        "known_runner_destination_count": int(
            runners.get_column("destination_base").is_not_null().sum()
        )
        if runners.height
        else 0,
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    """Write one deterministic JSON manifest for a materialized partition."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
