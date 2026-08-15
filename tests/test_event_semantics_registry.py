from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.event_semantics_registry import (
    current_event_semantics_frame,
    validate_event_semantics_frame,
    validate_sequence_semantics_links,
)


def test_current_event_semantics_is_unique_and_contains_pa_and_non_pa_events() -> None:
    semantics = current_event_semantics_frame()

    assert semantics.get_column("event_semantics_snapshot_id").n_unique() == 1
    assert semantics.get_column("event_type").n_unique() == semantics.height
    single = semantics.filter(pl.col("event_type") == "single").to_dicts()[0]
    caught = semantics.filter(pl.col("event_type") == "caught_stealing_2b").to_dicts()[0]
    assert single["is_plate_appearance"] is True
    assert caught["is_plate_appearance"] is False


def test_sequence_semantics_links_require_registered_matching_definition() -> None:
    semantics = current_event_semantics_frame()
    snapshot_id = semantics.get_column("event_semantics_snapshot_id")[0]
    sequences = pl.DataFrame(
        {
            "classification_status": ["official_true_pa", "official_non_pa"],
            "result_event_type": ["single", "caught_stealing_2b"],
            "is_plate_appearance": [True, False],
            "event_semantics_snapshot_id": [snapshot_id, snapshot_id],
        }
    )

    validate_sequence_semantics_links(sequences, semantics)

    wrong = sequences.with_columns(
        pl.when(pl.col("result_event_type") == "single")
        .then(pl.lit(False))
        .otherwise(pl.col("is_plate_appearance"))
        .alias("is_plate_appearance")
    )
    with pytest.raises(ValueError, match="disagrees"):
        validate_sequence_semantics_links(wrong, semantics)


def test_unclassified_sequence_cannot_claim_official_semantics() -> None:
    semantics = current_event_semantics_frame()
    snapshot_id = semantics.get_column("event_semantics_snapshot_id")[0]
    sequence = pl.DataFrame(
        {
            "classification_status": ["unclassified_source_sequence"],
            "result_event_type": [None],
            "is_plate_appearance": [None],
            "event_semantics_snapshot_id": [snapshot_id],
        },
        schema={
            "classification_status": pl.String,
            "result_event_type": pl.String,
            "is_plate_appearance": pl.Boolean,
            "event_semantics_snapshot_id": pl.String,
        },
    )

    with pytest.raises(ValueError, match="cannot claim"):
        validate_sequence_semantics_links(sequence, semantics)


def test_event_semantics_reject_duplicate_definition() -> None:
    semantics = current_event_semantics_frame()
    duplicate = pl.concat([semantics, semantics.head(1)], how="vertical_relaxed")
    with pytest.raises(ValueError, match="duplicate"):
        validate_event_semantics_frame(duplicate)
