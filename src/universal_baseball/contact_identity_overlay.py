"""Exception-only participant authority for reusable contact evidence.

ADR 020 accepts reusable physical contact rows by default but not their batter
identity unconditionally. Resolved player-game boxscores provide a cheap control:
if any player/contact count residual exists in a game, official PBP is fetched
for that game and top-level matchup batter becomes participant authority on the
matching physical contact keys.

This module is pure transformation logic. It never performs network requests.
Callers decide how official exception rows are fetched/cached and preserve that
source provenance separately.
"""

from __future__ import annotations

from typing import Any

import polars as pl


CONTACT_KEY = ("game_pk", "at_bat_index", "pitch_number")
PLAYER_GAME_KEY = ("game_id", "player_id")
SOURCE_DEFAULT = "source_default"
OFFICIAL_EXCEPTION_OVERLAY = "official_exception_overlay"
OFFICIAL_CONTACT_AUTHORITY_SCHEMA: dict[str, pl.DataType] = {
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    "official_batter_id": pl.Int64,
}


def _validate_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    missing = sorted(set(key) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing key columns: {missing}")
    duplicates = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} contains duplicate keys at {key}")


def project_official_contact_authority(
    pa_frame: pl.DataFrame,
    pitch_frame: pl.DataFrame,
) -> pl.DataFrame:
    """Project official PA/pitch evidence to physical-contact participant authority.

    ``pa_frame`` and ``pitch_frame`` are the tolerant canonical projections
    returned by ``official.fetch_official_game_evidence``. Only physical pitches
    whose official ``is_in_play`` flag is true enter the authority table. Batter
    identity always comes from the top-level PA/matchup row, never a mutable
    offensive-substitution event.
    """

    pa_required = {"game_pk", "at_bat_number", "batter_id"}
    pitch_required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "is_in_play",
    }
    missing_pa = sorted(pa_required - set(pa_frame.columns))
    missing_pitch = sorted(pitch_required - set(pitch_frame.columns))
    if missing_pa:
        raise ValueError(f"official PA frame missing contact authority columns: {missing_pa}")
    if missing_pitch:
        raise ValueError(
            f"official pitch frame missing contact authority columns: {missing_pitch}"
        )
    if pitch_frame.is_empty():
        return pl.DataFrame(schema=OFFICIAL_CONTACT_AUTHORITY_SCHEMA)

    pa = (
        pa_frame.select(
            pl.col("game_pk").cast(pl.Int64, strict=False),
            pl.col("at_bat_number").cast(pl.Int64, strict=False).alias("at_bat_index"),
            pl.col("batter_id").cast(pl.Int64, strict=False).alias("official_batter_id"),
        )
        .drop_nulls(["game_pk", "at_bat_index"])
    )
    duplicate_pa = (
        pa.group_by(["game_pk", "at_bat_index"])
        .agg(pl.col("official_batter_id").drop_nulls().n_unique().alias("batter_count"))
        .filter(pl.col("batter_count") > 1)
    )
    if not duplicate_pa.is_empty():
        raise ValueError("official PA evidence has conflicting matchup batter identity")
    pa = pa.unique(subset=["game_pk", "at_bat_index"], keep="any")

    contacts = (
        pitch_frame.filter(pl.col("is_in_play") == True)  # noqa: E712
        .select(
            pl.col("game_pk").cast(pl.Int64, strict=False),
            pl.col("at_bat_number").cast(pl.Int64, strict=False).alias("at_bat_index"),
            pl.col("pitch_number").cast(pl.Int64, strict=False),
        )
        .drop_nulls(list(CONTACT_KEY))
        .join(pa, on=["game_pk", "at_bat_index"], how="left")
        .select(list(OFFICIAL_CONTACT_AUTHORITY_SCHEMA))
        .cast(OFFICIAL_CONTACT_AUTHORITY_SCHEMA, strict=True)
        .sort(list(CONTACT_KEY))
    )
    _validate_unique(contacts, CONTACT_KEY, "official contact authority")
    if contacts.filter(pl.col("official_batter_id").is_null()).height:
        raise ValueError("official physical contact lacks top-level matchup batter")
    return contacts


def contact_identity_residuals(
    contacts: pl.DataFrame,
    player_games: pl.DataFrame,
) -> pl.DataFrame:
    """Compare reusable contact attribution with resolved player-game controls."""

    required_contacts = {*CONTACT_KEY, "source_batter_id"}
    missing_contacts = sorted(required_contacts - set(contacts.columns))
    if missing_contacts:
        raise ValueError(f"contacts missing identity-control columns: {missing_contacts}")
    required_expected = {"game_id", "player_id", "expected_contact_count"}
    missing_expected = sorted(required_expected - set(player_games.columns))
    if missing_expected:
        raise ValueError(f"player-games missing identity-control columns: {missing_expected}")

    _validate_unique(contacts, CONTACT_KEY, "contacts")
    _validate_unique(player_games, PLAYER_GAME_KEY, "player-games")

    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise ValueError("contacts contain unresolved source batter identity")

    contact_games = contacts.get_column("game_pk").cast(pl.Int64).unique()
    expected = (
        player_games.filter(pl.col("game_id").cast(pl.Int64).is_in(contact_games))
        .select(
            pl.col("game_id").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("expected_contact_count").cast(pl.Int64, strict=False),
        )
    )
    if expected.filter(pl.col("expected_contact_count").is_null()).height:
        raise ValueError("player-game control contains unresolved expected contact counts")

    observed = (
        contacts.select(
            pl.col("game_pk").cast(pl.Int64).alias("game_id"),
            pl.col("source_batter_id").cast(pl.Int64).alias("player_id"),
        )
        .group_by(list(PLAYER_GAME_KEY))
        .len(name="source_contact_count")
    )
    return (
        observed.join(expected, on=list(PLAYER_GAME_KEY), how="full", coalesce=True)
        .with_columns(
            pl.col("source_contact_count").fill_null(0).cast(pl.Int64),
            pl.col("expected_contact_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (
                pl.col("source_contact_count") - pl.col("expected_contact_count")
            ).alias("contact_count_difference")
        )
        .sort(list(PLAYER_GAME_KEY))
    )


def exception_games_from_residuals(residuals: pl.DataFrame) -> list[int]:
    """Return sorted games with any non-zero player contact residual."""

    required = {"game_id", "contact_count_difference"}
    missing = sorted(required - set(residuals.columns))
    if missing:
        raise ValueError(f"contact residuals missing columns: {missing}")
    return sorted(
        int(value)
        for value in residuals.filter(pl.col("contact_count_difference") != 0)
        .get_column("game_id")
        .unique()
        .to_list()
    )


def _validate_official_exception_keys(
    contacts: pl.DataFrame,
    official_contacts: pl.DataFrame,
    exception_games: list[int],
) -> None:
    required = {*CONTACT_KEY, "official_batter_id"}
    missing = sorted(required - set(official_contacts.columns))
    if missing:
        raise ValueError(f"official contact authority missing columns: {missing}")
    _validate_unique(official_contacts, CONTACT_KEY, "official contact authority")

    if not exception_games:
        if not official_contacts.is_empty():
            raise ValueError("official contact authority supplied when no exception games exist")
        return

    supplied_games = sorted(
        int(value) for value in official_contacts.get_column("game_pk").unique().to_list()
    )
    if supplied_games != exception_games:
        raise ValueError(
            "official contact authority game set does not equal player-game exception set"
        )
    if official_contacts.filter(pl.col("official_batter_id").is_null()).height:
        raise ValueError("official contact authority contains null batter identity")

    source_keys = (
        contacts.filter(pl.col("game_pk").is_in(exception_games))
        .select(list(CONTACT_KEY))
        .sort(list(CONTACT_KEY))
    )
    official_keys = official_contacts.select(list(CONTACT_KEY)).sort(list(CONTACT_KEY))
    source_only = source_keys.join(official_keys, on=list(CONTACT_KEY), how="anti")
    official_only = official_keys.join(source_keys, on=list(CONTACT_KEY), how="anti")
    if not source_only.is_empty() or not official_only.is_empty():
        raise ValueError(
            "official participant overlay requires exact physical contact-key equality "
            "for every exception game"
        )


def apply_contact_identity_authority(
    contacts: pl.DataFrame,
    player_games: pl.DataFrame,
    official_contacts: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Resolve production batter identity under the ADR 020 exception policy.

    ``official_contacts`` must contain exactly the contact rows for every game
    flagged by the player-game control, and no rows for unflagged games. If there
    are no exception games it must be an empty frame with the expected schema.
    """

    residuals = contact_identity_residuals(contacts, player_games)
    exception_games = exception_games_from_residuals(residuals)
    _validate_official_exception_keys(contacts, official_contacts, exception_games)

    if exception_games:
        authority = official_contacts.select(
            *[pl.col(column).cast(pl.Int64) for column in CONTACT_KEY],
            pl.col("official_batter_id").cast(pl.Int64),
        )
        output = (
            contacts.join(authority, on=list(CONTACT_KEY), how="left")
            .with_columns(
                pl.when(pl.col("game_pk").is_in(exception_games))
                .then(pl.col("official_batter_id"))
                .otherwise(pl.col("source_batter_id"))
                .cast(pl.Int64)
                .alias("batter_mlbam_id"),
                pl.when(pl.col("game_pk").is_in(exception_games))
                .then(pl.lit(OFFICIAL_EXCEPTION_OVERLAY))
                .otherwise(pl.lit(SOURCE_DEFAULT))
                .alias("participant_authority"),
            )
        )
    else:
        output = contacts.with_columns(
            pl.col("source_batter_id").cast(pl.Int64).alias("batter_mlbam_id"),
            pl.lit(SOURCE_DEFAULT).alias("participant_authority"),
        )

    changed_batter_count = output.filter(
        pl.col("batter_mlbam_id") != pl.col("source_batter_id")
    ).height
    overlay_count = output.filter(
        pl.col("participant_authority") == OFFICIAL_EXCEPTION_OVERLAY
    ).height
    metrics: dict[str, Any] = {
        "contact_count": output.height,
        "exception_game_count": len(exception_games),
        "exception_game_ids": exception_games,
        "official_overlay_contact_count": overlay_count,
        "source_default_contact_count": output.height - overlay_count,
        "changed_batter_contact_count": changed_batter_count,
        "player_game_residual_row_count": residuals.filter(
            pl.col("contact_count_difference") != 0
        ).height,
    }
    return output.drop("official_batter_id", strict=False), metrics
