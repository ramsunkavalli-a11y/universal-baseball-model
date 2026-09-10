import polars as pl
import pytest

from universal_baseball.fallback_coverage import audit_projection_fallbacks


def _paths() -> pl.DataFrame:
    return pl.DataFrame([
        {
            "player_id": 1,
            "season": 2026 + horizon,
            "horizon": horizon,
            "coverage_tier": "selected" if horizon <= 4 else "fallback",
            "probability_model_id": "probability",
            "workload_model_id": "workload",
            "evidence_tier": "population_prior",
            "talent_model_id": "talent",
            "baserunning_evidence_tier": "population_neutral",
            "baserunning_model_id": "running",
            "defense_evidence_tier": "population_neutral",
            "defense_model_id": "defense",
            "expected_war": 0.0,
        }
        for horizon in range(1, 7)
    ])


def test_complete_fallback_path_passes_with_population_prior() -> None:
    report = audit_projection_fallbacks(_paths(), component="hitter")
    assert report["players"] == 1
    assert report["complete_six_year_paths"]
    assert report["missing_provenance_rows"] == 0


def test_missing_horizon_or_provenance_fails_closed() -> None:
    with pytest.raises(ValueError, match="horizons 1-6"):
        audit_projection_fallbacks(_paths().filter(pl.col("horizon") < 6), component="hitter")
    with pytest.raises(ValueError, match="missing provenance"):
        audit_projection_fallbacks(
            _paths().with_columns(pl.lit("").alias("talent_model_id")),
            component="hitter",
        )
