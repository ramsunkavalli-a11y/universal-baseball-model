from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2e import (
    Stage2eFitError,
    certify_grouped_event_binary_equivalence,
    derive_binary_batter_sd,
    derive_hit_composition_batter_sd,
    fit_matched_binary_j0r,
    fit_matched_hit_composition_j0r,
)


def _binary_events(seed: int = 20260824, rows: int = 1600) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    player_effect = np.asarray([-0.5, -0.3, -0.1, 0.0, 0.1, 0.2, 0.35, 0.5])
    platoon_effect = {
        "L_vs_L": 0.15,
        "L_vs_R": -0.05,
        "R_vs_L": 0.08,
        "R_vs_R": -0.02,
    }
    cells = list(platoon_effect)
    records = []
    for index in range(rows):
        player = index % len(player_effect)
        cell = cells[index % len(cells)]
        pitcher = float(rng.normal(0.0, 0.2))
        logit = -1.0 + player_effect[player] + platoon_effect[cell] + 0.8 * pitcher
        response = int(rng.random() < 1.0 / (1.0 + np.exp(-logit)))
        records.append(
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
    return pl.DataFrame(records)


def _composition_events(seed: int = 20260825, rows: int = 1800) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    outcomes = np.asarray(["1B", "2B", "3B"])
    cells = ["L_vs_L", "L_vs_R", "R_vs_L", "R_vs_R"]
    records = []
    for index in range(rows):
        residual_2b = float(rng.normal(0.0, 0.2))
        residual_3b = float(rng.normal(0.0, 0.2))
        logits = np.asarray([0.0, -1.0 + 0.7 * residual_2b, -2.5 + 0.9 * residual_3b])
        probability = np.exp(logits - logits.max())
        probability /= probability.sum()
        records.append(
            {
                "player_id": index % 9,
                "season": 2022 + (index % 2),
                "league_id": 100 + (index % 2),
                "level_group": "AA",
                "platoon_cell": cells[index % 4],
                "HIT_COMPOSITION_eligible": True,
                "HIT_COMPOSITION_response": str(rng.choice(outcomes, p=probability)),
                "HIT_COMPOSITION_prior_pitcher_alr_residual_2B": residual_2b,
                "HIT_COMPOSITION_prior_pitcher_alr_residual_3B": residual_3b,
            }
        )
    return pl.DataFrame(records)


def test_fixed_information_scales_match_contract_formulas() -> None:
    assert derive_binary_batter_sd(0.25, 200.0) == pytest.approx(
        np.sqrt(1.0 / (200.0 * 0.25 * 0.75))
    )
    scales = derive_hit_composition_batter_sd(
        {"1B": 0.70, "2B": 0.25, "3B": 0.05}, 800.0
    )
    assert scales[0] == pytest.approx(
        np.sqrt(1.0 / (800.0 * 0.25) + 1.0 / (800.0 * 0.70))
    )
    assert scales[1] == pytest.approx(
        np.sqrt(1.0 / (800.0 * 0.05) + 1.0 / (800.0 * 0.70))
    )


def test_binary_j0r_fit_is_matched_traced_and_bounded() -> None:
    fit = fit_matched_binary_j0r(_binary_events(), "K", tolerance=1e-7)
    assert fit.diagnostics["identical_event_rows"] is True
    assert fit.diagnostics["event_count"] == 1600
    assert fit.context_increments.height == 8
    for phase in ("uncontextual", "contextual"):
        diagnostics = fit.diagnostics[phase]
        assert diagnostics["converged"] is True
        assert diagnostics["trace"]
        assert all(
            set(row)
            == {
                "iteration",
                "penalized_objective",
                "per_event_objective_improvement",
                "maximum_parameter_change",
                "accepted_step_size",
            }
            for row in diagnostics["trace"]
        )
    pitcher = fit.fixed_effects.filter(pl.col("effect_type") == "pitcher_coefficient")[
        "contextual_value"
    ].item()
    assert 0.0 <= pitcher <= 1.5


def test_grouped_and_event_uncontextual_fits_are_equivalent() -> None:
    result = certify_grouped_event_binary_equivalence(_binary_events(), "K")
    assert result["intercept_max_abs_delta"] <= 1e-10
    assert result["lsl_max_abs_delta"] <= 1e-10
    assert result["batter_max_abs_delta"] <= 1e-10
    assert result["objective_abs_delta"] <= 1e-8


def test_hit_composition_j0r_has_contrast_specific_fixed_scales() -> None:
    fit = fit_matched_hit_composition_j0r(_composition_events(), tolerance=1e-7)
    assert fit.context_increments.height == 9
    scales = fit.diagnostics["derived_batter_sd"]
    assert len(scales) == 2
    assert scales[0] != scales[1]
    assert fit.diagnostics["uncontextual"]["trace"]
    assert fit.diagnostics["contextual"]["trace"]


def test_intentional_nonconvergence_names_node_and_phase() -> None:
    with pytest.raises(Stage2eFitError) as caught:
        fit_matched_binary_j0r(
            _binary_events(rows=400),
            "K",
            max_iterations=1,
            tolerance=1e-20,
        )
    assert caught.value.node == "K"
    assert caught.value.phase in {"uncontextual", "contextual"}
    assert caught.value.trace


def test_hitter_probability_contract_is_unchanged() -> None:
    assert set(HITTER_TALENT_OUTCOMES) == {
        "K",
        "UBB",
        "HBP",
        "HR",
        "3B",
        "2B",
        "1B",
        "ROE",
        "FC_REACH",
        "SF",
        "MULTI_OUT",
        "OTHER_OUT",
    }
    assert len(HITTER_TALENT_OUTCOMES) == 12
