"""Inventory metadata for the reusable armstjc MiLB release assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
from typing import Any, Iterable

import requests


_ASSET_RE = re.compile(
    r"^(?P<year>\d{4})_(?P<period>\d{1,2})_(?P<level>aaa|aa|a\+|a|a-|rk)_pbp\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ArmstjcAsset:
    asset_id: int
    name: str
    size_bytes: int
    created_at_utc: datetime
    updated_at_utc: datetime
    browser_download_url: str
    year: int
    filename_period: int
    filename_level: str

    def as_record(self) -> dict[str, Any]:
        return asdict(self)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"GitHub timestamp is not timezone-aware: {value!r}")
    return parsed.astimezone(UTC)


def parse_pbp_asset_name(name: str) -> tuple[int, int, str] | None:
    """Return ``(year, filename_period, level)`` for recognized PBP assets."""

    match = _ASSET_RE.fullmatch(name.strip())
    if match is None:
        return None
    year = int(match.group("year"))
    period = int(match.group("period"))
    level = match.group("level").lower()
    if not 1 <= period <= 12:
        raise ValueError(f"recognized PBP asset has invalid filename period: {name!r}")
    return year, period, level


def asset_from_github_payload(payload: dict[str, Any]) -> ArmstjcAsset | None:
    parsed = parse_pbp_asset_name(str(payload.get("name", "")))
    if parsed is None:
        return None
    year, period, level = parsed
    required = {
        "id",
        "name",
        "size",
        "created_at",
        "updated_at",
        "browser_download_url",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"GitHub release asset missing fields: {missing}")
    return ArmstjcAsset(
        asset_id=int(payload["id"]),
        name=str(payload["name"]),
        size_bytes=int(payload["size"]),
        created_at_utc=_parse_utc(str(payload["created_at"])),
        updated_at_utc=_parse_utc(str(payload["updated_at"])),
        browser_download_url=str(payload["browser_download_url"]),
        year=year,
        filename_period=period,
        filename_level=level,
    )


def validate_asset_inventory(assets: Iterable[ArmstjcAsset]) -> list[ArmstjcAsset]:
    rows = list(assets)
    if not rows:
        raise ValueError("armstjc PBP asset inventory cannot be empty")
    names: set[str] = set()
    ids: set[int] = set()
    for asset in rows:
        if asset.name in names:
            raise ValueError(f"duplicate armstjc asset name: {asset.name}")
        if asset.asset_id in ids:
            raise ValueError(f"duplicate armstjc asset id: {asset.asset_id}")
        if asset.size_bytes <= 0:
            raise ValueError(f"armstjc asset has non-positive size: {asset.name}")
        if asset.updated_at_utc < asset.created_at_utc:
            raise ValueError(f"armstjc asset updated before creation: {asset.name}")
        names.add(asset.name)
        ids.add(asset.asset_id)
    return sorted(
        rows,
        key=lambda row: (
            row.year,
            row.filename_period,
            row.filename_level,
            row.created_at_utc,
            row.asset_id,
        ),
    )


def fetch_pbp_asset_inventory(
    *,
    owner: str = "armstjc",
    repo: str = "milb-data-repository",
    release_tag: str = "pbp",
    session: requests.Session | None = None,
    per_page: int = 100,
    max_pages: int = 50,
) -> list[ArmstjcAsset]:
    """Fetch every recognized PBP asset through GitHub's paginated REST API.

    This inventories metadata only. It does not download the CSV assets.
    """

    owns_session = session is None
    client = session or requests.Session()
    client.headers.setdefault(
        "User-Agent", "universal-baseball-model-source-inventory/0.1"
    )
    try:
        release_response = client.get(
            f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{release_tag}",
            timeout=30,
        )
        release_response.raise_for_status()
        release_id = int(release_response.json()["id"])

        assets: list[ArmstjcAsset] = []
        for page in range(1, max_pages + 1):
            response = client.get(
                f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}/assets",
                params={"per_page": per_page, "page": page},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("GitHub release assets response must be a list")
            if not payload:
                break
            for raw in payload:
                if not isinstance(raw, dict):
                    continue
                asset = asset_from_github_payload(raw)
                if asset is not None:
                    assets.append(asset)
            if len(payload) < per_page:
                break
        else:
            raise RuntimeError(
                f"armstjc asset inventory exceeded max_pages={max_pages}; refusing partial inventory"
            )
        return validate_asset_inventory(assets)
    finally:
        if owns_session:
            client.close()
