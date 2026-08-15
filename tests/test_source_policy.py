from __future__ import annotations

import json
from pathlib import Path

import pytest

from universal_baseball.source_policy import load_source_policies, source_policy_by_name


def test_repo_source_policy_manifest_is_valid() -> None:
    payload = load_source_policies(Path("config/source-policies.json"))

    armstjc = source_policy_by_name(payload, "armstjc_milb_pbp")
    chadwick = source_policy_by_name(payload, "chadwick_register")
    official = source_policy_by_name(payload, "mlb_stats_api_playbyplay")

    assert armstjc["license_id"] == "MIT"
    assert armstjc["attribution_required"] is True
    assert chadwick["license_id"] == "ODC-By-1.0"
    assert chadwick["attribution_required"] is True
    assert official["license_id"] is None
    assert official["redistribution_policy"] == "review_required_before_public_redistribution"


def test_source_policy_validation_rejects_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "policies.json"
    payload = {
        "manifest_version": 1,
        "sources": [
            {
                "source_name": "same",
                "upstream": "one",
                "role": "official_authority",
                "license_id": None,
                "attribution_required": None,
                "redistribution_policy": "review_required_before_public_redistribution",
                "notes": "one",
            },
            {
                "source_name": "same",
                "upstream": "two",
                "role": "official_authority",
                "license_id": None,
                "attribution_required": None,
                "redistribution_policy": "review_required_before_public_redistribution",
                "notes": "two",
            },
        ],
        "policy": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate source policy"):
        load_source_policies(path)
