from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value_source import (
    STRUCTURED_TERMINAL_GROUP,
    attach_narrative_terminal_groups,
    classify_terminal_result_description,
    project_terminal_pa_descriptions,
    terminal_group_from_structured_event_type,
)


def test_structured_terminal_event_mapping_matches_frozen_contract() -> None:
    assert STRUCTURED_TERMINAL_GROUP == {
        "single": "1B",
        "double": "2B",
        "triple": "3B",
        "home_run": "HR",
        "field_error": "ROE",
        "fielders_choice": "FC_REACH",
        "sac_fly": "SF",
        "double_play": "MULTI_OUT",
        "grounded_into_double_play": "MULTI_OUT",
        "sac_fly_double_play": "MULTI_OUT",
        "triple_play": "MULTI_OUT",
        "field_out": "OUT",
        "fielders_choice_out": "OUT",
        "force_out": "OUT",
    }
    assert terminal_group_from_structured_event_type("force_out") == "OUT"
    assert terminal_group_from_structured_event_type("fielders_choice") == "FC_REACH"
    assert terminal_group_from_structured_event_type("catcher_interf") is None
    assert terminal_group_from_structured_event_type(None) is None


def test_narrative_fallback_uses_source_reconciled_force_and_fc_distinctions() -> None:
    force = classify_terminal_result_description(
        "Example Batter grounds into a force out, shortstop A to second baseman B. Runner out at 2nd."
    )
    assert force.terminal_outcome_group == "OUT"
    assert force.status == "supported_narrative_fallback"

    fc_out = classify_terminal_result_description(
        "Example Batter reaches on a fielder's choice out, third baseman A to catcher B. Runner out at home."
    )
    assert fc_out.terminal_outcome_group == "OUT"
    assert fc_out.status == "supported_narrative_fallback"

    fc_reach = classify_terminal_result_description(
        "Example Batter reaches on a fielder's choice, fielded by third baseman A. Runner scores."
    )
    assert fc_reach.terminal_outcome_group == "FC_REACH"
    assert fc_reach.status == "supported_narrative_fallback"


def test_narrative_fallback_accepts_unambiguous_terminal_groups() -> None:
    examples = {
        "Example Batter singles on a line drive to center field.": "1B",
        "Example Batter hits a ground-rule double (4) on a fly ball to left field.": "2B",
        "Example Batter triples on a line drive to right field.": "3B",
        "Example Batter hits a grand slam (6) to center field.": "HR",
        "Example Batter reaches on a throwing error by shortstop Example Fielder.": "ROE",
        "Example Batter reaches on a fielder's choice, third baseman Example Fielder to catcher Example Catcher.": "FC_REACH",
        "Example Batter out on a sacrifice fly to center fielder Example Fielder.": "SF",
        "Example Batter grounds into a double play, shortstop A to second baseman B to first baseman C.": "MULTI_OUT",
        "Example Batter grounds out, second baseman A to first baseman B.": "OUT",
    }
    for description, expected in examples.items():
        result = classify_terminal_result_description(description)
        assert result.terminal_outcome_group == expected
        assert result.status == "supported_narrative_fallback"


def test_narrative_fallback_fails_closed_on_compound_or_special_results() -> None:
    compound = classify_terminal_result_description(
        "Example Batter singles on a line drive to right field. Example Batter lines into a double play."
    )
    assert compound.terminal_outcome_group is None
    assert compound.status == "ambiguous_narrative_groups"

    catcher_interference = classify_terminal_result_description(
        "Example Batter reaches on catcher interference by Example Catcher."
    )
    assert catcher_interference.terminal_outcome_group is None
    assert catcher_interference.status == "unsupported_special_result"

    bunt = classify_terminal_result_description(
        "Example Batter grounds out on a bunt, pitcher A to first baseman B."
    )
    assert bunt.terminal_outcome_group is None
    assert bunt.status == "unsupported_bunt"


def test_terminal_projection_uses_final_pitch_and_collapses_exact_release_duplicates() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": [10, 10, 10, 10, 11],
            "at_bat_number": [4, 4, 4, 4, 2],
            "pitch_number": [1, 2, 3, 3, 1],
            "game_type": ["R", "R", "R", "R", "S"],
            "description": [
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Postseason Batter doubles on a fly ball.",
            ],
            "des": [
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Example Batter singles on a line drive to left field.",
                "Postseason Batter doubles on a fly ball.",
            ],
        }
    )

    terminal = project_terminal_pa_descriptions(raw)
    assert terminal.height == 1
    row = terminal.row(0, named=True)
    assert row["game_pk"] == 10
    assert row["at_bat_index"] == 4
    assert row["terminal_pitch_number"] == 3
    assert row["raw_terminal_row_count"] == 2
    assert row["terminal_description_variant_count"] == 1

    classified = attach_narrative_terminal_groups(terminal)
    assert classified.get_column("terminal_outcome_group").to_list() == ["1B"]


def test_terminal_projection_rejects_conflicting_terminal_descriptions() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": [10, 10],
            "at_bat_number": [4, 4],
            "pitch_number": [3, 3],
            "game_type": ["R", "R"],
            "description": [
                "Example Batter singles on a line drive to left field.",
                "Example Batter doubles on a line drive to left field.",
            ],
        }
    )
    with pytest.raises(ValueError, match="conflicting result descriptions"):
        project_terminal_pa_descriptions(raw)
