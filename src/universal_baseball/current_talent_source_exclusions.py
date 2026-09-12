"""Narrow, fingerprinted exclusions for unusable historical game evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


CERTIFIED_GAME_EXCLUSION_POLICY = "certified_historical_game_exclusion_v1"


@dataclass(frozen=True, slots=True)
class HistoricalSourceGameExclusion:
    season: int
    game_id: int
    game_date: str
    source_kinds: frozenset[str]
    reason: str


HISTORICAL_SOURCE_GAME_EXCLUSIONS = (
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=755829,
        game_date="2024-06-16",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled: Rain; reusable source "
            "contains non-official positive-PA evidence."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=754395,
        game_date="2024-05-05",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled: Rain; reusable source "
            "contains non-official positive-PA evidence."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=774353,
        game_date="2024-07-09",
        source_kinds=frozenset({"pbp"}),
        reason=(
            "Reusable PBP has no same-game player-game league or participant authority; "
            "official feed supplies no player records."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=774292,
        game_date="2024-07-09",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled: Rain; reusable source "
            "contains non-official positive-PA evidence."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=774578,
        game_date="2024-07-09",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled: Lightning; reusable source "
            "contains non-official positive-PA evidence."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=774039,
        game_date="2024-07-09",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled; reusable source contains "
            "non-official positive-PA evidence."
        ),
    ),
    HistoricalSourceGameExclusion(
        season=2024,
        game_id=774458,
        game_date="2024-07-09",
        source_kinds=frozenset({"player_game", "pbp"}),
        reason=(
            "Official Stats API game record is Cancelled; reusable source contains "
            "non-official positive-PA evidence."
        ),
    ),
)


def apply_certified_historical_game_exclusions(
    frame: pl.DataFrame,
    *,
    season: int,
    source_kind: str,
    game_id_column: str,
    game_date_column: str,
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Exclude only registered games while requiring their date/type fingerprint."""

    if source_kind not in {"player_game", "pbp"}:
        raise ValueError(f"unsupported historical source kind: {source_kind!r}")
    required = {game_id_column, game_date_column}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"historical game exclusion missing fields: {missing}")
    result = frame
    evidence: list[dict[str, Any]] = []
    for exclusion in HISTORICAL_SOURCE_GAME_EXCLUSIONS:
        if exclusion.season != int(season) or source_kind not in exclusion.source_kinds:
            continue
        game_id = pl.col(game_id_column).cast(pl.Int64, strict=False)
        matches = result.filter(game_id == exclusion.game_id)
        if matches.is_empty():
            continue
        observed_dates = sorted(
            {
                str(value)[:10]
                for value in matches.get_column(game_date_column).drop_nulls().to_list()
            }
        )
        if observed_dates != [exclusion.game_date]:
            raise ValueError(
                f"certified game exclusion date drifted for game={exclusion.game_id}: "
                f"observed={observed_dates}, expected={exclusion.game_date}"
            )
        if "game_type" in matches.columns:
            observed_types = {
                str(value) for value in matches.get_column("game_type").drop_nulls().to_list()
            }
            if observed_types != {"R"}:
                raise ValueError(
                    f"certified game exclusion type drifted for game={exclusion.game_id}: "
                    f"observed={sorted(observed_types)}"
                )
        evidence.append(
            {
                "season": exclusion.season,
                "game_id": exclusion.game_id,
                "game_date": exclusion.game_date,
                "source_kind": source_kind,
                "excluded_source_rows": matches.height,
                "policy": CERTIFIED_GAME_EXCLUSION_POLICY,
                "reason": exclusion.reason,
            }
        )
        result = result.filter(game_id != exclusion.game_id)
    return result, evidence
