import polars as pl

from universal_baseball.current_talent_evidence_quarantine import (
    quarantine_game_ids,
    quarantine_player_game_keys,
)


def test_player_game_quarantine_removes_only_exact_keys() -> None:
    frame = pl.DataFrame(
        {
            "game_id": [10, 10, 11],
            "player_id": [100, 101, 100],
            "value": [1, 2, 3],
        }
    )
    kept, metrics = quarantine_player_game_keys(
        frame,
        {(10, 100)},
        game_column="game_id",
        player_column="player_id",
        label="controls",
    )
    assert kept.select("game_id", "player_id").rows() == [(10, 101), (11, 100)]
    assert metrics["quarantined_row_count"] == 1
    assert metrics["quarantined_keys"] == [[10, 100]]


def test_player_game_quarantine_supports_contact_key_columns() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": [10, 10],
            "source_batter_id": [100, 101],
            "pitch_number": [1, 2],
        }
    )
    kept, metrics = quarantine_player_game_keys(
        frame,
        {(10, 100)},
        game_column="game_pk",
        player_column="source_batter_id",
        label="contacts",
    )
    assert kept.get_column("source_batter_id").to_list() == [101]
    assert metrics["quarantined_row_count"] == 1


def test_whole_game_quarantine_does_not_touch_other_games() -> None:
    frame = pl.DataFrame({"game_pk": [10, 10, 11], "x": [1, 2, 3]})
    kept, metrics = quarantine_game_ids(
        frame,
        [10],
        game_column="game_pk",
        label="unresolved league identity",
    )
    assert kept.get_column("game_pk").to_list() == [11]
    assert metrics["quarantined_game_ids"] == [10]
    assert metrics["quarantined_row_count"] == 2


def test_empty_quarantine_is_noop() -> None:
    frame = pl.DataFrame({"game_id": [1], "player_id": [2]})
    kept, metrics = quarantine_player_game_keys(
        frame,
        [],
        game_column="game_id",
        player_column="player_id",
        label="noop",
    )
    assert kept.equals(frame)
    assert metrics["quarantined_row_count"] == 0
