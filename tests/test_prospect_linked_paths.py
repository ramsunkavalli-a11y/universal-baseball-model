import numpy as np
import polars as pl

from universal_baseball.prospect_linked_paths import simulate_linked_tail_blocks


def _coefficients() -> pl.DataFrame:
    rows = []
    for origin, feature_set, terms in (
        (
            "FRINGE_MLB",
            "age_elapsed_prior_workload",
            (
                "intercept", "transition_age_centered_scaled",
                "elapsed_year_centered_scaled", "elapsed_year_at_least_three",
                "prior_mlb_active", "log1p_prior_workload_vs_active_mean",
            ),
        ),
        (
            "MEANINGFUL_MLB",
            "age_elapsed",
            (
                "intercept", "transition_age_centered_scaled",
                "elapsed_year_centered_scaled", "elapsed_year_at_least_three",
            ),
        ),
    ):
        rows.extend(
            {
                "player_type": "hitter",
                "origin_state": origin,
                "feature_set": feature_set,
                "term": term,
                "coefficient": 30.0 if term == "intercept" else 0.0,
            }
            for term in terms
        )
    return pl.DataFrame(rows)


def test_tail_sampler_preserves_blocks_and_resamples_only_after_divergence() -> None:
    rows = []
    for player_id, states, workloads in (
        (1, ["FRINGE_MLB", "FRINGE_MLB", "FRINGE_MLB"], [50.0, 50.0, 50.0]),
        (2, ["MEANINGFUL_MLB", "MEANINGFUL_MLB", "ESTABLISHED_MLB"], [250.0, 250.0, 450.0]),
        (3, ["ESTABLISHED_MLB"] * 3, [450.0, 450.0, 450.0]),
    ):
        for year, (state, workload) in enumerate(zip(states, workloads), 1):
            rows.append(
                {
                    "path_player_id": player_id,
                    "player_type": "hitter",
                    "path_year": year,
                    "adjusted_workload": workload,
                    "raw_workload": workload,
                    "observed_career_state": state,
                }
            )
    result = simulate_linked_tail_blocks(
        np.random.default_rng(4),
        pl.DataFrame(rows),
        _coefficients(),
        np.array([300.0, 300.0, 300.0]),
        player_type="hitter",
        initial_age_years=22.0,
        direct_established_probability=1.0,
        draws=32,
    )
    assert result.adjusted_workload.shape == (32, 3)
    assert result.donor_player_ids.shape == (32, 3)
    assert result.tail_resamples > 0
    assert (np.diff(result.states, axis=1) >= 0).all()
    changed = result.donor_player_ids[:, 1] != result.donor_player_ids[:, 0]
    assert changed.any()
    assert (
        result.donor_player_ids[changed, 2]
        == result.donor_player_ids[changed, 1]
    ).all()
