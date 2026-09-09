from datetime import date

import polars as pl
import pytest

from universal_baseball.prospect_pbp_features import (
    aggregate_prospect_pbp_features,
    attach_prospect_pbp_features,
    contact_shape_design,
    contact_shape_priors,
)


def _source() -> tuple[pl.DataFrame, pl.DataFrame]:
    profile = pl.DataFrame(
        {
            "season": [2021] * 5,
            "game_date": [date(2021, 6, 1)] * 5,
            "game_pk": [10] * 5,
            "player_id": [1] * 5,
            "core_bin": ["PULL_GB", "CENTER_GB", "OPPO_LD", "PULL_OFFB", "IFFB"],
            "occurrence_count": [2, 1, 1, 1, 1],
        }
    )
    summary = pl.DataFrame(
        {
            "season": [2021], "game_date": [date(2021, 6, 1)],
            "game_pk": [10], "player_id": [1], "core_profile_event_count": [8],
        }
    )
    return profile, summary


def test_aggregate_contact_shape_counts() -> None:
    profile, summary = _source()
    result = aggregate_prospect_pbp_features(profile, summary, predictor_year=2021)
    assert result.select(
        "pbp_contact_count", "gb_count", "ld_count", "iffb_count",
        "pull_count", "center_count", "oppo_count",
    ).row(0) == (6.0, 3.0, 1.0, 1.0, 3.0, 1.0, 1.0)


def test_future_date_fails_closed() -> None:
    profile, summary = _source()
    with pytest.raises(ValueError, match="future"):
        aggregate_prospect_pbp_features(
            profile.with_columns(pl.lit(date(2022, 1, 1)).alias("game_date")),
            summary,
            predictor_year=2021,
        )


def test_missing_pbp_player_stays_in_denominator() -> None:
    profile, summary = _source()
    features = aggregate_prospect_pbp_features(profile, summary, predictor_year=2021)
    cohort = pl.DataFrame({"player_id": [1, 2], "target": [1, 0]})
    joined = attach_prospect_pbp_features(cohort, features)
    assert joined.height == 2
    assert joined.filter(pl.col("player_id") == 2).item(0, "pbp_observed") is False
    assert joined.filter(pl.col("player_id") == 2).item(0, "pbp_contact_count") == 0.0


def test_regression_pulls_small_samples_to_training_population() -> None:
    profile, summary = _source()
    features = aggregate_prospect_pbp_features(profile, summary, predictor_year=2021)
    priors = contact_shape_priors(features)
    raw = contact_shape_design(
        features, feature_family="combined", priors=priors, regression_strength=0.0
    )
    regressed = contact_shape_design(
        features, feature_family="combined", priors={field: 0.2 for field in priors},
        regression_strength=100.0,
    )
    assert raw.shape == (1, 7)
    assert regressed.shape == (1, 7)
    assert abs(regressed[0, 2] - 0.2) < abs(raw[0, 2] - 0.2)


def test_missing_pbp_design_uses_priors_without_nonfinite_values() -> None:
    profile, summary = _source()
    features = aggregate_prospect_pbp_features(profile, summary, predictor_year=2021)
    joined = attach_prospect_pbp_features(
        pl.DataFrame({"player_id": [2]}), features
    )
    priors = {field: 0.2 for field in contact_shape_priors(features)}
    design = contact_shape_design(
        joined, feature_family="combined", priors=priors, regression_strength=0.0
    )
    assert design.shape == (1, 7)
    assert (design == design).all()
