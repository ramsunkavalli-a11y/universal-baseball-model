"""Chronology-safe cumulative MLB-arrival model for pre-MLB players."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import log

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.hitter_opportunity_paths import hitter_level_tier
from universal_baseball.player_demographics import normalize_birth_country
from universal_baseball.draft_source import draft_pedigree_as_of
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS
from universal_baseball.prospect_outcome_quality import SHORTENED_2020_SCALE


ARRIVAL_MODEL_ID = "phase2_pre_mlb_two_year_arrival_v4_development_path"
LEVELS = ("A_OR_BELOW", "AA", "AAA", "INACTIVE", "UNKNOWN")
ROLES = ("C", "MIDDLE_INFIELD", "OUTFIELD", "CORNER", "STARTER", "SWINGMAN")
COUNTRIES = (
    "USA", "Dominican Republic", "Venezuela", "Mexico", "Cuba",
    "Puerto Rico", "Canada", "Colombia", "Panama", "Nicaragua",
    "Brazil", "Australia", "Japan", "South Korea", "Taiwan",
)
HITTER_POSITION_BY_STATSAPI_CODE = {
    "2": "C",
    "3": "1B",
    "4": "2B",
    "5": "3B",
    "6": "SS",
    "7": "LF",
    "8": "CF",
    "9": "RF",
    "10": "DH",
}


def _primary_affiliated_level(
    skill_stats: pl.DataFrame, *, snapshot_year: int, player_type: str
) -> pl.DataFrame:
    """Return the level carrying the most current-season workload.

    A short promotion or rehab appearance must not make a full season look like it
    was played at the highest level reached.  Ties favor the more advanced level,
    but workload always wins first.
    """

    workload = "plate_appearances" if player_type == "hitter" else "batters_faced"
    if "level_group" not in skill_stats.columns:
        # Older fixtures and imported sources may not carry an explicit level.
        # The caller then retains the chronology-safe snapshot level.
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "primary_level_tier": pl.String,
                "primary_level_workload_share": pl.Float64,
            }
        )
    level_order = {"A_OR_BELOW": 1, "AA": 2, "AAA": 3, "MLB": 4, "UNKNOWN": 0}
    by_level = (
        skill_stats.filter(
            (pl.col("season") == snapshot_year)
            & (pl.col("sport_id") != 1)
            & (pl.col(workload) > 0)
        )
        .with_columns(
            pl.col("level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("primary_level_tier")
        )
        .group_by("player_id", "primary_level_tier")
        .agg(pl.col(workload).sum().cast(pl.Float64).alias("primary_level_workload"))
        .with_columns(
            pl.col("primary_level_workload").sum().over("player_id")
            .alias("current_affiliated_workload"),
            pl.col("primary_level_tier").replace_strict(
                level_order, default=0
            ).alias("primary_level_order"),
        )
        .sort(
            ["player_id", "primary_level_workload", "primary_level_order"],
            descending=[False, True, True],
        )
        .unique("player_id", keep="first", maintain_order=True)
    )
    return by_level.select(
        "player_id",
        "primary_level_tier",
        (
            pl.col("primary_level_workload")
            / pl.col("current_affiliated_workload").clip(1.0, None)
        ).alias("primary_level_workload_share"),
    )


def _affiliated_development_path(
    skill_stats: pl.DataFrame, *, snapshot_year: int, player_type: str
) -> pl.DataFrame:
    """Summarize progression and inactivity using only seasons known at cutoff."""

    workload = "plate_appearances" if player_type == "hitter" else "batters_faced"
    if "level_group" not in skill_stats.columns:
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "level_progression": pl.Float64,
                "seasons_since_affiliated_activity": pl.Float64,
                "development_history_workload": pl.Float64,
                "development_history_seasons": pl.Float64,
            }
        )
    order = {"A_OR_BELOW": 1, "AA": 2, "AAA": 3, "MLB": 4, "UNKNOWN": 0}
    by_level = (
        skill_stats.filter(
            (pl.col("season") <= snapshot_year)
            & (pl.col("sport_id") != 1)
            & (pl.col(workload) > 0)
        )
        .with_columns(
            pl.col("level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("broad_level")
        )
        .group_by("player_id", "season", "broad_level")
        .agg(pl.col(workload).sum().cast(pl.Float64).alias("level_workload"))
        .with_columns(
            pl.col("broad_level").replace_strict(order, default=0).alias("level_order"),
            pl.col("level_workload").sum().over(["player_id", "season"])
            .alias("season_workload"),
        )
        .sort(
            ["player_id", "season", "level_workload", "level_order"],
            descending=[False, False, True, True],
        )
        .unique(["player_id", "season"], keep="first", maintain_order=True)
        .sort(["player_id", "season"])
        .with_columns(
            pl.col("level_order").shift(1).over("player_id").alias("prior_level_order")
        )
    )
    return (
        by_level.group_by("player_id")
        .agg(
            pl.col("season").max().alias("last_affiliated_season"),
            pl.col("season_workload").sum().alias("development_history_workload"),
            pl.col("season").n_unique().cast(pl.Float64).alias(
                "development_history_seasons"
            ),
            pl.when(pl.col("season") == snapshot_year)
            .then(pl.col("level_order") - pl.col("prior_level_order"))
            .otherwise(None)
            .drop_nulls()
            .last()
            .alias("level_progression"),
        )
        .with_columns(
            (pl.lit(snapshot_year) - pl.col("last_affiliated_season"))
            .cast(pl.Float64)
            .alias("seasons_since_affiliated_activity"),
            pl.col("level_progression").cast(pl.Float64).fill_null(0.0),
        )
        .drop("last_affiliated_season")
    )
def _primary_hitter_positions(
    basic_stats: pl.DataFrame, *, snapshot_year: int
) -> pl.DataFrame:
    """Choose one reproducible, games-weighted position per hitter-season."""

    game_weight = pl.col("games") if "games" in basic_stats.columns else pl.lit(1)
    return (
        basic_stats.filter(
            (pl.col("season") == snapshot_year)
            & (pl.col("stat_group") == "hitting")
            & (pl.col("sport_id") != 1)
            & pl.col("position_code").is_not_null()
        )
        .group_by("player_id", "position_code")
        .agg(game_weight.sum().alias("position_games"))
        .with_columns(
            pl.col("position_code").cast(pl.Int64, strict=False).fill_null(99)
            .alias("position_code_order")
        )
        .sort(
            ["player_id", "position_games", "position_code_order"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", pl.col("position_code").alias("position"))
    )


def _positive_component_roles(
    skill_stats: pl.DataFrame,
    *,
    snapshot_year: int,
    horizon: int,
    player_type: str,
) -> pl.DataFrame:
    """Label meaningful future MLB seasons with at-least-average core components."""

    future = skill_stats.filter(
        (pl.col("sport_id") == 1)
        & (pl.col("season") > snapshot_year)
        & (pl.col("season") <= snapshot_year + horizon)
    )
    if player_type == "hitter":
        season = (
            future.group_by("player_id", "season")
            .agg(
                pl.col("plate_appearances").sum().cast(pl.Float64).alias("workload"),
                (pl.col("base_on_balls") - pl.col("intentional_walks"))
                .sum().cast(pl.Float64).alias("ubb"),
                pl.col("hit_by_pitch").sum().cast(pl.Float64).alias("hbp"),
                (
                    pl.col("hits") - pl.col("doubles") - pl.col("triples")
                    - pl.col("home_runs")
                ).sum().cast(pl.Float64).alias("single"),
                pl.col("doubles").sum().cast(pl.Float64).alias("double"),
                pl.col("triples").sum().cast(pl.Float64).alias("triple"),
                pl.col("home_runs").sum().cast(pl.Float64).alias("hr"),
            )
            .with_columns(
                (
                    pl.col("ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
                    + pl.col("hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
                    + pl.col("single") * NEUTRAL_WOBA_WEIGHTS["1B"]
                    + pl.col("double") * NEUTRAL_WOBA_WEIGHTS["2B"]
                    + pl.col("triple") * NEUTRAL_WOBA_WEIGHTS["3B"]
                    + pl.col("hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
                ).alias("component_numerator")
            )
        )
        season = season.with_columns(
            pl.when(pl.col("season") == 2020)
            .then(pl.col("workload") * SHORTENED_2020_SCALE)
            .otherwise(pl.col("workload"))
            .alias("adjusted_workload"),
            (pl.col("component_numerator").sum().over("season")
             / pl.col("workload").sum().over("season")).alias("league_rate"),
            (pl.col("component_numerator") / pl.col("workload")).alias("player_rate"),
        )
        positive = (pl.col("adjusted_workload") >= 200) & (
            pl.col("player_rate") >= pl.col("league_rate")
        )
    else:
        season = (
            future.group_by("player_id", "season")
            .agg(
                pl.col("batters_faced").sum().cast(pl.Float64).alias("workload"),
                pl.col("strike_outs").sum().cast(pl.Float64).alias("so"),
                (pl.col("base_on_balls") - pl.col("intentional_walks"))
                .sum().cast(pl.Float64).alias("ubb"),
                pl.col("hit_batters").sum().cast(pl.Float64).alias("hbp"),
                pl.col("home_runs").sum().cast(pl.Float64).alias("hr"),
            )
            .with_columns(
                (
                    13.0 * pl.col("hr")
                    + 3.0 * (pl.col("ubb") + pl.col("hbp"))
                    - 2.0 * pl.col("so")
                ).alias("component_numerator")
            )
        )
        season = season.with_columns(
            pl.when(pl.col("season") == 2020)
            .then(pl.col("workload") * SHORTENED_2020_SCALE)
            .otherwise(pl.col("workload"))
            .alias("adjusted_workload"),
            (pl.col("component_numerator").sum().over("season")
             / pl.col("workload").sum().over("season")).alias("league_rate"),
            (pl.col("component_numerator") / pl.col("workload")).alias("player_rate"),
        )
        positive = (pl.col("adjusted_workload") >= 200) & (
            pl.col("player_rate") <= pl.col("league_rate")
        )
    return (
        season.filter(positive)
        .select("player_id").unique()
        .with_columns(
            pl.lit(1).cast(pl.Int64).alias(
                "positive_component_role_within_horizon"
            )
        )
    )


@dataclass(frozen=True, slots=True)
class ArrivalFit:
    player_type: str
    outcome_name: str
    target_column: str
    feature_set: str
    production_priors: tuple[float, float, float, float]
    production_regression: float
    model: LogisticRegression
    global_rate: float
    level_rates: dict[str, float]


def _role_tier(
    position: object, *, player_type: str, games: float = 0, starts: float = 0
) -> str:
    if player_type == "pitcher":
        if games <= 0:
            return "OTHER"
        if starts * 2 >= games:
            return "STARTER"
        return "RELIEVER" if starts == 0 else "SWINGMAN"
    value = str(position or "").upper()
    value = HITTER_POSITION_BY_STATSAPI_CODE.get(value, value)
    if value == "C":
        return "C"
    if value in {"2B", "SS"}:
        return "MIDDLE_INFIELD"
    if value in {"LF", "CF", "RF", "OF"}:
        return "OUTFIELD"
    if value in {"1B", "3B"}:
        return "CORNER"
    return "OTHER"


def _production_features(
    skill_stats: pl.DataFrame,
    basic_stats: pl.DataFrame,
    *,
    snapshot_year: int,
    player_type: str,
) -> pl.DataFrame:
    workload = "plate_appearances" if player_type == "hitter" else "batters_faced"
    history = skill_stats.filter(
        (pl.col("season") <= snapshot_year) & (pl.col("sport_id") != 1)
    )
    playing_history = history.group_by("player_id").agg(
        pl.col(workload).sum().cast(pl.Float64).alias("prior_affiliated_workload"),
        pl.col("season").n_unique().cast(pl.Float64).alias("prior_affiliated_seasons"),
    )
    current = history.filter(pl.col("season") == snapshot_year)
    if player_type == "hitter":
        current = current.group_by("player_id").agg(
            pl.col("plate_appearances").sum().cast(pl.Float64).alias(
                "current_milb_workload"
            ),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("n1"),
            pl.col("strike_outs").sum().alias("n2"),
            pl.col("home_runs").sum().alias("n3"),
            (pl.col("doubles") + pl.col("triples") + pl.col("home_runs"))
            .sum().alias("n4"),
        )
        position = _primary_hitter_positions(
            basic_stats, snapshot_year=snapshot_year
        )
        current = current.join(position, on="player_id", how="left").with_columns(
            pl.col("position").map_elements(
                lambda value: _role_tier(value, player_type="hitter"),
                return_dtype=pl.String,
            ).alias("role_tier")
        )
    else:
        current = current.group_by("player_id").agg(
            pl.col("batters_faced").sum().cast(pl.Float64).alias(
                "current_milb_workload"
            ),
            pl.col("strike_outs").sum().alias("n1"),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("n2"),
            pl.col("hit_batters").sum().alias("n3"),
            pl.col("home_runs").sum().alias("n4"),
            pl.col("games").sum().alias("games"),
            pl.col("starts").sum().alias("starts"),
        ).with_columns(
            pl.struct("games", "starts").map_elements(
                lambda row: _role_tier(
                    None,
                    player_type="pitcher",
                    games=row["games"],
                    starts=row["starts"],
                ),
                return_dtype=pl.String,
            ).alias("role_tier")
        )
    rates = [
        (pl.col(f"n{index}") / pl.col("current_milb_workload").clip(1.0, None))
        .clip(0.0, 1.0).alias(f"production_rate_{index}")
        for index in range(1, 5)
    ]
    primary_level = _primary_affiliated_level(
        skill_stats, snapshot_year=snapshot_year, player_type=player_type
    )
    return (
        current.with_columns(*rates)
        .join(playing_history, on="player_id", how="left")
        .join(primary_level, on="player_id", how="left", validate="1:1")
        .select(
            "player_id",
            "current_milb_workload",
            "prior_affiliated_workload",
            "prior_affiliated_seasons",
            "role_tier",
            "primary_level_tier",
            "primary_level_workload_share",
            *[f"production_rate_{index}" for index in range(1, 5)],
        )
    )


def _fill_predictor_nulls(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("current_milb_workload").fill_null(0.0),
        pl.col("prior_affiliated_workload").fill_null(0.0),
        pl.col("prior_affiliated_seasons").fill_null(0.0),
        pl.col("primary_level_workload_share").fill_null(0.0),
        pl.col("primary_level_tier").fill_null(pl.col("level_tier")),
        pl.col("level_progression").fill_null(0.0),
        pl.col("seasons_since_affiliated_activity").fill_null(6.0),
        pl.col("development_history_workload").fill_null(0.0),
        pl.col("development_history_seasons").fill_null(0.0),
        pl.col("role_tier").fill_null("OTHER"),
        pl.col("height_inches").fill_null(72.0),
        pl.col("weight_pounds").fill_null(190.0),
        pl.col("bat_side").fill_null("U"),
        pl.col("pitch_hand").fill_null("U"),
        pl.col("birth_country").fill_null("UNKNOWN"),
        pl.col("birth_city").fill_null("UNKNOWN"),
        pl.col("birth_state_province").fill_null("UNKNOWN"),
        pl.col("strike_zone_top").fill_null(3.4),
        pl.col("strike_zone_bottom").fill_null(1.6),
        pl.col("gender").fill_null("UNKNOWN"),
        pl.col("primary_position_code").fill_null(""),
        pl.col("rule4_drafted").fill_null(False),
        pl.col("draft_pick_quality").fill_null(0.0),
        pl.col("signing_bonus_percentile").fill_null(0.0),
        pl.col("signing_bonus_known").fill_null(False),
        pl.col("high_school_draftee").fill_null(False),
        *[
            pl.col(f"production_rate_{index}").fill_null(0.0)
            for index in range(1, 5)
        ],
    )


def _join_demographics(
    frame: pl.DataFrame, demographics: pl.DataFrame | None
) -> pl.DataFrame:
    columns = (
        "height_inches", "weight_pounds", "bat_side", "pitch_hand",
        "birth_country", "birth_city", "birth_state_province",
        "strike_zone_top", "strike_zone_bottom", "gender",
        "primary_position_code",
    )
    if demographics is None:
        return frame.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("height_inches"),
            pl.lit(None, dtype=pl.Float64).alias("weight_pounds"),
            pl.lit(None, dtype=pl.String).alias("bat_side"),
            pl.lit(None, dtype=pl.String).alias("pitch_hand"),
            pl.lit(None, dtype=pl.String).alias("birth_country"),
            pl.lit(None, dtype=pl.String).alias("birth_city"),
            pl.lit(None, dtype=pl.String).alias("birth_state_province"),
            pl.lit(None, dtype=pl.Float64).alias("strike_zone_top"),
            pl.lit(None, dtype=pl.Float64).alias("strike_zone_bottom"),
            pl.lit(None, dtype=pl.String).alias("gender"),
            pl.lit(None, dtype=pl.String).alias("primary_position_code"),
        )
    required = {"player_id", *columns}
    if missing := sorted(required - set(demographics.columns)):
        raise ValueError(f"demographics missing columns: {missing}")
    return frame.join(
        demographics.select("player_id", *columns),
        on="player_id", how="left", validate="m:1",
    )


def _join_pedigree(
    frame: pl.DataFrame,
    draft_history: pl.DataFrame | None,
    *,
    snapshot_year: int,
) -> pl.DataFrame:
    columns = (
        "rule4_drafted", "draft_pick_quality", "signing_bonus_percentile",
        "signing_bonus_known", "high_school_draftee",
    )
    if draft_history is None:
        return frame.with_columns(
            pl.lit(None, dtype=pl.Boolean).alias("rule4_drafted"),
            pl.lit(None, dtype=pl.Float64).alias("draft_pick_quality"),
            pl.lit(None, dtype=pl.Float64).alias("signing_bonus_percentile"),
            pl.lit(None, dtype=pl.Boolean).alias("signing_bonus_known"),
            pl.lit(None, dtype=pl.Boolean).alias("high_school_draftee"),
        )
    return frame.join(
        draft_pedigree_as_of(draft_history, snapshot_year).select(
            "player_id", *columns
        ),
        on="player_id", how="left", validate="m:1",
    )


def build_arrival_cohort(
    snapshots: pl.DataFrame,
    stats: pl.DataFrame,
    membership: pl.DataFrame,
    skill_stats: pl.DataFrame,
    debut_dates: pl.DataFrame,
    *,
    snapshot_year: int,
    horizon: int,
    player_type: str,
    demographics: pl.DataFrame | None = None,
    draft_history: pl.DataFrame | None = None,
    outcome_skill_stats: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build a pre-MLB cohort and observed cumulative debut outcome."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    if horizon < 1:
        raise ValueError("arrival horizon must be positive")
    debut_required = {"player_id", "mlb_debut_date"}
    if missing := sorted(debut_required - set(debut_dates.columns)):
        raise ValueError(f"debut dates missing fields: {missing}")
    if debut_dates.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("debut dates violate player grain")
    group = "hitting" if player_type == "hitter" else "pitching"
    workload = "plate_appearances" if player_type == "hitter" else "batters_faced"
    players = snapshots.filter(pl.col("snapshot_year") == snapshot_year).select(
        "player_id", "age_years", "as_of_level_group"
    )
    prior_mlb = (
        stats.filter(
            (pl.col("stat_group") == group)
            & (pl.col("sport_id") == 1)
            & (pl.col("season") <= snapshot_year)
            & (pl.col(workload) > 0)
        )
        .select("player_id").unique()
        .with_columns(pl.lit(True).alias("prior_mlb"))
    )
    official_debut = debut_dates.select("player_id", "mlb_debut_date")
    production = _production_features(
        skill_stats, stats, snapshot_year=snapshot_year, player_type=player_type
    )
    development = _affiliated_development_path(
        skill_stats, snapshot_year=snapshot_year, player_type=player_type
    )
    future_stats = stats.filter(
        (pl.col("stat_group") == group)
        & (pl.col("sport_id") == 1)
        & (pl.col("season") > snapshot_year)
        & (pl.col("season") <= snapshot_year + horizon)
        & (pl.col(workload) > 0)
    )
    future = (
        future_stats
        .select("player_id").unique()
        .with_columns(pl.lit(1).cast(pl.Int64).alias("arrived_within_horizon"))
    )
    season_workload = (
        future_stats.group_by("player_id", "season")
        .agg(pl.col(workload).sum().alias("raw_mlb_workload"))
        .with_columns(
            pl.when(pl.col("season") == 2020)
            .then(pl.col("raw_mlb_workload") * SHORTENED_2020_SCALE)
            .otherwise(pl.col("raw_mlb_workload"))
            .alias("mlb_workload")
        )
    )
    meaningful_role = (
        season_workload
        .filter(pl.col("mlb_workload") >= 200)
        .select("player_id").unique()
        .with_columns(
            pl.lit(1).cast(pl.Int64).alias("meaningful_role_within_horizon")
        )
    )
    high_workload = 400
    repeat_workload = 300 if player_type == "hitter" else 200
    established_role = (
        season_workload.group_by("player_id")
        .agg(
            pl.col("mlb_workload").max().alias("maximum_mlb_workload"),
            (pl.col("mlb_workload") >= repeat_workload)
            .sum().alias("repeat_workload_seasons"),
        )
        .filter(
            (pl.col("maximum_mlb_workload") >= high_workload)
            | (pl.col("repeat_workload_seasons") >= 2)
        )
        .select("player_id")
        .with_columns(
            pl.lit(1).cast(pl.Int64).alias("established_role_within_horizon")
        )
    )
    positive_component_role = _positive_component_roles(
        outcome_skill_stats if outcome_skill_stats is not None else skill_stats,
        snapshot_year=snapshot_year,
        horizon=horizon,
        player_type=player_type,
    )
    on_40man = membership.filter(pl.col("season") == snapshot_year).select(
        "player_id", "on_40man"
    )
    result = (
        players.join(prior_mlb, on="player_id", how="left")
        .join(official_debut, on="player_id", how="left", validate="m:1")
        .join(production, on="player_id", how="left")
        .join(development, on="player_id", how="left", validate="m:1")
        .join(on_40man, on="player_id", how="left")
        .join(future, on="player_id", how="left")
        .join(meaningful_role, on="player_id", how="left")
        .join(established_role, on="player_id", how="left")
        .join(positive_component_role, on="player_id", how="left")
        .with_columns(
            pl.col("prior_mlb").fill_null(False),
            pl.col("on_40man").fill_null(False),
            pl.col("arrived_within_horizon").fill_null(0),
            pl.col("meaningful_role_within_horizon").fill_null(0),
            pl.col("established_role_within_horizon").fill_null(0),
            pl.col("positive_component_role_within_horizon").fill_null(0),
            pl.col("as_of_level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("level_tier"),
        )
    )
    missing_future_debut = result.filter(
        (pl.col("arrived_within_horizon") == 1)
        & pl.col("mlb_debut_date").is_null()
    )
    if missing_future_debut.height:
        raise ValueError("future MLB arrivals lack official debut-date coverage")
    return (
        _fill_predictor_nulls(
            _join_pedigree(
                _join_demographics(result, demographics),
                draft_history,
                snapshot_year=snapshot_year,
            )
        )
        .filter(
            ~pl.col("prior_mlb")
            & (
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date").dt.year() > snapshot_year)
            )
            & (pl.col("level_tier") != "MLB")
            & pl.col("age_years").is_between(16.0, 30.0)
        )
        .select(
            "player_id", "age_years", "level_tier", "current_milb_workload",
            "primary_level_tier",
            "primary_level_workload_share",
            "level_progression", "seasons_since_affiliated_activity",
            "development_history_workload", "development_history_seasons",
            "prior_affiliated_workload", "prior_affiliated_seasons", "role_tier",
            *[f"production_rate_{index}" for index in range(1, 5)],
            "on_40man", "arrived_within_horizon", "meaningful_role_within_horizon",
            "established_role_within_horizon",
            "positive_component_role_within_horizon",
            "height_inches", "weight_pounds", "bat_side", "pitch_hand",
            "birth_country", "strike_zone_top", "strike_zone_bottom", "gender",
            "birth_city", "birth_state_province",
            "primary_position_code",
            "rule4_drafted", "draft_pick_quality", "signing_bonus_percentile",
            "signing_bonus_known", "high_school_draftee",
        )
        .sort("player_id")
    )


def build_current_arrival_predictors(
    snapshot: pl.DataFrame,
    current_stats: pl.DataFrame,
    current_control: pl.DataFrame,
    skill_stats: pl.DataFrame,
    *,
    player_type: str,
    demographics: pl.DataFrame | None = None,
    draft_history: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build current features for players with an official no-debut state."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    snapshot_year = int(current_stats.get_column("season").max())
    production = _production_features(
        skill_stats, current_stats, snapshot_year=snapshot_year, player_type=player_type
    )
    development = _affiliated_development_path(
        skill_stats, snapshot_year=snapshot_year, player_type=player_type
    )
    eligible = current_control.filter(pl.col("mlb_debut_date").is_null()).select(
        "player_id", "on_40man"
    )
    result = (
        snapshot.select("player_id", "age_years", "as_of_level_group")
        .join(eligible, on="player_id", how="inner", validate="1:1")
        .join(production, on="player_id", how="left", validate="1:1")
        .join(development, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("age_years").fill_null(24.0).clip(16.0, 30.0),
            pl.col("on_40man").fill_null(False),
            pl.col("as_of_level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("level_tier"),
        )
    )
    return (
        _fill_predictor_nulls(
            _join_pedigree(
                _join_demographics(result, demographics),
                draft_history,
                snapshot_year=snapshot_year,
            )
        )
        .select(
            "player_id", "age_years", "level_tier", "current_milb_workload",
            "primary_level_tier",
            "primary_level_workload_share",
            "level_progression", "seasons_since_affiliated_activity",
            "development_history_workload", "development_history_seasons",
            "prior_affiliated_workload", "prior_affiliated_seasons", "role_tier",
            *[f"production_rate_{index}" for index in range(1, 5)], "on_40man",
            "height_inches", "weight_pounds", "bat_side", "pitch_hand",
            "birth_country", "strike_zone_top", "strike_zone_bottom", "gender",
            "birth_city", "birth_state_province",
            "primary_position_code",
            "rule4_drafted", "draft_pick_quality", "signing_bonus_percentile",
            "signing_bonus_known", "high_school_draftee",
        )
        .sort("player_id")
    )


def arrival_design(
    frame: pl.DataFrame,
    *,
    feature_set: str = "core",
    production_priors: tuple[float, float, float, float] | None = None,
    production_regression: float = 0.0,
) -> np.ndarray:
    """Create the fixed low-dimensional, organization-free arrival design."""

    supported = {
        "core", "handedness", "origin", "stable_demographics",
        "stable_interactions", "physical", "handedness_physical",
        "all_demographics", "all_interactions", "development_interactions",
        "role_production_interactions", "baseball_interactions",
        "baseball_demographics",
        "draft_pedigree", "baseball_pedigree",
        "level_exposure", "development_path",
    }
    if feature_set not in supported:
        raise ValueError(f"unsupported arrival feature set: {feature_set}")
    if production_regression < 0:
        raise ValueError("production_regression cannot be negative")
    if production_regression > 0 and production_priors is None:
        raise ValueError("production priors are required when rates are regressed")
    priors = production_priors or (0.0, 0.0, 0.0, 0.0)
    if len(priors) != 4 or any(not 0.0 <= prior <= 1.0 for prior in priors):
        raise ValueError("production priors must contain four probabilities")
    rows = []
    for row in frame.iter_rows(named=True):
        level = hitter_level_tier(row["level_tier"])
        age_scaled = (float(row["age_years"]) - 23.0) / 5.0
        current_workload = float(row["current_milb_workload"])
        current_log = log(1.0 + current_workload) / log(601.0)
        prior_log = log(1.0 + float(row["prior_affiliated_workload"])) / log(1801.0)
        seasons_scaled = min(float(row["prior_affiliated_seasons"]), 6.0) / 6.0
        production_rates = [
            float(row[f"production_rate_{index}"]) for index in range(1, 5)
        ]
        if production_regression > 0:
            production_rates = [
                (current_workload * rate + production_regression * prior)
                / (current_workload + production_regression)
                for rate, prior in zip(production_rates, priors, strict=True)
            ]
        values = [
            age_scaled,
            current_log,
            prior_log,
            seasons_scaled,
            float(bool(row["on_40man"])),
        ]
        level_flags = [float(level == candidate) for candidate in LEVELS[:-1]]
        role_flags = [
            float(row["role_tier"] == candidate) for candidate in ROLES
        ]
        values.extend(level_flags)
        values.extend(role_flags)
        values.extend(production_rates)
        if feature_set in {"level_exposure", "development_path"}:
            primary_level = hitter_level_tier(row["primary_level_tier"])
            primary_flags = [
                float(primary_level == candidate) for candidate in LEVELS[:-1]
            ]
            primary_share = float(row["primary_level_workload_share"])
            values.extend(primary_flags)
            values.extend(
                [
                    primary_share,
                    float(primary_level != level),
                    *[age_scaled * flag for flag in primary_flags],
                ]
            )
        if feature_set == "development_path":
            values.extend(
                [
                    max(-1.0, min(1.0, float(row["level_progression"]) / 2.0)),
                    min(float(row["seasons_since_affiliated_activity"]), 3.0) / 3.0,
                    log(1.0 + float(row["development_history_workload"]))
                    / log(1801.0),
                    min(float(row["development_history_seasons"]), 6.0) / 6.0,
                ]
            )
        uses_development = feature_set in {
            "development_interactions", "baseball_interactions",
            "baseball_demographics", "baseball_pedigree",
        }
        uses_role_production = feature_set in {
            "role_production_interactions", "baseball_interactions",
            "baseball_demographics", "baseball_pedigree",
        }
        if uses_development:
            values.extend(age_scaled * flag for flag in level_flags)
            values.extend(
                [
                    age_scaled * current_log,
                    age_scaled * prior_log,
                    age_scaled * seasons_scaled,
                ]
            )
        if uses_role_production:
            values.extend(
                rate * flag for flag in role_flags for rate in production_rates
            )
        if feature_set in {"draft_pedigree", "baseball_pedigree"}:
            rule4 = float(bool(row["rule4_drafted"]))
            international = float(
                not bool(row["rule4_drafted"])
                and normalize_birth_country(row["birth_country"]) != "USA"
            )
            values.extend(
                [
                    rule4,
                    international,
                    float(row["draft_pick_quality"]),
                    float(bool(row["signing_bonus_known"])),
                    float(row["signing_bonus_percentile"]),
                    float(bool(row["high_school_draftee"])),
                    age_scaled * float(row["draft_pick_quality"]),
                ]
            )
        uses_hands = feature_set in {
            "handedness", "stable_demographics", "stable_interactions",
            "handedness_physical", "all_demographics", "all_interactions",
            "baseball_demographics",
        }
        uses_origin = feature_set in {
            "origin", "stable_demographics", "stable_interactions",
            "all_demographics", "all_interactions",
            "baseball_demographics",
        }
        uses_physical = feature_set in {
            "physical", "handedness_physical", "all_demographics", "all_interactions",
        }
        if uses_hands:
            values.extend(
                [
                    float(row["bat_side"] == "L"),
                    float(row["bat_side"] == "S"),
                    float(row["pitch_hand"] == "L"),
                    float(row["bat_side"] == row["pitch_hand"]),
                    float(row["gender"] != "M"),
                ]
            )
        if uses_origin:
            birth_country = normalize_birth_country(row["birth_country"])
            country_flags = [
                float(birth_country == country) for country in COUNTRIES
            ]
            values.extend(country_flags)
        if feature_set in {"stable_interactions", "baseball_demographics"}:
            values.extend(
                [
                    age_scaled * float(row["bat_side"] == "L"),
                    age_scaled * float(row["bat_side"] == "S"),
                    age_scaled * float(row["pitch_hand"] == "L"),
                ]
            )
            values.extend(age_scaled * flag for flag in country_flags)
        if uses_physical:
            height = float(row["height_inches"])
            weight = float(row["weight_pounds"])
            height_scaled = (height - 72.0) / 6.0
            weight_scaled = (weight - 190.0) / 40.0
            values.extend(
                [
                    height_scaled,
                    weight_scaled,
                    (weight / max(height * height, 1.0) - 0.0367) / 0.008,
                    (float(row["strike_zone_top"]) - 3.4) / 0.4,
                    (float(row["strike_zone_bottom"]) - 1.6) / 0.25,
                ]
            )
        if feature_set in {"handedness_physical", "all_interactions"}:
            values.extend(
                [
                    height_scaled * float(row["bat_side"] == "L"),
                    height_scaled * float(row["bat_side"] == "S"),
                    height_scaled * float(row["pitch_hand"] == "L"),
                    weight_scaled * float(row["pitch_hand"] == "L"),
                    age_scaled * height_scaled,
                    age_scaled * weight_scaled,
                ]
            )
        if feature_set in {"all_demographics", "all_interactions"}:
            values.extend(
                float(row["primary_position_code"] == code)
                for code in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "O", "Y")
            )
            for field in ("birth_city", "birth_state_province"):
                bucket = int.from_bytes(
                    sha256(str(row[field]).encode("utf-8")).digest()[:2], "big"
                ) % 16
                values.extend(float(bucket == candidate) for candidate in range(16))
        rows.append(values)
    return np.asarray(rows, dtype=float)


def fit_arrival_model(
    frame: pl.DataFrame,
    *,
    player_type: str,
    target_column: str = "arrived_within_horizon",
    outcome_name: str = "arrival",
    feature_set: str = "core",
    regularization_c: float = 1.0,
    production_regression: float = 0.0,
) -> ArrivalFit:
    if regularization_c <= 0:
        raise ValueError("regularization_c must be positive")
    if production_regression < 0:
        raise ValueError("production_regression cannot be negative")
    target = frame.get_column(target_column).to_numpy()
    if len(np.unique(target)) != 2:
        raise ValueError("arrival fitting requires both outcomes")
    workload = frame.get_column("current_milb_workload").to_numpy()
    total_workload = float(workload.sum())
    production_priors = tuple(
        float(
            np.dot(
                frame.get_column(f"production_rate_{index}").to_numpy(), workload
            )
            / total_workload
        )
        if total_workload > 0
        else 0.0
        for index in range(1, 5)
    )
    design = arrival_design(
        frame,
        feature_set=feature_set,
        production_priors=production_priors,
        production_regression=production_regression,
    )
    model = LogisticRegression(C=regularization_c, max_iter=2_000).fit(
        design, target
    )
    global_rate = float(target.mean())
    level_rates: dict[str, float] = {}
    for level in LEVELS:
        cell = frame.filter(pl.col("level_tier") == level)
        successes = float(cell.get_column(target_column).sum())
        level_rates[level] = (successes + 50.0 * global_rate) / (cell.height + 50.0)
    return ArrivalFit(
        player_type, outcome_name, target_column, feature_set,
        production_priors, production_regression,
        model, global_rate, level_rates,
    )


def predict_arrival(fit: ArrivalFit, frame: pl.DataFrame) -> pl.DataFrame:
    probability = fit.model.predict_proba(
        arrival_design(
            frame,
            feature_set=fit.feature_set,
            production_priors=fit.production_priors,
            production_regression=fit.production_regression,
        )
    )[:, 1]
    baseline = [
        fit.level_rates.get(hitter_level_tier(value), fit.global_rate)
        for value in frame.get_column("level_tier")
    ]
    return frame.with_columns(
        pl.Series(f"predicted_two_year_{fit.outcome_name}_probability", probability),
        pl.Series(f"baseline_two_year_{fit.outcome_name}_probability", baseline),
    )


def six_year_probability(two_year_probability: float) -> float:
    """Convert an observed two-year cumulative probability to three windows."""

    if not 0.0 <= two_year_probability <= 1.0:
        raise ValueError("arrival probability must be between zero and one")
    return 1.0 - (1.0 - two_year_probability) ** 3


def probability_metrics(
    scored: pl.DataFrame,
    column: str,
    *,
    observed_column: str = "arrived_within_horizon",
) -> dict[str, float]:
    observed = scored.get_column(observed_column).to_numpy().astype(float)
    predicted = np.clip(scored.get_column(column).to_numpy(), 1e-9, 1 - 1e-9)
    return {
        "brier": float(np.mean((predicted - observed) ** 2)),
        "log_loss": float(
            -np.mean(
                observed * np.log(predicted)
                + (1 - observed) * np.log(1 - predicted)
            )
        ),
        "observed_rate": float(observed.mean()),
        "predicted_rate": float(predicted.mean()),
    }
