from __future__ import annotations

import polars as pl

from universal_baseball.canonical_adapters import normalize_armstjc_pitch_observations


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def _normalize(codes: list[str | None], bb_types: list[str | None]) -> pl.DataFrame:
    row_count = len(codes)
    return normalize_armstjc_pitch_observations(
        pl.DataFrame(
            {
                "game_pk": ["1"] * row_count,
                "at_bat_number": [str(index) for index in range(row_count)],
                "pitch_number": ["1"] * row_count,
                "type": codes,
                "bb_type": bb_types,
            },
            schema_overrides={"type": pl.String, "bb_type": pl.String},
        ),
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    ).sort("at_bat_index")


def test_armstjc_d_e_x_codes_are_all_positive_in_play_evidence() -> None:
    result = _normalize(
        ["D", "E", "X", "B", "S"],
        ["ground_ball", "line_drive", "fly_ball", None, None],
    )
    assert result.get_column("is_in_play").to_list() == [True, True, True, False, False]


def test_preserved_hit_data_is_positive_backstop_for_unseen_code() -> None:
    result = _normalize(["future_code", None], ["popup", None])
    assert result.get_column("is_in_play").to_list() == [True, None]
