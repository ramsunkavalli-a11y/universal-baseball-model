"""Chronology-safe hitter level-tenure and advancement features.

Annual stat lines describe how much a player appeared at every level.  Dated
contact events add the level at which he finished the season.  Together they
distinguish a real level repeat from a short late promotion followed by a return.
"""

from __future__ import annotations

from collections import defaultdict
import math

import polars as pl


LEVEL_ALIASES = {
    "ROOKIE_COMPLEX": "RK",
    "ROOKIE": "RK",
    "HIGH_A": "A+",
    "SINGLE_A": "A",
    "SHORT_SEASON": "A-",
}
LEVEL_RANK = {"RK": 0, "A-": 1, "A": 2, "A+": 3, "AA": 4, "AAA": 5, "MLB": 6}
PARTIAL_TERMINAL_SHARE = 0.50
SUBSTANTIAL_LEVEL_SHARE = 0.50
COMPACT_LEVEL_PATH_FEATURES = (
    "level_path__primary_level_share",
    "level_path__terminal_evidence_available",
    "level_path__terminal_level_rank",
    "level_path__terminal_level_share",
    "level_path__primary_level_change",
    "level_path__terminal_level_change",
    "level_path__same_primary_as_prior",
    "level_path__returned_to_prior_terminal",
    "level_path__prior_terminal_level_share",
    "level_path__prior_terminal_partial_promotion",
    "level_path__returned_after_partial_promotion",
    "level_path__substantial_same_level_repeat",
    "level_path__prior_seasons_at_primary",
    "level_path__third_or_later_at_primary",
    "level_path__consecutive_seasons_at_primary",
    "level_path__log_prior_career_pa_at_primary",
    "level_path__below_previous_peak",
    "level_path__affiliated_seasons",
    "level_path__level_gain_per_affiliated_season",
)


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _normal_level(column: str) -> pl.Expr:
    return (
        pl.col(column)
        .cast(pl.String)
        .str.to_uppercase()
        .replace(LEVEL_ALIASES)
    )


def build_terminal_level_evidence(
    contacts: pl.DataFrame, games: pl.DataFrame
) -> pl.DataFrame:
    """Return the last observed contact level for each hitter-season.

    The evidence is deliberately labelled as contact-based.  It is an exact dated
    observation of the player's last recorded ball in play, not a claim that every
    plate appearance is present in the contact file.
    """

    _require(
        contacts,
        {"season", "game_pk", "at_bat_index", "player_id", "source_level"},
        "contact events",
    )
    _require(games, {"season", "game_pk", "game_date"}, "game context")
    game_dates = games.select("season", "game_pk", "game_date").unique(
        ["season", "game_pk"], keep="last"
    )
    events = (
        contacts.join(
            game_dates,
            on=["season", "game_pk"],
            how="left",
            validate="m:1",
        )
        .with_columns(_normal_level("source_level").alias("_level"))
        .with_columns(
            pl.col("_level")
            .replace_strict(LEVEL_RANK, default=None)
            .cast(pl.Int8)
            .alias("_rank")
        )
        .filter(pl.col("game_date").is_not_null() & pl.col("_rank").is_not_null())
        .sort(["season", "player_id", "game_date", "game_pk", "at_bat_index"])
    )
    if events.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "player_id": pl.Int64,
                "terminal_level_rank": pl.Int8,
                "terminal_contact_date": pl.Date,
            }
        )
    return (
        events.group_by("season", "player_id", maintain_order=True)
        .agg(
            pl.col("_rank").last().alias("terminal_level_rank"),
            pl.col("game_date").last().alias("terminal_contact_date"),
        )
        .sort(["season", "player_id"])
    )


def _previous_season_is_contiguous(previous: int, current: int) -> bool:
    return current - previous == 1 or (previous == 2019 and current == 2021)


def build_level_path_features(
    stats: pl.DataFrame,
    terminal_evidence: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build one cumulative, cutoff-safe development-path row per player-season."""

    _require(
        stats,
        {"season", "player_id", "level_group", "plate_appearances"},
        "hitter statistics",
    )
    source = (
        stats.with_columns(_normal_level("level_group").alias("_level"))
        .with_columns(
            pl.col("_level")
            .replace_strict(LEVEL_RANK, default=None)
            .cast(pl.Int8)
            .alias("_rank"),
            pl.col("plate_appearances").fill_null(0).cast(pl.Float64).alias("_pa"),
        )
        .filter(pl.col("_rank").is_not_null() & (pl.col("_pa") > 0))
        .group_by("season", "player_id", "_rank")
        .agg(pl.col("_pa").sum().alias("level_pa"))
        .sort(["player_id", "season", "_rank"])
    )
    if source.is_empty():
        raise ValueError("hitter statistics contain no positive supported level exposure")

    terminal_lookup: dict[tuple[int, int], int] = {}
    if terminal_evidence is not None and not terminal_evidence.is_empty():
        _require(
            terminal_evidence,
            {"season", "player_id", "terminal_level_rank"},
            "terminal evidence",
        )
        for row in terminal_evidence.select(
            "season", "player_id", "terminal_level_rank"
        ).iter_rows(named=True):
            rank = row["terminal_level_rank"]
            if rank is not None:
                terminal_lookup[(int(row["season"]), int(row["player_id"]))] = int(rank)

    rows: list[dict[str, int | float]] = []
    for player_frame in source.partition_by("player_id", maintain_order=True):
        player_id = int(player_frame.item(0, "player_id"))
        history: list[dict[str, object]] = []
        career_pa: defaultdict[int, float] = defaultdict(float)
        seasons_at_level: defaultdict[int, int] = defaultdict(int)
        first_primary_rank: int | None = None
        max_prior_rank = -1

        for season_frame in player_frame.partition_by("season", maintain_order=True):
            season = int(season_frame.item(0, "season"))
            exposure = {
                int(rank): float(pa)
                for rank, pa in season_frame.select("_rank", "level_pa").iter_rows()
            }
            total_pa = float(sum(exposure.values()))
            primary_rank = max(exposure, key=lambda rank: (exposure[rank], rank))
            highest_rank = max(exposure)
            primary_pa = exposure[primary_rank]
            primary_share = primary_pa / total_pa
            terminal_available = int((season, player_id) in terminal_lookup)
            terminal_rank = terminal_lookup.get((season, player_id), primary_rank)
            terminal_pa = exposure.get(terminal_rank, 0.0)
            terminal_share = terminal_pa / total_pa

            previous = history[-1] if history else None
            prior_primary_rank = int(previous["primary_rank"]) if previous else -1
            prior_terminal_rank = int(previous["terminal_rank"]) if previous else -1
            prior_terminal_pa = float(previous["terminal_pa"]) if previous else 0.0
            prior_terminal_share = (
                float(previous["terminal_share"]) if previous else 0.0
            )
            prior_primary_share = float(previous["primary_share"]) if previous else 0.0
            same_primary = int(previous is not None and primary_rank == prior_primary_rank)
            returned_to_terminal = int(
                previous is not None and primary_rank == prior_terminal_rank
            )
            prior_partial_promotion = int(
                previous is not None
                and prior_terminal_rank > prior_primary_rank
                and prior_terminal_share < PARTIAL_TERMINAL_SHARE
            )
            returned_after_partial = int(
                returned_to_terminal == 1 and prior_partial_promotion == 1
            )
            substantial_repeat = int(
                same_primary == 1
                and primary_share >= SUBSTANTIAL_LEVEL_SHARE
                and prior_primary_share >= SUBSTANTIAL_LEVEL_SHARE
            )

            prior_seasons_here = seasons_at_level[primary_rank]
            prior_pa_here = career_pa[primary_rank]
            consecutive = 1
            for earlier in reversed(history):
                earlier_season = int(earlier["season"])
                later_season = season if consecutive == 1 else int(
                    history[len(history) - consecutive + 1]["season"]
                )
                if not _previous_season_is_contiguous(earlier_season, later_season):
                    break
                earlier_exposure = earlier["exposure"]
                if not isinstance(earlier_exposure, dict) or primary_rank not in earlier_exposure:
                    break
                consecutive += 1

            if first_primary_rank is None:
                first_primary_rank = primary_rank
            affiliated_seasons = len(history) + 1
            rows.append(
                {
                    "season": season,
                    "player_id": player_id,
                    "level_path__available": 1,
                    "level_path__season_pa": total_pa,
                    "level_path__primary_level_rank": primary_rank,
                    "level_path__highest_level_rank": highest_rank,
                    "level_path__terminal_level_rank": terminal_rank,
                    "level_path__terminal_evidence_available": terminal_available,
                    "level_path__levels_played": len(exposure),
                    "level_path__multi_level_season": int(len(exposure) > 1),
                    "level_path__primary_level_pa": primary_pa,
                    "level_path__primary_level_share": primary_share,
                    "level_path__terminal_level_pa": terminal_pa,
                    "level_path__terminal_level_share": terminal_share,
                    "level_path__prior_primary_level_rank": prior_primary_rank,
                    "level_path__prior_terminal_level_rank": prior_terminal_rank,
                    "level_path__primary_level_change": (
                        primary_rank - prior_primary_rank if previous else 0
                    ),
                    "level_path__terminal_level_change": (
                        terminal_rank - prior_terminal_rank if previous else 0
                    ),
                    "level_path__same_primary_as_prior": same_primary,
                    "level_path__returned_to_prior_terminal": returned_to_terminal,
                    "level_path__prior_terminal_level_pa": prior_terminal_pa,
                    "level_path__prior_terminal_level_share": prior_terminal_share,
                    "level_path__prior_terminal_partial_promotion": prior_partial_promotion,
                    "level_path__returned_after_partial_promotion": returned_after_partial,
                    "level_path__substantial_same_level_repeat": substantial_repeat,
                    "level_path__prior_seasons_at_primary": prior_seasons_here,
                    "level_path__seasons_at_primary": prior_seasons_here + 1,
                    "level_path__third_or_later_at_primary": int(prior_seasons_here >= 2),
                    "level_path__consecutive_seasons_at_primary": consecutive,
                    "level_path__prior_career_pa_at_primary": prior_pa_here,
                    "level_path__career_pa_at_primary": prior_pa_here + primary_pa,
                    "level_path__log_prior_career_pa_at_primary": math.log1p(prior_pa_here),
                    "level_path__log_career_pa_at_primary": math.log1p(
                        prior_pa_here + primary_pa
                    ),
                    "level_path__max_prior_level_rank": max_prior_rank,
                    "level_path__below_previous_peak": int(
                        max_prior_rank >= 0 and primary_rank < max_prior_rank
                    ),
                    "level_path__affiliated_seasons": affiliated_seasons,
                    "level_path__calendar_years_since_first": season
                    - int(player_frame.item(0, "season")),
                    "level_path__level_gain_from_first": primary_rank
                    - int(first_primary_rank),
                    "level_path__level_gain_per_affiliated_season": (
                        (primary_rank - int(first_primary_rank))
                        / max(affiliated_seasons - 1, 1)
                    ),
                }
            )
            history.append(
                {
                    "season": season,
                    "exposure": exposure,
                    "primary_rank": primary_rank,
                    "primary_share": primary_share,
                    "terminal_rank": terminal_rank,
                    "terminal_pa": terminal_pa,
                    "terminal_share": terminal_share,
                }
            )
            for rank, pa in exposure.items():
                career_pa[rank] += pa
                seasons_at_level[rank] += 1
            max_prior_rank = max(max_prior_rank, highest_rank)

    return pl.DataFrame(rows).sort(["season", "player_id"])


def add_level_path_features(
    panel: pl.DataFrame, features: pl.DataFrame
) -> pl.DataFrame:
    """Attach the cumulative path known at each forecast origin."""

    _require(panel, {"origin_year", "player_id"}, "hitter panel")
    _require(features, {"season", "player_id"}, "level path features")
    feature_columns = [
        column for column in features.columns if column not in {"season", "player_id"}
    ]
    if not feature_columns:
        raise ValueError("level path feature block is empty")
    result = panel.join(
        features.rename({"season": "origin_year"}),
        on=["origin_year", "player_id"],
        how="left",
        validate="1:1",
    )
    return result.with_columns(
        pl.col(column).fill_null(0) for column in feature_columns
    ).sort(["origin_year", "player_id"])
