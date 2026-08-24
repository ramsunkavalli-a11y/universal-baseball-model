from math import nan

import polars as pl
import pytest

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_WEIGHTS,
    ROLLING_ORIGIN_FOLDS,
    aggregate_target_players,
    build_forecast_population,
    move_probability_mass,
    probability_vector_to_woba,
    rolling_origin_slices,
    score_hitter_predictions,
    score_nested_component_log_loss,
    validate_probability_vector,
    woba_to_neutral_batting_runs_per_600,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


def _probabilities() -> dict[str, float]:
    values = {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
    values["OTHER_OUT"] = 1.0
    return values


def _fold_rows() -> pl.DataFrame:
    rows = []
    for season, player_id, league_id, level, pa in (
        (2021, 1, 103, "MLB", 10),
        (2021, 2, 110, "aaa", 20),
        (2022, 1, 103, "MLB", 30),
        (2022, 3, 111, "aa", 40),
        (2023, 4, 112, "a+", 50),
        (2024, 5, 113, "a", 60),
    ):
        row = {
            "season": season,
            "league_id": league_id,
            "player_id": player_id,
            "level_group": level,
            "hitter_talent_pa": pa,
            "modeling_eligible": True,
            **{outcome: 0 for outcome in HITTER_TALENT_OUTCOMES},
        }
        row["OTHER_OUT"] = pa
        rows.append(row)
    return pl.DataFrame(rows)


def test_probability_simplex_is_finite_nonnegative_and_normalized() -> None:
    valid = _probabilities()
    validate_probability_vector(valid)

    negative = dict(valid)
    negative["OTHER_OUT"] = 1.1
    negative["K"] = -0.1
    with pytest.raises(ValueError, match="nonnegative"):
        validate_probability_vector(negative)

    nonfinite = dict(valid)
    nonfinite["OTHER_OUT"] = nan
    with pytest.raises(ValueError, match="finite"):
        validate_probability_vector(nonfinite)

    incomplete = dict(valid)
    incomplete["OTHER_OUT"] = 0.9
    with pytest.raises(ValueError, match="sum to one"):
        validate_probability_vector(incomplete)


def test_coherent_hit_mass_moves_increase_value_in_strict_order() -> None:
    baseline = _probabilities()
    values = []
    for outcome in ("1B", "2B", "3B", "HR"):
        moved = move_probability_mass(
            baseline,
            source="OTHER_OUT",
            destination=outcome,
            mass=0.1,
        )
        values.append(probability_vector_to_woba(moved))

    assert 0.0 < values[0] < values[1] < values[2] < values[3]
    assert (
        NEUTRAL_WOBA_WEIGHTS["1B"]
        < NEUTRAL_WOBA_WEIGHTS["2B"]
        < NEUTRAL_WOBA_WEIGHTS["3B"]
        < NEUTRAL_WOBA_WEIGHTS["HR"]
    )


def test_increasing_hr_on_the_simplex_increases_value_and_runs() -> None:
    baseline = _probabilities()
    improved = move_probability_mass(
        baseline,
        source="OTHER_OUT",
        destination="HR",
        mass=0.05,
    )
    baseline_woba = probability_vector_to_woba(baseline)
    improved_woba = probability_vector_to_woba(improved)
    assert improved_woba > baseline_woba
    assert woba_to_neutral_batting_runs_per_600(improved_woba) > (
        woba_to_neutral_batting_runs_per_600(baseline_woba)
    )


def test_target_membership_and_outcomes_cannot_change_training_slice() -> None:
    source = _fold_rows()
    fold = ROLLING_ORIGIN_FOLDS[0]
    training, target = rolling_origin_slices(source, fold)
    altered_target = target.with_columns(pl.lit(999).alias("OTHER_OUT"))
    altered = pl.concat(
        [source.filter(pl.col("season") != fold.target_season), altered_target],
        how="vertical_relaxed",
    )
    altered_training, _ = rolling_origin_slices(altered, fold)

    assert training.equals(altered_training)
    assert build_forecast_population(training).equals(
        build_forecast_population(altered_training)
    )


def test_target_player_aggregation_is_exhaustive_and_primary_level_is_stable() -> None:
    target = _fold_rows().filter(pl.col("season") == 2022)
    extra = target.filter(pl.col("player_id") == 1).with_columns(
        pl.lit(104).alias("league_id"),
        pl.lit("MLB").alias("level_group"),
        pl.lit(5).alias("hitter_talent_pa"),
        pl.lit(5).alias("OTHER_OUT"),
    )
    players = aggregate_target_players(
        pl.concat([target, extra], how="vertical_relaxed")
    )

    assert players.height == 2
    player = players.filter(pl.col("player_id") == 1).row(0, named=True)
    assert player["hitter_talent_pa"] == 35
    assert player["OTHER_OUT"] == 35
    assert player["primary_target_league_id"] == 103


def _scoring_targets() -> pl.DataFrame:
    rows = []
    for player_id, pa, terminal in ((1, 100, "HR"), (2, 10, "OTHER_OUT")):
        rows.append(
            {
                "player_id": player_id,
                "hitter_talent_pa": pa,
                **{
                    outcome: (pa if outcome == terminal else 0)
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows)


def test_perfect_prediction_improves_proper_scores_and_rate_errors() -> None:
    targets = _scoring_targets()
    perfect = targets.select("player_id").with_columns(
        *[
            pl.when(pl.col("player_id") == 1)
            .then(pl.lit(1.0 if outcome == "HR" else 0.0))
            .otherwise(pl.lit(1.0 if outcome == "OTHER_OUT" else 0.0))
            .alias(f"p_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    uniform = targets.select("player_id").with_columns(
        *[
            pl.lit(1.0 / len(HITTER_TALENT_OUTCOMES)).alias(f"p_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    perfect_score = score_hitter_predictions(perfect, targets, weighting="pa")
    uniform_score = score_hitter_predictions(uniform, targets, weighting="pa")
    assert perfect_score["terminal_log_loss"] < uniform_score["terminal_log_loss"]
    assert perfect_score["terminal_brier_score"] < uniform_score["terminal_brier_score"]
    assert perfect_score["woba_rmse"] == pytest.approx(0.0)
    assert perfect_score["runs_per_600_rmse"] == pytest.approx(0.0)


def test_player_and_pa_weighting_are_distinct() -> None:
    targets = _scoring_targets()
    predictions = targets.select("player_id").with_columns(
        *[
            pl.lit(1.0 / len(HITTER_TALENT_OUTCOMES)).alias(f"p_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    player_score = score_hitter_predictions(
        predictions, targets, weighting="player"
    )
    pa_score = score_hitter_predictions(predictions, targets, weighting="pa")
    assert player_score["players"] == pa_score["players"] == 2
    assert player_score["woba_rmse"] != pa_score["woba_rmse"]


def test_nested_component_scorer_uses_only_conditional_parent_events() -> None:
    targets = _scoring_targets()
    perfect = targets.select("player_id").with_columns(
        *[
            pl.when(pl.col("player_id") == 1)
            .then(pl.lit(1.0 if outcome == "HR" else 0.0))
            .otherwise(pl.lit(1.0 if outcome == "OTHER_OUT" else 0.0))
            .alias(f"p_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    result = score_nested_component_log_loss(
        perfect, targets, component="contact"
    )
    assert result["events"] == 110
    assert result["event_log_loss"] == pytest.approx(0.0)
