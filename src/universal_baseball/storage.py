"""Small durable Parquet storage utilities for canonical tables."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4

import polars as pl

from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_fingerprint(schema: pl.Schema | dict[str, pl.DataType]) -> str:
    """Return a stable fingerprint of ordered canonical column names/types."""

    material = [
        {"name": name, "dtype": str(dtype)}
        for name, dtype in schema.items()
    ]
    payload = json.dumps(material, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ParquetArtifact:
    table_name: str
    canonical_schema_version: str
    path: str
    row_count: int
    file_size_bytes: int
    file_sha256: str
    schema_sha256: str

    def as_record(self) -> dict[str, str | int]:
        return asdict(self)


def write_canonical_parquet(
    frame: pl.DataFrame,
    path: Path,
    *,
    table_name: str,
) -> ParquetArtifact:
    """Atomically write a canonical frame as compressed Parquet.

    The caller is responsible for table-specific schema validation before this
    function. Writing to a sibling temporary file and then replacing the target
    prevents an interrupted job from leaving a half-written canonical artifact.
    """

    if path.suffix.lower() != ".parquet":
        raise ValueError("canonical table path must end in .parquet")
    table = table_name.strip()
    if not table:
        raise ValueError("table_name cannot be blank")

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        frame.write_parquet(
            temporary,
            compression="zstd",
            statistics=True,
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()

    return ParquetArtifact(
        table_name=table,
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
        path=str(path),
        row_count=frame.height,
        file_size_bytes=path.stat().st_size,
        file_sha256=sha256_file(path),
        schema_sha256=schema_fingerprint(frame.schema),
    )
