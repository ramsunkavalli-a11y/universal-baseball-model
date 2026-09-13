from __future__ import annotations

from scripts.audit_prospect_separated_outcome_top50 import _assessment


def test_assessment_keeps_graduates_out_of_missing_model_bucket() -> None:
    assert _assessment({
        "expected_outcome_percentile": None,
        "model_coverage_status": "graduated_or_prior_mlb",
    }) == "graduated_or_prior_mlb"


def test_assessment_uses_frozen_model_percentiles_only() -> None:
    assert _assessment({
        "expected_outcome_percentile": 0.91,
        "conditional_rate_percentile": None,
        "outside_rank": 50,
        "outside_fv": 50,
    }) == "broad_agreement"
    assert _assessment({
        "expected_outcome_percentile": 0.50,
        "conditional_rate_percentile": 0.80,
        "outside_rank": 1,
        "outside_fv": 65,
    }) == "partial_agreement"
