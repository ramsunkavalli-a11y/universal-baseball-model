"""Canonical source-snapshot provenance utilities.

A source snapshot identifies immutable upstream evidence. Parser/normalizer code
is versioned separately so the same raw bytes can be re-normalized without
pretending the upstream source changed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import re
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validated_sha256(value: str) -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError("content_sha256 must be exactly 64 hexadecimal characters")
    return normalized


def _require_aware_utc(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field_name} must be normalized to UTC")
    return value


def make_source_snapshot_id(
    *,
    source_name: str,
    content_sha256: str,
    upstream_version: str | None = None,
) -> str:
    """Return a deterministic identity for immutable upstream content.

    The ID depends on the source family, exact content digest, and optional
    upstream version. It intentionally does not depend on parser version or
    retrieval path: changing our code does not change what the upstream bytes
    *are*.
    """

    source = source_name.strip()
    if not source:
        raise ValueError("source_name cannot be blank")
    digest = _validated_sha256(content_sha256)
    version = (upstream_version or "").strip()
    material = "\x1f".join((source, version, digest)).encode("utf-8")
    return sha256(material).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Immutable canonical metadata for one upstream source snapshot."""

    source_snapshot_id: str
    source_name: str
    source_role: str
    upstream_locator: str
    upstream_version: str | None
    content_sha256: str
    source_published_at_utc: datetime | None
    retrieved_at_utc: datetime
    knowledge_available_at_utc: datetime | None
    parser_name: str
    parser_version: str
    license_id: str | None
    raw_object_key: str

    @classmethod
    def build(
        cls,
        *,
        source_name: str,
        source_role: str,
        upstream_locator: str,
        content_sha256: str,
        retrieved_at_utc: datetime,
        parser_name: str,
        parser_version: str,
        raw_object_key: str,
        upstream_version: str | None = None,
        source_published_at_utc: datetime | None = None,
        knowledge_available_at_utc: datetime | None = None,
        license_id: str | None = None,
    ) -> "SourceSnapshot":
        source_name = source_name.strip()
        source_role = source_role.strip()
        upstream_locator = upstream_locator.strip()
        parser_name = parser_name.strip()
        parser_version = parser_version.strip()
        raw_object_key = raw_object_key.strip()
        if not all(
            (
                source_name,
                source_role,
                upstream_locator,
                parser_name,
                parser_version,
                raw_object_key,
            )
        ):
            raise ValueError("required source snapshot text fields cannot be blank")

        digest = _validated_sha256(content_sha256)
        published = _require_aware_utc(
            source_published_at_utc, "source_published_at_utc"
        )
        retrieved = _require_aware_utc(retrieved_at_utc, "retrieved_at_utc")
        knowledge = _require_aware_utc(
            knowledge_available_at_utc, "knowledge_available_at_utc"
        )
        assert retrieved is not None

        if published is not None and knowledge is not None and knowledge < published:
            raise ValueError(
                "knowledge_available_at_utc cannot precede source_published_at_utc"
            )
        if knowledge is not None and retrieved < knowledge:
            raise ValueError(
                "retrieved_at_utc cannot precede knowledge_available_at_utc"
            )

        version = upstream_version.strip() if upstream_version else None
        return cls(
            source_snapshot_id=make_source_snapshot_id(
                source_name=source_name,
                content_sha256=digest,
                upstream_version=version,
            ),
            source_name=source_name,
            source_role=source_role,
            upstream_locator=upstream_locator,
            upstream_version=version,
            content_sha256=digest,
            source_published_at_utc=published,
            retrieved_at_utc=retrieved,
            knowledge_available_at_utc=knowledge,
            parser_name=parser_name,
            parser_version=parser_version,
            license_id=license_id.strip() if license_id else None,
            raw_object_key=raw_object_key,
        )

    def as_record(self) -> dict[str, Any]:
        """Return a flat record suitable for a Polars source-snapshot table."""

        return asdict(self)
