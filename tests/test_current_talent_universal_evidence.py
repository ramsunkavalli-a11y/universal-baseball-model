import polars as pl
import pytest

from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)


def _summary(league_id: int, level: str, game_pk: int, player_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "game_date": ["2024-04-10"],
            "game_pk": [game_pk],
            "league_id": [league_id],
            "player_id": [player_id],
            "level_group": [level],
            "batting_plate_appearances": [4],
            "expected_contact_count": [2],
            "observed_contact_count": [2],
            "contact_count_residual": [0],
            "core_profile_event_count": [3],
            "bunt_contact_count": [0],
            "foul_air_excluded_count": [0],
            "unknown_contact_count": [1],
            "special_noncontact_count": [0],
            "pa_accounting_residual": [0],
            "participant_authority_status": [
                "source_default" if level != "MLB" else "savant_official"
            ],
            "source_capability_tier": [
                "universal_result_contact_profile_v2"
                if level != "MLB"
                else "mlb_savant_result_contact_profile_v2"
            ],
        }
    )


def _profile(league_id: int, level: str, game_pk: int, player_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024],
            "game_date": ["2024-04-10", "2024-04-10"],
            "game_pk": [game_pk, game_pk],
            "league_id": [league_id, league_id],
            "player_id": [player_id, player_id],
            "level_group": [level, level],
            "core_bin": ["K", "PULL_GB"],
            "occurrence_count": [2, 1],
        }
    )


def test_universal_evidence_combines_mlb_and_milb_without_translation() -> None:
    summary, profile, metrics = combine_universal_player_game_evidence(
        [_summary(117, "AAA", 1, 10), _summary(103, "MLB", 2, 20)],
        [_profile(117, "AAA", 1, 10), _profile(103, "MLB", 2, 20)],
        expected_seasons={2024},
    )
    assert summary.height == 2
    assert profile.height == 4
    assert metrics["actual_league_count"] == 2
    assert metrics["level_groups"] == ["AAA", "MLB"]
    assert metrics["total_expected_contacts"] == 4
    assert metrics["total_observed_contacts"] == 4
    assert metrics["total_unknown_contacts"] == 2
    assert set(summary.get_column("league_id").to_list()) == {117, 103}


def test_universal_evidence_rejects_wrong_level_label() -> None:
    with pytest.raises(ValueError, match="league/level context mismatch"):
        combine_universal_player_game_evidence(
            [_summary(117, "AA", 1, 10)],
            [_profile(117, "AA", 1, 10)],
        )


def test_universal_evidence_can_require_full_league_coverage() -> None:
    with pytest.raises(ValueError, match="league coverage mismatch"):
        combine_universal_player_game_evidence(
            [_summary(117, "AAA", 1, 10)],
            [_profile(117, "AAA", 1, 10)],
            require_all_universal_leagues=True,
        )


def test_universal_evidence_rejects_unexpected_season() -> None:
    with pytest.raises(ValueError, match="season coverage mismatch"):
        combine_universal_player_game_evidence(
            [_summary(117, "AAA", 1, 10)],
            [_profile(117, "AAA", 1, 10)],
            expected_seasons={2023},
        )
