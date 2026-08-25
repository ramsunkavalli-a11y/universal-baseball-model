from datetime import date

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2d import (
    apply_j0_context_increment,
    attach_binary_node_observation,
    build_prior_pitcher_binary_feature,
    build_prior_pitcher_hit_composition_features,
    fit_matched_binary_context_models,
    fit_matched_hit_composition_context_models,
)


def _events() -> pl.DataFrame:
    outcomes = ["K", "OTHER_OUT", "K", "OTHER_OUT", "K"]
    return pl.DataFrame(
        {
            "season": [2021] * 5,
            "game_date": [
                date(2021, 4, 1),
                date(2021, 4, 1),
                date(2021, 4, 2),
                date(2021, 4, 2),
                date(2021, 4, 3),
            ],
            "game_pk": [1, 1, 2, 2, 3],
            "at_bat_index": [0, 1, 0, 1, 0],
            "league_id": [100] * 5,
            "level_group": ["AA"] * 5,
            "pitcher_id": [10, 10, 10, 20, 10],
            "canonical_outcome": outcomes,
            "context_label_ready": [True] * 5,
        }
    )


def _base() -> dict[str, float]:
    return {
        "K": 0.25,
        "UBB": 0.10,
        "HBP": 0.01,
        "HR": 0.04,
        "3B": 0.01,
        "2B": 0.05,
        "1B": 0.16,
        "ROE": 0.02,
        "FC_REACH": 0.01,
        "SF": 0.02,
        "MULTI_OUT": 0.02,
        "OTHER_OUT": 0.31,
    }


def test_node_observations_follow_frozen_denominators() -> None:
    frame = pl.DataFrame(
        {
            "canonical_outcome": ["K", "UBB", "HBP", "HR", "IBB"],
            "context_label_ready": [True] * 5,
        }
    )
    k = attach_binary_node_observation(frame, "K")
    hbp = attach_binary_node_observation(frame, "HBP")
    assert k["K_response"].to_list() == [1, 0, 0, 0, None]
    assert hbp["HBP_response"].to_list() == [None, None, 1, 0, None]


def test_prior_pitcher_feature_excludes_entire_current_date() -> None:
    feature = build_prior_pitcher_binary_feature(_events(), "K").sort(
        ["game_date", "game_pk", "at_bat_index"]
    )
    day_one = feature.filter(pl.col("game_date") == date(2021, 4, 1))
    day_two_pitcher_10 = feature.filter(
        (pl.col("game_date") == date(2021, 4, 2)) & (pl.col("pitcher_id") == 10)
    )
    day_three = feature.filter(pl.col("game_date") == date(2021, 4, 3))
    assert day_one["K_prior_pitcher_denominator"].to_list() == [0.0, 0.0]
    assert day_one["K_prior_pitcher_log_odds_residual"].to_list() == [0.0, 0.0]
    assert day_two_pitcher_10["K_prior_pitcher_denominator"].item() == 2.0
    assert day_three["K_prior_pitcher_denominator"].item() == 3.0


def test_same_date_and_future_events_cannot_change_prior_feature() -> None:
    before = build_prior_pitcher_binary_feature(_events(), "K").filter(
        pl.col("game_pk") == 2
    )
    additions = pl.DataFrame(
        {
            "season": [2021, 2021],
            "game_date": [date(2021, 4, 2), date(2021, 5, 1)],
            "game_pk": [200, 201],
            "at_bat_index": [0, 0],
            "league_id": [100, 100],
            "level_group": ["AA", "AA"],
            "pitcher_id": [10, 10],
            "canonical_outcome": ["K", "K"],
            "context_label_ready": [True, True],
        }
    )
    after = build_prior_pitcher_binary_feature(
        pl.concat([_events(), additions]), "K"
    ).filter(pl.col("game_pk") == 2)
    columns = [
        "K_prior_pitcher_numerator",
        "K_prior_pitcher_denominator",
        "K_prior_context_numerator",
        "K_prior_context_denominator",
        "K_prior_pitcher_log_odds_residual",
    ]
    assert before.select(columns).equals(after.select(columns))


def test_missing_and_zero_context_increment_are_exact_base_fallbacks() -> None:
    base = _base()
    assert apply_j0_context_increment(base, None) == base
    assert apply_j0_context_increment(base, {}) == base
    assert apply_j0_context_increment(
        base,
        {
            "K": 0.0,
            "UBB": 0.0,
            "HBP": 0.0,
            "HR": 0.0,
            "NON_HR_REACH": 0.0,
            "HIT_2B": 0.0,
            "HIT_3B": 0.0,
        },
    ) == base


def test_node_increment_changes_only_its_nested_branch() -> None:
    base = _base()
    adjusted = apply_j0_context_increment(base, {"HR": 0.5})
    assert adjusted["K"] == pytest.approx(base["K"], abs=1e-12)
    assert adjusted["UBB"] == pytest.approx(base["UBB"], abs=1e-12)
    assert adjusted["HBP"] == pytest.approx(base["HBP"], abs=1e-12)
    assert adjusted["HR"] > base["HR"]
    assert sum(adjusted.values()) == pytest.approx(1.0, abs=1e-12)
    base_hit_mix = [base[outcome] / sum(base[x] for x in ("1B", "2B", "3B")) for outcome in ("1B", "2B", "3B")]
    adjusted_hit_mix = [adjusted[outcome] / sum(adjusted[x] for x in ("1B", "2B", "3B")) for outcome in ("1B", "2B", "3B")]
    assert adjusted_hit_mix == pytest.approx(base_hit_mix, abs=1e-12)


def test_hit_composition_increment_preserves_upstream_probability() -> None:
    base = _base()
    adjusted = apply_j0_context_increment(base, {"HIT_2B": 0.3, "HIT_3B": -0.2})
    assert sum(adjusted[x] for x in ("1B", "2B", "3B")) == pytest.approx(
        sum(base[x] for x in ("1B", "2B", "3B")), abs=1e-12
    )
    for outcome in set(HITTER_TALENT_OUTCOMES) - {"1B", "2B", "3B"}:
        assert adjusted[outcome] == pytest.approx(base[outcome], abs=1e-12)


def test_hit_composition_pitcher_feature_is_prior_only_and_zero_at_boundary() -> None:
    events = _events().with_columns(
        pl.Series("canonical_outcome", ["1B", "2B", "3B", "1B", "2B"])
    )
    feature = build_prior_pitcher_hit_composition_features(events)
    first = feature.filter(pl.col("game_date") == date(2021, 4, 1))
    later = feature.filter(pl.col("game_date") == date(2021, 4, 3))
    assert first["HIT_COMPOSITION_prior_pitcher_denominator"].to_list() == [0.0, 0.0]
    assert first["HIT_COMPOSITION_prior_pitcher_alr_residual_2B"].to_list() == [0.0, 0.0]
    assert later["HIT_COMPOSITION_prior_pitcher_denominator"].item() == 3.0

    future = events.with_columns(
        pl.when(pl.col("game_pk") == 3)
        .then(pl.date(2022, 4, 3))
        .otherwise(pl.col("game_date"))
        .alias("game_date"),
        pl.when(pl.col("game_pk") == 3)
        .then(pl.lit(2022))
        .otherwise(pl.col("season"))
        .alias("season"),
    )
    before = build_prior_pitcher_hit_composition_features(events).filter(
        pl.col("game_pk") == 2
    )
    after = build_prior_pitcher_hit_composition_features(future).filter(
        pl.col("game_pk") == 2
    )
    columns = [
        "HIT_COMPOSITION_prior_pitcher_denominator",
        "HIT_COMPOSITION_prior_pitcher_1B",
        "HIT_COMPOSITION_prior_pitcher_2B",
        "HIT_COMPOSITION_prior_pitcher_3B",
    ]
    assert before.select(columns).equals(after.select(columns))


def test_matched_contextual_fit_uses_identical_rows_and_fixed_penalties() -> None:
    rng = np.random.default_rng(20260824)
    rows = []
    player_effect = np.asarray([-0.5, -0.3, -0.1, 0.0, 0.1, 0.2, 0.35, 0.5])
    platoon_effect = {"L_vs_L": 0.15, "L_vs_R": -0.05, "R_vs_L": 0.08, "R_vs_R": -0.02}
    cells = list(platoon_effect)
    for index in range(1600):
        player = index % len(player_effect)
        cell = cells[index % len(cells)]
        pitcher = float(rng.normal(0.0, 0.2))
        logit = -1.0 + player_effect[player] + platoon_effect[cell] + 0.8 * pitcher
        response = int(rng.random() < 1.0 / (1.0 + np.exp(-logit)))
        rows.append(
            {
                "player_id": player,
                "season": 2022 + (index % 2),
                "league_id": 100 + (index % 2),
                "level_group": "AA",
                "platoon_cell": cell,
                "K_eligible": True,
                "K_response": response,
                "K_prior_pitcher_log_odds_residual": pitcher,
            }
        )
    fit = fit_matched_binary_context_models(
        pl.DataFrame(rows),
        "K",
        max_iterations=500,
        tolerance=1e-7,
        variance_max_iterations=50,
        variance_tolerance=0.01,
    )
    assert fit.metrics["identical_event_rows"] is True
    assert fit.metrics["event_count"] == 1600
    assert fit.context_increments.height == len(player_effect)
    pitcher = fit.fixed_effects.filter(
        pl.col("effect_type") == "pitcher_coefficient"
    )["contextual_value"].item()
    assert 0.0 <= pitcher <= 1.5
    assert fit.metrics["batter_variance_method"] == (
        "deterministic_laplace_em_marginal_likelihood"
    )


def test_matched_hit_composition_fit_preserves_one_cohort() -> None:
    rng = np.random.default_rng(20260825)
    rows = []
    cells = ["L_vs_L", "L_vs_R", "R_vs_L", "R_vs_R"]
    outcomes = np.asarray(["1B", "2B", "3B"])
    for index in range(1800):
        player = index % 9
        residual_2b = float(rng.normal(0.0, 0.2))
        residual_3b = float(rng.normal(0.0, 0.2))
        logits = np.asarray(
            [0.0, -1.0 + 0.7 * residual_2b, -2.5 + 0.9 * residual_3b]
        )
        probability = np.exp(logits - logits.max())
        probability /= probability.sum()
        outcome = str(rng.choice(outcomes, p=probability))
        rows.append(
            {
                "player_id": player,
                "season": 2022 + (index % 2),
                "league_id": 100 + (index % 2),
                "level_group": "AA",
                "platoon_cell": cells[index % 4],
                "HIT_COMPOSITION_eligible": True,
                "HIT_COMPOSITION_response": outcome,
                "HIT_COMPOSITION_prior_pitcher_alr_residual_2B": residual_2b,
                "HIT_COMPOSITION_prior_pitcher_alr_residual_3B": residual_3b,
            }
        )
    fit = fit_matched_hit_composition_context_models(
        pl.DataFrame(rows),
        max_iterations=500,
        tolerance=1e-7,
        variance_max_iterations=50,
        variance_tolerance=0.01,
    )
    assert fit.metrics["identical_event_rows"] is True
    assert fit.metrics["event_count"] == 1800
    assert fit.context_increments.height == 9
    coefficients = fit.fixed_effects.filter(
        pl.col("effect_type") == "pitcher_coefficient"
    )["contextual_value"].to_list()
    assert all(0.0 <= value <= 1.5 for value in coefficients)
