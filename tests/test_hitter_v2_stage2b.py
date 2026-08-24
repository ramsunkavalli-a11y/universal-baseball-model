import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b import (
    NodeOffsetFit,
    apply_node_calibration,
    apply_shape_residual,
    assemble_nested_probabilities,
    build_shape_features,
    fit_node_calibration,
    identity_node_calibration,
    nested_conditionals,
    zero_shape_residual,
)


def _probabilities(**updates: float) -> dict[str, float]:
    values = {
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
    values.update(updates)
    assert sum(values.values()) == pytest.approx(1.0)
    return values


def _prediction(player_id: int, **updates: float) -> dict[str, object]:
    probabilities = _probabilities(**updates)
    return {
        "player_id": player_id,
        "model_id": "C0_NESTED_EB",
        **{f"p_{outcome}": probabilities[outcome] for outcome in HITTER_TALENT_OUTCOMES},
    }


def _target(player_id: int, probabilities: dict[str, float], pa: int) -> dict[str, int]:
    counts = {
        outcome: int(round(probabilities[outcome] * pa))
        for outcome in HITTER_TALENT_OUTCOMES
    }
    counts["OTHER_OUT"] += pa - sum(counts.values())
    return {"player_id": player_id, **counts}


def _shape_history() -> pl.DataFrame:
    rows = []
    for season, player_id, league_id, level, counts in (
        (2021, 1, 103, "MLB", {"IFFB": 10, "PULL_OFFB": 30, "PULL_LD": 20, "PULL_GB": 40}),
        (2022, 1, 103, "MLB", {"IFFB": 5, "PULL_OFFB": 20, "PULL_LD": 35, "PULL_GB": 40}),
        (2022, 2, 103, "MLB", {"IFFB": 15, "PULL_OFFB": 25, "PULL_LD": 25, "PULL_GB": 35}),
        (2023, 1, 103, "MLB", {"IFFB": 1, "PULL_OFFB": 1, "PULL_LD": 90, "PULL_GB": 8}),
    ):
        expanded = {core_bin: 0 for core_bin in (
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
        )}
        expanded.update(counts)
        for core_bin, occurrence_count in expanded.items():
            # Positive context support for every frozen group is required.
            rows.append(
                {
                    "season": season,
                    "league_id": league_id,
                    "player_id": player_id,
                    "level_group": level,
                    "core_bin": core_bin,
                    "occurrence_count": max(occurrence_count, 1),
                }
            )
    return pl.DataFrame(rows)


def test_nested_decomposition_round_trip_is_coherent() -> None:
    probabilities = _probabilities()
    rebuilt = assemble_nested_probabilities(nested_conditionals(probabilities))

    assert rebuilt == pytest.approx(probabilities, abs=1e-12)
    assert sum(rebuilt.values()) == pytest.approx(1.0)


def test_identity_calibration_is_exact_passthrough() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(2)])
    adjusted = apply_node_calibration(base, identity_node_calibration())

    for outcome in HITTER_TALENT_OUTCOMES:
        assert adjusted[f"p_{outcome}"].to_list() == base[f"p_{outcome}"].to_list()
    assert adjusted["calibration_identity_fallback"].to_list() == [True, True]


def test_node_calibration_learns_only_from_prior_origin() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(2)])
    truth = _probabilities(K=0.17, UBB=0.10, HR=0.07)
    targets = pl.DataFrame([_target(1, truth, 20_000), _target(2, truth, 20_000)])

    fit = fit_node_calibration([(base, targets)])
    adjusted = apply_node_calibration(base, fit)

    assert fit.metrics["fit_origin_count"] == 1
    assert adjusted["p_K"][0] < base["p_K"][0]
    assert adjusted["p_HR"][0] > base["p_HR"][0]
    for row in adjusted.iter_rows(named=True):
        assert sum(row[f"p_{outcome}"] for outcome in HITTER_TALENT_OUTCOMES) == pytest.approx(1.0)


def test_shape_features_are_chronology_safe_reliable_and_population_complete() -> None:
    history = _shape_history()
    before = build_shape_features(
        history.filter(pl.col("season") <= 2022),
        [1, 2, 999],
        predictor_cutoff_season=2022,
        mode="trajectory",
    ).sort("player_id")
    with_future_rows = build_shape_features(
        history,
        [1, 2, 999],
        predictor_cutoff_season=2022,
        mode="trajectory",
    ).sort("player_id")

    assert before.equals(with_future_rows)
    assert before["player_id"].to_list() == [1, 2]
    assert before["shape_reliability"].min() > 0.0
    assert before["shape_reliability"].max() < 1.0
    assert before["shape_latest_season"].to_list() == [2022, 2022]


def test_zero_shape_residual_and_missing_shape_are_exact_base_fallbacks() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(999)])
    features = build_shape_features(
        _shape_history(),
        [1, 999],
        predictor_cutoff_season=2022,
        mode="trajectory",
    )
    adjusted = apply_shape_residual(
        base,
        features,
        zero_shape_residual("trajectory"),
        model_id="D1_TRAJECTORY_RESIDUAL",
    ).sort("player_id")

    for outcome in HITTER_TALENT_OUTCOMES:
        assert adjusted[f"p_{outcome}"].to_list() == base.sort("player_id")[f"p_{outcome}"].to_list()
    missing = adjusted.filter(pl.col("player_id") == 999).row(0, named=True)
    assert missing["shape_reliability"] == 0.0
    assert missing["shape_fallback_reason"] == "missing_shape_evidence"


def test_shape_residual_cannot_change_k_ubb_or_hbp_branches() -> None:
    base = pl.DataFrame([_prediction(1), _prediction(999)])
    features = build_shape_features(
        _shape_history(),
        [1, 999],
        predictor_cutoff_season=2022,
        mode="trajectory",
    )
    coefficients = zero_shape_residual("trajectory").coefficients.with_columns(
        pl.when(
            (pl.col("node") == "contact")
            & (pl.col("child") == "HR")
            & (pl.col("feature") == "LD")
        )
        .then(4.0)
        .otherwise(pl.col("coefficient"))
        .alias("coefficient")
    )
    fit = NodeOffsetFit(
        coefficients=coefficients,
        metrics={"shape_mode": "trajectory", "zero_residual_fallback": False},
    )
    adjusted = apply_shape_residual(
        base,
        features,
        fit,
        model_id="D1_TRAJECTORY_RESIDUAL",
    ).sort("player_id")

    supported = adjusted.filter(pl.col("player_id") == 1).row(0, named=True)
    original = base.filter(pl.col("player_id") == 1).row(0, named=True)
    assert supported["p_K"] == pytest.approx(original["p_K"], abs=1e-12)
    assert supported["p_UBB"] == pytest.approx(original["p_UBB"], abs=1e-12)
    assert supported["p_HBP"] == pytest.approx(original["p_HBP"], abs=1e-12)
    assert supported["p_HR"] != pytest.approx(original["p_HR"])
    missing = adjusted.filter(pl.col("player_id") == 999).row(0, named=True)
    for outcome in HITTER_TALENT_OUTCOMES:
        assert missing[f"p_{outcome}"] == original[f"p_{outcome}"]
