from __future__ import annotations

import pytest

from universal_baseball.bin_value_pooling import (
    evaluate_split_half_pooling,
    shrink_mean,
)


def _environment(
    season: int,
    league_id: int,
    league_name: str,
    *,
    candidate_mean: float,
    candidate_n: int,
    reference_mean: float,
    reference_n: int,
) -> dict:
    return {
        "season": season,
        "league_id": league_id,
        "league_name": league_name,
        "split_half": {
            "comparison": {
                "deltas": {
                    "BB_HBP": {
                        "candidate": {
                            "mean": candidate_mean,
                            "n": candidate_n,
                            "se": 0.05,
                        },
                        "reference": {
                            "mean": reference_mean,
                            "n": reference_n,
                            "se": 0.05,
                        },
                        "delta": candidate_mean - reference_mean,
                    }
                }
            }
        },
    }


def test_shrink_mean_uses_prior_equivalent_counts() -> None:
    assert shrink_mean(0.4, 100, 0.2, 100) == pytest.approx(0.3)
    assert shrink_mean(0.4, 100, 0.2, 0) == pytest.approx(0.4)


def test_group_prior_excludes_target_environment_and_reference_halves() -> None:
    reports = [
        _environment(
            2025,
            112,
            "PCL",
            candidate_mean=0.40,
            candidate_n=100,
            reference_mean=9.99,
            reference_n=80,
        ),
        _environment(
            2025,
            117,
            "IL",
            candidate_mean=0.20,
            candidate_n=50,
            reference_mean=-9.99,
            reference_n=70,
        ),
    ]

    result = evaluate_split_half_pooling(
        reports,
        pool_group_by_league={112: "AAA", 117: "AAA"},
        prior_strengths=[0, 100],
        scope="group",
    )
    pooled = [
        row
        for row in result["predictions"]
        if row["prior_strength"] == 100
    ]
    pcl = next(row for row in pooled if row["league_id"] == 112)
    il = next(row for row in pooled if row["league_id"] == 117)

    assert pcl["prior_mean"] == pytest.approx(0.20)
    assert pcl["prior_candidate_count"] == 50
    assert pcl["prior_environment_count"] == 1
    assert pcl["prediction"] == pytest.approx(0.30)

    assert il["prior_mean"] == pytest.approx(0.40)
    assert il["prior_candidate_count"] == 100
    assert il["prediction"] == pytest.approx((0.20 * 50 + 0.40 * 100) / 150)


def test_group_pooling_requires_at_least_two_environments_per_group() -> None:
    reports = [
        _environment(
            2025,
            112,
            "PCL",
            candidate_mean=0.4,
            candidate_n=100,
            reference_mean=0.5,
            reference_n=100,
        )
    ]

    with pytest.raises(ValueError, match="at least two environments"):
        evaluate_split_half_pooling(
            reports,
            pool_group_by_league={112: "AAA"},
            prior_strengths=[0, 25],
            scope="group",
        )


def test_all_scope_can_pool_across_explicit_groups() -> None:
    reports = [
        _environment(
            2025,
            112,
            "PCL",
            candidate_mean=0.40,
            candidate_n=100,
            reference_mean=0.45,
            reference_n=80,
        ),
        _environment(
            2024,
            121,
            "ACL",
            candidate_mean=0.10,
            candidate_n=50,
            reference_mean=0.15,
            reference_n=60,
        ),
    ]

    result = evaluate_split_half_pooling(
        reports,
        pool_group_by_league={112: "AAA", 121: "ROOKIE"},
        prior_strengths=[0, 50],
        scope="all",
    )
    pooled = [
        row
        for row in result["predictions"]
        if row["prior_strength"] == 50
    ]
    aaa = next(row for row in pooled if row["league_id"] == 112)
    rookie = next(row for row in pooled if row["league_id"] == 121)

    assert aaa["prior_mean"] == pytest.approx(0.10)
    assert rookie["prior_mean"] == pytest.approx(0.40)


def test_best_strength_is_reported_separately_by_pool_group() -> None:
    reports = [
        _environment(
            2025,
            112,
            "PCL",
            candidate_mean=0.50,
            candidate_n=20,
            reference_mean=0.35,
            reference_n=20,
        ),
        _environment(
            2025,
            117,
            "IL",
            candidate_mean=0.20,
            candidate_n=20,
            reference_mean=0.30,
            reference_n=20,
        ),
        _environment(
            2024,
            121,
            "ACL",
            candidate_mean=0.40,
            candidate_n=20,
            reference_mean=0.40,
            reference_n=20,
        ),
        _environment(
            2024,
            124,
            "FCL",
            candidate_mean=0.10,
            candidate_n=20,
            reference_mean=0.10,
            reference_n=20,
        ),
    ]

    result = evaluate_split_half_pooling(
        reports,
        pool_group_by_league={
            112: "AAA",
            117: "AAA",
            121: "ROOKIE",
            124: "ROOKIE",
        },
        prior_strengths=[0, 20],
        scope="group",
    )

    assert set(result["best_strength_by_group"]) == {"AAA", "ROOKIE"}
    assert result["best_strength_by_group"]["ROOKIE"]["mae"]["prior_strength"] == 0
