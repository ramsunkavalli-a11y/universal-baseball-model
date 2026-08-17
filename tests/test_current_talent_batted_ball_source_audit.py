from datetime import date

import polars as pl
import pytest

from scripts.audit_current_talent_batted_ball_source_semantics import (
    build_source_semantics_report,
)


def _raw() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "game_date": "2022-06-01",
                "game_pk": "1",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "2",
                "events": None,
                "type": "S",
                "des": "Batter hits a foul ball.",
                "description": "foul",
                "launch_speed": "72.0",
                "launch_angle": "-10.0",
            },
            {
                "game_date": "2022-06-01",
                "game_pk": "1",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "4",
                "events": "single",
                "type": "X",
                "des": "Batter singles on a line drive to center field.",
                "description": "hit_into_play",
                "launch_speed": "100.0",
                "launch_angle": "20.0",
            },
            {
                "game_date": "2022-06-02",
                "game_pk": "2",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "3",
                "events": "sac_bunt",
                "type": "X",
                "des": "Batter out on a sacrifice bunt, pitcher to first baseman.",
                "description": "hit_into_play",
                "launch_speed": "40.0",
                "launch_angle": "-30.0",
            },
            {
                "game_date": "2022-07-01",
                "game_pk": "3",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "1",
                "events": "double",
                "type": "X",
                "des": "Batter doubles on a line drive.",
                "description": "hit_into_play",
                "launch_speed": "105.0",
                "launch_angle": "18.0",
            },
        ]
    )


def test_source_audit_separates_fouls_bunts_and_model_bbe() -> None:
    report = build_source_semantics_report(_raw(), cutoff=date(2022, 7, 1))

    assert report["raw_pre_cutoff_rows"] == 3
    assert report["complete_ev_la_contact_rows"] == 3
    assert report["complete_ev_la_foul_rows"] == 1
    assert report["complete_result_bbe_before_bunt_exclusion"] == 2
    assert report["complete_result_bunts_excluded"] == 1
    assert report["canonical_result_non_bunt_bbe"] == 1
    assert report["player_with_pre_cutoff_bbe_count"] == 1
    assert report["player_ge20_bbe_count"] == 0
    assert report["model_scoring_performed"] is False
    assert report["residual_coefficients_fit"] is False


def test_source_audit_uses_same_20_bbe_eligibility_rule() -> None:
    rows = []
    for day in range(1, 21):
        rows.append(
            {
                "game_date": f"2022-06-{day:02d}",
                "game_pk": str(day),
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "1",
                "events": "single",
                "type": "X",
                "des": "Batter singles on a line drive.",
                "description": "hit_into_play",
                "launch_speed": "95.0",
                "launch_angle": "20.0",
            }
        )

    report = build_source_semantics_report(pl.DataFrame(rows), cutoff=date(2022, 7, 1))

    assert report["canonical_result_non_bunt_bbe"] == 20
    assert report["player_ge20_bbe_count"] == 1
    assert report["eligible_median_raw_complete_tracked_bbe"] == pytest.approx(20.0)
    assert report["eligible_mean_weighted_exit_velocity"] == pytest.approx(95.0)
    assert report["eligible_mean_weighted_sweet_spot_share"] == pytest.approx(1.0)
