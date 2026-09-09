from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from universal_baseball.durable_model_package import (
    PLAYING_TIME_REFIT_FILES,
    persist_playing_time_refit_package,
)
from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    PT_FORM_C,
    playing_time_continuous_features,
    playing_time_feature_names,
)
from universal_baseball.storage import write_canonical_parquet


def _coefficients(form: str, alpha: float) -> pl.DataFrame:
    features = playing_time_feature_names(form)
    rows = [
        {"component": "participation_logit", "feature": "intercept", "coefficient": -1.0}
    ]
    rows.extend(
        {
            "component": "participation_logit",
            "feature": feature,
            "coefficient": 0.01,
        }
        for feature in features
    )
    rows.extend(
        {
            "component": "positive_truncated_nb2",
            "feature": feature,
            "coefficient": 0.02,
        }
        for feature in ("intercept", *features)
    )
    rows.append(
        {
            "component": "positive_truncated_nb2",
            "feature": "alpha",
            "coefficient": alpha,
        }
    )
    return pl.DataFrame(rows)


def _standardization(form: str) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"feature": feature, "mean": 0.0, "scale": 1.0}
            for feature in playing_time_continuous_features(form)
        ],
        schema={"feature": pl.String, "mean": pl.Float64, "scale": pl.Float64},
    )


def _refit(root: Path) -> None:
    table_root = root / "tables"
    storage = {}
    inputs = {
        "candidate_coefficients": _coefficients(PT_FORM_C, 0.7),
        "candidate_standardization": _standardization(PT_FORM_C),
        "baseline0_coefficients": _coefficients(PT_FORM_B0, 0.8),
        "baseline0_standardization": _standardization(PT_FORM_B0),
    }
    for key, filename in PLAYING_TIME_REFIT_FILES.items():
        storage[key] = write_canonical_parquet(
            inputs[key], table_root / filename, table_name=key
        ).as_record()
    report = {
        "status": "frozen_ready_for_2025_source_materialization",
        "source_run_id": 123,
        "source_sha": "a" * 40,
        "selected_form": PT_FORM_C,
        "baseline0_form": PT_FORM_B0,
        "candidate_nb_alpha": 0.7,
        "baseline0_nb_alpha": 0.8,
        "candidate_training": {"training_observation_count": 100},
        "baseline0_training": {"training_observation_count": 100},
        "training_target_years": [2022, 2023, 2024],
        "package_versions": {"polars": pl.__version__},
        "decision": {"parameters_frozen_before_2025": True},
        "storage": storage,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(json.dumps(report), encoding="utf-8")


def test_persisted_package_is_complete_and_does_not_overwrite(tmp_path: Path) -> None:
    refit = tmp_path / "refit"
    destination = tmp_path / "durable" / "model-123"
    _refit(refit)

    manifest = persist_playing_time_refit_package(refit, destination)

    assert manifest["complete_scoring_package"] is True
    assert manifest["source_run_id"] == 123
    assert manifest["selected_feature_names"] == list(
        playing_time_feature_names(PT_FORM_C)
    )
    assert manifest["distribution_parameters"]["candidate_nb_alpha"] == 0.7
    assert (destination / "manifest.json").is_file()
    assert set((destination / "tables").iterdir()) == {
        destination / "tables" / filename
        for filename in PLAYING_TIME_REFIT_FILES.values()
    }
    with pytest.raises(FileExistsError):
        persist_playing_time_refit_package(refit, destination)


def test_persisted_package_rejects_a_tampered_parameter_file(tmp_path: Path) -> None:
    refit = tmp_path / "refit"
    _refit(refit)
    with (refit / "tables" / "candidate_coefficients.parquet").open("ab") as target:
        target.write(b"tampered")

    with pytest.raises(ValueError, match="size differs"):
        persist_playing_time_refit_package(refit, tmp_path / "durable")
