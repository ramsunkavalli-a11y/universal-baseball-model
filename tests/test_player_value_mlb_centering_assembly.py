from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_mlb_centering import (
    build_fixed_mlb_centering_reference,
)
from universal_baseball.player_value_mlb_centering_assembly import (
    FixedMLBReferenceMember,
    OfficialMLBReferenceCandidate,
    PlayingTimeReferenceCandidate,
    assemble_fixed_mlb_reference_components,
    reconcile_fixed_2024_mlb_reference_members,
    select_fixed_2024_mlb_reference_members,
    summarize_fixed_mlb_reference_membership,
)


def _playing_time_rows() -> list[PlayingTimeReferenceCandidate]:
    return [
        PlayingTimeReferenceCandidate(3, 0.0, 125.0),
        PlayingTimeReferenceCandidate(2, 300.0, 280.0),
        PlayingTimeReferenceCandidate(1, 500.0, 480.0),
    ]


def test_membership_uses_observed_pa_only_as_positive_cohort_predicate() -> None:
    members = select_fixed_2024_mlb_reference_members(
        _playing_time_rows(),
        expected_player_count=2,
    )
    assert members == (
        FixedMLBReferenceMember(1, 480.0),
        FixedMLBReferenceMember(2, 280.0),
    )
    summary = summarize_fixed_mlb_reference_membership(members)
    assert summary.reference_season == 2024
    assert summary.reference_player_count == 2
    assert summary.aggregate_projected_mlb_pa == pytest.approx(760.0)


def test_official_membership_reconciliation_ignores_pa_accounting_difference() -> None:
    official = [
        OfficialMLBReferenceCandidate(1, 510.0),
        OfficialMLBReferenceCandidate(2, 305.0),
        OfficialMLBReferenceCandidate(3, 0.0),
    ]
    members = reconcile_fixed_2024_mlb_reference_members(
        _playing_time_rows(),
        official,
        expected_player_count=2,
    )
    assert members == (
        FixedMLBReferenceMember(1, 480.0),
        FixedMLBReferenceMember(2, 280.0),
    )


def test_official_membership_can_include_playing_time_zero_observed_pa_row() -> None:
    official = [
        OfficialMLBReferenceCandidate(1, 510.0),
        OfficialMLBReferenceCandidate(3, 5.0),
    ]
    members = reconcile_fixed_2024_mlb_reference_members(
        _playing_time_rows(),
        official,
        expected_player_count=2,
    )
    assert members == (
        FixedMLBReferenceMember(1, 480.0),
        FixedMLBReferenceMember(3, 125.0),
    )


def test_official_member_missing_playing_time_exposure_fails_closed() -> None:
    official = [
        OfficialMLBReferenceCandidate(1, 510.0),
        OfficialMLBReferenceCandidate(4, 5.0),
    ]
    with pytest.raises(ValueError, match="missing Playing Time projected-PA rows"):
        reconcile_fixed_2024_mlb_reference_members(
            _playing_time_rows(),
            official,
            expected_player_count=2,
        )


def test_official_membership_count_is_fail_closed() -> None:
    official = [OfficialMLBReferenceCandidate(1, 510.0)]
    with pytest.raises(ValueError, match="official 2024 MLB positive-PA cohort count mismatch"):
        reconcile_fixed_2024_mlb_reference_members(
            _playing_time_rows(),
            official,
            expected_player_count=2,
        )


def test_membership_count_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="cohort count mismatch"):
        select_fixed_2024_mlb_reference_members(
            _playing_time_rows(),
            expected_player_count=3,
        )


def test_duplicate_playing_time_player_is_rejected_even_outside_cohort() -> None:
    rows = _playing_time_rows() + [PlayingTimeReferenceCandidate(3, 0.0, 50.0)]
    with pytest.raises(ValueError, match="duplicate Playing Time player_id"):
        select_fixed_2024_mlb_reference_members(rows, expected_player_count=2)


def test_duplicate_official_player_is_rejected() -> None:
    official = [
        OfficialMLBReferenceCandidate(1, 500.0),
        OfficialMLBReferenceCandidate(1, 10.0),
    ]
    with pytest.raises(ValueError, match="duplicate official MLB player_id"):
        reconcile_fixed_2024_mlb_reference_members(
            _playing_time_rows(),
            official,
            expected_player_count=1,
        )


@pytest.mark.parametrize(
    ("observed_pa", "projected_pa"),
    [
        (-1.0, 100.0),
        (1.0, -1.0),
        (math.nan, 100.0),
        (1.0, math.inf),
    ],
)
def test_invalid_playing_time_values_are_rejected(
    observed_pa: float,
    projected_pa: float,
) -> None:
    rows = [PlayingTimeReferenceCandidate(1, observed_pa, projected_pa)]
    with pytest.raises(ValueError):
        select_fixed_2024_mlb_reference_members(rows, expected_player_count=1)


def test_component_assembly_requires_explicit_coverage_for_every_member() -> None:
    members = select_fixed_2024_mlb_reference_members(
        _playing_time_rows(),
        expected_player_count=2,
    )
    assembled = assemble_fixed_mlb_reference_components(
        members,
        batting_runs_by_player={1: 8.0, 2: -3.0, 99: 100.0},
        baserunning_runs_by_player={1: 1.0, 2: 0.0},
        defense_runs_by_player={1: -2.0, 2: 2.0},
        positional_runs_by_player={1: -4.0, 2: -1.0},
    )
    assert [row.player_id for row in assembled] == [1, 2]
    result = build_fixed_mlb_centering_reference(assembled)
    assert result.reference_player_count == 2
    assert result.aggregate_projected_mlb_pa == pytest.approx(760.0)
    assert abs(result.post_centering_residual_runs) <= result.tolerance_runs


def test_missing_component_is_rejected_instead_of_dropping_player() -> None:
    members = select_fixed_2024_mlb_reference_members(
        _playing_time_rows(),
        expected_player_count=2,
    )
    with pytest.raises(ValueError, match="missing component rows: defense_runs"):
        assemble_fixed_mlb_reference_components(
            members,
            batting_runs_by_player={1: 0.0, 2: 0.0},
            baserunning_runs_by_player={1: 0.0, 2: 0.0},
            defense_runs_by_player={1: 0.0},
            positional_runs_by_player={1: 0.0, 2: 0.0},
        )


def test_explicit_neutral_fallback_is_valid_component_evidence() -> None:
    member = (FixedMLBReferenceMember(1, 200.0),)
    assembled = assemble_fixed_mlb_reference_components(
        member,
        batting_runs_by_player={1: 0.0},
        baserunning_runs_by_player={1: 0.0},
        defense_runs_by_player={1: 0.0},
        positional_runs_by_player={1: 0.0},
    )
    assert assembled[0].batting_runs == 0.0
    assert assembled[0].baserunning_runs == 0.0
    assert assembled[0].defense_runs == 0.0
    assert assembled[0].positional_runs == 0.0


def test_nonfinite_component_is_rejected() -> None:
    member = (FixedMLBReferenceMember(1, 200.0),)
    with pytest.raises(ValueError, match="batting_runs\\[1\\] must be finite"):
        assemble_fixed_mlb_reference_components(
            member,
            batting_runs_by_player={1: math.nan},
            baserunning_runs_by_player={1: 0.0},
            defense_runs_by_player={1: 0.0},
            positional_runs_by_player={1: 0.0},
        )
