"""Validation for the project source-attribution/redistribution policy manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_ALLOWED_REDISTRIBUTION = {
    "license_permits_reuse_with_notice",
    "attribution_required",
    "review_required_before_public_redistribution",
    "follow_upstream_notice",
}
_ALLOWED_ROLES = {
    "historical_bootstrap",
    "official_authority",
    "crosswalk",
    "tracking_enrichment_candidate",
    "historical_mlb_validation_candidate",
}


def load_source_policies(path: Path) -> dict[str, Any]:
    """Load and fail-fast validate the machine-readable source policy manifest."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("manifest_version") != 1:
        raise ValueError("unsupported source policy manifest_version")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source policy manifest must contain non-empty sources list")

    names: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"source policy entry {index} must be an object")
        required = {"source_name", "upstream", "role", "redistribution_policy", "notes"}
        missing = sorted(required - set(source))
        if missing:
            raise ValueError(f"source policy entry {index} missing fields: {missing}")
        name = str(source["source_name"]).strip()
        if not name:
            raise ValueError(f"source policy entry {index} has blank source_name")
        if name in names:
            raise ValueError(f"duplicate source policy: {name}")
        names.add(name)
        if source["role"] not in _ALLOWED_ROLES:
            raise ValueError(f"source policy {name} has unknown role {source['role']!r}")
        if source["redistribution_policy"] not in _ALLOWED_REDISTRIBUTION:
            raise ValueError(
                f"source policy {name} has unknown redistribution policy "
                f"{source['redistribution_policy']!r}"
            )
        attribution = source.get("attribution_required")
        if attribution not in (True, False, None):
            raise ValueError(
                f"source policy {name} attribution_required must be true/false/null"
            )
        license_id = source.get("license_id")
        if license_id is not None and not str(license_id).strip():
            raise ValueError(f"source policy {name} has blank license_id")

    policy = payload.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("source policy manifest missing top-level policy object")
    return payload


def source_policy_by_name(payload: dict[str, Any], source_name: str) -> dict[str, Any]:
    for source in payload["sources"]:
        if source["source_name"] == source_name:
            return source
    raise KeyError(source_name)
