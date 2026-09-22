"""Minor-league catcher throwing and blocking from historical PBP."""

from __future__ import annotations

import re

import polars as pl


_CAUGHT = re.compile(r"\bcaught stealing\b", re.I)
_STOLEN = re.compile(r"\b(?:steals|stolen base)\b", re.I)
_PICKOFF = re.compile(r"\b(?:pickoff|picked off)\b", re.I)


def extract_catcher_deterrence_opportunities(
    terminal_plays: pl.DataFrame,
) -> pl.DataFrame:
    """Return steal-eligible PA starts, including the many non-attempts."""

    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "terminal_pitch_number",
        "pa_description",
        "fielder_2",
        "pitcher",
        "p_throws",
        "stand",
        "outs_when_up",
        "inning",
        "bat_score",
        "fld_score",
        "park_key",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
    }
    if missing := sorted(required - set(terminal_plays.columns)):
        raise ValueError(f"terminal plays missing deterrence fields: {missing}")
    description = pl.col("pa_description").fill_null("").str.to_lowercase()
    clean_attempt = description.str.contains(r"\b(?:caught stealing|steals|stolen base)\b") & ~description.str.contains(
        r"\b(?:pickoff|picked off)\b"
    )
    common = terminal_plays.filter(
        pl.col("fielder_2").is_not_null()
        & pl.col("pitcher").is_not_null()
        & pl.col("outs_when_up").is_between(0, 2)
    ).with_columns(
        pl.col("fielder_2").cast(pl.Int64).alias("catcher_id"),
        pl.col("pitcher").cast(pl.Int64).alias("pitcher_id"),
        pl.col("p_throws").fill_null("U").alias("pitcher_hand"),
        pl.col("stand").fill_null("U").alias("batter_side"),
        pl.col("park_key").fill_null("unknown_park").alias("park_key"),
        pl.col("terminal_pitch_number").clip(1, 6).alias("pitch_window"),
        pl.col("inning").clip(1, 10).alias("inning_band"),
        (pl.col("bat_score") - pl.col("fld_score")).clip(-3, 3).alias(
            "score_band"
        ),
        clean_attempt.alias("clean_steal_attempt"),
    )
    second = (
        common.filter(
            pl.col("start_runner_1b").is_not_null()
            & pl.col("start_runner_2b").is_null()
        )
        .with_columns(
            pl.col("start_runner_1b").cast(pl.Int64).alias("runner_id"),
            pl.lit("2nd").alias("attempt_base"),
            (
                pl.col("clean_steal_attempt")
                & description.str.contains(r"\b2nd\b")
            )
            .cast(pl.Int8)
            .alias("steal_attempted"),
        )
    )
    third = (
        common.filter(
            pl.col("start_runner_2b").is_not_null()
            & pl.col("start_runner_3b").is_null()
        )
        .with_columns(
            pl.col("start_runner_2b").cast(pl.Int64).alias("runner_id"),
            pl.lit("3rd").alias("attempt_base"),
            (
                pl.col("clean_steal_attempt")
                & description.str.contains(r"\b3rd\b")
            )
            .cast(pl.Int8)
            .alias("steal_attempted"),
        )
    )
    return pl.concat([second, third], how="vertical_relaxed").sort(
        "season", "game_pk", "at_bat_index", "attempt_base"
    )


def _attempt_base(description: str) -> str | None:
    match = re.search(r"\b(2nd|3rd|home)\b", description, re.I)
    return match.group(1).lower() if match else None


def extract_catcher_throwing_attempts(terminal_plays: pl.DataFrame) -> pl.DataFrame:
    """Extract non-pickoff steal attempts with known catcher and pitcher.

    The historical PA narrative exposes both successful steals and caught
    stealings, including compound strikeout/steal plays. Runner identity is not
    guessed from English names; the first catcher model therefore separates
    catcher and pitcher but leaves the runner effect for a linked-name upgrade.
    """

    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "pa_description",
        "fielder_2",
        "pitcher",
        "p_throws",
        "outs_when_up",
        "park_key",
    }
    missing = sorted(required - set(terminal_plays.columns))
    if missing:
        raise ValueError(f"terminal plays missing catcher throwing fields: {missing}")
    rows = []
    for row in terminal_plays.iter_rows(named=True):
        description = str(row.get("pa_description") or "").strip()
        if not description or _PICKOFF.search(description):
            continue
        caught = bool(_CAUGHT.search(description))
        stolen = bool(_STOLEN.search(description)) and not caught
        if caught == stolen:
            continue
        attempt_base = _attempt_base(description)
        if attempt_base is None or row.get("fielder_2") is None or row.get("pitcher") is None:
            continue
        rows.append(
            {
                "season": row["season"],
                "level": row["level"],
                "game_pk": row["game_pk"],
                "at_bat_index": row["at_bat_index"],
                "catcher_id": row["fielder_2"],
                "pitcher_id": row["pitcher"],
                "pitcher_hand": row.get("p_throws"),
                "outs_before": row.get("outs_when_up"),
                "park_key": row.get("park_key"),
                "attempt_base": attempt_base,
                "caught_stealing": int(caught),
                "pa_description": description,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "level": pl.String,
                "game_pk": pl.Int64,
                "at_bat_index": pl.Int64,
                "catcher_id": pl.Int64,
                "pitcher_id": pl.Int64,
                "pitcher_hand": pl.String,
                "outs_before": pl.Int64,
                "park_key": pl.String,
                "attempt_base": pl.String,
                "caught_stealing": pl.Int8,
                "pa_description": pl.String,
            }
        )
    return pl.DataFrame(rows).with_columns(
        pl.col("season").cast(pl.Int64),
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("catcher_id").cast(pl.Int64),
        pl.col("pitcher_id").cast(pl.Int64),
        pl.col("caught_stealing").cast(pl.Int8),
    )


def extract_catcher_blocking_opportunities(catcher_pitches: pl.DataFrame) -> pl.DataFrame:
    """Return clean one-dirt-ball PAs with runners aboard."""

    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "fielder_2",
        "pitcher",
        "p_throws",
        "stand",
        "balls",
        "strikes",
        "plate_x",
        "plate_z",
        "sz_top",
        "sz_bot",
        "home_team",
        "start_runner_count",
        "clean_block_opportunity",
        "block_result",
    }
    missing = sorted(required - set(catcher_pitches.columns))
    if missing:
        raise ValueError(f"catcher pitches missing blocking fields: {missing}")
    return (
        catcher_pitches.filter(
            pl.col("clean_block_opportunity")
            & pl.col("fielder_2").is_not_null()
            & pl.col("pitcher").is_not_null()
            & pl.col("block_result").is_not_null()
        )
        .with_columns(
            pl.col("fielder_2").alias("catcher_id"),
            pl.col("pitcher").alias("pitcher_id"),
            pl.col("p_throws").fill_null("U").alias("pitcher_hand"),
            pl.col("stand").fill_null("U").alias("batter_side"),
            pl.concat_str(
                [pl.col("season"), pl.col("home_team").fill_null("unknown")],
                separator=":",
            ).alias("park_key"),
            pl.col("block_result")
            .is_in(["passed_ball", "wild_pitch"])
            .cast(pl.Int8)
            .alias("block_failure"),
            pl.when(
                pl.col("plate_z").is_not_null()
                & pl.col("sz_bot").is_not_null()
                & pl.col("sz_top").is_not_null()
                & (pl.col("sz_top") > pl.col("sz_bot"))
            )
            .then(
                (pl.col("plate_z") - pl.col("sz_bot"))
                / (pl.col("sz_top") - pl.col("sz_bot"))
            )
            .otherwise(None)
            .alias("normalized_plate_z"),
        )
    )


def score_binary_context_residuals(
    events: pl.DataFrame,
    *,
    outcome_column: str,
    context_columns: list[str],
    park_column: str = "park_key",
    context_prior: float = 50.0,
    park_prior: float = 100.0,
) -> pl.DataFrame:
    """Attach leave-one-out context and park expectations for a binary result."""

    required = {"season", "level", outcome_column, park_column, *context_columns}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"catcher events missing context fields: {missing}")
    work = events.with_columns(
        pl.col(outcome_column).cast(pl.Float64).alias("actual_outcome"),
        pl.col(park_column).fill_null("unknown_park").alias("park_context"),
    )
    broad_keys = ["season", "level"]
    context_keys = [*broad_keys, *context_columns]
    park_keys = [*context_keys, "park_context"]
    broad = work.group_by(broad_keys).agg(
        pl.col("actual_outcome").sum().alias("broad_successes"),
        pl.len().alias("broad_opportunities"),
    ).with_columns(
        (pl.col("broad_successes") / pl.col("broad_opportunities")).alias(
            "broad_rate"
        )
    )
    context = work.group_by(context_keys).agg(
        pl.col("actual_outcome").sum().alias("context_successes"),
        pl.len().alias("context_opportunities"),
    )
    park = work.group_by(park_keys).agg(
        pl.col("actual_outcome").sum().alias("park_successes"),
        pl.len().alias("park_opportunities"),
    )
    return (
        work.join(broad, on=broad_keys, validate="m:1")
        .join(context, on=context_keys, validate="m:1")
        .join(park, on=park_keys, validate="m:1")
        .with_columns(
            (
                (
                    pl.col("context_successes") - pl.col("actual_outcome")
                    + context_prior * pl.col("broad_rate")
                )
                / (pl.col("context_opportunities") - 1 + context_prior)
            ).alias("context_expected_outcome")
        )
        .with_columns(
            (
                (
                    pl.col("park_successes") - pl.col("actual_outcome")
                    + park_prior * pl.col("context_expected_outcome")
                )
                / (pl.col("park_opportunities") - 1 + park_prior)
            ).alias("expected_outcome")
        )
        .with_columns(
            (pl.col("actual_outcome") - pl.col("expected_outcome")).alias(
                "context_residual"
            )
        )
    )


def fit_crossed_catcher_pitcher_effects(
    scored: pl.DataFrame,
    *,
    catcher_prior: float,
    pitcher_prior: float,
    iterations: int = 12,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fit additive shrinkage effects ``residual = catcher + pitcher``."""

    required = {"season", "catcher_id", "pitcher_id", "context_residual"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"scored catcher events missing crossed fields: {missing}")
    work = scored.drop_nulls(["catcher_id", "pitcher_id", "context_residual"]).select(
        "season", "catcher_id", "pitcher_id", "context_residual"
    )
    catchers = work.select("season", "catcher_id").unique().with_columns(
        pl.lit(0.0).alias("catcher_effect")
    )
    pitchers = work.select("season", "pitcher_id").unique().with_columns(
        pl.lit(0.0).alias("pitcher_effect")
    )
    for _ in range(iterations):
        catchers = (
            work.join(pitchers, on=["season", "pitcher_id"], validate="m:1")
            .group_by("season", "catcher_id")
            .agg(
                pl.len().alias("opportunities"),
                (pl.col("context_residual") - pl.col("pitcher_effect"))
                .sum()
                .alias("numerator"),
            )
            .with_columns(
                (pl.col("numerator") / (pl.col("opportunities") + catcher_prior)).alias(
                    "catcher_effect"
                )
            )
        )
        pitchers = (
            work.join(catchers, on=["season", "catcher_id"], validate="m:1")
            .group_by("season", "pitcher_id")
            .agg(
                pl.len().alias("opportunities"),
                (pl.col("context_residual") - pl.col("catcher_effect"))
                .sum()
                .alias("numerator"),
            )
            .with_columns(
                (pl.col("numerator") / (pl.col("opportunities") + pitcher_prior)).alias(
                    "pitcher_effect"
                )
            )
        )
    return (
        catchers.select(
            "season",
            pl.col("catcher_id").alias("player_id"),
            "opportunities",
            pl.col("catcher_effect").alias("effect"),
        ),
        pitchers.select(
            "season",
            pl.col("pitcher_id").alias("player_id"),
            "opportunities",
            pl.col("pitcher_effect").alias("effect"),
        ),
    )


def fit_crossed_deterrence_effects(
    scored: pl.DataFrame,
    *,
    catcher_prior: float = 500.0,
    pitcher_prior: float = 500.0,
    runner_prior: float = 100.0,
    iterations: int = 12,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Separate catcher, pitcher, and runner effects on steal-attempt frequency."""

    if min(catcher_prior, pitcher_prior, runner_prior) <= 0 or iterations <= 0:
        raise ValueError("deterrence priors and iterations must be positive")
    required = {
        "season",
        "catcher_id",
        "pitcher_id",
        "runner_id",
        "context_residual",
    }
    if missing := sorted(required - set(scored.columns)):
        raise ValueError(f"scored deterrence events missing fields: {missing}")
    work = scored.drop_nulls(list(required)).select(*sorted(required))
    effects = {
        entity: work.select("season", f"{entity}_id")
        .unique()
        .with_columns(pl.lit(0.0).alias(f"{entity}_effect"))
        for entity in ("catcher", "pitcher", "runner")
    }
    priors = {
        "catcher": catcher_prior,
        "pitcher": pitcher_prior,
        "runner": runner_prior,
    }
    for _ in range(iterations):
        for entity in ("catcher", "pitcher", "runner"):
            joined = work
            other_effects = []
            for other in effects:
                if other == entity:
                    continue
                joined = joined.join(
                    effects[other], on=["season", f"{other}_id"], validate="m:1"
                )
                other_effects.append(pl.col(f"{other}_effect"))
            effects[entity] = (
                joined.group_by("season", f"{entity}_id")
                .agg(
                    pl.len().alias("opportunities"),
                    (
                        pl.col("context_residual") - pl.sum_horizontal(*other_effects)
                    )
                    .sum()
                    .alias("numerator"),
                )
                .with_columns(
                    (
                        pl.col("numerator")
                        / (pl.col("opportunities") + priors[entity])
                    ).alias(f"{entity}_effect")
                )
            )

    def finish(entity: str) -> pl.DataFrame:
        return effects[entity].select(
            "season",
            pl.col(f"{entity}_id").alias("player_id"),
            "opportunities",
            pl.col(f"{entity}_effect").alias("effect"),
        )

    return finish("catcher"), finish("pitcher"), finish("runner")
