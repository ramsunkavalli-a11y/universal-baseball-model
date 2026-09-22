import pytest

from universal_baseball.hitter_model_tournament import (
    SUPPORTED_ENGINES,
    _engine_models,
)


def test_requested_engine_families_are_registered() -> None:
    assert {
        "catboost",
        "xgboost",
        "lightgbm",
        "ebm",
        "gpboost",
        "ngboost",
    }.issubset(SUPPORTED_ENGINES)


def test_unknown_engine_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported engine"):
        _engine_models("mystery", 1)
