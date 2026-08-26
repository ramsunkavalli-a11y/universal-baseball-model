import polars as pl
import pytest

from universal_baseball.hitter_v2_historical_bridge import (
    canonicalize_stints,
    evidence_band,
    matched_pair,
    player_seasons,
    transition_label,
)


def test_bridge_classifies_level_changes_and_multi_stints() -> None:
    raw = pl.DataFrame(
        {
            "season": [2019, 2019, 2020, 2019, 2020],
            "player_id": [1, 1, 1, 2, 2],
            "level_group": ["AA", "AAA", "MLB", "AAA", "AA"],
            "pa": [100, 200, 50, 400, 300],
            "source": ["A", "A", "B", "A", "B"],
        }
    )
    seasons = player_seasons(canonicalize_stints(raw))
    pair = matched_pair(
        seasons,
        origin_season=2019,
        destination_season=2020,
        comparison="TEST",
    ).sort("player_id")
    assert pair["transition"].to_list() == ["AMBIGUOUS", "DEMOTION"]
    assert pair["origin_evidence_band"].to_list() == ["300_599", "300_599"]


def test_bridge_level_order_and_evidence_boundaries_are_frozen() -> None:
    assert transition_label("SINGLE_A", "AA") == "PROMOTION"
    assert transition_label("MLB", "MLB") == "SAME"
    assert [evidence_band(pa) for pa in (99, 100, 299, 300, 599, 600)] == [
        "LT100",
        "100_299",
        "100_299",
        "300_599",
        "300_599",
        "600_PLUS",
    ]


def test_bridge_fails_closed_on_unknown_level_or_negative_pa() -> None:
    base = {
        "season": [2019],
        "player_id": [1],
        "level_group": ["UNKNOWN"],
        "pa": [1],
        "source": ["A"],
    }
    with pytest.raises(ValueError, match="unknown bridge levels"):
        canonicalize_stints(pl.DataFrame(base))
    base["level_group"] = ["AA"]
    base["pa"] = [-1]
    with pytest.raises(ValueError, match="cannot be negative"):
        canonicalize_stints(pl.DataFrame(base))
