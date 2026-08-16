"""Reusable armstjc MiLB player-game boxscore release helpers.

The public ``game_player_stats`` release is useful as a cheap, game-grain
identity check against pitch-level PBP. It is not treated as canonical truth:
raw release snapshots retain provenance and exact duplicates are removed before
aggregation. When cumulative player-game batting snapshots conflict, a current
state is selected only when exactly one observation component-wise dominates
all alternatives across PA, AB, SO, SF, and SH. Non-monotonic conflicts remain
unresolved rather than being ordered by filename or upload time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import os
import re
from typing import Any, Iterable

import polars as pl
import requests


_PLAYER_GAME_ASSET_RE = re.compile(
    r"^(?P<year>\d{4})_(?P<period>\d{1,2})_(?P<level>aaa|aa|a\+|a|a-|rk|win)"
    r"_player_game_stats\.csv$",
    re.IGNORECASE,
)

PLAYER_GAME_KEY = ["game_id", "player_id"]
_CONTACT_INPUTS = ["batting_AB", "batting_SO", "batting_SF", "batting_SH"]
_BATTING_FIELDS = ["batting_PA", *_CONTACT_INPUTS]
_METADATA_FIELDS = ["game_date", "game_type", "league_id", "team_id"]


@dataclass(frozen=True, slots=True)
class ArmstjcPlayerGameAsset:
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


def _apply_optional_github_auth(client: requests.Session) -> None:
    """Use Actions/CLI GitHub auth when available without requiring credentials.

    Public armstjc release inventory works anonymously, but long CI sessions can
    exhaust GitHub's low unauthenticated REST quota.  ``GITHUB_TOKEN`` is exposed
    explicitly by workflows that need the inventory; ``GH_TOKEN`` keeps local
    GitHub CLI environments equally reusable.  An explicitly configured session
    Authorization header always wins.
    """

    if "Authorization" in client.headers:
        return
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        client.headers["Authorization"] = f"Bearer {token}"


def parse_player_game_asset_name(name: str) -> tuple[int, int, str] | None:
    """Return ``(year, filename_period, level)`` for recognized assets."""

    match = _PLAYER_GAME_ASSET_RE.fullmatch(name.strip())
    if match is None:
        return None
    year = int(match.group("year"))
    period = int(match.group("period"))
    level = match.group("level").lower()
    if not 1 <= period <= 12:
        raise ValueError(f"recognized player-game asset has invalid period: {name!r}")
    return year, period, level


def player_game_asset_from_github_payload(
    payload: dict[str, Any],
) -> ArmstjcPlayerGameAsset | None:
    parsed = parse_player_game_asset_name(str(payload.get("name", "")))
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
        raise ValueError(f"GitHub player-game release asset missing fields: {missing}")
    return ArmstjcPlayerGameAsset(
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


def validate_player_game_asset_inventory(
    assets: Iterable[ArmstjcPlayerGameAsset],
) -> list[ArmstjcPlayerGameAsset]:
    rows = list(assets)
    if not rows:
        raise ValueError("armstjc player-game asset inventory cannot be empty")
    names: set[str] = set()
    ids: set[int] = set()
    for asset in rows:
        if asset.name in names:
            raise ValueError(f"duplicate armstjc player-game asset name: {asset.name}")
        if asset.asset_id in ids:
            raise ValueError(f"duplicate armstjc player-game asset id: {asset.asset_id}")
        if asset.size_bytes <= 0:
            raise ValueError(f"armstjc player-game asset has non-positive size: {asset.name}")
        if asset.updated_at_utc < asset.created_at_utc:
            raise ValueError(f"armstjc player-game asset updated before creation: {asset.name}")
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


def fetch_player_game_asset_inventory(
    *,
    owner: str = "armstjc",
    repo: str = "milb-data-repository",
    release_tag: str = "game_player_stats",
    session: requests.Session | None = None,
    per_page: int = 100,
    max_pages: int = 50,
) -> list[ArmstjcPlayerGameAsset]:
    """Fetch recognized player-game assets from the paginated GitHub release."""

    owns_session = session is None
    client = session or requests.Session()
    client.headers.setdefault(
        "User-Agent", "universal-baseball-model-player-game-inventory/0.1"
    )
    _apply_optional_github_auth(client)
    try:
        release_response = client.get(
            f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{release_tag}",
            timeout=30,
        )
        release_response.raise_for_status()
        release_id = int(release_response.json()["id"])

        assets: list[ArmstjcPlayerGameAsset] = []
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
                asset = player_game_asset_from_github_payload(raw)
                if asset is not None:
                    assets.append(asset)
            if len(payload) < per_page:
                break
        else:
            raise RuntimeError(
                f"player-game asset inventory exceeded max_pages={max_pages}; "
                "refusing partial inventory"
            )
        return validate_player_game_asset_inventory(assets)
    finally:
        if owns_session:
            client.close()


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def project_player_game_batting(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None = None,
    game_type: str | None = "R",
) -> pl.DataFrame:
    """Project a raw player-game CSV to fields needed for contact reconciliation.

    Batting rows with no batting stat payload are retained with a zero expected
    contact count. Partially populated batting contact inputs are kept as null
    rather than silently interpreted as zero.
    """

    required = {
        "game_id",
        "game_date",
        "game_type",
        "league_id",
        "team_id",
        "player_id",
        *_BATTING_FIELDS,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_asset} missing player-game fields: {missing}")

    projected = frame.select(
        _int_expr("game_id"),
        pl.col("game_date").cast(pl.String),
        pl.col("game_type").cast(pl.String),
        _int_expr("league_id"),
        _int_expr("team_id"),
        _int_expr("player_id"),
        *[_int_expr(field) for field in _BATTING_FIELDS],
        pl.lit(str(source_asset)).alias("source_asset"),
    ).drop_nulls(PLAYER_GAME_KEY)

    if season is not None:
        projected = projected.filter(pl.col("game_date").str.starts_with(f"{int(season)}-"))
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == str(game_type))

    all_batting_null = pl.all_horizontal([pl.col(field).is_null() for field in _BATTING_FIELDS])
    all_contact_inputs_present = pl.all_horizontal(
        [pl.col(field).is_not_null() for field in _CONTACT_INPUTS]
    )
    expected_contact = (
        pl.col("batting_AB")
        - pl.col("batting_SO")
        + pl.col("batting_SF")
        + pl.col("batting_SH")
    )
    return projected.with_columns(
        pl.when(all_batting_null)
        .then(pl.lit(0, dtype=pl.Int64))
        .when(all_contact_inputs_present)
        .then(expected_contact)
        .otherwise(None)
        .alias("expected_contact_count")
    )


def player_game_contact_residuals(frame: pl.DataFrame) -> pl.DataFrame:
    """Summarize contact-count residuals at player-game grain."""

    required = {"game_id", "player_id", "expected_contact_count", "source_asset"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"player-game frame missing residual fields: {missing}")

    return (
        frame.group_by(PLAYER_GAME_KEY)
        .agg(
            pl.col("expected_contact_count").max().alias("expected_contact_count"),
            pl.col("source_asset").n_unique().alias("source_asset_count"),
        )
        .sort(PLAYER_GAME_KEY)
    )
