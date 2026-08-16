"""Reusable armstjc MiLB player-game boxscore release helpers.

The public ``game_player_stats`` release is useful as a cheap, game-grain
identity check against pitch-level PBP.  It is not treated as canonical truth:
raw release snapshots retain provenance and exact duplicates are removed before
aggregation.  When cumulative player-game batting snapshots conflict, a current
state is selected only when exactly one observation component-wise dominates
all alternatives across PA, AB, SO, SF, and SH.  Non-monotonic conflicts remain
unresolved rather than being ordered by filename or upload time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
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
    contact count.  Partially populated batting contact inputs are kept as null
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
        *[_int_expr(column) for column in _BATTING_FIELDS],
        pl.lit(source_asset).alias("source_asset"),
    ).drop_nulls(PLAYER_GAME_KEY)

    if season is not None:
        projected = projected.filter(pl.col("game_date").str.starts_with(f"{season}-"))
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == game_type)

    has_any_batting = pl.any_horizontal(
        [pl.col(column).is_not_null() for column in _BATTING_FIELDS]
    )
    has_all_contact_inputs = pl.all_horizontal(
        [pl.col(column).is_not_null() for column in _CONTACT_INPUTS]
    )
    expected_contact = (
        pl.when(has_all_contact_inputs)
        .then(
            pl.col("batting_AB")
            - pl.col("batting_SO")
            + pl.col("batting_SF")
            + pl.col("batting_SH")
        )
        .when(~has_any_batting)
        .then(pl.lit(0, dtype=pl.Int64))
        .otherwise(None)
        .alias("expected_contact_count")
    )
    return projected.with_columns(expected_contact)


def _cumulative_batting_dominates(
    candidate: dict[str, Any], other: dict[str, Any]
) -> bool:
    """Whether candidate can be a later cumulative snapshot than ``other``.

    A null in the earlier observation provides no lower bound.  Any non-null
    earlier value must remain non-null and may not decrease in the candidate.
    """

    for field in _BATTING_FIELDS:
        candidate_value = candidate[field]
        other_value = other[field]
        if other_value is None:
            continue
        if candidate_value is None or int(candidate_value) < int(other_value):
            return False
    return True


def _resolved_row_from_selection(
    *,
    key: dict[str, int],
    summary: dict[str, Any],
    selection: dict[str, Any] | None,
    resolution: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        **key,
        "distinct_observation_count": int(summary["distinct_observation_count"]),
        "source_asset_count": int(summary["source_asset_count"]),
        "source_assets": summary["source_assets"],
        "batting_vector_count": int(summary["batting_vector_count"]),
        "resolved_by_componentwise_dominance": resolution == "componentwise_dominance",
        "player_game_resolution": resolution,
    }
    for field in _METADATA_FIELDS + _BATTING_FIELDS + ["expected_contact_count"]:
        row[field] = selection[field] if selection is not None else None
    return row


def resolve_player_game_batting(
    observations: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Exact-dedup and conservatively resolve cumulative player-game snapshots.

    The upstream monthly builder currently appends each successfully parsed game
    twice, so exact duplicates are measured and removed first.  Assets can also
    carry partial snapshots of games outside their apparent filename period.
    Filename chronology is therefore not used to pick a winner.

    For each player-game, immutable metadata must agree.  If more than one
    distinct cumulative batting vector exists, a current observation is selected
    only when exactly one vector component-wise dominates every alternative
    across PA, AB, SO, SF, and SH.  Otherwise that player-game stays unresolved.
    """

    if observations.is_empty():
        raise ValueError("player-game observations cannot be empty")
    required = set(
        PLAYER_GAME_KEY
        + _METADATA_FIELDS
        + _BATTING_FIELDS
        + ["expected_contact_count", "source_asset"]
    )
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"player-game observations missing fields: {missing}")

    raw_rows = observations.height
    exact = observations.unique(maintain_order=True)
    exact_duplicate_rows = raw_rows - exact.height

    # First collapse rows that differ only in release provenance.  This leaves
    # one logical observation per distinct player-game state while retaining
    # source provenance separately in the group summary.
    logical_fields = _METADATA_FIELDS + _BATTING_FIELDS + ["expected_contact_count"]
    logical = exact.select(PLAYER_GAME_KEY + logical_fields).unique(maintain_order=True)
    summaries = (
        exact.group_by(PLAYER_GAME_KEY)
        .agg(
            pl.len().alias("distinct_observation_count"),
            pl.col("source_asset").n_unique().alias("source_asset_count"),
            pl.col("source_asset").unique().sort().alias("source_assets"),
            pl.struct(_BATTING_FIELDS).n_unique().alias("batting_vector_count"),
            *[
                pl.col(field).drop_nulls().n_unique().alias(f"{field}_value_count")
                for field in _METADATA_FIELDS
            ],
        )
        .sort(PLAYER_GAME_KEY)
    )
    summary_by_key = {
        (int(row["game_id"]), int(row["player_id"])): row
        for row in summaries.to_dicts()
    }

    resolved_rows: list[dict[str, Any]] = []
    conflict_count = 0
    dominance_resolved_count = 0
    unresolved_conflict_count = 0
    metadata_conflict_count = 0

    for group in logical.partition_by(PLAYER_GAME_KEY, maintain_order=True):
        rows = group.to_dicts()
        first = rows[0]
        key_tuple = (int(first["game_id"]), int(first["player_id"]))
        summary = summary_by_key[key_tuple]
        key = {"game_id": key_tuple[0], "player_id": key_tuple[1]}

        metadata_conflict = any(
            int(summary[f"{field}_value_count"]) > 1 for field in _METADATA_FIELDS
        )
        if metadata_conflict:
            metadata_conflict_count += 1
            unresolved_conflict_count += 1
            resolved_rows.append(
                _resolved_row_from_selection(
                    key=key,
                    summary=summary,
                    selection=None,
                    resolution="unresolved_metadata_conflict",
                )
            )
            continue

        # Metadata nulls can differ from non-nulls across otherwise compatible
        # snapshots.  Fill each selected row with the sole non-null group value.
        metadata_values: dict[str, Any] = {}
        for field in _METADATA_FIELDS:
            non_null = [row[field] for row in rows if row[field] is not None]
            metadata_values[field] = non_null[0] if non_null else None

        # Distinct batting vectors, not source asset labels, define a snapshot
        # conflict.  This is what exposed the three 2024 AAA partial-game states.
        by_vector: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in rows:
            vector = tuple(row[field] for field in _BATTING_FIELDS)
            by_vector.setdefault(vector, row)
        candidates = list(by_vector.values())

        if len(candidates) == 1:
            selected = dict(candidates[0])
            selected.update(metadata_values)
            resolved_rows.append(
                _resolved_row_from_selection(
                    key=key,
                    summary=summary,
                    selection=selected,
                    resolution="consensus",
                )
            )
            continue

        conflict_count += 1
        dominators = [
            candidate
            for candidate in candidates
            if all(
                _cumulative_batting_dominates(candidate, other)
                for other in candidates
            )
        ]
        if len(dominators) == 1:
            selected = dict(dominators[0])
            selected.update(metadata_values)
            dominance_resolved_count += 1
            resolved_rows.append(
                _resolved_row_from_selection(
                    key=key,
                    summary=summary,
                    selection=selected,
                    resolution="componentwise_dominance",
                )
            )
        else:
            unresolved_conflict_count += 1
            resolved_rows.append(
                _resolved_row_from_selection(
                    key=key,
                    summary=summary,
                    selection=None,
                    resolution="unresolved_nonmonotonic_conflict",
                )
            )

    resolved = pl.DataFrame(resolved_rows).sort(PLAYER_GAME_KEY)
    # Restore stable integer dtypes after dict-based resolution.
    resolved = resolved.with_columns(
        *[
            pl.col(field).cast(pl.Int64, strict=False)
            for field in [
                "game_id",
                "player_id",
                "league_id",
                "team_id",
                *_BATTING_FIELDS,
                "expected_contact_count",
                "distinct_observation_count",
                "source_asset_count",
                "batting_vector_count",
            ]
        ]
    )
    unresolved_contact_count = resolved.filter(
        pl.col("expected_contact_count").is_null()
    ).height

    diagnostics = {
        "raw_observation_count": raw_rows,
        "exact_unique_observation_count": exact.height,
        "exact_duplicate_row_count": exact_duplicate_rows,
        "resolved_player_game_count": resolved.height,
        "conflicting_player_game_count": conflict_count,
        "resolved_by_componentwise_dominance_count": dominance_resolved_count,
        "unresolved_conflicting_player_game_count": unresolved_conflict_count,
        "metadata_conflict_player_game_count": metadata_conflict_count,
        "unresolved_expected_contact_player_game_count": unresolved_contact_count,
    }
    return resolved, diagnostics


def identify_unambiguous_contact_reassignments(
    comparison: pl.DataFrame,
) -> pl.DataFrame:
    """Find strict source-only +1/-1 player-game reassignments.

    A game is repairable without official PBP only when exactly two players have
    non-zero residuals, one is +1 and the other -1, and the +1 player has exactly
    one source contact but zero expected boxscore contacts.  Under those
    conditions the contaminated source contact is unique and its recipient is
    unique.  Everything else stays in the exception queue.
    """

    required = {
        "game_id",
        "player_id",
        "source_contact_count",
        "expected_contact_count",
        "difference",
    }
    missing = sorted(required - set(comparison.columns))
    if missing:
        raise ValueError(f"contact comparison missing fields: {missing}")

    rows: list[dict[str, int]] = []
    for game in comparison.filter(pl.col("difference") != 0).partition_by(
        "game_id", maintain_order=True
    ):
        if game.height != 2:
            continue
        positive = game.filter(pl.col("difference") == 1)
        negative = game.filter(pl.col("difference") == -1)
        if positive.height != 1 or negative.height != 1:
            continue
        donor = positive.row(0, named=True)
        recipient = negative.row(0, named=True)
        if (
            int(donor["source_contact_count"]) != 1
            or int(donor["expected_contact_count"]) != 0
        ):
            continue
        rows.append(
            {
                "game_id": int(donor["game_id"]),
                "source_batter_id": int(donor["player_id"]),
                "reassigned_batter_id": int(recipient["player_id"]),
            }
        )

    return pl.DataFrame(
        rows,
        schema={
            "game_id": pl.Int64,
            "source_batter_id": pl.Int64,
            "reassigned_batter_id": pl.Int64,
        },
    )
