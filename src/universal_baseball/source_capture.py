"""Durable, hash-verified persistence for parsed official-source responses."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            default=str,
        )
        + "\n"
    ).encode("utf-8")


def persist_parsed_json_captures(
    captures: Iterable[tuple[str, Mapping[str, Any]]],
    destination: Path,
) -> dict[str, object]:
    """Persist API payload values and a manifest without overstating byte fidelity.

    Source adapters currently expose ``response.json()`` values rather than the
    original response bytes.  The retained files therefore preserve the parsed
    JSON value with deterministic encoding.  Their hashes verify those retained
    files; they are not hashes of the server's original response body.
    """

    destination.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    seen_names: set[str] = set()
    for name, capture in captures:
        if not name or Path(name).name != name or not name.endswith(".json"):
            raise ValueError(f"capture name must be a plain .json filename: {name!r}")
        if name in seen_names:
            raise ValueError(f"duplicate capture filename: {name}")
        seen_names.add(name)
        payload = capture.get("payload")
        if not isinstance(payload, (dict, list)):
            raise ValueError(f"capture {name} lacks a JSON object or list payload")
        content = _canonical_json_bytes(payload)
        (destination / name).write_bytes(content)
        records.append(
            {
                "file": name,
                "requested_url": str(capture.get("requested_url") or ""),
                "source_snapshot_id": capture.get("source_snapshot_id"),
                "status_code": int(capture["status_code"]),
                "content_type": str(capture.get("content_type") or ""),
                "size_bytes": len(content),
                "sha256": sha256(content).hexdigest(),
                "representation": "canonical_utf8_json_from_parsed_response",
                "original_response_bytes_retained": False,
                "retrieval_time": None,
                "retrieval_time_basis": "not_exposed_by_current_source_adapter",
            }
        )

    manifest: dict[str, object] = {
        "schema_version": 1,
        "capture_count": len(records),
        "representation": "canonical_utf8_json_from_parsed_response",
        "original_response_bytes_retained": False,
        "records": records,
    }
    manifest_bytes = _canonical_json_bytes(manifest)
    (destination / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def verify_parsed_json_capture_manifest(destination: Path) -> None:
    """Fail if a retained capture is missing or differs from its manifest hash."""

    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    records = manifest.get("records")
    if not isinstance(records, list) or manifest.get("capture_count") != len(records):
        raise ValueError("capture manifest count is invalid")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("file"), str):
            raise ValueError("capture manifest record is invalid")
        path = destination / record["file"]
        if Path(record["file"]).name != record["file"] or not path.is_file():
            raise ValueError(f"capture file is missing: {record['file']}")
        if sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
            raise ValueError(f"capture hash mismatch: {record['file']}")
