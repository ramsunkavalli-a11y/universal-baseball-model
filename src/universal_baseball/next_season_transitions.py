"""Complete next-season MLB transition rows, including inactivity and censoring."""

from __future__ import annotations

from collections.abc import Collection

import polars as pl


STATES = frozenset({"hitter_only", "pitcher_only", "both_workloads", "inactive", "right_censored"})


def _annual(frame: pl.DataFrame, workload: str, label: str) -> pl.DataFrame:
    required = {"season", "player_id", workload}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"{label} missing columns: {missing}")
    result = frame.select("season", "player_id", workload).cast(
        {"season": pl.Int64, "player_id": pl.Int64, workload: pl.Int64}, strict=True
    )
    if result.filter(
        pl.any_horizontal(pl.col("season").is_null(), pl.col("player_id").is_null(), pl.col(workload).is_null())
        | (pl.col("player_id") <= 0)
        | (pl.col(workload) < 0)
    ).height:
        raise ValueError(f"{label} has invalid season, player, or workload")
    return result.group_by("season", "player_id").agg(pl.col(workload).sum())


def _state(pa: pl.Expr, bf: pl.Expr, *, censored: pl.Expr | None = None) -> pl.Expr:
    expression = (
        pl.when((pa > 0) & (bf > 0)).then(pl.lit("both_workloads"))
        .when(pa > 0).then(pl.lit("hitter_only"))
        .when(bf > 0).then(pl.lit("pitcher_only"))
        .otherwise(pl.lit("inactive"))
    )
    if censored is not None:
        expression = pl.when(censored).then(pl.lit("right_censored")).otherwise(expression)
    return expression


def build_next_season_transitions(
    hitting: pl.DataFrame,
    pitching: pl.DataFrame,
    *,
    complete_seasons: Collection[int],
    source_seasons: Collection[int] | None = None,
) -> pl.DataFrame:
    """Give every active source player one next-season outcome.

    Missing rows in a certified complete target season are observed inactivity.
    Missing rows beyond the complete boundary are right censored and stay null.
    Rates for active returners remain a separate conditional estimand.
    """

    bat = _annual(hitting, "batting_pa", "hitting")
    pit = _annual(pitching, "pitching_bf", "pitching")
    complete = sorted({int(season) for season in complete_seasons})
    if not complete:
        raise ValueError("complete_seasons cannot be empty")
    if complete != list(range(complete[0], complete[-1] + 1)):
        raise ValueError("complete_seasons must be contiguous")
    requested = sorted(
        {int(season) for season in source_seasons}
        if source_seasons is not None else set(complete)
    )
    if outside := sorted(set(requested) - set(complete)):
        raise ValueError(f"source seasons are not certified complete: {outside}")

    source = pl.concat(
        [
            bat.select(
                "season", "player_id", pl.col("batting_pa"),
                pl.lit(0, dtype=pl.Int64).alias("pitching_bf"),
            ),
            pit.select(
                "season", "player_id",
                pl.lit(0, dtype=pl.Int64).alias("batting_pa"), pl.col("pitching_bf"),
            ),
        ],
        how="vertical",
    ).group_by("season", "player_id").agg(
        pl.col("batting_pa").sum(), pl.col("pitching_bf").sum()
    ).filter(
        pl.col("season").is_in(requested)
        & ((pl.col("batting_pa") > 0) | (pl.col("pitching_bf") > 0))
    ).rename(
        {"season": "source_season", "batting_pa": "source_batting_pa", "pitching_bf": "source_pitching_bf"}
    ).with_columns(
        (pl.col("source_season") + 1).alias("target_season"),
        _state(pl.col("source_batting_pa"), pl.col("source_pitching_bf")).alias("source_state"),
    )

    target = bat.join(pit, on=["season", "player_id"], how="full", coalesce=True).with_columns(
        pl.col("batting_pa").fill_null(0), pl.col("pitching_bf").fill_null(0)
    ).rename(
        {"season": "target_season", "batting_pa": "target_batting_pa", "pitching_bf": "target_pitching_bf"}
    )
    result = source.join(target, on=["target_season", "player_id"], how="left")
    censored = ~pl.col("target_season").is_in(complete)
    result = result.with_columns(
        pl.when(censored).then(None).otherwise(pl.col("target_batting_pa").fill_null(0)).cast(pl.Int64).alias("target_batting_pa"),
        pl.when(censored).then(None).otherwise(pl.col("target_pitching_bf").fill_null(0)).cast(pl.Int64).alias("target_pitching_bf"),
        censored.alias("is_right_censored"),
    ).with_columns(
        _state(
            pl.col("target_batting_pa"), pl.col("target_pitching_bf"),
            censored=pl.col("is_right_censored"),
        ).alias("target_state"),
        pl.when(pl.col("is_right_censored")).then(None).otherwise(
            (pl.col("target_batting_pa") > 0) | (pl.col("target_pitching_bf") > 0)
        ).cast(pl.Boolean).alias("returned_any"),
    ).select(
        "source_season", "target_season", "player_id", "source_state",
        "source_batting_pa", "source_pitching_bf", "target_state",
        "target_batting_pa", "target_pitching_bf", "returned_any", "is_right_censored",
    ).sort(["source_season", "player_id"])
    if result.group_by("source_season", "player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("next-season transitions violate source player-season grain")
    if result.filter(~pl.col("source_state").is_in(sorted(STATES - {"inactive", "right_censored"}))).height:
        raise ValueError("transition source must be active")
    return result
