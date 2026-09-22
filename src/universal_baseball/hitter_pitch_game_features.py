"""Universal result/count pitch-sequence and game-environment hitter features.

The public MiLB PBP source has complete pitch result and count sequences at every
affiliated level even when pitch type, velocity, and location are absent.  This
module deliberately uses only that universal evidence.  Game conditions come
from the official bulk schedule feed and describe the game baseline, not
minute-by-minute weather.
"""

from __future__ import annotations

from collections.abc import Iterable

import polars as pl


SWING_CODES = frozenset(
    {"S", "W", "Q", "M", "T", "O", "F", "L", "R", "X", "D", "E", "Y", "J", "Z"}
)
NO_CONTACT_SWING_CODES = frozenset({"S", "W", "Q", "M", "T", "O"})
FOUL_CODES = frozenset({"F", "L", "R"})
IN_PLAY_CODES = frozenset({"X", "D", "E", "Y", "J", "Z"})
CONTACT_CODES = FOUL_CODES | IN_PLAY_CODES
CALLED_DECISION_CODES = frozenset({"B", "*B", "C"})

PITCH_FEATURE_KEY = ("season", "player_id")
_SEQUENCE_KEY = ("game_pk", "at_bat_index")


def classify_pitch_sequence(pitches: pl.DataFrame) -> pl.DataFrame:
    """Add pre-pitch count and universal result-family indicators."""

    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter",
        "pitcher",
        "stand",
        "p_throws",
        "balls",
        "strikes",
        "pitch_result_code",
    }
    missing = sorted(required - set(pitches.columns))
    if missing:
        raise ValueError(f"pitch observations missing fields: {missing}")
    result = pitches.select(sorted(required)).drop_nulls(
        ["season", "game_pk", "at_bat_index", "pitch_number", "batter", "pitcher"]
    )
    result = result.sort([*_SEQUENCE_KEY, "pitch_number"])
    result = result.with_columns(
        pl.col("balls").shift(1).over(_SEQUENCE_KEY).alias("pre_balls"),
        pl.col("strikes").shift(1).over(_SEQUENCE_KEY).alias("pre_strikes"),
        pl.col("pitch_result_code").cast(pl.String).str.to_uppercase(),
        pl.col("stand").cast(pl.String).str.to_uppercase().fill_null("U"),
        pl.col("p_throws").cast(pl.String).str.to_uppercase().fill_null("U"),
    ).with_columns(
        pl.when(pl.col("pitch_number") == 1)
        .then(pl.lit(0))
        .otherwise(pl.col("pre_balls"))
        .cast(pl.Int8)
        .alias("pre_balls"),
        pl.when(pl.col("pitch_number") == 1)
        .then(pl.lit(0))
        .otherwise(pl.col("pre_strikes"))
        .cast(pl.Int8)
        .alias("pre_strikes"),
    )
    return result.with_columns(
        pl.col("pitch_result_code").is_in(SWING_CODES).alias("is_swing"),
        pl.col("pitch_result_code").is_in(NO_CONTACT_SWING_CODES).alias("is_whiff"),
        pl.col("pitch_result_code").is_in(FOUL_CODES).alias("is_foul"),
        pl.col("pitch_result_code").is_in(IN_PLAY_CODES).alias("is_in_play"),
        pl.col("pitch_result_code").is_in(CONTACT_CODES).alias("is_contact"),
        pl.col("pitch_result_code").is_in(CALLED_DECISION_CODES).alias(
            "is_called_decision"
        ),
        (pl.col("pitch_result_code") == "C").alias("is_called_strike"),
        pl.col("pitch_result_code").is_in(["B", "*B"]).alias("is_called_ball"),
        (pl.col("pitch_result_code") == "*B").alias("is_dirt_ball"),
        (pl.col("pitch_number") == 1).alias("is_first_pitch"),
        (pl.col("pre_strikes") == 2).alias("is_two_strike_pitch"),
        ((pl.col("pre_balls") == 3) & (pl.col("pre_strikes") == 2)).alias(
            "is_full_count_pitch"
        ),
        (pl.col("p_throws") == "L").alias("vs_left_pitcher"),
        (pl.col("stand") == "L").alias("bats_left_on_pitch"),
    )


def attach_game_environment(
    pitches: pl.DataFrame, game_context: pl.DataFrame
) -> pl.DataFrame:
    """Attach one official game-baseline context record to every pitch."""

    if "game_pk" not in game_context.columns:
        raise ValueError("game context missing game_pk")
    context_columns = [
        "game_pk",
        "day_night",
        "temperature_f",
        "wind_mph",
        "wind_direction",
        "weather_condition",
        "turf_type",
        "roof_type",
        "left_field_line_ft",
        "center_field_ft",
        "right_field_line_ft",
        "attendance",
        "game_duration_minutes",
        "delay_duration_minutes",
        "home_plate_umpire_id",
        "venue_id",
        "scheduled_datetime_utc",
        "first_pitch_datetime_utc",
    ]
    available = [column for column in context_columns if column in game_context.columns]
    context = game_context.select(available)
    if context.group_by("game_pk").len().filter(pl.col("len") != 1).height:
        raise ValueError("game context is not unique by game_pk")
    result = pitches.join(context, on="game_pk", how="left", validate="m:1")
    string_defaults = {
        "day_night": "",
        "wind_direction": "",
        "weather_condition": "",
        "turf_type": "",
        "roof_type": "",
    }
    for column, default in string_defaults.items():
        if column not in result.columns:
            result = result.with_columns(pl.lit(default).alias(column))
    for column in (
        "temperature_f",
        "wind_mph",
        "left_field_line_ft",
        "center_field_ft",
        "right_field_line_ft",
        "attendance",
        "game_duration_minutes",
        "delay_duration_minutes",
        "home_plate_umpire_id",
        "venue_id",
    ):
        if column not in result.columns:
            result = result.with_columns(pl.lit(None, dtype=pl.Float64).alias(column))
    wind = pl.col("wind_direction").fill_null("").str.to_lowercase()
    weather = pl.col("weather_condition").fill_null("").str.to_lowercase()
    return result.with_columns(
        pl.col("temperature_f").is_not_null().alias("game_context_known"),
        (pl.col("day_night").fill_null("").str.to_lowercase() == "night").alias(
            "is_night"
        ),
        wind.str.contains("out to").alias("wind_out"),
        wind.str.contains("in from").alias("wind_in"),
        (
            wind.str.contains("l to r")
            | wind.str.contains("r to l")
            | wind.str.contains("left to right")
            | wind.str.contains("right to left")
        ).alias("wind_cross"),
        (wind.str.contains("calm") | (pl.col("wind_mph") == 0).fill_null(False)).alias(
            "wind_calm"
        ),
        (pl.col("temperature_f") >= 85).fill_null(False).alias("weather_hot"),
        (pl.col("temperature_f") <= 50).fill_null(False).alias("weather_cold"),
        weather.str.contains("rain|drizzle|showers").alias("weather_rain"),
        weather.str.contains("cloud|overcast").alias("weather_cloudy"),
        (
            (pl.col("turf_type").fill_null("").str.len_chars() > 0)
            & (pl.col("turf_type").fill_null("").str.to_lowercase() != "grass")
        ).alias("artificial_surface"),
        pl.col("roof_type")
        .fill_null("")
        .str.to_lowercase()
        .is_in(["closed", "dome"])
        .alias("roof_closed_or_dome"),
    )


def _safe_ratio(success: str, exposure: str, alias: str) -> pl.Expr:
    return (
        pl.when(pl.col(exposure) > 0)
        .then(pl.col(success) / pl.col(exposure))
        .otherwise(None)
        .alias(alias)
    )


def _shrink_rate(
    success: str,
    exposure: str,
    prior: float,
    weight: float,
    alias: str,
) -> pl.Expr:
    return (
        (pl.col(success) + float(weight) * float(prior))
        / (pl.col(exposure) + float(weight))
    ).alias(alias)


def _rate_prior(frame: pl.DataFrame, success: str, exposure: str) -> float:
    totals = frame.select(pl.col(success).sum(), pl.col(exposure).sum()).row(0)
    return float(totals[0] / totals[1]) if totals[1] else 0.0


def _pitcher_adjusted_batter_residual(
    pitches: pl.DataFrame,
    *,
    eligible: pl.Expr,
    outcome: str,
    name: str,
    pitcher_prior: float = 250.0,
    hitter_prior: float = 100.0,
    adjust_umpire: bool = False,
) -> pl.DataFrame:
    """Return batter residuals after count/matchup/level and pitcher adjustment."""

    rows = pitches.filter(eligible).select(
        "season",
        "level",
        "batter",
        "pitcher",
        "pre_balls",
        "pre_strikes",
        "stand",
        "p_throws",
        "home_plate_umpire_id",
        pl.col(outcome).cast(pl.Float64).alias("y"),
    )
    if rows.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "player_id": pl.Int64,
                f"oa_{name}": pl.Float64,
                f"oa_{name}_opportunities": pl.UInt32,
            }
        )
    broad = rows.group_by("season", "level").agg(
        pl.col("y").mean().alias("broad_rate")
    )
    cell_keys = [
        "season",
        "level",
        "pre_balls",
        "pre_strikes",
        "stand",
        "p_throws",
    ]
    cells = (
        rows.group_by(cell_keys)
        .agg(pl.col("y").sum().alias("cell_success"), pl.len().alias("cell_n"))
        .join(broad, on=["season", "level"], validate="m:1")
        .with_columns(
            ((pl.col("cell_success") + 50.0 * pl.col("broad_rate")) / (pl.col("cell_n") + 50.0)).alias(
                "cell_expected"
            )
        )
        .select(*cell_keys, "cell_expected")
    )
    rows = rows.join(cells, on=cell_keys, validate="m:1").with_columns(
        (pl.col("y") - pl.col("cell_expected")).alias("cell_residual")
    )
    pitcher = rows.group_by("season", "pitcher").agg(
        pl.col("cell_residual").sum().alias("pitcher_residual_sum"),
        pl.len().alias("pitcher_n"),
    ).with_columns(
        (pl.col("pitcher_residual_sum") / (pl.col("pitcher_n") + pitcher_prior)).alias(
            "pitcher_effect"
        )
    )
    rows = rows.join(
        pitcher.select("season", "pitcher", "pitcher_effect"),
        on=["season", "pitcher"],
        validate="m:1",
    )
    if adjust_umpire:
        umpire = (
            rows.drop_nulls("home_plate_umpire_id")
            .group_by("season", "home_plate_umpire_id")
            .agg(
                pl.col("cell_residual").sum().alias("umpire_residual_sum"),
                pl.len().alias("umpire_n"),
            )
            .with_columns(
                (pl.col("umpire_residual_sum") / (pl.col("umpire_n") + 200.0)).alias(
                    "umpire_effect"
                )
            )
        )
        rows = rows.join(
            umpire.select("season", "home_plate_umpire_id", "umpire_effect"),
            on=["season", "home_plate_umpire_id"],
            how="left",
            validate="m:1",
        ).with_columns(pl.col("umpire_effect").fill_null(0.0))
    else:
        rows = rows.with_columns(pl.lit(0.0).alias("umpire_effect"))
    return (
        rows.with_columns(
            (
                pl.col("y")
                - (
                    pl.col("cell_expected")
                    + pl.col("pitcher_effect")
                    + pl.col("umpire_effect")
                ).clip(0.001, 0.999)
            ).alias("fully_adjusted_residual")
        )
        .group_by("season", pl.col("batter").alias("player_id"))
        .agg(
            pl.col("fully_adjusted_residual").sum().alias("residual_sum"),
            pl.len().alias(f"oa_{name}_opportunities"),
        )
        .with_columns(
            (
                pl.col("residual_sum")
                / (pl.col(f"oa_{name}_opportunities") + hitter_prior)
            ).alias(f"oa_{name}")
        )
        .drop("residual_sum")
    )


def _split_features(pitches: pl.DataFrame, prior_weight: float) -> pl.DataFrame:
    split = (
        pitches.filter(pl.col("p_throws").is_in(["L", "R"]))
        .group_by("season", pl.col("batter").alias("player_id"), "p_throws")
        .agg(
            pl.len().alias("split_pitches"),
            pl.col("is_swing").sum().alias("split_swings"),
            (pl.col("is_contact") & pl.col("is_swing")).sum().alias(
                "split_contacts"
            ),
            pl.col("is_called_decision").sum().alias("split_called_decisions"),
            pl.col("is_called_strike").sum().alias("split_called_strikes"),
        )
        .with_columns(
            _safe_ratio("split_swings", "split_pitches", "raw_split_swing_rate"),
            _safe_ratio(
                "split_contacts", "split_swings", "raw_split_contact_per_swing"
            ),
            _safe_ratio(
                "split_called_strikes",
                "split_called_decisions",
                "raw_split_called_strike_rate",
            ),
        )
    )
    player = split.group_by("season", "player_id").agg(
        pl.col("split_swings").sum().alias("all_swings"),
        pl.col("split_pitches").sum().alias("all_pitches"),
        pl.col("split_contacts").sum().alias("all_contacts"),
        pl.col("split_called_decisions").sum().alias("all_called_decisions"),
        pl.col("split_called_strikes").sum().alias("all_called_strikes"),
    ).with_columns(
        _safe_ratio("all_swings", "all_pitches", "player_swing_rate"),
        _safe_ratio("all_contacts", "all_swings", "player_contact_per_swing"),
        _safe_ratio(
            "all_called_strikes",
            "all_called_decisions",
            "player_called_strike_rate",
        ),
    )
    split = split.join(player, on=["season", "player_id"], validate="m:1").with_columns(
        (
            (pl.col("split_swings") + prior_weight * pl.col("player_swing_rate"))
            / (pl.col("split_pitches") + prior_weight)
        ).alias("split_swing_rate"),
        (
            (pl.col("split_contacts") + prior_weight * pl.col("player_contact_per_swing"))
            / (pl.col("split_swings") + prior_weight)
        ).alias("split_contact_per_swing"),
        (
            (
                pl.col("split_called_strikes")
                + prior_weight * pl.col("player_called_strike_rate")
            )
            / (pl.col("split_called_decisions") + prior_weight)
        ).alias("split_called_strike_rate"),
    )
    values = split.select(
        "season",
        "player_id",
        "p_throws",
        "split_pitches",
        "split_swing_rate",
        "split_contact_per_swing",
        "split_called_strike_rate",
    ).pivot(
        on="p_throws",
        index=["season", "player_id"],
        values=[
            "split_pitches",
            "split_swing_rate",
            "split_contact_per_swing",
            "split_called_strike_rate",
        ],
    )
    renames = {}
    for column in values.columns:
        if column in PITCH_FEATURE_KEY:
            continue
        base, hand = column.rsplit("_", maxsplit=1)
        renames[column] = f"{base.lower()}_vs_{hand.lower()}"
    values = values.rename(renames)
    expected = [
        f"{metric}_vs_{hand}"
        for metric in (
            "split_pitches",
            "split_swing_rate",
            "split_contact_per_swing",
            "split_called_strike_rate",
        )
        for hand in ("l", "r")
    ]
    for column in expected:
        if column not in values.columns:
            values = values.with_columns(pl.lit(None, dtype=pl.Float64).alias(column))
    return values.select(*PITCH_FEATURE_KEY, *expected)


def build_player_season_pitch_game_features(
    pitches: pl.DataFrame,
    game_context: pl.DataFrame,
    *,
    rate_prior_weight: float = 100.0,
    split_prior_weight: float = 75.0,
) -> pl.DataFrame:
    """Build one universal pitch/game feature row per hitter-season."""

    rows = attach_game_environment(classify_pitch_sequence(pitches), game_context)
    player = rows.group_by("season", pl.col("batter").alias("player_id")).agg(
        pl.len().alias("pitch_count"),
        pl.struct(_SEQUENCE_KEY).n_unique().alias("pa_count"),
        pl.col("game_pk").n_unique().alias("game_count"),
        pl.col("is_swing").sum().alias("swing_count"),
        pl.col("is_contact").sum().alias("contact_count"),
        pl.col("is_whiff").sum().alias("whiff_count"),
        pl.col("is_foul").sum().alias("foul_count"),
        pl.col("is_in_play").sum().alias("in_play_count"),
        pl.col("is_called_decision").sum().alias("called_decision_count"),
        pl.col("is_called_strike").sum().alias("called_strike_count"),
        pl.col("is_dirt_ball").sum().alias("dirt_ball_count"),
        pl.col("is_first_pitch").sum().alias("first_pitch_count"),
        (pl.col("is_first_pitch") & pl.col("is_swing")).sum().alias(
            "first_pitch_swing_count"
        ),
        (pl.col("is_first_pitch") & pl.col("is_called_strike")).sum().alias(
            "first_pitch_called_strike_count"
        ),
        pl.col("is_two_strike_pitch").sum().alias("two_strike_pitch_count"),
        (pl.col("is_two_strike_pitch") & pl.col("is_swing")).sum().alias(
            "two_strike_swing_count"
        ),
        (pl.col("is_two_strike_pitch") & pl.col("is_contact")).sum().alias(
            "two_strike_contact_count"
        ),
        (pl.col("is_two_strike_pitch") & pl.col("is_whiff")).sum().alias(
            "two_strike_whiff_count"
        ),
        pl.col("vs_left_pitcher").sum().alias("vs_left_pitch_count"),
        pl.col("bats_left_on_pitch").sum().alias("bats_left_pitch_count"),
    )
    rate_specs = {
        "swing_rate": ("swing_count", "pitch_count"),
        "contact_per_swing": ("contact_count", "swing_count"),
        "whiff_per_swing": ("whiff_count", "swing_count"),
        "foul_per_swing": ("foul_count", "swing_count"),
        "in_play_per_swing": ("in_play_count", "swing_count"),
        "called_strike_rate": ("called_strike_count", "called_decision_count"),
        "dirt_ball_rate": ("dirt_ball_count", "pitch_count"),
        "first_pitch_swing_rate": ("first_pitch_swing_count", "first_pitch_count"),
        "first_pitch_called_strike_rate": (
            "first_pitch_called_strike_count",
            "first_pitch_count",
        ),
        "two_strike_contact_per_swing": (
            "two_strike_contact_count",
            "two_strike_swing_count",
        ),
        "two_strike_whiff_per_swing": (
            "two_strike_whiff_count",
            "two_strike_swing_count",
        ),
        "vs_left_pitch_share": ("vs_left_pitch_count", "pitch_count"),
        "bats_left_pitch_share": ("bats_left_pitch_count", "pitch_count"),
    }
    priors = {
        name: _rate_prior(player, success, exposure)
        for name, (success, exposure) in rate_specs.items()
    }
    player = player.with_columns(
        (pl.col("pitch_count") / pl.col("pa_count").clip(lower_bound=1)).alias(
            "pitches_per_pa"
        ),
        *[
            _shrink_rate(
                success,
                exposure,
                priors[name],
                rate_prior_weight,
                name,
            )
            for name, (success, exposure) in rate_specs.items()
        ],
    )

    pa = rows.group_by("season", "batter", *_SEQUENCE_KEY).agg(
        pl.col("is_two_strike_pitch").any().alias("pa_reached_two_strikes"),
        pl.col("is_full_count_pitch").any().alias("pa_reached_full_count"),
        pl.col("game_context_known").first().alias("game_context_known"),
        pl.col("temperature_f").first(),
        pl.col("wind_mph").first(),
        pl.col("is_night").first(),
        pl.col("wind_out").first(),
        pl.col("wind_in").first(),
        pl.col("wind_cross").first(),
        pl.col("wind_calm").first(),
        pl.col("weather_hot").first(),
        pl.col("weather_cold").first(),
        pl.col("weather_rain").first(),
        pl.col("weather_cloudy").first(),
        pl.col("artificial_surface").first(),
        pl.col("roof_closed_or_dome").first(),
        pl.col("left_field_line_ft").first(),
        pl.col("center_field_ft").first(),
        pl.col("right_field_line_ft").first(),
        pl.col("attendance").first(),
        pl.col("game_duration_minutes").first(),
        pl.col("delay_duration_minutes").first(),
        pl.col("venue_id").first(),
        pl.col("home_plate_umpire_id").first(),
    )
    environment = pa.group_by(
        "season", pl.col("batter").alias("player_id")
    ).agg(
        pl.col("pa_reached_two_strikes").mean().alias("two_strike_pa_rate"),
        pl.col("pa_reached_full_count").mean().alias("full_count_pa_rate"),
        pl.col("game_context_known").mean().alias("game_context_coverage"),
        pl.col("temperature_f").mean().alias("mean_temperature_f"),
        pl.col("temperature_f").std().alias("sd_temperature_f"),
        pl.col("wind_mph").mean().alias("mean_wind_mph"),
        pl.col("is_night").mean().alias("night_pa_share"),
        pl.col("wind_out").mean().alias("wind_out_pa_share"),
        pl.col("wind_in").mean().alias("wind_in_pa_share"),
        pl.col("wind_cross").mean().alias("wind_cross_pa_share"),
        pl.col("wind_calm").mean().alias("wind_calm_pa_share"),
        pl.col("weather_hot").mean().alias("hot_pa_share"),
        pl.col("weather_cold").mean().alias("cold_pa_share"),
        pl.col("weather_rain").mean().alias("rain_pa_share"),
        pl.col("weather_cloudy").mean().alias("cloudy_pa_share"),
        pl.col("artificial_surface").mean().alias("artificial_surface_pa_share"),
        pl.col("roof_closed_or_dome").mean().alias("closed_roof_pa_share"),
        pl.col("left_field_line_ft").mean().alias("mean_left_field_line_ft"),
        pl.col("center_field_ft").mean().alias("mean_center_field_ft"),
        pl.col("right_field_line_ft").mean().alias("mean_right_field_line_ft"),
        pl.col("attendance").mean().alias("mean_attendance"),
        pl.col("game_duration_minutes").mean().alias("mean_game_duration_minutes"),
        pl.col("delay_duration_minutes").mean().alias("mean_delay_minutes"),
        pl.col("venue_id").drop_nulls().n_unique().alias("unique_venues"),
        pl.col("home_plate_umpire_id").drop_nulls().n_unique().alias(
            "unique_home_plate_umpires"
        ),
    )
    adjusted_specs = (
        (pl.lit(True), "is_swing", "swing_rate", False),
        (pl.col("is_swing"), "is_contact", "contact_per_swing", False),
        (
            pl.col("is_called_decision"),
            "is_called_strike",
            "called_strike_rate",
            True,
        ),
        (
            pl.col("is_first_pitch"),
            "is_swing",
            "first_pitch_swing_rate",
            False,
        ),
        (
            pl.col("is_two_strike_pitch") & pl.col("is_swing"),
            "is_contact",
            "two_strike_contact_per_swing",
            False,
        ),
    )
    result = player.join(environment, on=list(PITCH_FEATURE_KEY), validate="1:1")
    for eligible, outcome, name, adjust_umpire in adjusted_specs:
        result = result.join(
            _pitcher_adjusted_batter_residual(
                rows,
                eligible=eligible,
                outcome=outcome,
                name=name,
                adjust_umpire=adjust_umpire,
            ),
            on=list(PITCH_FEATURE_KEY),
            how="left",
            validate="1:1",
        )
    result = result.join(
        _split_features(rows, split_prior_weight),
        on=list(PITCH_FEATURE_KEY),
        how="left",
        validate="1:1",
    )
    return result.sort(PITCH_FEATURE_KEY)


def attach_pitch_game_lags(
    panel: pl.DataFrame,
    annual_features: pl.DataFrame,
    *,
    lags: Iterable[int] = (0, 1, 2),
) -> pl.DataFrame:
    """Join numeric player-season pitch/game features to the value panel."""

    required_panel = {"origin_year", "player_id"}
    if not required_panel.issubset(panel.columns):
        raise ValueError("modeling panel missing origin_year/player_id")
    if not set(PITCH_FEATURE_KEY).issubset(annual_features.columns):
        raise ValueError("annual pitch features missing season/player_id")
    feature_columns = [
        column for column in annual_features.columns if column not in PITCH_FEATURE_KEY
    ]
    non_numeric = [
        column
        for column in feature_columns
        if not annual_features.schema[column].is_numeric()
    ]
    if non_numeric:
        raise ValueError(f"pitch/game lag features must be numeric: {non_numeric}")
    result = panel
    for lag in lags:
        renamed = annual_features.select(
            (pl.col("season") + int(lag)).alias("origin_year"),
            "player_id",
            *[
                pl.col(column).alias(f"pitch_lag{lag}__{column}")
                for column in feature_columns
            ],
            pl.lit(1, dtype=pl.Int8).alias(f"pitch_lag{lag}__available"),
        )
        result = result.join(
            renamed,
            on=["origin_year", "player_id"],
            how="left",
            validate="m:1",
        ).with_columns(
            pl.col(f"pitch_lag{lag}__available").fill_null(0)
        )
    return result
