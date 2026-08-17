from __future__ import annotations

from datetime import date
from pathlib import Path

from universal_baseball.retrosheet import (
    find_plays_csv_member,
    load_plays_contact_value_transitions,
    load_plays_transitions,
)


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


def _contact_header() -> str:
    return (
        "gid,date,gametype,inning,top_bot,pn,pa,outs_pre,outs_post,"
        "br1_pre,br2_pre,br3_pre,br1_post,br2_post,br3_post,runs,score_v,score_h,"
        "single,double,triple,hr,sh,sf,roe,fc,othout,noout,bip,bunt,gdp,othdp,tp\n"
    )


def test_contact_value_projection_is_strictly_pre_cutoff_and_regular_season(tmp_path: Path) -> None:
    path = tmp_path / "plays.csv"
    path.write_text(
        _contact_header()
        + "G1,2021-07-14,regular,1,0,1,1,0,0,,,,runner,,,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0\n"
        + "G2,2021-07-15,regular,1,0,1,1,0,0,,,,runner,,,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0\n"
        + "G3,2021-07-14,allstar,1,0,1,1,0,0,,,,runner,,,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0\n",
        encoding="utf-8",
    )

    result = load_plays_contact_value_transitions(path, cutoff_date=date(2021, 7, 15))

    assert result.get_column("game_pk").to_list() == ["G1"]
    row = result.row(0, named=True)
    assert row["game_date"].isoformat() == "2021-07-14"
    assert row["terminal_outcome_group"] == "1B"
    assert row["contact_value_target_candidate"] is True
    assert row["contact_value_mapping_supported"] is True


def test_contact_value_projection_maps_frozen_terminal_groups_and_exposes_unsupported(tmp_path: Path) -> None:
    path = tmp_path / "plays.csv"
    rows = [
        # gid, outcome flags after score_h
        "S,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0",
        "D,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0",
        "T,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0",
        "H,2021-06-01,regular,1,0,1,1,0,0,,,,,,,1,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0",
        "E,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0",
        "F,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0",
        "SF,2021-06-01,regular,1,0,1,1,0,1,,,,,,,,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0",
        "DP,2021-06-01,regular,1,0,1,1,0,2,r,,,,,,,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,0",
        "O,2021-06-01,regular,1,0,1,1,0,1,,,,,,,,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0",
        "U,2021-06-01,regular,1,0,1,1,0,0,,,,r,,,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0",
        # Bunt is deliberately outside the target even if it is otherwise an out.
        "B,2021-06-01,regular,1,0,1,1,0,1,,,,,,,,0,0,0,0,0,1,0,0,0,1,0,0,1,1,0,0,0",
    ]
    path.write_text(_contact_header() + "\n".join(rows) + "\n", encoding="utf-8")

    result = load_plays_contact_value_transitions(path, cutoff_date=date(2021, 7, 15))
    mapped = {row["game_pk"]: row for row in result.to_dicts()}

    assert mapped["S"]["terminal_outcome_group"] == "1B"
    assert mapped["D"]["terminal_outcome_group"] == "2B"
    assert mapped["T"]["terminal_outcome_group"] == "3B"
    assert mapped["H"]["terminal_outcome_group"] == "HR"
    assert mapped["E"]["terminal_outcome_group"] == "ROE"
    assert mapped["F"]["terminal_outcome_group"] == "FC_REACH"
    assert mapped["SF"]["terminal_outcome_group"] == "SF"
    assert mapped["DP"]["terminal_outcome_group"] == "MULTI_OUT"
    assert mapped["O"]["terminal_outcome_group"] == "OUT"
    assert mapped["U"]["contact_value_target_candidate"] is True
    assert mapped["U"]["contact_value_mapping_supported"] is False
    assert mapped["U"]["terminal_outcome_group"] is None
    assert mapped["B"]["contact_value_target_candidate"] is False
