import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_validation import (
    build_player_scoring_surface,
    build_evaluation_subgroups,
    fold_primary_gate,
    paired_player_bootstrap_rmse_delta,
    predicted_woba_decile_calibration,
    terminal_component_calibration,
    subgroup_reversal_gate,
    summarize_scoring_surface,
)


def _targets() -> pl.DataFrame:
    rows = []
    for player_id in range(1, 21):
        pa = 100
        hr = player_id * 2
        rows.append(
            {
                "player_id": player_id,
                "hitter_talent_pa": pa,
                "primary_target_level_group": "MLB",
                **{
                    outcome: (
                        hr
                        if outcome == "HR"
                        else pa - hr
                        if outcome == "OTHER_OUT"
                        else 0
                    )
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows)


def _predictions(*, shift: float = 0.0) -> pl.DataFrame:
    rows = []
    for player_id in range(1, 21):
        hr = min(max(player_id * 0.02 + shift, 0.001), 0.999)
        rows.append(
            {
                "player_id": player_id,
                **{
                    f"p_{outcome}": (
                        hr
                        if outcome == "HR"
                        else 1.0 - hr
                        if outcome == "OTHER_OUT"
                        else 0.0
                    )
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows)


def test_surface_and_deciles_preserve_all_players() -> None:
    surface = build_player_scoring_surface(
        _predictions(), _targets(), model_id="test", fold_id="V"
    )
    deciles = predicted_woba_decile_calibration(surface)
    assert surface.height == 20
    assert len(deciles) == 10
    assert sum(int(row["players"]) for row in deciles) == 20
    assert max(float(row["absolute_woba_error"]) for row in deciles) == pytest.approx(0.0)


def test_component_calibration_identifies_varying_hr_surface() -> None:
    calibration = terminal_component_calibration(
        _predictions(), _targets(), weighting="player"
    )
    hr = next(row for row in calibration if row["outcome"] == "HR")
    assert hr["identifiable"] is True
    assert hr["intercept"] == pytest.approx(0.0, abs=1e-12)
    assert hr["slope"] == pytest.approx(1.0)


def test_paired_bootstrap_requires_identical_keys_and_favors_better_surface() -> None:
    candidate = build_player_scoring_surface(
        _predictions(), _targets(), model_id="candidate", fold_id="V"
    )
    baseline = build_player_scoring_surface(
        _predictions(shift=0.05), _targets(), model_id="baseline", fold_id="V"
    )
    result = paired_player_bootstrap_rmse_delta(
        candidate,
        baseline,
        error_column="woba_error",
        resamples=500,
    )
    assert result["observed_candidate_minus_baseline_rmse"] < 0.0
    assert result["upper_bound_below_zero"] is True

    with pytest.raises(ValueError, match="identical player-fold keys"):
        paired_player_bootstrap_rmse_delta(
            candidate.head(19),
            baseline,
            error_column="woba_error",
            resamples=10,
        )


def test_fold_gate_uses_metric_specific_strongest_baseline() -> None:
    candidate = {
        "terminal_log_loss": 0.9,
        "terminal_brier_score": 0.7,
        "woba_mae": 0.01,
        "woba_rmse": 0.02,
        "runs_per_600_mae": 5.0,
        "runs_per_600_rmse": 10.0,
    }
    b0 = {key: value + 0.1 for key, value in candidate.items()}
    b1 = {key: value + 0.2 for key, value in candidate.items()}
    gate = fold_primary_gate(candidate, b0, b1)
    assert gate["pass"] is True
    assert all(
        comparison["baseline_id"] == "B0_ONE_YEAR_EB"
        for comparison in gate["comparisons"].values()
    )


def test_subgroup_builder_uses_training_rates_and_target_level_only_for_labels() -> None:
    training = pl.DataFrame(
        [
            {
                "player_id": row["player_id"],
                "season": 2021,
                "league_id": 1,
                "level_group": "AAA",
                "hitter_talent_pa": 200,
                "K": row["player_id"] * 2,
                "HR": row["player_id"],
            }
            for row in _targets().iter_rows(named=True)
        ]
    )
    ages = pl.DataFrame(
        {"player_id": list(range(1, 21)), "age_years": [19.0 + value for value in range(20)]}
    )
    subgroups = build_evaluation_subgroups(training, _targets(), ages)
    assert subgroups.height == 20
    assert set(subgroups["movement_band"].unique()) == {"promotion"}
    assert "high_K" in set(subgroups["k_band"].unique())
    assert "low_power" in set(subgroups["hr_power_band"].unique())


def test_surface_summary_and_reversal_gate_are_consistent() -> None:
    surface = build_player_scoring_surface(
        _predictions(), _targets(), model_id="candidate", fold_id="V"
    )
    summary = summarize_scoring_surface(surface, weighting="player")
    assert summary["woba_rmse"] == pytest.approx(0.0)
    baseline = dict(summary)
    baseline.update(
        {
            "woba_rmse": 0.001,
            "runs_per_600_rmse": 0.1,
            "terminal_log_loss": 0.01,
            "terminal_brier_score": 0.01,
        }
    )
    candidate = dict(baseline)
    candidate.update(
        {
            "woba_rmse": 0.004,
            "runs_per_600_rmse": 1.0,
            "terminal_log_loss": 0.02,
            "terminal_brier_score": 0.02,
        }
    )
    assert subgroup_reversal_gate(candidate, baseline, baseline)["pass"] is False
