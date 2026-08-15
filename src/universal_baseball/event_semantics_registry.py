"""Versioned official event-type semantics as canonical reference data."""

from __future__ import annotations

import polars as pl

from universal_baseball.canonical_adapters import current_event_semantics_snapshot_id
from universal_baseball.event_types import KNOWN_EVENT_TYPES, PLATE_APPEARANCE_EVENT_TYPES


EVENT_SEMANTICS_VERSION = "mlb_event_types_2026-08-15"
EVENT_SEMANTICS_SCHEMA: dict[str, pl.DataType] = {
    "event_semantics_snapshot_id": pl.String,
    "event_semantics_version": pl.String,
    "event_type": pl.String,
    "is_plate_appearance": pl.Boolean,
}
_HEX64_PATTERN = r"^[0-9a-f]{64}$"


def current_event_semantics_frame() -> pl.DataFrame:
    """Materialize the exact frozen MLB event semantics used by the project."""

    snapshot_id = current_event_semantics_snapshot_id()
    rows = [
        {
            "event_semantics_snapshot_id": snapshot_id,
            "event_semantics_version": EVENT_SEMANTICS_VERSION,
            "event_type": event_type,
            "is_plate_appearance": event_type in PLATE_APPEARANCE_EVENT_TYPES,
        }
        for event_type in sorted(KNOWN_EVENT_TYPES)
    ]
    return validate_event_semantics_frame(pl.DataFrame(rows))


def validate_event_semantics_frame(frame: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(set(EVENT_SEMANTICS_SCHEMA) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(EVENT_SEMANTICS_SCHEMA))
    if missing:
        raise ValueError(f"event semantics missing columns: {missing}")
    if extra:
        raise ValueError(f"event semantics has undeclared columns: {extra}")

    result = frame.select(list(EVENT_SEMANTICS_SCHEMA)).cast(
        EVENT_SEMANTICS_SCHEMA, strict=True
    )
    if result.is_empty():
        raise ValueError("event semantics cannot be empty")
    if result.null_count().sum_horizontal().item() != 0:
        raise ValueError("event semantics cannot contain null values")
    invalid_id = result.filter(
        ~pl.col("event_semantics_snapshot_id").str.contains(_HEX64_PATTERN)
    )
    if not invalid_id.is_empty():
        raise ValueError("event semantics contains invalid snapshot ID")
    duplicates = (
        result.group_by(["event_semantics_snapshot_id", "event_type"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("event semantics contains duplicate event-type definitions")

    # One snapshot ID must describe one complete semantic mapping/version.
    snapshot_versions = (
        result.group_by("event_semantics_snapshot_id")
        .agg(pl.col("event_semantics_version").n_unique().alias("versions"))
        .filter(pl.col("versions") != 1)
    )
    if not snapshot_versions.is_empty():
        raise ValueError("event semantics snapshot mixes semantic versions")
    return result


def validate_sequence_semantics_links(
    sequences: pl.DataFrame,
    semantics: pl.DataFrame,
) -> None:
    """Prove classified sequence rows use a registered, matching event definition."""

    required = {
        "classification_status",
        "result_event_type",
        "is_plate_appearance",
        "event_semantics_snapshot_id",
    }
    missing = sorted(required - set(sequences.columns))
    if missing:
        raise ValueError(f"play sequences missing semantics columns: {missing}")
    definitions = validate_event_semantics_frame(semantics)

    # Unclassified source sequences cannot borrow the authority of the frozen
    # official semantics registry. Check this independently of whether the frame
    # also contains classified rows; otherwise an all-unclassified frame could
    # escape through the classified-empty early return below.
    unclassified = sequences.filter(
        pl.col("classification_status") == "unclassified_source_sequence"
    )
    if not unclassified.is_empty():
        invalid_unclassified = unclassified.filter(
            pl.col("event_semantics_snapshot_id").is_not_null()
        )
        if not invalid_unclassified.is_empty():
            raise ValueError(
                "unclassified source sequence cannot claim registered official semantics"
            )

    classified = sequences.filter(
        pl.col("classification_status").is_in(["official_true_pa", "official_non_pa"])
    )
    if classified.is_empty():
        return
    invalid_nulls = classified.filter(
        pl.col("result_event_type").is_null()
        | pl.col("is_plate_appearance").is_null()
        | pl.col("event_semantics_snapshot_id").is_null()
    )
    if not invalid_nulls.is_empty():
        raise ValueError("classified play sequences have incomplete event semantics")

    joined = classified.join(
        definitions.select(
            [
                "event_semantics_snapshot_id",
                "event_type",
                pl.col("is_plate_appearance").alias("expected_is_plate_appearance"),
            ]
        ),
        left_on=["event_semantics_snapshot_id", "result_event_type"],
        right_on=["event_semantics_snapshot_id", "event_type"],
        how="left",
    )
    missing_definition = joined.filter(pl.col("expected_is_plate_appearance").is_null())
    if not missing_definition.is_empty():
        raise ValueError("classified play sequence references unregistered event semantics")
    disagreement = joined.filter(
        pl.col("is_plate_appearance") != pl.col("expected_is_plate_appearance")
    )
    if not disagreement.is_empty():
        raise ValueError("play sequence PA classification disagrees with registered semantics")
