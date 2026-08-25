import polars as pl
import pytest

from universal_baseball.hitter_v2_event_labels import (
    attach_structured_terminal_event,
    attach_terminal_pa_labels,
    classify_terminal_pa,
    reconcile_terminal_pa_labels,
)
from universal_baseball.hitter_v2_outcomes import TERMINAL_OUTCOMES


@pytest.mark.parametrize(
    ("event", "description", "expected"),
    [
        ("home_run", "irrelevant", "HR"),
        (None, "Example Batter intentionally walks.", "IBB"),
        (None, "Example Batter walks.", "UBB"),
        (None, "Example Batter hit by pitch.", "HBP"),
        (None, "Example Batter strikes out swinging.", "K"),
        (None, "Example Batter called out on strikes.", "K"),
        (None, "Example Batter singles on a line drive.", "1B"),
        (None, "Example Batter grounds out to shortstop.", "OTHER_OUT"),
        (None, "Example Batter out on a sacrifice bunt.", "SH_OR_SPECIAL"),
        (None, "Example Batter reaches on catcher interference.", "SH_OR_SPECIAL"),
    ],
)
def test_terminal_label_taxonomy(
    event: str | None, description: str, expected: str
) -> None:
    assert classify_terminal_pa(event_type=event, description=description).outcome == (
        expected
    )


def _labeled_sidecar() -> pl.DataFrame:
    outcomes = ["K", "UBB", "HR", "OTHER_OUT"]
    return pl.DataFrame(
        {
            "season": [2024] * 4,
            "game_pk": [1] * 4,
            "at_bat_index": list(range(4)),
            "player_id": [10] * 4,
            "canonical_outcome": outcomes,
            "matchup_ready": [True] * 4,
            "modeling_join_ready": [True] * 4,
        }
    )


def _player_game() -> pl.DataFrame:
    row = {outcome: 0 for outcome in TERMINAL_OUTCOMES}
    row.update(
        {
            "season": 2024,
            "game_id": 1,
            "player_id": 10,
            "modeling_eligible": True,
            "accepted_terminal_pa": 4,
            "K": 1,
            "UBB": 1,
            "HR": 1,
            "OTHER_OUT": 1,
        }
    )
    return pl.DataFrame([row])


def test_direct_labels_must_match_every_player_game_outcome() -> None:
    attached, reconciliation = reconcile_terminal_pa_labels(
        _labeled_sidecar(), _player_game()
    )
    assert reconciliation["context_label_player_game_ready"].item()
    assert attached["context_label_ready"].to_list() == [True] * 4

    wrong = _labeled_sidecar().with_columns(
        pl.when(pl.col("canonical_outcome") == "HR")
        .then(pl.lit("1B"))
        .otherwise(pl.col("canonical_outcome"))
        .alias("canonical_outcome")
    )
    attached, reconciliation = reconcile_terminal_pa_labels(wrong, _player_game())
    assert not reconciliation["context_label_player_game_ready"].item()
    assert reconciliation["context_label_reconciliation_status"].item() == (
        "direct_outcome_count_mismatch"
    )
    assert attached["context_label_ready"].to_list() == [False] * 4


def test_unresolved_label_fails_closed_and_duplicates_raise() -> None:
    unresolved = _labeled_sidecar().with_columns(
        pl.when(pl.col("at_bat_index") == 0)
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.col("canonical_outcome"))
        .alias("canonical_outcome")
    )
    _, reconciliation = reconcile_terminal_pa_labels(unresolved, _player_game())
    assert reconciliation["context_label_reconciliation_status"].item() == (
        "unresolved_direct_label"
    )

    duplicate = pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_index": [0, 0],
            "pa_description": ["A walks.", "A walks."],
        }
    )
    with pytest.raises(ValueError, match="not unique"):
        attach_terminal_pa_labels(duplicate)


def test_structured_event_uses_exact_terminal_pitch_and_fails_conflicts() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "at_bat_number": [0, 0, 0],
            "pitch_number": [1, 2, 2],
            "game_type": ["R", "R", "R"],
            "events": [None, "walk", "intent_walk"],
        }
    )
    terminal = pl.DataFrame(
        {
            "game_pk": [1],
            "at_bat_index": [0],
            "terminal_pitch_number": [2],
            "pa_description": ["Example Batter walks."],
        }
    )
    attached = attach_structured_terminal_event(raw, terminal)
    assert attached["event_variant_count"].item() == 2
    assert attached["structured_event"].item() is None
    assert attached["structured_event_conflict"].item()
