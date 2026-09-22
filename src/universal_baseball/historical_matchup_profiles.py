"""Chronology-safe all-level hitter and pitcher matchup profiles."""

from __future__ import annotations

from collections.abc import Iterable

import polars as pl


LEVEL_RANK = {"rk": 0, "a-": 1, "a": 2, "a+": 3, "aa": 4, "aaa": 5}
RECENCY_WEIGHTS = {1: 5.0, 2: 4.0, 3: 3.0}

# Numerator, denominator and a deliberately conservative empirical-Bayes prior.
PROFILE_SPECS: dict[str, tuple[str, str, float]] = {
    "k": ("strikeout", "pa", 150.0),
    "control": ("control_failure", "pa", 200.0),
    "hr": ("home_run", "pa", 400.0),
    "hit_bip": ("hit_on_contact", "bip", 400.0),
    "damage_bip": ("damage_on_contact", "bip", 500.0),
    "gb_bip": ("ground_ball", "bip", 250.0),
    "air_bip": ("air_ball", "bip", 250.0),
    "ld_bip": ("line_drive", "bip", 400.0),
    "pu_bip": ("popup", "bip", 500.0),
}

TARGET_SPECS: dict[str, tuple[str, str]] = {
    "strikeout": ("strikeout", "pa"),
    "control_failure": ("control_failure", "pa"),
    "home_run": ("home_run", "pa"),
    "ground_ball_on_contact": ("ground_ball", "bip"),
    "damage_on_contact": ("damage_on_contact", "bip"),
    "hit_on_contact": ("hit_on_contact", "bip"),
}


def add_matchup_outcomes(plate_appearances: pl.DataFrame) -> pl.DataFrame:
    """Attach universal contact and damage targets to classified terminal PAs."""

    required = {
        "season",
        "level",
        "batter_id",
        "pitcher_id",
        "pitcher_hand",
        "batter_side",
        "bb_type",
        "terminal_outcome_group",
        "strikeout",
        "control_failure",
        "home_run",
    }
    missing = sorted(required - set(plate_appearances.columns))
    if missing:
        raise ValueError(f"classified plate appearances missing fields: {missing}")
    group = pl.col("terminal_outcome_group").fill_null("")
    contact_type = pl.col("bb_type").cast(pl.String, strict=False).fill_null("")
    is_bip = group.is_in(
        ["1B", "2B", "3B", "HR", "OUT", "MULTI_OUT", "SF", "ROE", "FC_REACH"]
    )
    return plate_appearances.with_columns(
        pl.lit(1, dtype=pl.Int8).alias("pa"),
        is_bip.cast(pl.Int8).alias("bip"),
        group.is_in(["1B", "2B", "3B", "HR"])
        .cast(pl.Int8)
        .alias("hit_on_contact"),
        group.is_in(["2B", "3B", "HR"])
        .cast(pl.Int8)
        .alias("damage_on_contact"),
        (is_bip & (contact_type == "ground_ball"))
        .cast(pl.Int8)
        .alias("ground_ball"),
        (is_bip & contact_type.is_in(["fly_ball", "popup", "pop_up"]))
        .cast(pl.Int8)
        .alias("air_ball"),
        (is_bip & (contact_type == "line_drive"))
        .cast(pl.Int8)
        .alias("line_drive"),
        (is_bip & contact_type.is_in(["popup", "pop_up"]))
        .cast(pl.Int8)
        .alias("popup"),
        pl.col("level").replace_strict(LEVEL_RANK, default=None).alias("level_rank"),
    )


def _season_level_rates(events: pl.DataFrame) -> pl.DataFrame:
    expressions: list[pl.Expr] = []
    for name, (numerator, denominator, _) in PROFILE_SPECS.items():
        expressions.extend(
            [
                pl.col(numerator).sum().alias(f"env_{name}_successes"),
                pl.col(denominator).sum().alias(f"env_{name}_opportunities"),
            ]
        )
    environment = events.group_by("season", "level").agg(*expressions)
    return environment.with_columns(
        *[
            (
                pl.col(f"env_{name}_successes")
                / pl.col(f"env_{name}_opportunities")
            ).alias(f"env_{name}_rate")
            for name in PROFILE_SPECS
        ]
    )


def _player_season_level(events: pl.DataFrame, *, player_column: str) -> pl.DataFrame:
    expressions: list[pl.Expr] = []
    for name, (numerator, denominator, _) in PROFILE_SPECS.items():
        expressions.extend(
            [
                pl.col(numerator).sum().alias(f"{name}_successes"),
                pl.col(denominator).sum().alias(f"{name}_opportunities"),
            ]
        )
    return events.group_by("season", "level", player_column).agg(*expressions)


def build_prior_profiles(
    events: pl.DataFrame,
    *,
    player_column: str,
    prefix: str,
    target_seasons: Iterable[int],
) -> pl.DataFrame:
    """Build prior-only, level-season-neutral player profiles for each target year."""

    if player_column not in events.columns:
        raise ValueError(f"events lack player column {player_column}")
    environment = _season_level_rates(events)
    player = _player_season_level(events, player_column=player_column).join(
        environment, on=["season", "level"], validate="m:1"
    )
    player = player.with_columns(
        *[
            (
                pl.col(f"{name}_successes")
                - pl.col(f"{name}_opportunities") * pl.col(f"env_{name}_rate")
            ).alias(f"{name}_residual_sum")
            for name in PROFILE_SPECS
        ]
    )

    frames: list[pl.DataFrame] = []
    for target_season in sorted(set(int(year) for year in target_seasons)):
        history = player.filter(
            pl.col("season").is_between(target_season - 3, target_season - 1)
        ).with_columns(
            pl.col("season")
            .replace_strict(
                {
                    target_season - lag: weight
                    for lag, weight in RECENCY_WEIGHTS.items()
                },
                default=0.0,
            )
            .alias("recency_weight")
        )
        if history.is_empty():
            continue
        aggregated = history.group_by(player_column).agg(
            pl.col("k_opportunities").sum().alias("history_pa"),
            *[
                (
                    pl.col(f"{name}_residual_sum") * pl.col("recency_weight")
                )
                .sum()
                .alias(f"{name}_weighted_residual")
                for name in PROFILE_SPECS
            ],
            *[
                (
                    pl.col(f"{name}_opportunities") * pl.col("recency_weight")
                )
                .sum()
                .alias(f"{name}_weighted_opportunities")
                for name in PROFILE_SPECS
            ],
        )
        latest = (
            history.sort(
                player_column,
                "season",
                "k_opportunities",
                descending=[False, True, True],
            )
            .unique(subset=[player_column], keep="first", maintain_order=True)
            .select(
                player_column,
                pl.col("level").replace_strict(LEVEL_RANK, default=None).alias(
                    "last_level_rank"
                ),
            )
        )
        profile = aggregated.join(latest, on=player_column, validate="1:1").with_columns(
            *[
                (
                    pl.col(f"{name}_weighted_residual")
                    / (
                        pl.col(f"{name}_weighted_opportunities")
                        + float(prior)
                    )
                ).alias(f"{prefix}_{name}")
                for name, (_, _, prior) in PROFILE_SPECS.items()
            ],
            pl.lit(target_season, dtype=pl.Int64).alias("target_season"),
        )
        frames.append(
            profile.select(
                "target_season",
                pl.col(player_column).alias("player_id"),
                pl.col("history_pa").alias(f"{prefix}_history_pa"),
                pl.col("last_level_rank").alias(f"{prefix}_last_level_rank"),
                *(f"{prefix}_{name}" for name in PROFILE_SPECS),
            )
        )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical_relaxed").sort(
        "target_season", "player_id"
    )


def build_prior_split_profiles(
    events: pl.DataFrame,
    *,
    player_column: str,
    split_column: str,
    prefix: str,
    overall_profiles: pl.DataFrame,
    target_seasons: Iterable[int],
) -> pl.DataFrame:
    """Build prior-only handedness splits, shrunk toward each overall profile.

    A hitter is split by opposing pitcher hand; a pitcher is split by batter
    side.  The league environment is calculated within the same handedness
    cell, so the feature represents a player's excess performance in that
    matchup rather than the ordinary league platoon effect.
    """

    required = {player_column, split_column}
    if missing := sorted(required - set(events.columns)):
        raise ValueError(f"events lack split-profile fields: {missing}")

    expressions: list[pl.Expr] = []
    for name, (numerator, denominator, _) in PROFILE_SPECS.items():
        expressions.extend(
            [
                pl.col(numerator).sum().alias(f"{name}_successes"),
                pl.col(denominator).sum().alias(f"{name}_opportunities"),
            ]
        )
    environment = events.group_by("season", "level", split_column).agg(
        *[
            expression.alias(f"env_{expression.meta.output_name()}")
            for expression in expressions
        ]
    )
    environment = environment.with_columns(
        *[
            (
                pl.col(f"env_{name}_successes")
                / pl.col(f"env_{name}_opportunities")
            ).alias(f"env_{name}_rate")
            for name in PROFILE_SPECS
        ]
    )
    player = (
        events.group_by("season", "level", player_column, split_column)
        .agg(*expressions)
        .join(
            environment,
            on=["season", "level", split_column],
            validate="m:1",
        )
        .with_columns(
            *[
                (
                    pl.col(f"{name}_successes")
                    - pl.col(f"{name}_opportunities")
                    * pl.col(f"env_{name}_rate")
                ).alias(f"{name}_residual_sum")
                for name in PROFILE_SPECS
            ]
        )
    )

    frames: list[pl.DataFrame] = []
    for target_season in sorted(set(int(year) for year in target_seasons)):
        history = player.filter(
            pl.col("season").is_between(target_season - 3, target_season - 1)
        ).with_columns(
            pl.col("season")
            .replace_strict(
                {
                    target_season - lag: weight
                    for lag, weight in RECENCY_WEIGHTS.items()
                },
                default=0.0,
            )
            .alias("recency_weight")
        )
        if history.is_empty():
            continue
        aggregated = history.group_by(player_column, split_column).agg(
            pl.col("k_opportunities").sum().alias("split_history_pa"),
            *[
                (
                    pl.col(f"{name}_residual_sum") * pl.col("recency_weight")
                )
                .sum()
                .alias(f"{name}_weighted_residual")
                for name in PROFILE_SPECS
            ],
            *[
                (
                    pl.col(f"{name}_opportunities") * pl.col("recency_weight")
                )
                .sum()
                .alias(f"{name}_weighted_opportunities")
                for name in PROFILE_SPECS
            ],
        )
        anchors = overall_profiles.filter(
            pl.col("target_season") == target_season
        ).select("player_id", *(f"{prefix[0]}_{name}" for name in PROFILE_SPECS))
        profile = (
            aggregated.with_columns(
                pl.lit(target_season, dtype=pl.Int64).alias("target_season")
            )
            .rename({player_column: "player_id"})
            .join(anchors, on="player_id", how="left", validate="m:1")
            .with_columns(
                *[
                    (
                        (
                            pl.col(f"{name}_weighted_residual")
                            + float(prior)
                            * pl.col(f"{prefix[0]}_{name}").fill_null(0.0)
                        )
                        / (
                            pl.col(f"{name}_weighted_opportunities")
                            + float(prior)
                        )
                    ).alias(f"{prefix}_{name}")
                    for name, (_, _, prior) in PROFILE_SPECS.items()
                ]
            )
        )
        frames.append(
            profile.select(
                "target_season",
                "player_id",
                split_column,
                pl.col("split_history_pa").alias(f"{prefix}_history_pa"),
                *(f"{prefix}_{name}" for name in PROFILE_SPECS),
            )
        )
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="vertical_relaxed").sort(
        "target_season", "player_id", split_column
    )


def build_matchup_cells(
    events: pl.DataFrame,
    *,
    hitter_profiles: pl.DataFrame,
    pitcher_profiles: pl.DataFrame,
) -> pl.DataFrame:
    """Aggregate target PAs and attach strictly prior hitter/pitcher profiles."""

    expressions = [pl.col(column).sum().alias(column) for column in {
        numerator for numerator, _ in TARGET_SPECS.values()
    } | {denominator for _, denominator in TARGET_SPECS.values()}]
    cells = events.group_by(
        "season",
        "level",
        "level_rank",
        "batter_id",
        "pitcher_id",
        "pitcher_hand",
        "batter_side",
    ).agg(*expressions)
    first_pair = events.group_by("batter_id", "pitcher_id").agg(
        pl.col("season").min().alias("first_pair_season")
    )
    cells = (
        cells.join(first_pair, on=["batter_id", "pitcher_id"], validate="m:1")
        .with_columns((pl.col("season") == pl.col("first_pair_season")).alias("new_pair"))
        .join(
            hitter_profiles.rename(
                {"target_season": "season", "player_id": "batter_id"}
            ),
            on=["season", "batter_id"],
            how="left",
            validate="m:1",
        )
        .join(
            pitcher_profiles.rename(
                {"target_season": "season", "player_id": "pitcher_id"}
            ),
            on=["season", "pitcher_id"],
            how="left",
            validate="m:1",
        )
    )
    profile_columns = [
        *(f"h_{name}" for name in PROFILE_SPECS),
        *(f"p_{name}" for name in PROFILE_SPECS),
    ]
    return cells.with_columns(
        *[pl.col(column).fill_null(0.0) for column in profile_columns],
        pl.col("h_history_pa").fill_null(0).cast(pl.Float64),
        pl.col("p_history_pa").fill_null(0).cast(pl.Float64),
        pl.col("h_last_level_rank")
        .fill_null(pl.col("level_rank"))
        .cast(pl.Float64),
        pl.col("p_last_level_rank")
        .fill_null(pl.col("level_rank"))
        .cast(pl.Float64),
        (pl.col("level_rank") > pl.col("h_last_level_rank").fill_null(pl.col("level_rank")))
        .alias("hitter_advanced"),
        (pl.col("level_rank") > pl.col("p_last_level_rank").fill_null(pl.col("level_rank")))
        .alias("pitcher_advanced"),
    )
