from copy import deepcopy
import json
from pathlib import Path

import pytest

from universal_baseball.playing_time_fit_artifact import (
    playing_time_fit_from_artifact,
    playing_time_fit_to_artifact,
)
from universal_baseball.playing_time_model import (
    PT_FORM_P,
    PT_FORM_U,
    PlayingTimeHurdleFit,
    PlayingTimeStandardization,
    playing_time_continuous_features,
    playing_time_feature_names,
)
from universal_baseball.storage import sha256_file


def _fit() -> PlayingTimeHurdleFit:
    features = playing_time_feature_names(PT_FORM_U)
    continuous = playing_time_continuous_features(PT_FORM_U)
    return PlayingTimeHurdleFit(
        form=PT_FORM_U,
        feature_names=features,
        continuous_features=continuous,
        standardization=PlayingTimeStandardization(
            means={feature: float(index) for index, feature in enumerate(continuous)},
            scales={feature: float(index + 1) for index, feature in enumerate(continuous)},
        ),
        logistic_intercept=-0.25,
        logistic_coefficients=tuple(float(index) / 10.0 for index in range(len(features))),
        nb_coefficients=tuple(
            float(index) / 20.0 for index in range(len(features) + 1)
        ),
        nb_alpha=0.75,
        participation_training_players=100,
        positive_training_players=40,
        metrics={"future_team_used": False},
    )


def test_playing_time_fit_artifact_round_trip() -> None:
    fit = _fit()
    assert playing_time_fit_from_artifact(playing_time_fit_to_artifact(fit)) == fit


def test_playing_time_fit_artifact_rejects_feature_drift() -> None:
    payload = deepcopy(playing_time_fit_to_artifact(_fit()))
    payload["feature_names"] = payload["feature_names"][:-1]
    with pytest.raises(ValueError, match="feature contract"):
        playing_time_fit_from_artifact(payload)


def test_playing_time_fit_artifact_rejects_invalid_scale() -> None:
    payload = deepcopy(playing_time_fit_to_artifact(_fit()))
    feature = payload["continuous_features"][0]
    payload["standardization"]["scales"][feature] = 0.0
    with pytest.raises(ValueError, match="standardization is invalid"):
        playing_time_fit_from_artifact(payload)


def test_durable_pre2025_replay_package_matches_manifest() -> None:
    root = (
        Path(__file__).parents[1]
        / "model_artifacts"
        / "opportunity-v2-pre2025-replay"
    )
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    expected_forms = {
        "hitter-opportunity-fit.json": PT_FORM_U,
        "pitcher-opportunity-fit.json": PT_FORM_P,
    }
    for name, expected_form in expected_forms.items():
        path = root / name
        assert sha256_file(path) == manifest["artifacts"][name]["sha256"]
        fit = playing_time_fit_from_artifact(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert fit.form == expected_form
