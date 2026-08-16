"""Reusable GitHub release inventory for armstjc season-player statistics.

A release filename is discovery metadata, not evidence that the CSV is populated
or model-ready.  This helper records exact asset metadata and keeps zero/tiny
placeholder detection explicit so historical admission code does not construct
URLs or assume that a named asset contains data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
from typing import Any, Iterable, Literal

import requests


SeasonStatKind = Literal["batting", "pitching"]
_SEASON_STAT_ASSET_RE = re.compile(
    r"^(?P<year>\d{4})_(?P<level>aaa|aa|a\+|a|a-|rk|win)_season_"
    r"(?P<kind>batting|pitching)_stats\.csv$",
    re.IGNORECASE,
)
_RELEASE_TAGS: dict[SeasonStatKind, str] = {
    "batting": "season_player_batting",
    "pitching": "season_player_pitching",
}


@dataclass(frozen=True, slots=True)
class ArmstjcSeasonStatAsset:
    asset_id: int
    name: str
    size_bytes: int
    created_at_utc: datetime
    updated_at_utc: datetime
    browser_download_url: str
    year: int
    filename_level: str
    kind: SeasonStatKind

    def as_record(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_nonempty(self) -> bool:
        return self.size_bytes > 1


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"GitHub timestamp is not timezone-aware: {value!r}")
    return parsed.astimezone(UTC)


def parse_season_stat_asset_name(name: str) -> tuple[int, str, SeasonStatKind] | None:
    match = _SEASON_STAT_ASSET_RE.fullmatch(name.strip())
    if match is None:
        return None
    kind = match.group("kind").lower()
    if kind not in _RELEASE_TAGS:
        raise ValueError(f"unsupported season-stat kind in asset name: {name!r}")
    return int(match.group("year")), match.group("level").lower(), kind  # type: ignore[return-value]


def season_stat_asset_from_github_payload(
    payload: dict[str, Any],
    *,
    expected_kind: SeasonStatKind | None = None,
) -> ArmstjcSeasonStatAsset | None:
    parsed = parse_season_stat_asset_name(str(payload.get("name", "")))
    if parsed is None:
        return None
    year, level, kind = parsed
    if expected_kind is not None and kind != expected_kind:
        return None
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
        raise ValueError(f"GitHub season-stat release asset missing fields: {missing}")
    return ArmstjcSeasonStatAsset(
        asset_id=int(payload["id"]),
        name=str(payload["name"]),
        size_bytes=int(payload["size"]),
        created_at_utc=_parse_utc(str(payload["created_at"])),
        updated_at_utc=_parse_utc(str(payload["updated_at"])),
        browser_download_url=str(payload["browser_download_url"]),
        year=year,
        filename_level=level,
        kind=kind,
    )


def validate_season_stat_asset_inventory(
    assets: Iterable[ArmstjcSeasonStatAsset],
) -> list[ArmstjcSeasonStatAsset]:
    rows = list(assets)
    if not rows:
        raise ValueError("armstjc season-stat asset inventory cannot be empty")
    names: set[str] = set()
    ids: set[int] = set()
    for asset in rows:
        if asset.name in names:
            raise ValueError(f"duplicate armstjc season-stat asset name: {asset.name}")
        if asset.asset_id in ids:
            raise ValueError(f"duplicate armstjc season-stat asset id: {asset.asset_id}")
        if asset.size_bytes < 0:
            raise ValueError(f"armstjc season-stat asset has negative size: {asset.name}")
        if asset.updated_at_utc < asset.created_at_utc:
            raise ValueError(f"armstjc season-stat asset updated before creation: {asset.name}")
        names.add(asset.name)
        ids.add(asset.asset_id)
    return sorted(rows, key=lambda row: (row.year, row.filename_level, row.kind, row.asset_id))


def fetch_season_stat_asset_inventory(
    kind: SeasonStatKind,
    *,
    owner: str = "armstjc",
    repo: str = "milb-data-repository",
    session: requests.Session | None = None,
    per_page: int = 100,
    max_pages: int = 50,
) -> list[ArmstjcSeasonStatAsset]:
    """Fetch recognized season-player assets from the paginated GitHub release."""

    if kind not in _RELEASE_TAGS:
        raise ValueError(f"unsupported season-stat kind: {kind!r}")
    owns_session = session is None
    client = session or requests.Session()
    client.headers.setdefault("User-Agent", "universal-baseball-model-season-stat-inventory/0.1")
    try:
        release_response = client.get(
            f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{_RELEASE_TAGS[kind]}",
            timeout=30,
        )
        release_response.raise_for_status()
        release_id = int(release_response.json()["id"])

        assets: list[ArmstjcSeasonStatAsset] = []
        for page in range(1, max_pages + 1):
            response = client.get(
                f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}/assets",
                params={"per_page": per_page, "page": page},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("GitHub season-stat release assets response must be a list")
            if not payload:
                break
            for raw in payload:
                if not isinstance(raw, dict):
                    continue
                asset = season_stat_asset_from_github_payload(raw, expected_kind=kind)
                if asset is not None:
                    assets.append(asset)
            if len(payload) < per_page:
                break
        else:
            raise RuntimeError(
                f"season-stat asset inventory exceeded max_pages={max_pages}; refusing partial inventory"
            )
        return validate_season_stat_asset_inventory(assets)
    finally:
        if owns_session:
            client.close()


def select_season_stat_asset(
    assets: Iterable[ArmstjcSeasonStatAsset],
    *,
    year: int,
    filename_level: str,
    kind: SeasonStatKind,
    require_nonempty: bool = True,
) -> ArmstjcSeasonStatAsset:
    """Select exactly one explicit year × filename-level × kind asset."""

    key_level = str(filename_level).strip().lower()
    matches = [
        asset
        for asset in assets
        if asset.year == int(year) and asset.filename_level == key_level and asset.kind == kind
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {year} {key_level} {kind} season-stat asset; found {len(matches)}"
        )
    asset = matches[0]
    if require_nonempty and not asset.is_nonempty:
        raise ValueError(
            f"season-stat asset is empty/placeholder: {asset.name} size={asset.size_bytes}"
        )
    return asset
