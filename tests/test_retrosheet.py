from __future__ import annotations

from pathlib import Path

from universal_baseball.retrosheet import find_plays_csv_member, load_plays_transitions


def test_find_plays_csv_member_prefers_play_named_csv() -> None:
    assert find_plays_csv_member(["notes.csv", "2024plays.csv", "README.txt"]) == "2024plays.csv"


def test_retrosheet_transition_projection_preserves_state_changes(tmp_path: Path) -> None:
    path = tmp_path / "plays.csv"
    path.write_text(
        "gid,inning,top_bot,pn,pa,outs_pre,outs_post,br1_pre,br2_pre,br3_pre,br1_post,br2_post,br3_post,runs,score_v,score_h\n"
        "GAME1,1,0,0,0,0,0,,,,,,,,0,0\n"
        "GAME1,1,0,1,1,0,0,,,,runner,,,0,0,0\n"
        "GAME1,1,0,2,0,0,0,runner,,,,runner,,0,0,0\n"
        "GAME1,1,0,3,1,0,1,,runner,,,,,1,0,0\n",
        encoding="utf-8",
    )

    result = load_plays_transitions(path)
    # Row 0 is inert and row 2 moves the runner first->second, so three rows are candidates.
    assert result.height == 3
    rows = result.to_dicts()
    assert rows[0]["at_bat_index"] == 1
    assert rows[0]["start_bases_code"] == 0
    assert rows[0]["end_bases_code"] == 1
    assert rows[1]["at_bat_index"] == 2
    assert rows[1]["start_bases_code"] == 1
    assert rows[1]["end_bases_code"] == 2
    assert rows[2]["runs_scored"] == 1
    assert rows[2]["end_outs"] == 1
    assert rows[2]["end_bat_score"] == 1
