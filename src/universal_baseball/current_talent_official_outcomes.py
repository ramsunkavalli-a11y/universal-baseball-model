"""Residual-triggered official game-log authority for historical batting outcomes.

Current Talent snapshots need game-grain chronology. A season aggregate can
identify that a player × league rollup disagrees with reusable player-game
history, but it cannot safely say *which game* should change. This module keeps
those responsibilities separate:

- season aggregates are an independent residual trigger/check;
- current official Stats API ``gameLog`` splits are the narrow adjudication
  oracle because they preserve game identity;
- source player-game values remain unchanged when official game logs agree;
- existing games may receive field-level official overlays;
- an official-only positive-PA game may be inserted explicitly at its official
  game date;
- distinct-team official splits for one player/game may be collapsed only when
  their identity/date/vector semantics agree; other duplicate official games fail closed;
- source-only positive-PA games, missing official fields, or post-overlay total
  disagreement fail closed.

The resulting history is retrospective corrected-event history. It must never be
labeled a vintage information-set backtest unless source availability at the
historical as-of date was separately captured.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

import polars as pl

from universal_baseball.current_talent_milb_evidence import OUTCOME_FIELDS


OFFICIAL_TO_OUTCOME: dict[str, str] = {
    "plateAppearances": "batting_PA",
    "atBats": "batting_AB",
    "baseOnBalls": "batting_BB",
    "hitByPitch": "batting_HBP",
    "strikeOuts": "batting_SO",
    "sacFlies": "batting_SF",
    "sacBunts": "batting_SH",
    "catchersInterference": "batting_CI",
}
OFFICIAL_GAME_LOG_POLICY = "residual_triggered_official_game_log_v2"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _row_aligned_to_schema(
    frame: pl.DataFrame,
    values: Mapping[str, Any],
) -> pl.DataFrame:
    """Build one row with exactly ``frame``'s column order and dtypes.

    Official-only historical games lack source-only metadata columns by design.
    Those fields must become typed nulls rather than relying on Polars diagonal
    concat inference, which can pair incompatible inferred dtypes (for example a
    Python ``date`` beside an integer column) when the source schema evolves.
    """

    if frame.is_empty() and not frame.columns:
        raise ValueError("cannot align an official outcome insert to an empty schema")
    expressions: list[pl.Expr] = []
    for column, dtype in frame.schema.items():
        value = values.get(column)
        if value is None:
            expressions.append(pl.lit(None, dtype=dtype).alias(column))
        else:
            expressions.append(
                pl.lit(value).cast(dtype, strict=False).alias(column)
            )
    row = pl.select(expressions)
    if row.schema != frame.schema:
        raise ValueError(
            "official outcome insert schema alignment failed: "
            f"row={row.schema}, target={frame.schema}"
        )
    return row


def official_game_log_endpoint(*, player_id: int, sport_id: int, season: int) -> str:
    params = {
        "stats": "gameLog",
        "group": "hitting",
        "season": int(season),
        "sportId": int(sport_id),
    }
    return f"people/{int(player_id)}/stats?{urlencode(params)}"


def _collapse_distinct_team_game_splits(frame: pl.DataFrame) -> pl.DataFrame:
    """Collapse safe same-player/game/league official team-stint splits.

    The Stats API can expose one game twice when a player has batting stats for
    two different teams under the same official game identity. Treat those as
    additive game components only when date, game type, league, player, and the
    complete outcome vector are all usable and every split has a distinct,
    non-null team. Same-team duplicates remain an error.
    """

    if frame.is_empty():
        return frame

    rows: list[dict[str, Any]] = []
    for group in frame.partition_by(
        ["game_id", "player_id", "league_id"], maintain_order=True
    ):
        if group.height == 1:
            rows.append(group.row(0, named=True))
            continue

        game_id = int(group.get_column("game_id")[0])
        player_id = int(group.get_column("player_id")[0])

        if group.get_column("game_date").null_count():
            raise ValueError(
                f"official duplicate gameLog rows lack date for player={player_id} "
                f"game={game_id}"
            )
        if group.get_column("game_date").n_unique() != 1:
            raise ValueError(
                f"official duplicate gameLog rows disagree on date for player={player_id} "
                f"game={game_id}"
            )
        if (
            group.get_column("game_type").null_count()
            or group.get_column("game_type").n_unique() != 1
        ):
            raise ValueError(
                f"official duplicate gameLog rows disagree on game type for player={player_id} "
                f"game={game_id}"
            )
        team_ids = group.get_column("team_id")
        if team_ids.null_count() or team_ids.n_unique() != group.height:
            raise ValueError(
                f"official duplicate gameLog rows are not distinct-team splits for "
                f"player={player_id} game={game_id}"
            )
        if any(group.get_column(field).null_count() for field in OUTCOME_FIELDS):
            raise ValueError(
                f"official duplicate gameLog rows lack complete outcome vectors for "
                f"player={player_id} game={game_id}"
            )

        first = group.row(0, named=True)
        rows.append(
            {
                **first,
                "team_id": None,
                **{
                    field: int(group.get_column(field).sum() or 0)
                    for field in OUTCOME_FIELDS
                },
            }
        )

    return pl.DataFrame(rows, schema=frame.schema, strict=False).sort(
        ["game_id", "player_id", "league_id"]
    )


def project_official_hitting_game_log(
    payload: Mapping[str, Any],
    *,
    player_id: int,
    sport_id: int,
) -> pl.DataFrame:
    """Project one official hitting gameLog payload to the MiLB outcome vector."""

    rows: list[dict[str, Any]] = []
    for stats_group in payload.get("stats") or []:
        for raw_split in _mapping(stats_group).get("splits") or []:
            split = _mapping(raw_split)
            game = _mapping(split.get("game"))
            league = _mapping(split.get("league"))
            team = _mapping(split.get("team"))
            sport = _mapping(split.get("sport"))
            stat = _mapping(split.get("stat"))
            game_id = _int(game.get("gamePk"))
            if game_id is None:
                game_id = _int(game.get("pk"))
            if game_id is None:
                game_id = _int(game.get("id"))
            if game_id is None:
                continue
            split_sport_id = _int(sport.get("id"))
            if split_sport_id is not None and split_sport_id != int(sport_id):
                raise ValueError(
                    f"official gameLog sport mismatch for player={player_id}: "
                    f"{split_sport_id} vs requested {sport_id}"
                )
            rows.append(
                {
                    "game_id": game_id,
                    "player_id": int(player_id),
                    "game_date": split.get("date"),
                    "game_type": split.get("gameType"),
                    "league_id": _int(league.get("id")),
                    "team_id": _int(team.get("id")),
                    **{
                        outcome_field: _int(stat.get(official_field))
                        for official_field, outcome_field in OFFICIAL_TO_OUTCOME.items()
                    },
                }
            )
    if not rows:
        return pl.DataFrame(
            schema={
                "game_id": pl.Int64,
                "player_id": pl.Int64,
                "game_date": pl.Date,
                "game_type": pl.String,
                "league_id": pl.Int64,
                "team_id": pl.Int64,
                **{field: pl.Int64 for field in OUTCOME_FIELDS},
            }
        )
    projected = pl.DataFrame(rows).with_columns(
        pl.col("game_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("game_date").cast(pl.String).str.to_date(strict=False),
        pl.col("game_type").cast(pl.String),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("team_id").cast(pl.Int64, strict=False),
        *[pl.col(field).cast(pl.Int64, strict=False) for field in OUTCOME_FIELDS],
    )
    return _collapse_distinct_team_game_splits(projected)


def _sum_vector(frame: pl.DataFrame) -> dict[str, int]:
    return {
        field: int(frame.get_column(field).fill_null(0).sum() or 0)
        for field in OUTCOME_FIELDS
    }


def apply_official_game_log_outcome_authority(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Adjudicate one residual player × actual-league slice at game grain.

    Existing source safe dates are preserved on overlays. An official-only
    positive-PA game is inserted using the official game date and explicitly
    marked as such. Official-only zero-PA appearances are not batting evidence.
    """

    source_required = {
        "game_id",
        "player_id",
        "game_date",
        "game_date_conflict",
        "game_type",
        "league_id",
        "source_asset_count",
        "outcome_resolution",
        *OUTCOME_FIELDS,
    }
    official_required = {
        "game_id",
        "player_id",
        "game_date",
        "game_type",
        "league_id",
        *OUTCOME_FIELDS,
    }
    missing_source = sorted(source_required - set(resolved_outcomes.columns))
    missing_official = sorted(official_required - set(official_game_log.columns))
    if missing_source:
        raise ValueError(f"resolved outcomes missing official-adjudication fields: {missing_source}")
    if missing_official:
        raise ValueError(f"official gameLog missing adjudication fields: {missing_official}")

    target_source = resolved_outcomes.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    target_official = official_game_log.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
    )
    if target_source.is_empty():
        raise ValueError(f"no positive-PA source evidence for player={player_id} league={league_id}")
    if target_official.is_empty():
        diagnostic_games = sorted(
            int(value) for value in target_source.get_column("game_id").unique().to_list()
        )
        diagnostic_totals = _sum_vector(target_source)
        raise ValueError(
            f"no official gameLog evidence for player={player_id} league={league_id}; "
            f"source_games={diagnostic_games}; source_totals={diagnostic_totals}"
        )

    duplicate_official = target_official.group_by("game_id").len().filter(pl.col("len") > 1)
    if not duplicate_official.is_empty():
        raise ValueError("official gameLog is not unique by game for target player/league")
    official_positive = target_official.filter(
        pl.col("batting_PA").is_not_null() & (pl.col("batting_PA") > 0)
    )
    incomplete_official = official_positive.filter(
        pl.col("game_date").is_null()
        | pl.any_horizontal([pl.col(field).is_null() for field in OUTCOME_FIELDS])
    )
    if not incomplete_official.is_empty():
        raise ValueError("official positive-PA gameLog rows lack date or complete outcome vector")

    source_games = set(int(v) for v in target_source.get_column("game_id").unique().to_list())
    official_games = set(int(v) for v in official_positive.get_column("game_id").unique().to_list())
    source_only = sorted(source_games - official_games)
    if source_only:
        raise ValueError(
            f"source has positive-PA games absent from official gameLog for player={player_id}: {source_only}"
        )

    if "outcome_authority" in resolved_outcomes.columns:
        working = resolved_outcomes
    else:
        working = resolved_outcomes.with_columns(
            pl.lit("player_game_source").alias("outcome_authority")
        )

    evidence_rows: list[dict[str, Any]] = []
    overlay_games: list[int] = []
    insert_games: list[int] = []
    for game_id in sorted(source_games & official_games):
        source_row = target_source.filter(pl.col("game_id") == game_id).row(0, named=True)
        official_row = official_positive.filter(pl.col("game_id") == game_id).row(0, named=True)
        changed = [
            field for field in OUTCOME_FIELDS
            if int(source_row[field] or 0) != int(official_row[field] or 0)
        ]
        if not changed:
            continue
        overlay_games.append(game_id)
        predicate = (
            (pl.col("game_id") == game_id)
            & (pl.col("player_id") == int(player_id))
            & (pl.col("league_id") == int(league_id))
        )
        working = working.with_columns(
            *[
                pl.when(predicate)
                .then(pl.lit(int(official_row[field] or 0)))
                .otherwise(pl.col(field))
                .cast(pl.Int64)
                .alias(field)
                for field in OUTCOME_FIELDS
            ],
            pl.when(predicate)
            .then(pl.lit("official_game_log_overlay"))
            .otherwise(pl.col("outcome_resolution"))
            .alias("outcome_resolution"),
            pl.when(predicate)
            .then(pl.lit("official_game_log"))
            .otherwise(pl.col("outcome_authority"))
            .alias("outcome_authority"),
        )
        for field in changed:
            evidence_rows.append(
                {
                    "player_id": int(player_id),
                    "league_id": int(league_id),
                    "game_id": game_id,
                    "field": field,
                    "source_value": int(source_row[field] or 0),
                    "official_value": int(official_row[field] or 0),
                    "action": "overlay_existing_game",
                    "source_game_date": source_row["game_date"],
                    "official_game_date": official_row["game_date"],
                    "retained_game_date": source_row["game_date"],
                    "game_date_authority": "player_game_safe_date_retained",
                }
            )

    official_only_positive = sorted(official_games - source_games)
    for game_id in official_only_positive:
        official_row = official_positive.filter(pl.col("game_id") == game_id).row(0, named=True)
        insert_games.append(game_id)
        insert_values = {
            "game_id": game_id,
            "player_id": int(player_id),
            "game_date": official_row["game_date"],
            "game_date_conflict": False,
            "game_type": "R",
            "league_id": int(league_id),
            **{field: int(official_row[field] or 0) for field in OUTCOME_FIELDS},
            "source_asset_count": 0,
            "outcome_resolution": "official_game_log_insert",
            "outcome_authority": "official_game_log",
        }
        insert_frame = _row_aligned_to_schema(working, insert_values)
        working = pl.concat([working, insert_frame], how="vertical")
        for field in OUTCOME_FIELDS:
            official_value = int(official_row[field] or 0)
            if official_value == 0:
                continue
            evidence_rows.append(
                {
                    "player_id": int(player_id),
                    "league_id": int(league_id),
                    "game_id": game_id,
                    "field": field,
                    "source_value": None,
                    "official_value": official_value,
                    "action": "insert_official_only_positive_pa_game",
                    "source_game_date": None,
                    "official_game_date": official_row["game_date"],
                    "retained_game_date": official_row["game_date"],
                    "game_date_authority": "official_game_log_retrospective_date",
                }
            )

    corrected_target = working.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    source_totals = _sum_vector(target_source)
    official_totals = _sum_vector(official_positive)
    corrected_totals = _sum_vector(corrected_target)
    if corrected_totals != official_totals:
        raise ValueError(
            "official gameLog adjudication did not reconcile target totals: "
            f"corrected={corrected_totals}, official={official_totals}"
        )

    evidence_schema = {
        "player_id": pl.Int64,
        "league_id": pl.Int64,
        "game_id": pl.Int64,
        "field": pl.String,
        "source_value": pl.Int64,
        "official_value": pl.Int64,
        "action": pl.String,
        "source_game_date": pl.Date,
        "official_game_date": pl.Date,
        "retained_game_date": pl.Date,
        "game_date_authority": pl.String,
    }
    evidence = (
        pl.DataFrame(evidence_rows, schema=evidence_schema, strict=False)
        if evidence_rows
        else pl.DataFrame(schema=evidence_schema)
    )
    classification = (
        "official_confirms_source"
        if source_totals == official_totals
        else "official_corrects_player_game_source"
    )
    return (
        working.sort(["game_id", "player_id"]),
        evidence.sort(["game_id", "field"]),
        {
            "policy": OFFICIAL_GAME_LOG_POLICY,
            "player_id": int(player_id),
            "league_id": int(league_id),
            "classification": classification,
            "source_positive_pa_game_count": len(source_games),
            "official_positive_pa_game_count": len(official_games),
            "overlay_existing_game_count": len(overlay_games),
            "insert_official_only_positive_pa_game_count": len(insert_games),
            "source_only_positive_pa_game_count": 0,
            "changed_field_count": int(evidence.height),
            "source_totals": source_totals,
            "official_totals": official_totals,
            "corrected_totals": corrected_totals,
            "retrospective_corrected_history": True,
            "vintage_information_set": False,
        },
    )
