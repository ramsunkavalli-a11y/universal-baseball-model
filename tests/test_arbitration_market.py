from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)


def test_arbitration_baseline_has_four_monotone_classes() -> None:
    shares = FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS
    assert list(shares) == [1, 2, 3, 4]
    assert list(shares.values()) == [0.15, 0.35, 0.50, 0.75]
