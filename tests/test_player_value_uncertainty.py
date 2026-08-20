from __future__ import annotations

import json
from dataclasses import astuple

import numpy as np
import pytest

from universal_baseball.player_value_uncertainty import (
    NB2_ALPHA,
    batting_run_variance,
    defense_run_variance_at_expected_pa,
    recover_untruncated_nb2_mean,
    sample_hurdle_plate_appearances,
    simulate_player_uncertainty,
    structural_zero_uncertainty,
)


def test_nb2_truncated_mean_inversion_and_sampling_are_deterministic() -> None:
    target = 240.0
    mu = recover_untruncated_nb2_mean(target)
    size = 1.0 / NB2_ALPHA
    p_zero = (size / (size + mu)) ** size
    assert mu / (1.0 - p_zero) == pytest.approx(target, rel=1e-10)

    first = sample_hurdle_plate_appearances(
        np.random.default_rng(7),
        draws=50_000,
        participation_probability=0.6,
        positive_truncated_mean=target,
    )
    second = sample_hurdle_plate_appearances(
        np.random.default_rng(7),
        draws=50_000,
        participation_probability=0.6,
        positive_truncated_mean=target,
    )
    np.testing.assert_array_equal(first, second)
    assert np.all(first >= 0)
    assert np.all(first[first > 0] >= 1)
    assert first.mean() == pytest.approx(0.6 * target, rel=0.025)


def test_batting_variance_declines_with_more_posterior_evidence() -> None:
    pa = np.asarray([0.0, 1.0, 600.0])
    probabilities = [0.25, 0.75]
    values = [-0.2, 0.4]
    sparse = batting_run_variance(
        pa,
        probabilities=probabilities,
        centered_bin_run_values=values,
        core_event_rate_per_pa=0.95,
        posterior_concentration=100.0,
    )
    strong = batting_run_variance(
        pa,
        probabilities=probabilities,
        centered_bin_run_values=values,
        core_event_rate_per_pa=0.95,
        posterior_concentration=1000.0,
    )
    assert sparse[0] == 0.0
    assert sparse[1] == pytest.approx(strong[1])
    assert sparse[2] > strong[2] > 0.0


def test_defense_variance_uses_actual_families_and_zero_missing_catcher_opportunity() -> None:
    row = {
        "defense_families_json": json.dumps(
            {
                "range_families": {"SS": "T1"},
                "throwing_family": "C2",
                "blocking_family": "B0",
                "framing_family": "F0",
            }
        ),
        "projected_outs_SS": 1000.0,
    }
    variance = defense_run_variance_at_expected_pa(
        final_row=row,
        catcher_opportunities={
            "throwing": {"H1_fixed_50_50_hybrid": 20.0},
        },
        general_run_rates={"SS": 0.002},
        catcher_run_rates={"throwing": 0.05, "blocking": 0.001, "framing": 0.001},
    )
    assert variance == pytest.approx(
        0.878640460280284 * (1000.0 * 0.002) ** 2
        + 0.9385276019479529 * (20.0 * 0.05) ** 2
    )


def test_player_simulation_is_repeatable_nested_and_variance_shares_sum() -> None:
    kwargs = {
        "player_id": 650333,
        "point_war": 3.0,
        "point_runs_above_replacement": 30.0,
        "expected_pa": 400.0,
        "participation_probability": 0.8,
        "positive_truncated_mean": 500.0,
        "runs_per_win": 10.0,
        "batting_probabilities": [0.25, 0.75],
        "centered_bin_run_values": [-0.2, 0.4],
        "core_event_rate_per_pa": 0.95,
        "batting_posterior_concentration": 300.0,
        "defense_variance_at_expected_pa": 9.0,
        "draws": 5_000,
    }
    first = simulate_player_uncertainty(**kwargs)
    second = simulate_player_uncertainty(**kwargs)
    assert first == second
    assert first.war_p025 <= first.war_p10 <= first.median_war <= first.war_p90 <= first.war_p975
    assert first.interval_95_width >= first.interval_80_width >= 0.0
    assert (
        first.playing_time_variance_share
        + first.batting_variance_share
        + first.defense_variance_share
    ) == pytest.approx(1.0, abs=1e-12)


def test_structural_zero_is_all_zero() -> None:
    result = structural_zero_uncertainty()
    assert all(value == 0.0 for value in astuple(result))
