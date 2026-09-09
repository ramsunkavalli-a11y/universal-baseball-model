"""Chronology-safe cumulative MLB-arrival model for pre-MLB players."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import log

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.hitter_opportunity_paths import hitter_level_tier


ARRIVAL_MODEL_ID = "phase2_pre_mlb_two_year_arrival_v1"
LEVELS = ("A_OR_BELOW", "AA", "AAA", "INACTIVE", "UNKNOWN")
ROLES = ("C", "MIDDLE_INFIELD", "OUTFIELD", "CORNER", "STARTER", "SWINGMAN")
COUNTRIES = (
    "USA", "Dominican Republic", "Venezuela", "Mexico", "Cuba",
    "Puerto Rico", "Canada", "Colombia", "Panama", "Nicaragua",
    "Brazil", "Australia", "Japan", "South Korea", "Taiwan",
)


@dataclass(frozen=True, slots=True)
class ArrivalFit:
    player_type: str
    outcome_name: str
    target_column: str
    feature_set: str
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
        position = (
            basic_stats.filter(
                (pl.col("season") == snapshot_year)
                & (pl.col("stat_group") == "hitting")
                & (pl.col("sport_id") != 1)
            )
            .group_by("player_id")
            .agg(pl.col("position_code").drop_nulls().mode().first().alias("position"))
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
    return (
        current.with_columns(*rates)
        .join(playing_history, on="player_id", how="left")
        .select(
            "player_id",
            "current_milb_workload",
            "prior_affiliated_workload",
            "prior_affiliated_seasons",
            "role_tier",
            *[f"production_rate_{index}" for index in range(1, 5)],
        )
    )


def _fill_predictor_nulls(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("current_milb_workload").fill_null(0.0),
        pl.col("prior_affiliated_workload").fill_null(0.0),
        pl.col("prior_affiliated_seasons").fill_null(0.0),
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


def build_arrival_cohort(
    snapshots: pl.DataFrame,
    stats: pl.DataFrame,
    membership: pl.DataFrame,
    skill_stats: pl.DataFrame,
    *,
    snapshot_year: int,
    horizon: int,
    player_type: str,
    demographics: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build a pre-MLB cohort and observed cumulative debut outcome."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    if horizon < 1:
        raise ValueError("arrival horizon must be positive")
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
    production = _production_features(
        skill_stats, stats, snapshot_year=snapshot_year, player_type=player_type
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
    meaningful_role = (
        future_stats.group_by("player_id", "season")
        .agg(pl.col(workload).sum().alias("mlb_workload"))
        .filter(pl.col("mlb_workload") >= 200)
        .select("player_id").unique()
        .with_columns(
            pl.lit(1).cast(pl.Int64).alias("meaningful_role_within_horizon")
        )
    )
    on_40man = membership.filter(pl.col("season") == snapshot_year).select(
        "player_id", "on_40man"
    )
    result = (
        players.join(prior_mlb, on="player_id", how="left")
        .join(production, on="player_id", how="left")
        .join(on_40man, on="player_id", how="left")
        .join(future, on="player_id", how="left")
        .join(meaningful_role, on="player_id", how="left")
        .with_columns(
            pl.col("prior_mlb").fill_null(False),
            pl.col("on_40man").fill_null(False),
            pl.col("arrived_within_horizon").fill_null(0),
            pl.col("meaningful_role_within_horizon").fill_null(0),
            pl.col("as_of_level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("level_tier"),
        )
    )
    return (
        _fill_predictor_nulls(_join_demographics(result, demographics))
        .filter(
            ~pl.col("prior_mlb")
            & (pl.col("level_tier") != "MLB")
            & pl.col("age_years").is_between(16.0, 30.0)
        )
        .select(
            "player_id", "age_years", "level_tier", "current_milb_workload",
            "prior_affiliated_workload", "prior_affiliated_seasons", "role_tier",
            *[f"production_rate_{index}" for index in range(1, 5)],
            "on_40man", "arrived_within_horizon", "meaningful_role_within_horizon",
            "height_inches", "weight_pounds", "bat_side", "pitch_hand",
            "birth_country", "strike_zone_top", "strike_zone_bottom", "gender",
            "birth_city", "birth_state_province",
            "primary_position_code",
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
) -> pl.DataFrame:
    """Build current features for players with an official no-debut state."""

    if player_type not in {"hitter", "pitcher"}:
        raise ValueError("player_type must be hitter or pitcher")
    snapshot_year = int(current_stats.get_column("season").max())
    production = _production_features(
        skill_stats, current_stats, snapshot_year=snapshot_year, player_type=player_type
    )
    eligible = current_control.filter(pl.col("mlb_debut_date").is_null()).select(
        "player_id", "on_40man"
    )
    result = (
        snapshot.select("player_id", "age_years", "as_of_level_group")
        .join(eligible, on="player_id", how="inner", validate="1:1")
        .join(production, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("age_years").fill_null(24.0).clip(16.0, 30.0),
            pl.col("on_40man").fill_null(False),
            pl.col("as_of_level_group").map_elements(
                hitter_level_tier, return_dtype=pl.String
            ).alias("level_tier"),
        )
    )
    return (
        _fill_predictor_nulls(_join_demographics(result, demographics))
        .select(
            "player_id", "age_years", "level_tier", "current_milb_workload",
            "prior_affiliated_workload", "prior_affiliated_seasons", "role_tier",
            *[f"production_rate_{index}" for index in range(1, 5)], "on_40man",
            "height_inches", "weight_pounds", "bat_side", "pitch_hand",
            "birth_country", "strike_zone_top", "strike_zone_bottom", "gender",
            "birth_city", "birth_state_province",
            "primary_position_code",
        )
        .sort("player_id")
    )


def arrival_design(frame: pl.DataFrame, *, feature_set: str = "core") -> np.ndarray:
    """Create the fixed low-dimensional, organization-free arrival design."""

    supported = {
        "core", "handedness", "origin", "stable_demographics",
        "stable_interactions", "physical", "handedness_physical",
        "all_demographics", "all_interactions",
    }
    if feature_set not in supported:
        raise ValueError(f"unsupported arrival feature set: {feature_set}")
    rows = []
    for row in frame.iter_rows(named=True):
        level = hitter_level_tier(row["level_tier"])
        age_scaled = (float(row["age_years"]) - 23.0) / 5.0
        values = [
            age_scaled,
            log(1.0 + float(row["current_milb_workload"])) / log(601.0),
            log(1.0 + float(row["prior_affiliated_workload"])) / log(1801.0),
            min(float(row["prior_affiliated_seasons"]), 6.0) / 6.0,
            float(bool(row["on_40man"])),
        ]
        values.extend(float(level == candidate) for candidate in LEVELS[:-1])
        values.extend(float(row["role_tier"] == candidate) for candidate in ROLES)
        values.extend(float(row[f"production_rate_{index}"]) for index in range(1, 5))
        uses_hands = feature_set in {
            "handedness", "stable_demographics", "stable_interactions",
            "handedness_physical", "all_demographics", "all_interactions",
        }
        uses_origin = feature_set in {
            "origin", "stable_demographics", "stable_interactions",
            "all_demographics", "all_interactions",
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
            country_flags = [
                float(row["birth_country"] == country) for country in COUNTRIES
            ]
            values.extend(country_flags)
        if feature_set == "stable_interactions":
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
) -> ArrivalFit:
    target = frame.get_column(target_column).to_numpy()
    if len(np.unique(target)) != 2:
        raise ValueError("arrival fitting requires both outcomes")
    model = LogisticRegression(C=1.0, max_iter=2_000).fit(
        arrival_design(frame, feature_set=feature_set), target
    )
    global_rate = float(target.mean())
    level_rates: dict[str, float] = {}
    for level in LEVELS:
        cell = frame.filter(pl.col("level_tier") == level)
        successes = float(cell.get_column(target_column).sum())
        level_rates[level] = (successes + 50.0 * global_rate) / (cell.height + 50.0)
    return ArrivalFit(
        player_type, outcome_name, target_column, feature_set,
        model, global_rate, level_rates,
    )


def predict_arrival(fit: ArrivalFit, frame: pl.DataFrame) -> pl.DataFrame:
    probability = fit.model.predict_proba(
        arrival_design(frame, feature_set=fit.feature_set)
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
