import json

import pytest

from universal_baseball.source_capture import (
    persist_parsed_json_captures,
    verify_parsed_json_capture_manifest,
)


def test_persist_and_verify_parsed_json_captures(tmp_path) -> None:
    destination = tmp_path / "captures"
    manifest = persist_parsed_json_captures(
        [
            (
                "teams.json",
                {
                    "requested_url": "https://example.test/teams?season=2026",
                    "status_code": 200,
                    "content_type": "application/json",
                    "payload": {"teams": [{"name": "B", "id": 2}]},
                },
            )
        ],
        destination,
    )

    assert manifest["capture_count"] == 1
    assert manifest["original_response_bytes_retained"] is False
    record = manifest["records"][0]
    assert record["retrieval_time"] is None
    assert json.loads((destination / "teams.json").read_text()) == {
        "teams": [{"id": 2, "name": "B"}]
    }
    verify_parsed_json_capture_manifest(destination)


def test_verify_capture_manifest_detects_changed_payload(tmp_path) -> None:
    destination = tmp_path / "captures"
    persist_parsed_json_captures(
        [("people-001.json", {"status_code": 200, "payload": {"people": []}})],
        destination,
    )
    (destination / "people-001.json").write_text('{"people":[1]}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="capture hash mismatch"):
        verify_parsed_json_capture_manifest(destination)


@pytest.mark.parametrize("name", ["../escape.json", "nested/file.json", "capture.txt"])
def test_capture_filename_must_be_safe(name, tmp_path) -> None:
    with pytest.raises(ValueError, match="plain .json filename"):
        persist_parsed_json_captures(
            [(name, {"status_code": 200, "payload": {}})], tmp_path
        )
