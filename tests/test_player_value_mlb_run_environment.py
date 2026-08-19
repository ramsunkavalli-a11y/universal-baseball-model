from __future__ import annotations

import pytest

from universal_baseball.player_value_mlb_run_environment import innings_pitched_to_outs


def test_baseball_innings_notation_parses_to_outs() -> None:
    assert innings_pitched_to_outs("0.0") == 0
    assert innings_pitched_to_outs("1.0") == 3
    assert innings_pitched_to_outs("12.1") == 37
    assert innings_pitched_to_outs("12.2") == 38


@pytest.mark.parametrize("value", ["1.3", "-1.0", "", None])
def test_invalid_baseball_innings_notation_is_rejected(value: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        innings_pitched_to_outs(value)
