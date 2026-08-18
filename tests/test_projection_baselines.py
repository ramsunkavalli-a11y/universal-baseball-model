import polars as pl
import pytest

from universal_baseball.projection_baselines import (
    PROJECTION_BASELINE0_METHOD,
    build_projection_baseline0,
)
from universal_baseball.projection_validation import (
    PROJECTION_V1_CONFIRMATION_FOLD,
    PROJECTION_V1_DEVELOPMENT_FOLDS,
)


def _profile() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 1, 2, 2],
            "core_bin": ["A", "B", "A", "B"],
            "baseline2_latent_probability": [0.25, 0.75, 0.6, 0.4],
        }
    )


def test_projection_baseline0_carries_frozen_current_talent_forward_exactly():
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[-1]
    output, metrics = build_projection_baseline0(_profile(), fold=fold)

    assert output.get_column("projection_probability").to_list() == [0.25, 0.75, 0.6, 0.4]
    assert output.get_column("projection_method").unique().to_list() == [
        PROJECTION_BASELINE0_METHOD
    ]
    assert output.get_column("as_of_date").unique().to_list() == [fold.snapshot_date]
    assert output.get_column("projection_target_start").unique().to_list() == [fold.target_start]
    assert output.get_column("projection_target_end").unique().to_list() == [fold.target_end]
    assert metrics["probabilities_changed_from_current_talent"] is False
    assert metrics["playing_time_modeled"] is False
    assert metrics["future_level_used"] is False
    assert metrics["player_count"] == 2


def test_projection_baseline0_rejects_duplicate_keys():
    frame = pl.concat([_profile(), _profile().head(1)])
    with pytest.raises(ValueError, match="duplicate"):
        build_projection_baseline0(frame, fold=PROJECTION_V1_DEVELOPMENT_FOLDS[0])


def test_projection_baseline0_rejects_invalid_probability_sums():
    frame = _profile().with_columns(
        pl.when(pl.col("player_id") == 1)
        .then(pl.col("baseline2_latent_probability") * 0.5)
        .otherwise(pl.col("baseline2_latent_probability"))
        .alias("baseline2_latent_probability")
    )
    with pytest.raises(ValueError, match="sum to one"):
        build_projection_baseline0(frame, fold=PROJECTION_V1_DEVELOPMENT_FOLDS[0])


def test_projection_baseline0_rejects_nonfinite_probability():
    frame = _profile().with_columns(
        pl.when((pl.col("player_id") == 1) & (pl.col("core_bin") == "A"))
        .then(float("nan"))
        .otherwise(pl.col("baseline2_latent_probability"))
        .alias("baseline2_latent_probability")
    )
    with pytest.raises(ValueError, match="invalid probabilities"):
        build_projection_baseline0(frame, fold=PROJECTION_V1_DEVELOPMENT_FOLDS[0])


def test_projection_baseline0_confirmation_is_quarantined_by_default():
    with pytest.raises(ValueError, match="quarantined"):
        build_projection_baseline0(_profile(), fold=PROJECTION_V1_CONFIRMATION_FOLD)


def test_projection_baseline0_confirmation_requires_explicit_authorization():
    output, metrics = build_projection_baseline0(
        _profile(),
        fold=PROJECTION_V1_CONFIRMATION_FOLD,
        allow_confirmation=True,
    )
    assert output.get_column("projection_confirmation_fold").unique().to_list() == [True]
    assert metrics["confirmation_access_explicitly_authorized"] is True
