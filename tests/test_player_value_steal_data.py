from __future__ import annotations

import pytest

from universal_baseball.player_value_steal_data import (
    StealStint,
    build_loo_player_season_summaries,
)


def _stint(
    player_id: int,
    *,
    season: int = 2023,
    source: str = "MLB",
    environment_id: str = "MLB",
    tier: str = "MLB",
    hits: float = 30,
    doubles: float = 5,
    triples: float = 1,
    home_runs: float = 4,
    walks: float = 10,
    intentional_walks: float = 1,
    hit_by_pitch: float = 1,
    stolen_bases: float = 5,
    caught_stealing: float = 1,
) -> StealStint:
    return StealStint(
        season=season,
        source=source,
        environment_id=environment_id,
        tier=tier,
        player_id=player_id,
        player_name=f"Player {player_id}",
        plate_appearances=100,
        hits=hits,
        doubles=doubles,
        triples=triples,
        home_runs=home_runs,
        walks=walks,
        intentional_walks=intentional_walks,
        hit_by_pitch=hit_by_pitch,
        stolen_bases=stolen_bases,
        caught_stealing=caught_stealing,
    )


def test_portable_opportunity_proxy_matches_wsb_components() -> None:
    row = _stint(1)
    assert row.singles == 20
    assert row.opportunity_proxy == 30  # 1B + BB + HBP - IBB
    assert row.attempts == 6


def test_mlb_environment_baseline_is_leave_one_player_out() -> None:
    rows = [
        _stint(1, stolen_bases=5, caught_stealing=1),
        _stint(2, stolen_bases=2, caught_stealing=1),
        _stint(3, stolen_bases=1, caught_stealing=1),
    ]

    summaries, audit = build_loo_player_season_summaries(rows)
    by_player = {row.player_id: row for row in summaries}

    # Every player has opportunity proxy 30. For player 1 the other two players
    # have 5 attempts over 60 proxy opportunities.
    assert by_player[1].expected_attempts == pytest.approx(30 * (5 / 60))
    # Other players have 3 successes in 5 attempts, so player 1's expected
    # successes are six observed attempts times the LOO .600 baseline.
    assert by_player[1].expected_successes == pytest.approx(6 * (3 / 5))
    assert audit.actual_environment_attempt_rows == 3
    assert audit.level_fallback_attempt_rows == 0


def test_milb_sparse_actual_league_falls_back_to_leave_one_out_level() -> None:
    rows = [
        _stint(
            1,
            source="MiLB",
            environment_id="MILB:101",
            tier="AA",
            stolen_bases=2,
            caught_stealing=1,
        ),
        _stint(
            2,
            source="MiLB",
            environment_id="MILB:102",
            tier="AA",
            stolen_bases=3,
            caught_stealing=1,
        ),
        _stint(
            3,
            source="MiLB",
            environment_id="MILB:102",
            tier="AA",
            stolen_bases=1,
            caught_stealing=1,
        ),
    ]

    summaries, audit = build_loo_player_season_summaries(rows)
    by_player = {row.player_id: row for row in summaries}

    # Each tiny actual league is well below the 500-opportunity threshold, so
    # player 1 uses the AA season baseline formed only from players 2 and 3.
    assert by_player[1].expected_attempts == pytest.approx(30 * (6 / 60))
    assert audit.level_fallback_attempt_rows == 3
    assert audit.actual_environment_attempt_rows == 0


def test_multiteam_same_environment_is_aggregated_before_loo() -> None:
    player_one_a = _stint(1, stolen_bases=2, caught_stealing=0)
    player_one_b = _stint(1, stolen_bases=3, caught_stealing=1)
    other = _stint(2, stolen_bases=2, caught_stealing=1)

    summaries, audit = build_loo_player_season_summaries(
        [player_one_a, player_one_b, other]
    )
    by_player = {row.player_id: row for row in summaries}

    assert len(summaries) == 2
    assert audit.player_environment_stint_count == 2
    assert by_player[1].attempts == 6
    assert by_player[1].opportunity_proxy == 60
    # The LOO baseline for player 1 is based on player 2 only, not on one of
    # player 1's own team rows.
    assert by_player[1].expected_attempts == pytest.approx(60 * (3 / 30))


def test_invalid_extra_base_hit_identity_fails_closed() -> None:
    with pytest.raises(ValueError, match="extra-base hits cannot exceed hits"):
        _stint(1, hits=5, doubles=3, triples=1, home_runs=2)
