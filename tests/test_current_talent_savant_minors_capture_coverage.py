from datetime import date
from pathlib import Path
import sys

import polars as pl

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from capture_current_talent_savant_minors_tracking import (  # noqa: E402
    _certified_player_games_through,
)


def test_certified_player_games_through_excludes_games_after_capture_end(tmp_path) -> None:
    pl.DataFrame(
        {
            "game_date": ["2022-08-30", "2022-09-01"],
            "game_pk": [1, 2],
            "player_id": [10, 20],
            "league_id": [117, 117],
            "level_group": ["AAA", "AAA"],
        }
    ).write_parquet(tmp_path / "current_talent_game_summary_2022_aaa.parquet")

    observed = _certified_player_games_through(tmp_path, 2022, date(2022, 8, 31))

    assert observed.get_column("game_pk").to_list() == [1]
    assert observed.get_column("season").to_list() == [2022]
