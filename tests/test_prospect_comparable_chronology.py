from __future__ import annotations

from scripts.audit_prospect_comparable_chronology import (
    HORIZON,
    REFERENCE_ORIGINS,
    VALIDATION_ORIGINS,
    _passes,
)


def _summary() -> dict[str, object]:
    return {
        "historical_comparables": {"mae": 0.8, "rmse": 0.9},
        "population_baseline": {"mae": 1.0, "rmse": 1.1},
        "arrival_historical_comparables": {"brier": 0.08, "log_loss": 0.30},
        "arrival_population_baseline": {"brier": 0.10, "log_loss": 0.35},
        "conditional_support_sensitivity": {
            "10": {
                "arrivals": 25,
                "historical_comparables_mae": 0.7,
                "population_baseline_mae": 0.8,
                "historical_comparables_rmse": 0.9,
                "population_baseline_rmse": 1.0,
            }
        },
    }


def test_frozen_validation_origins_only_use_completed_reference_outcomes() -> None:
    for target in VALIDATION_ORIGINS:
        references = [
            origin for origin in REFERENCE_ORIGINS if origin + HORIZON < target
        ]
        assert references
        assert max(references) + HORIZON < target


def test_gate_requires_every_metric_and_conditional_support() -> None:
    summary = _summary()
    assert _passes(summary)

    summary["conditional_support_sensitivity"]["10"]["arrivals"] = 19
    assert not _passes(summary)
