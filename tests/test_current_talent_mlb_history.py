import polars as pl
import pytest

from universal_baseball.current_talent_mlb_history import (
    reconcile_mlb_game_evidence_to_official_backbone,
)
from universal_baseball.mlb_season_stats import MLB_BATTING_BACKBONE_SCHEMA


def _summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2021, 2021, 2021],
            "game_date": ["2021-04-01", "2021-04-02", "2021-04-03"],
            "game_pk": [1, 2, 3],
            "league_id": [103, 103, 104],
            "player_id": [10, 10, 20],
            "level_group": ["MLB", "MLB", "MLB"],
            "batting_plate_appearances": [4, 4, 4],
            "expected_contact_count": [2, 2, 1],
            "observed_contact_count": [2, 2, 2],
            "contact_count_residual": [0, 0, 1],
            "core_profile_event_count": [4, 4, 3],
            "bunt_contact_count": [0, 0, 0],
            "foul_air_excluded_count": [0, 0, 0],
            "unknown_contact_count": [0, 0, 1],
            "special_noncontact_count": [0, 0, 1],
            "pa_accounting_residual": [0, 0, 0],
            "participant_authority_status": ["savant_official"] * 3,
            "source_capability_tier": ["mlb_savant_result_contact_profile_v2"] * 3,
        }
    )


def _profile() -> pl.DataFrame:
    rows = []
    for season, game_date, game_pk, league_id, player_id, contact_count in [
        (2021, "2021-04-01", 1, 103, 10, 2),
        (2021, "2021-04-02", 2, 103, 10, 2),
        (2021, "2021-04-03", 3, 104, 20, 1),
    ]:
        base = {
            "season": season,
            "game_date": game_date,
            "game_pk": game_pk,
            "league_id": league_id,
            "player_id": player_id,
            "level_group": "MLB",
        }
        rows.extend(
            [
                {**base, "core_bin": "BB_HBP", "occurrence_count": 1},
                {**base, "core_bin": "K", "occurrence_count": 1},
                {**base, "core_bin": "PULL_GB", "occurrence_count": contact_count},
            ]
        )
    return pl.DataFrame(rows)


def _backbone_row(
    *,
    league_id: int,
    player_id: int,
    pa: int,
    ab: int,
    bb: int,
    hbp: int,
    k: int,
    sh: int = 0,
    sf: int = 0,
) -> dict[str, object]:
    return {
        "season": 2021,
        "league_id": league_id,
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "batting_plate_appearances": pa,
        "batting_at_bats": ab,
        "batting_base_on_balls": bb,
        "batting_intentional_walks": 0,
        "batting_hit_by_pitch": hbp,
        "batting_strike_outs": k,
        "batting_sac_bunts": sh,
        "batting_sac_flies": sf,
        "batting_balls_in_play": ab - k + sh + sf,
        "simple_pa_accounting_residual": ab + bb + hbp + sh + sf - pa,
    }


def _backbone() -> pl.DataFrame:
    rows = [
        # Player 10: 8 PA = 6 AB + 1 BB + 1 HBP; 6 AB - 2 K = 4 result contacts.
        _backbone_row(league_id=103, player_id=10, pa=8, ab=6, bb=1, hbp=1, k=2),
        # Player 20: one PA is official interference/non-AB accounting.
        _backbone_row(league_id=104, player_id=20, pa=4, ab=2, bb=1, hbp=0, k=1),
        # A zero-PA official split is allowed to exist without fabricated game chronology.
        _backbone_row(league_id=104, player_id=30, pa=0, ab=0, bb=0, hbp=0, k=0),
    ]
    return pl.DataFrame(rows, schema=MLB_BATTING_BACKBONE_SCHEMA)


def test_historical_mlb_reconciliation_is_exact_on_official_outcomes() -> None:
    comparison, metrics = reconcile_mlb_game_evidence_to_official_backbone(
        _summary(), _profile(), _backbone()
    )

    assert metrics["exact_outcome_reconciliation"] is True
    assert metrics["exact_outcome_mismatch_row_count"] == 0
    assert metrics["game_plate_appearances"] == 12
    assert metrics["official_plate_appearances"] == 12
    assert metrics["game_bb_hbp"] == 3
    assert metrics["official_bb_hbp"] == 3
    assert metrics["game_strikeouts"] == 3
    assert metrics["official_strikeouts"] == 3
    assert metrics["game_expected_contacts"] == 5
    assert metrics["official_expected_contacts"] == 5
    assert metrics["game_special_noncontact"] == 1
    assert metrics["official_special_noncontact"] == 1

    # Physical contact can differ from boxscore result-contact accounting and remains diagnostic.
    assert metrics["observed_physical_contacts"] == 6
    assert metrics["physical_contact_residual"] == 1
    assert metrics["physical_contact_residual_is_diagnostic_only"] is True

    zero_pa = comparison.filter(pl.col("player_id") == 30).row(0, named=True)
    assert zero_pa["game_pa"] == 0
    assert zero_pa["official_pa"] == 0
    assert zero_pa["has_exact_outcome_mismatch"] is False


def test_historical_mlb_reconciliation_fails_on_official_outcome_mismatch() -> None:
    bad = _backbone().with_columns(
        pl.when(pl.col("player_id") == 10)
        .then(pl.col("batting_plate_appearances") + 1)
        .otherwise(pl.col("batting_plate_appearances"))
        .alias("batting_plate_appearances"),
        pl.when(pl.col("player_id") == 10)
        .then(pl.col("simple_pa_accounting_residual") - 1)
        .otherwise(pl.col("simple_pa_accounting_residual"))
        .alias("simple_pa_accounting_residual"),
    )
    with pytest.raises(ValueError, match="does not reconcile"):
        reconcile_mlb_game_evidence_to_official_backbone(_summary(), _profile(), bad)

    comparison, metrics = reconcile_mlb_game_evidence_to_official_backbone(
        _summary(), _profile(), bad, require_exact=False
    )
    player10 = comparison.filter(pl.col("player_id") == 10).row(0, named=True)
    assert player10["pa_difference"] == -1
    assert player10["special_noncontact_difference"] == -1
    assert metrics["exact_outcome_mismatch_row_count"] == 1


def test_historical_mlb_reconciliation_rejects_impossible_negative_special_pa() -> None:
    impossible = _backbone().with_columns(
        pl.when(pl.col("player_id") == 20)
        .then(pl.lit(5))
        .otherwise(pl.col("batting_at_bats"))
        .alias("batting_at_bats"),
        pl.when(pl.col("player_id") == 20)
        .then(pl.lit(2))
        .otherwise(pl.col("batting_balls_in_play"))
        .alias("batting_balls_in_play"),
        pl.when(pl.col("player_id") == 20)
        .then(pl.lit(2))
        .otherwise(pl.col("simple_pa_accounting_residual"))
        .alias("simple_pa_accounting_residual"),
    )
    with pytest.raises(ValueError, match="negative special non-contact"):
        reconcile_mlb_game_evidence_to_official_backbone(
            _summary(), _profile(), impossible, require_exact=False
        )
