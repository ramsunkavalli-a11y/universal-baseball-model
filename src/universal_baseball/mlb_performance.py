"""MLB-specific source assembly for the universal batting Performance layer.

Baseball Savant supplies reusable MLB pitch/contact/profile evidence while the
bulk MLB Stats API supplies standard player-season outcome totals at actual
AL/NL grain. This module joins Savant batting-team evidence to the authoritative
season team->league map and provides deterministic source-side outcome summaries
for reconciliation.

Contextual bin values are intentionally outside this module; MLB must use the
same fixed 24-state RE24 definition as MiLB (ADR 022).
"""

from __future__ import annotations

from collections.abc import Iterable

import polars as pl

from universal_baseball.mlb_season_stats import MlbTeamLeague


MLB_LEAGUE_IDS = frozenset({103, 104})


def assign_savant_actual_league(
    savant: pl.DataFrame,
    team_leagues: Iterable[MlbTeamLeague],
) -> pl.DataFrame:
    """Assign each regular-season Savant row to batting team's AL/NL league.

    The mapping is season-specific authority from MLB team metadata. Unknown or
    missing batting-team abbreviations are hard errors because silently dropping
    them would corrupt traded-player actual-league Performance grain.
    """

    required = {"batting_team", "game_pk", "at_bat_index", "pitch_number"}
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"Savant rows missing MLB league-assignment fields: {missing}")
    if savant.is_empty():
        return savant.with_columns(pl.lit(None, dtype=pl.Int64).alias("league_id"))

    mapping_rows = [
        {
            "batting_team": row.abbreviation,
            "league_id": int(row.league_id),
            "league_name": row.league_name,
        }
        for row in team_leagues
    ]
    if not mapping_rows:
        raise ValueError("MLB team-league authority is empty")
    mapping = pl.DataFrame(mapping_rows).unique(subset=["batting_team"], keep="none")
    if mapping.height != len(mapping_rows):
        raise ValueError("MLB team-league authority has duplicate abbreviations")

    missing_team = savant.filter(
        pl.col("batting_team").is_null()
        | (pl.col("batting_team").cast(pl.String).str.strip_chars() == "")
    )
    if not missing_team.is_empty():
        raise ValueError(
            f"Savant has {missing_team.height} rows without resolvable batting team"
        )

    observed = set(str(value) for value in savant.get_column("batting_team").unique())
    known = set(str(value) for value in mapping.get_column("batting_team").unique())
    unknown = sorted(observed - known)
    if unknown:
        raise ValueError(f"Savant batting-team abbreviations absent from MLB authority: {unknown}")

    result = savant.join(mapping, on="batting_team", how="left")
    unresolved = result.filter(~pl.col("league_id").is_in(sorted(MLB_LEAGUE_IDS)))
    if not unresolved.is_empty():
        raise ValueError("Savant rows remain without certified AL/NL league assignment")
    return result.with_columns(pl.col("league_id").cast(pl.Int64))


def summarize_savant_terminal_outcomes(savant: pl.DataFrame) -> pl.DataFrame:
    """Summarize Savant true-PA terminal outcomes by player × actual league."""

    required = {
        "game_year",
        "league_id",
        "batter_mlbam_id",
        "events",
        "is_plate_appearance_terminal",
    }
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"Savant rows missing terminal outcome fields: {missing}")
    if savant.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "league_id": pl.Int64,
                "player_id": pl.Int64,
                "savant_plate_appearances": pl.Int64,
                "savant_base_on_balls": pl.Int64,
                "savant_hit_by_pitch": pl.Int64,
                "savant_strike_outs": pl.Int64,
            }
        )

    terminal = savant.filter(pl.col("is_plate_appearance_terminal"))
    if terminal.filter(pl.col("batter_mlbam_id").is_null()).height:
        raise ValueError("Savant true-PA terminal rows contain null batter identity")
    duplicate_sequences = (
        terminal.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_sequences.is_empty():
        raise ValueError("Savant contains multiple true-PA terminal rows per play sequence")

    return (
        terminal.group_by(
            pl.col("game_year").cast(pl.Int64).alias("season"),
            pl.col("league_id").cast(pl.Int64),
            pl.col("batter_mlbam_id").cast(pl.Int64).alias("player_id"),
        )
        .agg(
            pl.len().alias("savant_plate_appearances"),
            pl.col("events")
            .is_in(["walk", "intent_walk"])
            .cast(pl.Int64)
            .sum()
            .alias("savant_base_on_balls"),
            (pl.col("events") == "hit_by_pitch")
            .cast(pl.Int64)
            .sum()
            .alias("savant_hit_by_pitch"),
            pl.col("events")
            .is_in(["strikeout", "strikeout_double_play"])
            .cast(pl.Int64)
            .sum()
            .alias("savant_strike_outs"),
        )
        .sort(["season", "league_id", "player_id"])
    )


def summarize_savant_contacts(savant: pl.DataFrame) -> pl.DataFrame:
    """Count reusable Savant physical contacts by player × actual league."""

    required = {"game_year", "league_id", "batter_mlbam_id", "is_contact"}
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"Savant rows missing contact summary fields: {missing}")
    if savant.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "league_id": pl.Int64,
                "player_id": pl.Int64,
                "savant_contact_count": pl.Int64,
            }
        )
    contacts = savant.filter(pl.col("is_contact"))
    return (
        contacts.group_by(
            pl.col("game_year").cast(pl.Int64).alias("season"),
            pl.col("league_id").cast(pl.Int64),
            pl.col("batter_mlbam_id").cast(pl.Int64).alias("player_id"),
        )
        .len(name="savant_contact_count")
        .sort(["season", "league_id", "player_id"])
    )
