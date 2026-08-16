"""Reusable MiLB source helpers for historical Current Talent materialization.

These transformations are deliberately independent of season-level Performance
calibration. They turn resolved/authorized reusable contact evidence into the
same contact-profile taxonomy used by the frozen Performance layer and provide
strict actual-league handling for explicitly supplied historical evidence.

Older reusable PBP can omit ``league_id`` even when the same game's structured
player-game boxscore row carries it.  Historical enrichment is therefore allowed
only through a unique same-game player-game map; filename level is never used as
a substitute for actual league identity.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events


AUTHORIZED_CONTACT_REQUIRED = frozenset(
    {
        "game_date",
        "league_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "participant_authority",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    }
)


def _integer_expr(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def derive_player_game_league_map(
    player_game_rows: pl.DataFrame,
    *,
    game_type: str | None = "R",
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Derive one structured actual-league ID per player-game source game.

    Multiple players/snapshots may observe the same game, but every non-null
    ``league_id`` must agree.  This map is suitable for enriching an older PBP
    schema that lacks league identity; it is not an environment translation.
    """

    required = {"game_id", "league_id"}
    if game_type is not None:
        required.add("game_type")
    missing = sorted(required - set(player_game_rows.columns))
    if missing:
        raise ValueError(f"player-game league-map source missing fields: {missing}")
    if player_game_rows.is_empty():
        raise ValueError("player-game league-map source cannot be empty")

    projected = player_game_rows.select(
        _integer_expr("game_id", "game_pk"),
        _integer_expr("league_id", "league_id"),
        *([pl.col("game_type").cast(pl.String)] if game_type is not None else []),
    ).drop_nulls(["game_pk"])
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == str(game_type))

    nonnull = projected.filter(pl.col("league_id").is_not_null())
    conflicts = (
        nonnull.group_by("game_pk")
        .agg(pl.col("league_id").n_unique().alias("league_id_count"))
        .filter(pl.col("league_id_count") > 1)
    )
    if not conflicts.is_empty():
        raise ValueError("player-game source has conflicting actual-league IDs within game")

    mapping = (
        nonnull.group_by("game_pk")
        .agg(pl.col("league_id").first().cast(pl.Int64).alias("league_id"))
        .sort("game_pk")
    )
    if mapping.is_empty():
        raise ValueError("player-game source produced no non-null game league mapping")
    return mapping, {
        "source_row_count": int(player_game_rows.height),
        "eligible_game_count": int(projected.get_column("game_pk").n_unique()),
        "mapped_game_count": int(mapping.height),
        "conflicting_game_count": 0,
        "league_id_authority": "player_game_same_game_structured",
    }


def enrich_historical_pbp_league_id(
    pbp_rows: pl.DataFrame,
    game_league_map: pl.DataFrame,
    *,
    source_asset: str,
    game_type: str | None = "R",
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Fill/validate historical PBP league identity from a same-game map.

    Native PBP league IDs, when present, are retained and must agree with the
    player-game map.  When the column is absent or null, only the unique same-game
    structured player-game value may fill it.  Regular-season PBP games lacking a
    map fail rather than inheriting a league from filename level.
    """

    if "game_pk" not in pbp_rows.columns:
        raise ValueError(f"{source_asset} missing game_pk for historical league enrichment")
    required_map = {"game_pk", "league_id"}
    missing_map = sorted(required_map - set(game_league_map.columns))
    if missing_map:
        raise ValueError(f"historical game league map missing fields: {missing_map}")
    duplicate_map = game_league_map.group_by("game_pk").len().filter(pl.col("len") > 1)
    if not duplicate_map.is_empty():
        raise ValueError("historical game league map is not unique by game_pk")

    native_present = "league_id" in pbp_rows.columns
    working = pbp_rows.with_columns(_integer_expr("game_pk", "_join_game_pk"))
    if native_present:
        working = working.with_columns(_integer_expr("league_id", "_native_league_id"))
    else:
        working = working.with_columns(pl.lit(None, dtype=pl.Int64).alias("_native_league_id"))

    authority_map = game_league_map.select(
        pl.col("game_pk").cast(pl.Int64).alias("_join_game_pk"),
        pl.col("league_id").cast(pl.Int64).alias("_mapped_league_id"),
    )
    joined = working.join(authority_map, on="_join_game_pk", how="left")

    eligible = joined
    if game_type is not None:
        if "game_type" not in joined.columns:
            raise ValueError(f"{source_asset} missing game_type for historical league enrichment")
        eligible = joined.filter(pl.col("game_type").cast(pl.String) == str(game_type))

    missing_authority = eligible.filter(pl.col("_mapped_league_id").is_null())
    if not missing_authority.is_empty():
        missing_games = sorted(
            int(value)
            for value in missing_authority.get_column("_join_game_pk").drop_nulls().unique().to_list()
        )
        raise ValueError(
            f"{source_asset} has regular-season PBP games without same-game league authority: "
            f"{missing_games[:20]}"
        )
    disagreements = eligible.filter(
        pl.col("_native_league_id").is_not_null()
        & (pl.col("_native_league_id") != pl.col("_mapped_league_id"))
    )
    if not disagreements.is_empty():
        raise ValueError(f"{source_asset} native PBP league IDs disagree with player-game map")

    enriched = (
        joined.with_columns(
            pl.coalesce([pl.col("_native_league_id"), pl.col("_mapped_league_id")])
            .cast(pl.Int64)
            .alias("league_id")
        )
        .drop("_join_game_pk", "_native_league_id", "_mapped_league_id")
    )
    filled = int(
        eligible.filter(
            pl.col("_native_league_id").is_null() & pl.col("_mapped_league_id").is_not_null()
        ).height
    )
    return enriched, {
        "source_asset": str(source_asset),
        "native_league_id_column_present": bool(native_present),
        "eligible_regular_season_row_count": int(eligible.height),
        "filled_league_id_row_count": filled,
        "missing_same_game_authority_row_count": 0,
        "native_vs_map_disagreement_row_count": 0,
        "league_id_authority": (
            "pbp_native_validated_against_player_game_same_game"
            if native_present
            else "player_game_same_game_structured"
        ),
    }


def validate_expected_actual_leagues(
    frame: pl.DataFrame,
    *,
    league_column: str,
    expected_league_ids: frozenset[int],
    label: str,
) -> dict[str, Any]:
    """Require exact non-null actual-league coverage for one historical slice."""

    if league_column not in frame.columns:
        raise ValueError(f"{label} missing actual-league column {league_column!r}")
    if not expected_league_ids:
        raise ValueError(f"{label} expected actual-league set cannot be empty")
    observed = {
        int(value)
        for value in frame.get_column(league_column).drop_nulls().cast(pl.Int64).unique().to_list()
    }
    expected = {int(value) for value in expected_league_ids}
    if observed != expected:
        raise ValueError(
            f"{label} actual-league coverage mismatch: "
            f"observed={sorted(observed)}, expected={sorted(expected)}"
        )
    return {
        "observed_league_ids": sorted(observed),
        "expected_league_ids": sorted(expected),
        "exact_actual_league_coverage": True,
    }


def classify_milb_current_talent_contacts(
    authorized_contacts: pl.DataFrame,
) -> pl.DataFrame:
    """Classify authorized historical physical contacts into frozen profile bins.

    No run values or season-end Performance totals are consulted. ``season`` is
    derived only from the retained event date, and source geometry/narrative is
    preserved as the contact-classification evidence.
    """

    missing = sorted(AUTHORIZED_CONTACT_REQUIRED - set(authorized_contacts.columns))
    if missing:
        raise ValueError(f"authorized MiLB contacts missing profile fields: {missing}")
    if authorized_contacts.is_empty():
        raise ValueError("authorized MiLB contacts cannot be empty")

    input_frame = (
        authorized_contacts.with_columns(
            pl.col("game_date")
            .cast(pl.String)
            .str.slice(0, 4)
            .cast(pl.Int64, strict=False)
            .alias("season"),
            pl.lit("source_certified_mirror").alias("result_description_authority"),
        )
        .select(
            "season",
            "league_id",
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "batter_mlbam_id",
            "participant_authority",
            "result_description_authority",
            "batter_side",
            "bb_type",
            "hc_x",
            "hc_y",
            "result_description",
        )
    )
    if input_frame.filter(pl.col("season").is_null()).height:
        raise ValueError("authorized MiLB contacts contain unparseable event year")

    classified = classify_contact_profile_events(input_frame)
    if classified.height != authorized_contacts.height:
        raise ValueError(
            "MiLB Current Talent contact classification changed physical row count: "
            f"{classified.height} vs {authorized_contacts.height}"
        )
    return classified
