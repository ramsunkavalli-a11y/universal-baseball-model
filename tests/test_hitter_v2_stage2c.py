import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b import NodeOffsetFit
from universal_baseball.hitter_v2_stage2c import (
    FIXED_PRIOR_EVENTS,
    GROUND_MODE,
    POWER_MODE,
    Stage2cFit,
    apply_stage2c_residual,
    build_stage2c_features,
    fit_stage2c_residual,
    zero_stage2c_fit,
)


def _probabilities() -> dict[str, float]:
    return {
        "K": 0.22,
        "UBB": 0.08,
        "HBP": 0.01,
        "HR": 0.04,
        "3B": 0.005,
        "2B": 0.045,
        "1B": 0.16,
        "ROE": 0.015,
        "FC_REACH": 0.01,
        "SF": 0.025,
        "MULTI_OUT": 0.02,
        "OTHER_OUT": 0.37,
    }


def _prediction(player_id: int) -> dict[str, object]:
    return {
        "player_id": player_id,
        "model_id": "C0_NESTED_EB",
        **{f"p_{key}": value for key, value in _probabilities().items()},
    }


def _shape_history() -> pl.DataFrame:
    profiles = (
        (2021, 1, {"PULL_OFFB": 30, "CENTER_OFFB": 10, "OPPO_OFFB": 10, "PULL_GB": 20, "CENTER_GB": 15, "OPPO_GB": 5}),
        (2021, 2, {"PULL_OFFB": 5, "CENTER_OFFB": 20, "OPPO_OFFB": 25, "PULL_GB": 10, "CENTER_GB": 15, "OPPO_GB": 25}),
        (2022, 1, {"PULL_OFFB": 45, "CENTER_OFFB": 10, "OPPO_OFFB": 5, "PULL_GB": 15, "CENTER_GB": 10, "OPPO_GB": 5}),
        (2022, 2, {"PULL_OFFB": 5, "CENTER_OFFB": 20, "OPPO_OFFB": 25, "PULL_GB": 5, "CENTER_GB": 15, "OPPO_GB": 30}),
        (2023, 1, {"PULL_OFFB": 1, "CENTER_OFFB": 1, "OPPO_OFFB": 98}),
    )
    rows = []
    for season, player_id, values in profiles:
        for core_bin in HITTER_SHAPE_BINS:
            rows.append(
                {
                    "season": season,
                    "league_id": 103,
                    "player_id": player_id,
                    "level_group": "MLB",
                    "core_bin": core_bin,
                    "occurrence_count": values.get(core_bin, 1),
                }
            )
    return pl.DataFrame(rows)


HITTER_SHAPE_BINS = (
    "IFFB",
    "PULL_OFFB",
    "CENTER_OFFB",
    "OPPO_OFFB",
    "PULL_LD",
    "CENTER_LD",
    "OPPO_LD",
    "PULL_GB",
    "CENTER_GB",
    "OPPO_GB",
)


def _fit(mode: str, coefficients: dict[tuple[str, str], float]) -> Stage2cFit:
    return Stage2cFit(
        coefficients=pl.DataFrame(
            [
                {"contrast": contrast, "feature": feature, "coefficient": value}
                for (contrast, feature), value in coefficients.items()
            ]
        ),
        metrics={"shape_mode": mode, "zero_increment_fallback": False},
    )


def test_stage2c_features_are_chronology_safe_and_nested() -> None:
    history = _shape_history()
    before = build_stage2c_features(
        history.filter(pl.col("season") <= 2022),
        [1, 2, 999],
        predictor_cutoff_season=2022,
        mode=POWER_MODE,
    ).sort("player_id")
    with_future = build_stage2c_features(
        history,
        [1, 2, 999],
        predictor_cutoff_season=2022,
        mode=POWER_MODE,
    ).sort("player_id")

    assert before.equals(with_future)
    assert before["player_id"].to_list() == [1, 2]
    assert before["shape_feature_pull_offb_per_offb"][0] > 0.0
    assert before["shape_feature_pull_offb_per_offb"][1] < 0.0
    for name in ("offb_per_contact", "pull_offb_per_offb"):
        evidence = before[f"shape_evidence_{name}"]
        reliability = before[f"shape_reliability_{name}"]
        assert reliability.to_list() == pytest.approx(
            (evidence / (evidence + FIXED_PRIOR_EVENTS)).to_list()
        )


def test_zero_and_missing_stage2c_features_are_exact_fallbacks() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(999)]).sort("player_id")
    features = build_stage2c_features(
        _shape_history(), [1, 999], predictor_cutoff_season=2022, mode=POWER_MODE
    )
    adjusted = apply_stage2c_residual(
        base,
        features,
        zero_stage2c_fit(POWER_MODE),
        model_id="E1_NESTED_PULLED_OFFB_POWER",
    ).sort("player_id")

    for outcome in HITTER_TALENT_OUTCOMES:
        assert adjusted[f"p_{outcome}"].to_list() == base[f"p_{outcome}"].to_list()
    assert adjusted["shape_fallback_reason"].to_list() == [
        "zero_increment_no_prior_origin",
        "missing_shape_evidence",
    ]


def test_power_residual_changes_only_hr_and_xbh_contrasts() -> None:
    base = pl.DataFrame([_prediction(1)])
    features = build_stage2c_features(
        _shape_history(), [1], predictor_cutoff_season=2022, mode=POWER_MODE
    )
    fit = _fit(
        POWER_MODE,
        {
            ("hr_per_contact", "offb_per_contact"): 1.0,
            ("hr_per_contact", "pull_offb_per_offb"): 2.0,
            ("xbh_per_hit", "offb_per_contact"): 1.0,
            ("xbh_per_hit", "pull_offb_per_offb"): 2.0,
        },
    )
    adjusted = apply_stage2c_residual(
        base, features, fit, model_id="E1_NESTED_PULLED_OFFB_POWER"
    ).row(0, named=True)
    original = base.row(0, named=True)

    for outcome in ("K", "UBB", "HBP"):
        assert adjusted[f"p_{outcome}"] == pytest.approx(original[f"p_{outcome}"])
    assert adjusted["p_HR"] > original["p_HR"]
    old_triple_share = original["p_3B"] / (original["p_2B"] + original["p_3B"])
    new_triple_share = adjusted["p_3B"] / (adjusted["p_2B"] + adjusted["p_3B"])
    assert new_triple_share == pytest.approx(old_triple_share)
    assert sum(adjusted[f"p_{value}"] for value in HITTER_TALENT_OUTCOMES) == pytest.approx(1.0)


def test_ground_residual_cannot_change_hr_or_hit_mix() -> None:
    base = pl.DataFrame([_prediction(2)]).with_columns(
        pl.lit("E1_NESTED_PULLED_OFFB_POWER").alias("model_id")
    )
    features = build_stage2c_features(
        _shape_history(), [2], predictor_cutoff_season=2022, mode=GROUND_MODE
    )
    fit = _fit(
        GROUND_MODE,
        {
            ("reach_per_non_hr_contact", "gb_per_contact"): 1.0,
            ("reach_per_non_hr_contact", "oppo_gb_per_gb"): 2.0,
        },
    )
    adjusted = apply_stage2c_residual(
        base, features, fit, model_id="E2_SEPARATE_GROUND_DIRECTION"
    ).row(0, named=True)
    original = base.row(0, named=True)

    for outcome in ("K", "UBB", "HBP", "HR"):
        assert adjusted[f"p_{outcome}"] == pytest.approx(original[f"p_{outcome}"])
    old_hit_mix = [original[f"p_{value}"] / sum(original[f"p_{x}"] for x in ("1B", "2B", "3B")) for value in ("1B", "2B", "3B")]
    new_hit_mix = [adjusted[f"p_{value}"] / sum(adjusted[f"p_{x}"] for x in ("1B", "2B", "3B")) for value in ("1B", "2B", "3B")]
    assert new_hit_mix == pytest.approx(old_hit_mix)


def test_stage2c_fit_uses_explicit_prior_origin_only() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(2)])
    features = build_stage2c_features(
        _shape_history(), [1, 2], predictor_cutoff_season=2022, mode=POWER_MODE
    )
    targets = pl.DataFrame(
        [
            {"player_id": 1, "K": 2000, "UBB": 800, "HBP": 100, "HR": 900, "3B": 50, "2B": 700, "1B": 1200, "ROE": 150, "FC_REACH": 100, "SF": 250, "MULTI_OUT": 200, "OTHER_OUT": 3550},
            {"player_id": 2, "K": 2000, "UBB": 800, "HBP": 100, "HR": 100, "3B": 10, "2B": 200, "1B": 2100, "ROE": 150, "FC_REACH": 100, "SF": 250, "MULTI_OUT": 200, "OTHER_OUT": 3990},
        ]
    )
    fit = fit_stage2c_residual([(base, targets, features)], mode=POWER_MODE)

    assert fit.metrics["fit_origin_count"] == 1
    assert fit.metrics["zero_increment_fallback"] is False
    assert fit.coefficients.height == 4


def test_stage2c_does_not_accept_stage2b_fit_surface() -> None:
    with pytest.raises((AttributeError, KeyError, ValueError)):
        apply_stage2c_residual(
            pl.DataFrame([_prediction(1)]),
            build_stage2c_features(
                _shape_history(), [1], predictor_cutoff_season=2022, mode=POWER_MODE
            ),
            NodeOffsetFit(pl.DataFrame(), {"shape_mode": POWER_MODE}),  # type: ignore[arg-type]
            model_id="wrong",
        )


def test_ground_residual_rejects_non_e1_base() -> None:
    features = build_stage2c_features(
        _shape_history(), [2], predictor_cutoff_season=2022, mode=GROUND_MODE
    )
    with pytest.raises(ValueError, match="must be applied on E1"):
        apply_stage2c_residual(
            pl.DataFrame([_prediction(2)]),
            features,
            zero_stage2c_fit(GROUND_MODE),
            model_id="E2_SEPARATE_GROUND_DIRECTION",
        )
