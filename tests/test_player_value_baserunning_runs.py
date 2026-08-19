from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_baserunning_runs import (
    build_baserunning_reference,
    project_advancement_runs,
    project_baserunning_runs,
    project_steal_runs,
)


@pytest.fixture
def reference():
    return build_baserunning_reference(
        season=2024,
        plate_appearances=182449,
        runs=21343,
        outs=129349,
        steal_opportunity_proxy=42342,
        steal_attempts=4578,
        stolen_bases=3617,
        advancement_opportunities=12931,
    )


def test_2024_reference_constants(reference) -> None:
    assert reference.runs_per_out == pytest.approx(0.16500320837424332)
    assert reference.run_value_stolen_base == 0.2
    assert reference.run_value_caught_stealing == pytest.approx(
        -0.40500641674848664
    )
    assert reference.steal_opportunities_per_pa == pytest.approx(
        0.2320758129669113
    )
    assert reference.steal_attempt_rate == pytest.approx(0.1081195975627037)
    assert reference.steal_success_probability == pytest.approx(
        0.790083005679336
    )
    assert reference.league_steal_runs_per_opportunity == pytest.approx(
        0.007892608603861519
    )
    assert reference.advancement_opportunities_per_pa == pytest.approx(
        0.0708746005733109
    )


def test_neutral_steal_player_is_zero_runs(reference) -> None:
    _, _, _, _, runs = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.0,
        success_logodds_residual=0.0,
        reference=reference,
    )
    assert runs == pytest.approx(0.0, abs=1e-12)


def test_more_attempts_help_at_reference_success_rate(reference) -> None:
    neutral = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.0,
        success_logodds_residual=0.0,
        reference=reference,
    )[-1]
    aggressive = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.5,
        success_logodds_residual=0.0,
        reference=reference,
    )[-1]
    assert aggressive > neutral


def test_more_attempts_hurt_when_success_probability_is_bad(reference) -> None:
    # A large negative log-odds residual puts the runner well below the
    # break-even success rate implied by the frozen run values.
    conservative = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=0.5,
        success_logodds_residual=-2.0,
        reference=reference,
    )[-1]
    aggressive = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.5,
        success_logodds_residual=-2.0,
        reference=reference,
    )[-1]
    assert aggressive < conservative


def test_positive_success_residual_improves_steal_runs(reference) -> None:
    baseline = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.0,
        success_logodds_residual=0.0,
        reference=reference,
    )[-1]
    better = project_steal_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.0,
        success_logodds_residual=0.5,
        reference=reference,
    )[-1]
    assert better > baseline


def test_advancement_uses_only_common_reference_exposure(reference) -> None:
    opportunities, runs = project_advancement_runs(
        projected_mlb_pa=600,
        advancement_rate=0.04,
        reference=reference,
    )
    assert opportunities == pytest.approx(
        600 * reference.advancement_opportunities_per_pa
    )
    assert runs == pytest.approx(opportunities * 0.04)


def test_zero_projected_pa_zeroes_every_baserunning_run(reference) -> None:
    projection = project_baserunning_runs(
        projected_mlb_pa=0,
        attempt_multiplier=4.0,
        success_logodds_residual=2.0,
        advancement_rate=0.2,
        reference=reference,
    )
    assert projection.steal_runs == pytest.approx(0.0)
    assert projection.advancement_runs == pytest.approx(0.0)
    assert projection.gidp_residual_runs == 0.0
    assert projection.baserunning_runs == pytest.approx(0.0)


def test_gidp_residual_is_explicitly_zero_in_v1(reference) -> None:
    projection = project_baserunning_runs(
        projected_mlb_pa=600,
        attempt_multiplier=1.2,
        success_logodds_residual=0.2,
        advancement_rate=0.03,
        reference=reference,
    )
    assert projection.gidp_residual_runs == 0.0
    assert projection.baserunning_runs == pytest.approx(
        projection.steal_runs + projection.advancement_runs
    )


def test_reference_rejects_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="stolen_bases"):
        build_baserunning_reference(
            season=2024,
            plate_appearances=100,
            runs=10,
            outs=50,
            steal_opportunity_proxy=20,
            steal_attempts=5,
            stolen_bases=6,
            advancement_opportunities=10,
        )

    with pytest.raises(ValueError, match="steal_attempts"):
        build_baserunning_reference(
            season=2024,
            plate_appearances=100,
            runs=10,
            outs=50,
            steal_opportunity_proxy=4,
            steal_attempts=5,
            stolen_bases=4,
            advancement_opportunities=10,
        )


def test_projection_rejects_nonfinite_skill_inputs(reference) -> None:
    with pytest.raises(ValueError, match="success_logodds_residual"):
        project_steal_runs(
            projected_mlb_pa=600,
            attempt_multiplier=1.0,
            success_logodds_residual=math.nan,
            reference=reference,
        )
    with pytest.raises(ValueError, match="advancement_rate"):
        project_advancement_runs(
            projected_mlb_pa=600,
            advancement_rate=math.inf,
            reference=reference,
        )
