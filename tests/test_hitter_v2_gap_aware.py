import polars as pl
import pytest

from universal_baseball.hitter_v2_gap_aware import assemble_gap_aware_history
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


def _history(season: int, level: str, player: int) -> pl.DataFrame:
    row: dict[str, object] = {
        "season": season,
        "league_id": 1,
        "player_id": player,
        "level_group": level,
        "hitter_talent_pa": 1,
        "modeling_eligible": True,
    }
    row.update({outcome: int(outcome == "HR") for outcome in HITTER_TALENT_OUTCOMES})
    return pl.DataFrame([row])


def test_gap_aware_history_skips_missing_season_without_zero_rows() -> None:
    result = assemble_gap_aware_history(
        _history(2021, "aa", 1),
        _history(2019, "AA", 1),
        _history(2020, "MLB", 2),
        predictor_cutoff_season=2021,
    )
    assert result["season"].to_list() == [2019, 2020, 2021]
    assert result.filter(
        (pl.col("season") == 2020) & (pl.col("level_group") != "MLB")
    ).is_empty()


def test_gap_aware_history_rejects_constructed_2020_milb() -> None:
    with pytest.raises(ValueError, match="cannot construct 2020 MiLB"):
        assemble_gap_aware_history(
            _history(2021, "aa", 1),
            _history(2019, "AA", 1),
            _history(2020, "AAA", 2),
            predictor_cutoff_season=2021,
        )
