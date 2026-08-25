import json
from pathlib import Path

import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import probability_links
from universal_baseball.hitter_v2_stage2f_scoring import (
    primary_gate,
    subgroup_reversal_gate,
    translate_target_to_reference,
)


ROOT = Path(__file__).resolve().parents[1]


def _target() -> pl.DataFrame:
    counts = {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
    counts.update({"K": 20.0, "HR": 10.0, "1B": 20.0, "OTHER_OUT": 50.0})
    return pl.DataFrame(
        [{"player_id": 1, "hitter_talent_pa": 100.0, "primary_target_level_group": "AA", **counts}]
    )


def test_target_translation_uses_only_frozen_all_offsets() -> None:
    before = _target()
    components = probability_links(
        {outcome: float(before[outcome][0]) / 100.0 for outcome in HITTER_TALENT_OUTCOMES}
    )
    offsets = pl.DataFrame(
        [
            {
                "component": component,
                "age_band": band,
                "level": "AA",
                "link_offset_to_MLB": 0.5 if component == "contact" else 0.0,
            }
            for component in components
            for band in ("ALL", "21_23")
        ]
    ).with_columns(
        pl.when((pl.col("component") == "contact") & (pl.col("age_band") == "21_23"))
        .then(9.0)
        .otherwise(pl.col("link_offset_to_MLB"))
        .alias("link_offset_to_MLB")
    )
    after = translate_target_to_reference(before, offsets)
    assert after["HR"][0] > before["HR"][0]
    assert sum(float(after[outcome][0]) for outcome in HITTER_TALENT_OUTCOMES) == pytest.approx(100.0)
    assert after["primary_target_level_group"][0] == "AA"


def test_primary_gate_compares_each_metric_to_its_strongest_baseline() -> None:
    baselines = {
        "B0": {metric: 1.0 for metric in ("terminal_log_loss", "terminal_brier_score", "woba_rmse", "runs_per_600_rmse")},
        "B1": {metric: 0.9 for metric in ("terminal_log_loss", "terminal_brier_score", "woba_rmse", "runs_per_600_rmse")},
        "C0": {metric: 0.95 for metric in ("terminal_log_loss", "terminal_brier_score", "woba_rmse", "runs_per_600_rmse")},
    }
    candidate = {metric: 0.89 for metric in baselines["B0"]}
    assert primary_gate(candidate, baselines)["pass"] is True
    candidate["woba_rmse"] = 0.91
    assert primary_gate(candidate, baselines)["pass"] is False


def test_subgroup_guardrail_rejects_material_joint_reversal() -> None:
    baseline = {
        "terminal_log_loss": 0.4,
        "terminal_brier_score": 0.3,
        "woba_rmse": 0.05,
        "runs_per_600_rmse": 20.0,
    }
    candidate = {
        "terminal_log_loss": 0.401,
        "terminal_brier_score": 0.301,
        "woba_rmse": 0.053,
        "runs_per_600_rmse": 20.6,
    }
    gate = subgroup_reversal_gate(candidate, {"B0": baseline})
    assert gate["rate_reversal"] is True
    assert gate["proper_score_reversal"] is True
    assert gate["pass"] is False


def test_runner_source_has_no_protected_or_parameter_write_path() -> None:
    source = (ROOT / "scripts/score_hitter_v2_stage2f_H0.py").read_text(encoding="utf-8")
    assert "2026" not in source
    assert "fit_h0_surfaces" not in source
    assert "select_surface_configuration" not in source
    assert "target_player_league_seasons" not in source


def test_authorization_still_forbids_retuning_and_downstream_gates() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-stage2f-H0-scoring-authorization.json").read_text(encoding="utf-8")
    )
    assert authorization["current_gate"]["model_parameter_changes_open"] is False
    assert not any(authorization["immutable_boundaries"].values())
