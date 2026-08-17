from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value_mlb_source import (
    materialize_mlb_contact_value_target_contacts,
)


def _row(
    *,
    game_pk: int,
    at_bat_index: int,
    pitch_number: int,
    event: str | None,
    description: str,
    terminal: bool,
    contact: bool,
    bb_type: str = "ground_ball",
    year: int = 2022,
) -> dict[str, object]:
    return {
        "game_date": f"{year}-07-01",
        "game_year": year,
        "game_pk": game_pk,
        "league_id": 103,
        "at_bat_index": at_bat_index,
        "pitch_number": pitch_number,
        "batter_mlbam_id": 5000 + at_bat_index,
        "events": event,
        "result_description": description,
        "is_plate_appearance_terminal": terminal,
        "is_contact": contact,
        "batter_side": "R",
        "bb_type": bb_type,
        "hc_x": 125.42,
        "hc_y": 100.0,
    }


def _frame() -> pl.DataFrame:
    return pl.DataFrame(
        [
            # Earlier physical contact/foul in a PA: never a target because it is
            # not the terminal pitch.
            _row(
                game_pk=10,
                at_bat_index=1,
                pitch_number=2,
                event=None,
                description="foul",
                terminal=False,
                contact=True,
                bb_type="ground_ball",
            ),
            _row(
                game_pk=10,
                at_bat_index=1,
                pitch_number=3,
                event="single",
                description="Batter singles on a ground ball.",
                terminal=True,
                contact=True,
                bb_type="ground_ball",
            ),
            _row(
                game_pk=10,
                at_bat_index=2,
                pitch_number=4,
                event="home_run",
                description="Batter homers to center field.",
                terminal=True,
                contact=True,
                bb_type="fly_ball",
            ),
            # Certified special-outcome exception: physical contact exists but
            # terminal field_error + explicit interference error is not ROE.
            _row(
                game_pk=10,
                at_bat_index=3,
                pitch_number=3,
                event="field_error",
                description="Batter reaches on an interference error.",
                terminal=True,
                contact=True,
                bb_type="ground_ball",
            ),
            # Bunt is physical contact but outside the frozen core target.
            _row(
                game_pk=10,
                at_bat_index=4,
                pitch_number=2,
                event="field_out",
                description="Batter bunts out.",
                terminal=True,
                contact=True,
                bb_type="bunt_grounder",
            ),
        ]
    )


def test_mlb_source_keeps_only_supported_terminal_core_contacts() -> None:
    target, metrics = materialize_mlb_contact_value_target_contacts(_frame())

    assert target.height == 2
    assert target.get_column("terminal_outcome_group").to_list() == ["1B", "HR"]
    assert set(target.get_column("contact_bin").to_list()) == {"CENTER_GB", "CENTER_OFFB"}
    assert set(target.get_column("level_group").to_list()) == {"MLB"}
    assert set(target.get_column("participant_authority").to_list()) == {"savant_official"}
    assert set(target.get_column("terminal_outcome_status").to_list()) == {
        "supported_structured_savant_event"
    }

    assert metrics["classified_physical_contact_count"] == 5
    assert metrics["terminal_physical_contact_count"] == 4
    assert metrics["core_terminal_contact_count"] == 3
    assert metrics["supported_target_contact_count"] == 2
    assert metrics["unsupported_core_terminal_contact_count"] == 1
    assert metrics["unsupported_terminal_status_counts_all_terminal_contacts"] == {
        "unsupported_special_result": 1
    }
    assert metrics["model_scoring"] is False
    assert metrics["accessed_2023"] is False
    assert metrics["terminal_values_attached"] is False
    assert metrics["baseline_fitted"] is False
    assert metrics["richer_residual_fitted"] is False


def test_mlb_source_labels_structured_sac_bunt_even_if_upstream_shape_looks_core() -> None:
    # 2021 contains two real Savant rows whose structured result is
    # sac_bunt_double_play and whose narrative says "ground bunts".  The older
    # general-purpose profile normalizer's exact-word "bunt" regex does not turn
    # those raw ground_ball shapes into BUNT, so Challenger 2 must still exclude
    # them from the structured terminal event itself.
    frame = pl.DataFrame(
        [
            _row(
                game_pk=15,
                at_bat_index=5,
                pitch_number=2,
                event="sac_bunt_double_play",
                description="Batter ground bunts into a sacrifice double play.",
                terminal=True,
                contact=True,
                bb_type="ground_ball",
            )
        ]
    )
    target, metrics = materialize_mlb_contact_value_target_contacts(frame)
    assert target.is_empty()
    assert metrics["core_terminal_contact_count"] == 1
    assert metrics["unsupported_core_terminal_contact_count"] == 1
    assert metrics["unsupported_terminal_status_counts_all_terminal_contacts"] == {
        "unsupported_bunt": 1
    }


def test_mlb_source_rejects_2023_before_materialization() -> None:
    frame = pl.DataFrame(
        [
            _row(
                game_pk=20,
                at_bat_index=1,
                pitch_number=1,
                event="single",
                description="Batter singles.",
                terminal=True,
                contact=True,
                year=2023,
            )
        ]
    )
    with pytest.raises(ValueError, match="rejects unauthorized seasons.*2023"):
        materialize_mlb_contact_value_target_contacts(frame)


def test_mlb_source_rejects_duplicate_pitch_keys() -> None:
    frame = _frame()
    duplicated = pl.concat([frame, frame.head(1)], how="vertical_relaxed")
    with pytest.raises(ValueError, match="duplicate canonical pitch keys"):
        materialize_mlb_contact_value_target_contacts(duplicated)


def test_mlb_source_uses_structured_event_not_narrative_guess() -> None:
    # Narrative says single, but structured Savant result is field_out.  The
    # challenger source must follow the structured terminal event.
    frame = pl.DataFrame(
        [
            _row(
                game_pk=30,
                at_bat_index=1,
                pitch_number=1,
                event="field_out",
                description="Narrative contains the word singles but structured result is out.",
                terminal=True,
                contact=True,
            )
        ]
    )
    target, _ = materialize_mlb_contact_value_target_contacts(frame)
    assert target.height == 1
    assert target.row(0, named=True)["terminal_outcome_group"] == "OUT"
