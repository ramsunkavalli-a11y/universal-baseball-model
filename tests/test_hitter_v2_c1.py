import polars as pl
import pytest

from universal_baseball.hitter_v2_c1 import (
    age_change_offsets,
    adjust_multi_out_for_gidp,
    aggregate_player_park_exposure,
    apply_log_probability_offsets,
    attach_relative_ages,
    build_adjacent_movement_observations,
    estimate_visitor_park_offsets,
    estimate_player_gidp_rates,
    estimate_player_season_probabilities,
    fit_ridge_age_offsets,
    neutralize_player_season_parks,
    remove_age_from_movement_observations,
    solve_level_offsets,
    select_c1_adjustment_hyperparameters,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


def _probabilities() -> dict[str, float]:
    values = {outcome: 0.01 for outcome in HITTER_TALENT_OUTCOMES}
    values["K"] = 0.20
    values["UBB"] = 0.08
    values["HBP"] = 0.02
    values["HR"] = 0.05
    values["1B"] = 0.15
    values["2B"] = 0.05
    values["3B"] = 0.01
    values["ROE"] = 0.02
    values["FC_REACH"] = 0.02
    values["SF"] = 0.03
    values["MULTI_OUT"] = 0.04
    values["OTHER_OUT"] = 0.33
    assert sum(values.values()) == pytest.approx(1.0)
    return values


def _player_games() -> pl.DataFrame:
    rows = []
    for player_id, team_id, venue_id, home_runs in (
        (1, 10, 100, 10),
        (2, 11, 100, 0),
        (3, 10, 101, 0),
        (4, 11, 101, 0),
    ):
        counts = {outcome: 0 for outcome in HITTER_TALENT_OUTCOMES}
        counts["HR"] = home_runs
        counts["OTHER_OUT"] = 10 - home_runs
        rows.append(
            {
                "season": 2021,
                "game_id": venue_id,
                "league_id": 103,
                "team_id": team_id,
                "player_id": player_id,
                "level_group": "MLB",
                "hitter_talent_pa": 10,
                **counts,
            }
        )
    return pl.DataFrame(rows)


def _park_context() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2021] * 4,
            "game_id": [100, 100, 101, 101],
            "team_id": [10, 11, 10, 11],
            "player_id": [1, 2, 3, 4],
            "venue_id": [100, 100, 101, 101],
            "away_team_id": [10, 10, 10, 10],
            "venue_context_eligible": [True, True, True, True],
        }
    )


def test_zero_log_offsets_reproduce_probability_vector_exactly() -> None:
    probabilities = _probabilities()
    adjusted = apply_log_probability_offsets(
        probabilities, {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
    )
    assert adjusted == pytest.approx(probabilities, abs=1e-15)


def test_park_estimator_uses_visitors_and_rejects_future_rows() -> None:
    offsets = estimate_visitor_park_offsets(
        _player_games(),
        _park_context(),
        predictor_cutoff_season=2021,
        prior_pa=10.0,
    )
    venue_100 = offsets.filter(pl.col("venue_id") == 100).row(0, named=True)
    venue_101 = offsets.filter(pl.col("venue_id") == 101).row(0, named=True)
    assert venue_100["venue_pa"] == 10.0
    assert venue_100["park_log_offset_HR"] > venue_101["park_log_offset_HR"]

    future = _player_games().with_columns(pl.lit(2022).alias("season"))
    with pytest.raises(ValueError, match="after the predictor cutoff"):
        estimate_visitor_park_offsets(
            future,
            _park_context(),
            predictor_cutoff_season=2021,
            prior_pa=10.0,
        )


def test_player_park_exposure_is_pa_weighted_and_missing_rows_are_absent() -> None:
    games = _player_games()
    context = _park_context()
    offsets = estimate_visitor_park_offsets(
        games, context, predictor_cutoff_season=2021, prior_pa=10.0
    )
    exposure = aggregate_player_park_exposure(
        games,
        context,
        offsets,
        predictor_cutoff_season=2021,
    )
    assert exposure["player_id"].to_list() == [1, 2, 3, 4]
    assert exposure["park_evidence_pa"].to_list() == [10.0] * 4


def test_level_solution_is_mlb_anchored_and_flags_disconnected_levels() -> None:
    rows = []
    for source, destination, delta in (
        ("AAA", "MLB", 0.2),
        ("AA", "AAA", 0.1),
        ("R", "DSL", 0.5),
    ):
        rows.append(
            {
                "source_level": source,
                "destination_level": destination,
                "pair_weight": 100.0,
                **{
                    f"delta_{outcome}": delta
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    solved = solve_level_offsets(pl.DataFrame(rows), prior_mover_pa=100.0)
    mlb = solved.filter(pl.col("level_group") == "MLB").row(0, named=True)
    rookie = solved.filter(pl.col("level_group") == "R").row(0, named=True)
    assert mlb["level_log_offset_HR"] == 0.0
    assert mlb["translation_connected_to_mlb"] is True
    assert rookie["translation_connected_to_mlb"] is False
    assert rookie["level_log_offset_HR"] == 0.0


def test_gidp_fallback_is_exact_and_adjustment_preserves_upstream_mass() -> None:
    probabilities = _probabilities()
    fallback, reason = adjust_multi_out_for_gidp(
        probabilities,
        opportunity_rate=None,
        conversion_rate=None,
        non_gidp_multi_out_rate=None,
    )
    assert fallback == probabilities
    assert reason == "missing_gidp_opportunity_evidence"

    adjusted, reason = adjust_multi_out_for_gidp(
        probabilities,
        opportunity_rate=0.10,
        conversion_rate=0.20,
        non_gidp_multi_out_rate=0.01,
    )
    assert reason is None
    assert adjusted["MULTI_OUT"] == pytest.approx(0.03)
    for outcome in ("K", "UBB", "HBP", "HR", "1B", "2B", "3B", "ROE", "FC_REACH"):
        assert adjusted[outcome] == probabilities[outcome]
    assert sum(adjusted.values()) == pytest.approx(1.0)


def test_player_season_movement_and_age_pipeline_is_chronology_safe() -> None:
    games = pl.concat(
        [
            _player_games(),
            _player_games().with_columns(
                pl.lit(2022).alias("season"),
                pl.when(pl.col("player_id") <= 2)
                .then(pl.lit("AAA"))
                .otherwise(pl.lit("MLB"))
                .alias("level_group"),
            ),
        ],
        how="vertical_relaxed",
    )
    seasons = estimate_player_season_probabilities(
        games,
        predictor_cutoff_season=2022,
        component_prior_pa=50.0,
    )
    zero_exposure = seasons.select("player_id", "season").with_columns(
        pl.lit(10.0).alias("park_evidence_pa"),
        *[
            pl.lit(0.0).alias(f"park_log_offset_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ],
    )
    neutral = neutralize_player_season_parks(seasons, zero_exposure)
    ages = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4] * 2,
            "season": [2021] * 4 + [2022] * 4,
            "age_years": [20.0, 22.0, 24.0, 26.0, 21.0, 23.0, 25.0, 27.0],
        }
    )
    aged = attach_relative_ages(neutral, ages)
    movement = build_adjacent_movement_observations(aged)
    assert movement.height == 4
    first_pass = solve_level_offsets(movement, prior_mover_pa=100.0)
    coefficients = fit_ridge_age_offsets(
        movement, first_pass, ridge_penalty=10.0
    )
    assert coefficients.height == len(HITTER_TALENT_OUTCOMES)
    offsets, fallback = age_change_offsets((25.0, 25.0), coefficients)
    assert fallback is None
    assert set(offsets) == set(HITTER_TALENT_OUTCOMES)
    adjusted_movement = remove_age_from_movement_observations(
        movement, coefficients
    )
    assert adjusted_movement.height == movement.height


def test_gidp_rate_estimator_retains_missing_player_fallback() -> None:
    history = pl.DataFrame(
        {
            "player_id": [1, 1],
            "season": [2021, 2022],
            "gidp_opportunities": [10, 20],
            "batting_GiDP": [2, 4],
            "MULTI_OUT": [3, 6],
            "accepted_terminal_pa": [100, 200],
            "gidp_opportunity_modeling_eligible": [True, True],
        }
    )
    estimates = estimate_player_gidp_rates(
        history,
        [1, 999],
        predictor_cutoff_season=2022,
        half_life_seasons=2.0,
        prior_pa=100.0,
    )
    known = estimates.filter(pl.col("player_id") == 1).row(0, named=True)
    missing = estimates.filter(pl.col("player_id") == 999).row(0, named=True)
    assert known["gidp_evidence_available"] is True
    assert 0.0 < known["gidp_opportunity_rate"] < 1.0
    assert missing["gidp_evidence_available"] is False
    assert missing["gidp_opportunity_rate"] is None


def test_c1_selector_uses_larger_pooling_and_ridge_on_tie() -> None:
    scores = pl.DataFrame(
        {
            "park_prior_pa": [500.0, 2000.0, 2000.0],
            "movement_prior_pa": [500.0, 100.0, 500.0],
            "ridge_penalty": [100.0, 100.0, 100.0],
            "event_log_loss": [1.0, 1.0 + 5e-9, 1.0 + 5e-9],
        }
    )
    selected = select_c1_adjustment_hyperparameters(scores)
    assert selected["movement_prior_pa"] == 500.0
    assert selected["park_prior_pa"] == 2000.0
    assert selected["ridge_penalty"] == 100.0
