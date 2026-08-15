from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.game_observation import validate_game_observation
from universal_baseball.resolution import (
    game_resolution_conflicts,
    resolve_game_observations_across_snapshots,
)


LEFT_NORMALIZATION = "a" * 64
LEFT_SNAPSHOT = "b" * 64
RIGHT_NORMALIZATION = "c" * 64
RIGHT_SNAPSHOT = "d" * 64


def _game_row(
    *,
    normalization_id: str,
    source_snapshot_id: str,
    payload_hash: str,
    home_team: str,
) -> dict[str, object]:
    return {
        "normalization_id": normalization_id,
        "source_snapshot_id": source_snapshot_id,
        "game_pk": 123,
        "payload_hash": payload_hash,
        "evidence_row_count": 10,
        "official_date": date(2023, 8, 1),
        "season": 2023,
        "level_name": "Rookie",
        "normalized_level": "Rookie",
        "home_team": home_team,
        "away_team": "Away",
    }


def _definitions(*, right_version: str = "1") -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "normalization_id": LEFT_NORMALIZATION,
                "source_snapshot_id": LEFT_SNAPSHOT,
                "normalizer_name": "armstjc_game_adapter",
                "normalizer_version": "1",
                "canonical_schema_version": "0.1",
            },
            {
                "normalization_id": RIGHT_NORMALIZATION,
                "source_snapshot_id": RIGHT_SNAPSHOT,
                "normalizer_name": "armstjc_game_adapter",
                "normalizer_version": right_version,
                "canonical_schema_version": "0.1",
            },
        ]
    )


def test_game_resolution_keeps_stable_date_but_flags_changed_label() -> None:
    observations = validate_game_observation(
        pl.DataFrame(
            [
                _game_row(
                    normalization_id=LEFT_NORMALIZATION,
                    source_snapshot_id=LEFT_SNAPSHOT,
                    payload_hash="e" * 64,
                    home_team="Old Label",
                ),
                _game_row(
                    normalization_id=RIGHT_NORMALIZATION,
                    source_snapshot_id=RIGHT_SNAPSHOT,
                    payload_hash="f" * 64,
                    home_team="New Label",
                ),
            ]
        )
    )

    resolved = resolve_game_observations_across_snapshots(
        observations,
        _definitions(),
    )
    row = resolved.to_dicts()[0]

    assert row["official_date"] == date(2023, 8, 1)
    assert row["season"] == 2023
    assert row["normalized_level"] == "Rookie"
    assert row["away_team"] == "Away"
    assert row["home_team"] is None
    assert row["conflict_fields"] == ["home_team"]
    assert row["conflict_field_count"] == 1
    assert row["source_snapshot_count"] == 2
    assert row["raw_source_row_count"] == 20
    assert game_resolution_conflicts(resolved).height == 1


def test_game_resolution_rejects_mixed_normalizer_versions() -> None:
    observations = validate_game_observation(
        pl.DataFrame(
            [
                _game_row(
                    normalization_id=LEFT_NORMALIZATION,
                    source_snapshot_id=LEFT_SNAPSHOT,
                    payload_hash="e" * 64,
                    home_team="Same",
                ),
                _game_row(
                    normalization_id=RIGHT_NORMALIZATION,
                    source_snapshot_id=RIGHT_SNAPSHOT,
                    payload_hash="f" * 64,
                    home_team="Same",
                ),
            ]
        )
    )

    with pytest.raises(ValueError, match="cannot mix normalizer/schema versions"):
        resolve_game_observations_across_snapshots(
            observations,
            _definitions(right_version="2"),
        )
