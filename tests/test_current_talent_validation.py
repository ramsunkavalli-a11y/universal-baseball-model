from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.current_talent_validation import (
    COMPLETE_GAME_AGGREGATE_CAP_POLICY,
    PRIMARY_FUTURE_HORIZON,
    add_cutoff_membership,
    build_future_target_window,
    cap_future_pa_for_aggregate_metrics,
    cap_future_player_games_for_aggregate_metrics,
    future_window,
    in_season_snapshot_dates,
)


def _future_summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024, 2024, 2024, 2024],
            "game_date": [
                "2024-04-30",
                "2024-05-01",
                "2024-05-15",
                "2024-06-01",
                "2024-06-15",
                "2024-07-30",
                "2024-05-02",
            ],
            "game_pk": [99, 100, 101, 102, 103, 104, 200],
            "league_id": [117, 117, 117, 1, 1, 1, 109],
            "player_id": [1, 1, 1, 1, 1, 1, 2],
            "level_group": ["AAA", "AAA", "AAA", "MLB", "MLB", "MLB", "AA"],
            "batting_plate_appearances": [4, 100, 98, 5, 4, 4, 6],
            "expected_contact_count": [2, 60, 60, 3, 2, 2, 4],
            "observed_contact_count": [2, 60, 60, 3, 2, 2, 4],
            "contact_count_residual": [0, 0, 0, 0, 0, 0, 0],
            "core_profile_event_count": [4, 100, 98, 5, 4, 4, 6],
            "bunt_contact_count": [0, 0, 0, 0, 0, 0, 0],
            "foul_air_excluded_count": [0, 0, 0, 0, 0, 0, 0],
            "unknown_contact_count": [0, 0, 0, 0, 0, 0, 0],
            "special_noncontact_count": [0, 0, 0, 0, 0, 0, 0],
            "pa_accounting_residual": [0, 0, 0, 0, 0, 0, 0],
            "participant_authority_status": ["source_default"] * 7,
            "source_capability_tier": ["test_result_profile"] * 7,
        }
    )


def _future_profile() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    games = [
        # game_pk, date, league, player, level, K, BB/HBP, core contact
        (99, "2024-04-30", 117, 1, "AAA", 1, 1, 2),
        (100, "2024-05-01", 117, 1, "AAA", 20, 20, 60),
        (101, "2024-05-15", 117, 1, "AAA", 18, 20, 60),
        (102, "2024-06-01", 1, 1, "MLB", 1, 1, 3),
        (103, "2024-06-15", 1, 1, "MLB", 1, 1, 2),
        (104, "2024-07-30", 1, 1, "MLB", 1, 1, 2),
        (200, "2024-05-02", 109, 2, "AA", 1, 1, 4),
    ]
    for game_pk, game_date, league_id, player_id, level_group, k, bb, contact in games:
        for core_bin, count in (("K", k), ("BB_HBP", bb), ("PULL_GB", contact)):
            rows.append(
                {
                    "season": 2024,
                    "game_date": game_date,
                    "game_pk": game_pk,
                    "league_id": league_id,
                    "player_id": player_id,
                    "level_group": level_group,
                    "core_bin": core_bin,
                    "occurrence_count": count,
                }
            )
    return pl.DataFrame(rows)


def test_month_start_snapshots_and_primary_window() -> None:
    assert in_season_snapshot_dates(2024) == (
        date(2024, 5, 1),
        date(2024, 6, 1),
        date(2024, 7, 1),
        date(2024, 8, 1),
        date(2024, 9, 1),
    )
    assert future_window(date(2024, 5, 1), PRIMARY_FUTURE_HORIZON) == (
        date(2024, 5, 1),
        date(2024, 7, 30),
    )


def test_cutoff_membership_has_no_same_day_leakage() -> None:
    frame = pl.DataFrame(
        {
            "game_date": ["2024-04-30", "2024-05-01", "2024-07-29", "2024-07-30"],
            "row": [1, 2, 3, 4],
        }
    )
    result = add_cutoff_membership(frame, cutoff=date(2024, 5, 1))
    rows = {row["row"]: row for row in result.to_dicts()}
    assert rows[1]["is_predictor_evidence"] is True
    assert rows[1]["is_future_target_evidence"] is False
    assert rows[2]["is_predictor_evidence"] is False
    assert rows[2]["is_future_target_evidence"] is True
    assert rows[3]["is_future_target_evidence"] is True
    assert rows[4]["is_future_target_evidence"] is False
    assert rows[4]["is_outside_validation_window"] is True


def test_player_game_future_window_preserves_uncapped_actual_environment_evidence() -> None:
    summary, profile, metrics = build_future_target_window(
        _future_summary(),
        _future_profile(),
        cutoff=date(2024, 5, 1),
    )

    # April 30 is predictor evidence and July 30 is the exclusive 90-day end.
    assert set(summary.get_column("game_pk").to_list()) == {100, 101, 102, 103, 200}
    assert metrics["future_plate_appearances"] == 213
    assert metrics["future_player_game_count"] == 5
    assert metrics["future_player_count"] == 2
    assert metrics["future_actual_league_count"] == 3
    assert metrics["future_level_count"] == 3
    assert metrics["future_window_end"] == "2024-07-30"
    assert metrics["likelihood_surface"] == "all_realized_future_player_game_evidence_uncapped"

    player1 = summary.filter(pl.col("player_id") == 1)
    assert set(player1.get_column("level_group").to_list()) == {"AAA", "MLB"}
    assert player1.filter(pl.col("game_pk") == 100).get_column("days_after_cutoff").item() == 0
    assert profile.get_column("occurrence_count").sum() == summary.get_column(
        "core_profile_event_count"
    ).sum()


def test_complete_game_aggregate_cap_never_splits_outcome_vectors() -> None:
    future_summary, future_profile, _ = build_future_target_window(
        _future_summary(),
        _future_profile(),
        cutoff=date(2024, 5, 1),
    )
    capped_summary, capped_profile, metrics = cap_future_player_games_for_aggregate_metrics(
        future_summary,
        future_profile,
        cap=200,
    )

    # Player 1 reaches 198 PA after the first two games. The next complete game
    # would push the total to 203, so it and every later game are excluded.
    player1 = capped_summary.filter(pl.col("player_id") == 1)
    assert player1.get_column("game_pk").to_list() == [100, 101]
    assert player1.get_column("batting_plate_appearances").sum() == 198
    assert capped_profile.filter(pl.col("player_id") == 1).get_column("occurrence_count").sum() == 198

    # Player 2 remains fully represented because its realized future PA is below cap.
    assert capped_summary.filter(pl.col("player_id") == 2).get_column(
        "batting_plate_appearances"
    ).sum() == 6
    assert metrics["aggregate_cap_policy"] == COMPLETE_GAME_AGGREGATE_CAP_POLICY
    assert metrics["uncapped_plate_appearances"] == 213
    assert metrics["capped_plate_appearances"] == 204
    assert metrics["player_window_over_cap_count"] == 1
    assert metrics["complete_game_cap_shortfall_pa"] == 2


def test_future_pa_cap_is_chronological_and_per_player() -> None:
    rows = []
    for player_id in (1, 2):
        for index in range(4):
            rows.append(
                {
                    "player_id": player_id,
                    "game_date": f"2024-05-{4-index:02d}",
                    "game_pk": 100 + (4 - index),
                    "at_bat_index": index,
                    "token": f"{player_id}-{index}",
                }
            )
    capped = cap_future_pa_for_aggregate_metrics(pl.DataFrame(rows), cap=2)
    assert capped.group_by("player_id").len().sort("player_id").get_column("len").to_list() == [2, 2]
    # Earliest game dates survive regardless of input order.
    assert set(capped.get_column("game_date").to_list()) == {"2024-05-01", "2024-05-02"}
