from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from universal_baseball.provenance import SourceSnapshot, make_source_snapshot_id


DIGEST = "a" * 64


def test_source_snapshot_id_is_deterministic_and_parser_independent() -> None:
    first = make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=DIGEST,
        upstream_version="pbp-release",
    )
    second = make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=DIGEST.upper(),
        upstream_version="pbp-release",
    )

    assert first == second
    assert len(first) == 64


def test_source_snapshot_build_validates_and_preserves_temporal_semantics() -> None:
    published = datetime(2026, 8, 1, 12, tzinfo=UTC)
    knowledge = datetime(2026, 8, 1, 12, tzinfo=UTC)
    retrieved = datetime(2026, 8, 15, 19, tzinfo=UTC)

    snapshot = SourceSnapshot.build(
        source_name="armstjc_milb_pbp",
        source_role="historical_bootstrap",
        upstream_locator="release://2025_3_aaa_pbp.csv",
        upstream_version="pbp",
        content_sha256=DIGEST,
        source_published_at_utc=published,
        retrieved_at_utc=retrieved,
        knowledge_available_at_utc=knowledge,
        parser_name="armstjc_adapter",
        parser_version="0.1",
        license_id="MIT",
        raw_object_key="quarantine/armstjc/2025_3_aaa_pbp.csv",
    )

    assert snapshot.content_sha256 == DIGEST
    assert snapshot.source_published_at_utc == published
    assert snapshot.knowledge_available_at_utc == knowledge
    assert snapshot.retrieved_at_utc == retrieved
    assert snapshot.as_record()["source_snapshot_id"] == snapshot.source_snapshot_id


def test_unknown_historical_availability_stays_null() -> None:
    snapshot = SourceSnapshot.build(
        source_name="mlb_stats_api",
        source_role="official_authority",
        upstream_locator="game/39715/playByPlay",
        content_sha256="b" * 64,
        retrieved_at_utc=datetime(2026, 8, 15, 19, tzinfo=UTC),
        parser_name="official_projection",
        parser_version="0.1",
        raw_object_key="quarantine/mlb/game-39715.json",
    )

    assert snapshot.source_published_at_utc is None
    assert snapshot.knowledge_available_at_utc is None


def test_snapshot_rejects_fake_or_inconsistent_time_provenance() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SourceSnapshot.build(
            source_name="source",
            source_role="role",
            upstream_locator="thing",
            content_sha256=DIGEST,
            retrieved_at_utc=datetime(2026, 8, 15),
            parser_name="parser",
            parser_version="1",
            raw_object_key="raw/thing",
        )

    non_utc = timezone(timedelta(hours=-7))
    with pytest.raises(ValueError, match="normalized to UTC"):
        SourceSnapshot.build(
            source_name="source",
            source_role="role",
            upstream_locator="thing",
            content_sha256=DIGEST,
            retrieved_at_utc=datetime(2026, 8, 15, tzinfo=non_utc),
            parser_name="parser",
            parser_version="1",
            raw_object_key="raw/thing",
        )

    published = datetime(2026, 8, 10, tzinfo=UTC)
    knowledge = datetime(2026, 8, 9, tzinfo=UTC)
    with pytest.raises(ValueError, match="cannot precede source_published"):
        SourceSnapshot.build(
            source_name="source",
            source_role="role",
            upstream_locator="thing",
            content_sha256=DIGEST,
            source_published_at_utc=published,
            knowledge_available_at_utc=knowledge,
            retrieved_at_utc=datetime(2026, 8, 15, tzinfo=UTC),
            parser_name="parser",
            parser_version="1",
            raw_object_key="raw/thing",
        )


def test_snapshot_id_changes_with_source_family_or_content() -> None:
    baseline = make_source_snapshot_id(
        source_name="source-a",
        content_sha256="a" * 64,
    )
    assert baseline != make_source_snapshot_id(
        source_name="source-b",
        content_sha256="a" * 64,
    )
    assert baseline != make_source_snapshot_id(
        source_name="source-a",
        content_sha256="b" * 64,
    )
