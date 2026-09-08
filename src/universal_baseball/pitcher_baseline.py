"""Transparent Marcel-class pitcher component baseline.

The baseline uses three prior seasons with 3/2/1 recency weights, regresses
component rates to a role-appropriate population mean, and reports reliability.
It forecasts rate skill only. Future participation and workload are separate.
"""

from __future__ import annotations

from math import log

import polars as pl


PITCHER_BASELINE_METHOD = "pitcher_components_321_role_regressed_v1"
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")
PITCHER_RATE_COLUMNS = tuple(f"predicted_{component}_rate" for component in PITCHER_COMPONENTS)
PITCHER_HISTORY_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    "pitching_games": pl.Int64,
    "pitching_starts": pl.Int64,
    "pitching_bf": pl.Int64,
    "pitching_so": pl.Int64,
    "pitching_ubb": pl.Int64,
    "pitching_hbp": pl.Int64,
    "pitching_hr": pl.Int64,
}


def _validate_history(history: pl.DataFrame, *, forecast_season: int) -> pl.DataFrame:
    missing = sorted(set(PITCHER_HISTORY_SCHEMA) - set(history.columns))
    extra = sorted(set(history.columns) - set(PITCHER_HISTORY_SCHEMA))
    if missing:
        raise ValueError(f"pitcher history missing columns: {missing}")
    if extra:
        raise ValueError(f"pitcher history has undeclared columns: {extra}")
    result = history.select(list(PITCHER_HISTORY_SCHEMA)).cast(
        PITCHER_HISTORY_SCHEMA,
        strict=True,
    )
    if result.filter(pl.col("season") >= forecast_season).height:
        raise ValueError("pitcher history crosses forecast cutoff")
    counts = [column for column in PITCHER_HISTORY_SCHEMA if column.startswith("pitching_")]
    if result.filter(
        pl.col("player_id").is_null()
        | (pl.col("player_id") <= 0)
        | pl.any_horizontal([pl.col(column).is_null() | (pl.col(column) < 0) for column in counts])
    ).height:
        raise ValueError("pitcher history has invalid identities or counts")
    if result.group_by(["season", "player_id"]).len().filter(pl.col("len") > 1).height:
        raise ValueError("pitcher history violates player-season grain")
    if result.filter(
        (pl.col("pitching_starts") > pl.col("pitching_games"))
        | (pl.col("pitching_so") + pl.col("pitching_ubb")
           + pl.col("pitching_hbp") + pl.col("pitching_hr")
           > pl.col("pitching_bf"))
        | ((pl.col("pitching_bf") > 0) & (pl.col("pitching_games") == 0))
    ).height:
        raise ValueError("pitcher history violates component relationships")
    return result


def _validate_players(players: pl.DataFrame) -> pl.DataFrame:
    if set(players.columns) != {"player_id"}:
        raise ValueError("pitcher forecast denominator must contain only player_id")
    result = players.select(pl.col("player_id").cast(pl.Int64, strict=True))
    if result.filter(pl.col("player_id").is_null() | (pl.col("player_id") <= 0)).height:
        raise ValueError("pitcher forecast denominator has invalid player_id")
    if result.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("pitcher forecast denominator has duplicate player_id")
    return result.sort("player_id")


def build_pitcher_component_baseline(
    players: pl.DataFrame,
    history: pl.DataFrame,
    *,
    forecast_season: int,
    regression_bf: float = 200.0,
    role_regression_games: float = 20.0,
) -> pl.DataFrame:
    """Forecast pitcher BF-component rates for every required player.

    `regression_bf` and `role_regression_games` are explicit baseline constants,
    not tuned results. Players with no usable history receive the global prior
    and zero reliability rather than being omitted.
    """

    if regression_bf <= 0 or role_regression_games <= 0:
        raise ValueError("pitcher regression strengths must be positive")
    denominator = _validate_players(players)
    source = _validate_history(history, forecast_season=forecast_season).filter(
        pl.col("season").is_between(forecast_season - 3, forecast_season - 1)
    )
    positive = source.filter(pl.col("pitching_bf") > 0).with_columns(
        (forecast_season - pl.col("season")).replace_strict(
            {1: 3.0, 2: 2.0, 3: 1.0},
            return_dtype=pl.Float64,
        ).alias("recency_weight"),
        (pl.col("pitching_starts") / pl.col("pitching_games"))
        .fill_nan(0.0)
        .alias("starter_share"),
    ).with_columns(
        pl.when(pl.col("starter_share") >= 0.5)
        .then(pl.lit("starter"))
        .otherwise(pl.lit("reliever"))
        .alias("observed_role"),
        (
            pl.col("pitching_bf")
            - pl.col("pitching_so")
            - pl.col("pitching_ubb")
            - pl.col("pitching_hbp")
            - pl.col("pitching_hr")
        ).alias("pitching_other"),
    )
    if positive.is_empty():
        raise ValueError("pitcher baseline requires positive-BF population history")

    count_columns = {
        "so": "pitching_so",
        "ubb": "pitching_ubb",
        "hbp": "pitching_hbp",
        "hr": "pitching_hr",
        "other": "pitching_other",
    }
    global_bf = float(positive.get_column("pitching_bf").sum())
    global_rates = {
        component: float(positive.get_column(column).sum()) / global_bf
        for component, column in count_columns.items()
    }
    global_starter_share = float(positive.get_column("pitching_starts").sum()) / float(
        positive.get_column("pitching_games").sum()
    )

    role_priors: dict[str, dict[str, float]] = {}
    for key, group in positive.group_by("observed_role"):
        role = str(key[0])
        bf = float(group.get_column("pitching_bf").sum())
        role_priors[role] = {
            component: float(group.get_column(column).sum()) / bf
            for component, column in count_columns.items()
        }

    weighted = positive.group_by("player_id").agg(
        (pl.col("pitching_bf") * pl.col("recency_weight")).sum().alias("weighted_bf"),
        (pl.col("pitching_games") * pl.col("recency_weight")).sum().alias("weighted_games"),
        (pl.col("pitching_starts") * pl.col("recency_weight")).sum().alias("weighted_starts"),
        *(
            (pl.col(column) * pl.col("recency_weight")).sum().alias(f"weighted_{component}")
            for component, column in count_columns.items()
        ),
        pl.col("season").max().alias("most_recent_history_season"),
    )
    joined = denominator.join(weighted, on="player_id", how="left")
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        weighted_games = float(row["weighted_games"] or 0.0)
        weighted_starts = float(row["weighted_starts"] or 0.0)
        starter_share = (
            weighted_starts + role_regression_games * global_starter_share
        ) / (weighted_games + role_regression_games)
        role = "starter" if starter_share >= 0.5 else "reliever"
        prior = role_priors.get(role, global_rates)
        weighted_bf = float(row["weighted_bf"] or 0.0)
        rates = {
            component: (
                float(row[f"weighted_{component}"] or 0.0)
                + regression_bf * prior[component]
            )
            / (weighted_bf + regression_bf)
            for component in PITCHER_COMPONENTS
        }
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "forecast_season": int(forecast_season),
                "predicted_role": role,
                "predicted_starter_share": starter_share,
                "weighted_history_bf": weighted_bf,
                "reliability": weighted_bf / (weighted_bf + regression_bf),
                "most_recent_history_season": row["most_recent_history_season"],
                **{
                    f"predicted_{component}_rate": rates[component]
                    for component in PITCHER_COMPONENTS
                },
                "pitcher_baseline_method": PITCHER_BASELINE_METHOD,
            }
        )
    result = pl.DataFrame(rows).sort("player_id")
    rate_sum = sum((pl.col(column) for column in PITCHER_RATE_COLUMNS), start=pl.lit(0.0))
    if result.filter((rate_sum - 1.0).abs() > 1e-12).height:
        raise RuntimeError("pitcher baseline component probabilities do not sum to one")
    if result.filter(
        (pl.col("reliability") < 0)
        | (pl.col("reliability") >= 1)
        | (pl.col("predicted_starter_share") < 0)
        | (pl.col("predicted_starter_share") > 1)
    ).height:
        raise RuntimeError("pitcher baseline produced invalid reliability or role share")
    return result


def score_pitcher_component_rates(
    predictions: pl.DataFrame,
    targets: pl.DataFrame,
) -> dict[str, object]:
    """Score BF-weighted component log loss and calibration on positive BF.

    The target population is a scoring choice only. Target membership and target
    role never enter `build_pitcher_component_baseline`.
    """

    required_predictions = {"player_id", *PITCHER_RATE_COLUMNS}
    if missing := sorted(required_predictions - set(predictions.columns)):
        raise ValueError(f"pitcher predictions missing scoring fields: {missing}")
    if predictions.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("pitcher predictions violate player_id grain")
    target = _validate_history(targets, forecast_season=int(targets["season"].max()) + 1)
    if target.get_column("season").n_unique() != 1:
        raise ValueError("pitcher rate scoring requires exactly one target season")
    target = target.filter(pl.col("pitching_bf") > 0)
    prediction_ids = set(predictions.get_column("player_id").to_list())
    target_ids = set(target.get_column("player_id").to_list())
    if prediction_ids != target_ids:
        raise ValueError("pitcher prediction and target coverage differs")
    joined = predictions.join(target, on="player_id", how="inner", validate="1:1")
    component_columns = {
        "so": "pitching_so",
        "ubb": "pitching_ubb",
        "hbp": "pitching_hbp",
        "hr": "pitching_hr",
    }
    target_other = (
        pl.col("pitching_bf")
        - sum((pl.col(column) for column in component_columns.values()), start=pl.lit(0))
    ).alias("pitching_other")
    joined = joined.with_columns(target_other)
    target_columns = {**component_columns, "other": "pitching_other"}
    nll = 0.0
    total_bf = int(joined.get_column("pitching_bf").sum())
    calibration: dict[str, dict[str, float]] = {}
    for component, target_column in target_columns.items():
        predicted_rate = f"predicted_{component}_rate"
        predicted_count = float(
            joined.select((pl.col(predicted_rate) * pl.col("pitching_bf")).sum()).item()
        )
        observed_count = int(joined.get_column(target_column).sum())
        calibration[component] = {
            "observed_rate": observed_count / total_bf,
            "predicted_rate": predicted_count / total_bf,
            "rate_bias": (predicted_count - observed_count) / total_bf,
        }
        for count, probability in joined.select(target_column, predicted_rate).iter_rows():
            if probability <= 0.0 or probability > 1.0:
                raise ValueError("pitcher prediction contains invalid component probability")
            nll -= int(count) * log(float(probability))
    return {
        "players": joined.height,
        "batters_faced": total_bf,
        "bf_weighted_component_log_loss": nll / total_bf,
        "calibration": calibration,
    }
