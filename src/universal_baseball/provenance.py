"""Canonical source and normalization provenance utilities.

An upstream source snapshot and our interpretation of that snapshot are separate
identities. Re-running newer normalization code over identical raw bytes must
create a new normalization definition without pretending the upstream evidence
changed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import re
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validated_sha256(value: str, *, field_name: str = "content_sha256") -> str:
    normalized = value.strip().lower()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(
            f"{field_name} must be exactly 64 hexadecimal characters"
        )
    return normalized


def _require_aware_utc(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if offset.total_seconds() != 0:
        raise ValueError(f"{field_name} must be normalized to UTC")
    return value


def make_source_snapshot_id(
    *,
    source_name: str,
    content_sha256: str,
    upstream_version: str | None = None,
) -> str:
    """Return a deterministic identity for immutable upstream content."""

    source = source_name.strip()
    if not source:
        raise ValueError("source_name cannot be blank")
    digest = _validated_sha256(content_sha256)
    version = (upstream_version or "").strip()
    material = "\x1f".join((source, version, digest)).encode("utf-8")
    return sha256(material).hexdigest()


def make_normalization_id(
    *,
    source_snapshot_id: str,
    normalizer_name: str,
    normalizer_version: str,
    canonical_schema_version: str,
) -> str:
    """Identify the deterministic interpretation applied to one source snapshot."""

    snapshot = _validated_sha256(
        source_snapshot_id, field_name="source_snapshot_id"
    )
    name = normalizer_name.strip()
    version = normalizer_version.strip()
    schema_version = canonical_schema_version.strip()
    if not all((name, version, schema_version)):
        raise ValueError("normalization definition text fields cannot be blank")
    material = "\x1f".join(
        (snapshot, name, version, schema_version)
    ).encode("utf-8")
    return sha256(material).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Immutable metadata for one exact upstream source representation."""

    source_snapshot_id: str
    source_name: str
    source_role: str
    upstream_locator: str
    upstream_version: str | None
    content_sha256: str
    source_published_at_utc: datetime | None
    retrieved_at_utc: datetime
    knowledge_available_at_utc: datetime | None
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
        raw_object_key: str,
        upstream_version: str | None = None,
        source_published_at_utc: datetime | None = None,
        knowledge_available_at_utc: datetime | None = None,
        license_id: str | None = None,
    ) -> "SourceSnapshot":
        source_name = source_name.strip()
        source_role = source_role.strip()
        upstream_locator = upstream_locator.strip()
        raw_object_key = raw_object_key.strip()
        if not all((source_name, source_role, upstream_locator, raw_object_key)):
            raise ValueError("required source snapshot text fields cannot be blank")

        digest = _validated_sha256(content_sha256)
        published = _require_aware_utc(
            source_published_at_utc, "source_published_at_utc"
        )
        retrieved = _require_aware_utc(retrieved_at_utc, "retrieved_at_utc")
        knowledge = _require_aware_utc(
            knowledge_available_at_utc, "knowledge_available_at_utc"
        )
        if retrieved is None:
            raise ValueError("retrieved_at_utc is required")

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
            license_id=license_id.strip() if license_id else None,
            raw_object_key=raw_object_key,
        )

    def as_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NormalizationDefinition:
    """Versioned interpretation of one immutable source snapshot."""

    normalization_id: str
    source_snapshot_id: str
    normalizer_name: str
    normalizer_version: str
    canonical_schema_version: str

    @classmethod
    def build(
        cls,
        *,
        source_snapshot_id: str,
        normalizer_name: str,
        normalizer_version: str,
        canonical_schema_version: str,
    ) -> "NormalizationDefinition":
        snapshot = _validated_sha256(
            source_snapshot_id, field_name="source_snapshot_id"
        )
        name = normalizer_name.strip()
        version = normalizer_version.strip()
        schema_version = canonical_schema_version.strip()
        normalization_id = make_normalization_id(
            source_snapshot_id=snapshot,
            normalizer_name=name,
            normalizer_version=version,
            canonical_schema_version=schema_version,
        )
        return cls(
            normalization_id=normalization_id,
            source_snapshot_id=snapshot,
            normalizer_name=name,
            normalizer_version=version,
            canonical_schema_version=schema_version,
        )

    def as_record(self) -> dict[str, Any]:
        return asdict(self)
