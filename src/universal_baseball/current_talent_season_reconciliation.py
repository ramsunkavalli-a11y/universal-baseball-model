"""Reconcile resolved MiLB player-game outcomes to season-player aggregates.

This is an independent admission check for historical Current Talent evidence.
The player-game source is summed to player × actual-league × season grain and
compared with the separately published season-player batting release after that
release is standardized by ``standardize_armstjc_season_stats``. Team rows are
aggregated within actual league so trades do not create false mismatches.

No mismatch is repaired here. Differences remain explicit diagnostic evidence
for source-coverage or semantic investigation before a season enters model
training.
"""

from __future__ import annotations

from typing import Any

import polars as pl


OUTCOME_RECONCILIATION_KEY = ("season", "league_id", "player_id")
OUTCOME_FIELD_MAP: tuple[tuple[str, str, str], ...] = (
    ("batting_PA", "batting_plate_appearances", "plate_appearances"),
    ("batting_BB", "batting_base_on_balls", "walks"),
    ("batting_HBP", "batting_hit_by_pitch", "hit_by_pitch"),
    ("batting_SO", "batting_strike_outs", "strikeouts"),
)


def reconcile_resolved_outcomes_to_season_aggregates(
    resolved_outcomes: pl.DataFrame,
    season_aggregates: pl.DataFrame,
    *,
    season: int,
    expected_league_ids: frozenset[int] | None = None,
    require_exact: bool = False,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Compare historical game outcomes with the independent season backbone.

    ``season_aggregates`` must already be standardized by
    ``standardize_armstjc_season_stats(..., "batting")``. ``require_exact=False``
    is the default because a newly audited historical season should persist
    discrepancy evidence before an acceptance decision is made. Callers may
    promote exactness later if empirical history supports it.
    """

    game_required = {"game_date", "game_type", "league_id", "player_id", "outcome_resolution"}
    game_required.update(game_field for game_field, _, _ in OUTCOME_FIELD_MAP)
    season_required = {"season", "league_id", "player_id"}
    season_required.update(season_field for _, season_field, _ in OUTCOME_FIELD_MAP)
    missing_game = sorted(game_required - set(resolved_outcomes.columns))
    missing_season = sorted(season_required - set(season_aggregates.columns))
    if missing_game:
        raise ValueError(f"resolved outcomes missing season-reconciliation fields: {missing_game}")
    if missing_season:
        raise ValueError(f"season aggregates missing reconciliation fields: {missing_season}")

    year = int(season)
    games = resolved_outcomes.filter(
        (pl.col("game_type") == "R")
        & pl.col("game_date").is_not_null()
        & (pl.col("game_date").dt.year() == year)
    )
    unresolved = games.filter(
        pl.col("outcome_resolution").str.starts_with("unresolved")
        | pl.any_horizontal(
            [pl.col(game_field).is_null() for game_field, _, _ in OUTCOME_FIELD_MAP]
        )
    )
    if not unresolved.is_empty():
        raise ValueError(
            "resolved outcomes contain unresolved/null fields required for season reconciliation"
        )

    aggregate = season_aggregates.filter(pl.col("season").cast(pl.Int64, strict=False) == year)
    if expected_league_ids is not None:
        expected = sorted(int(value) for value in expected_league_ids)
        games = games.filter(pl.col("league_id").is_in(expected))
        aggregate = aggregate.filter(pl.col("league_id").cast(pl.Int64, strict=False).is_in(expected))
        observed_game_leagues = sorted(
            int(value) for value in games.get_column("league_id").drop_nulls().unique().to_list()
        )
        observed_aggregate_leagues = sorted(
            int(value)
            for value in aggregate.get_column("league_id")
            .cast(pl.Int64, strict=False)
            .drop_nulls()
            .unique()
            .to_list()
        )
        if observed_game_leagues != expected:
            raise ValueError(
                f"game outcomes do not cover expected actual leagues: {observed_game_leagues} vs {expected}"
            )
        if observed_aggregate_leagues != expected:
            raise ValueError(
                "season aggregates do not cover expected actual leagues: "
                f"{observed_aggregate_leagues} vs {expected}"
            )

    game_rollup = (
        games.with_columns(pl.lit(year).cast(pl.Int64).alias("season"))
        .group_by(["season", "league_id", "player_id"])
        .agg(
            *[
                pl.col(game_field).sum().cast(pl.Int64).alias(f"game_{label}")
                for game_field, _, label in OUTCOME_FIELD_MAP
            ]
        )
    )
    aggregate_rollup = (
        aggregate.select(
            pl.col("season").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64, strict=False),
            pl.col("player_id").cast(pl.Int64, strict=False),
            *[
                pl.col(season_field).cast(pl.Int64, strict=False)
                for _, season_field, _ in OUTCOME_FIELD_MAP
            ],
        )
        .drop_nulls(["season", "league_id", "player_id"])
        .group_by(["season", "league_id", "player_id"])
        .agg(
            *[
                pl.col(season_field).sum().cast(pl.Int64).alias(f"season_{label}")
                for _, season_field, label in OUTCOME_FIELD_MAP
            ]
        )
    )

    fill_columns = [
        column
        for _, _, label in OUTCOME_FIELD_MAP
        for column in (f"game_{label}", f"season_{label}")
    ]
    difference_columns = [f"{label}_difference" for _, _, label in OUTCOME_FIELD_MAP]
    comparison = (
        game_rollup.join(
            aggregate_rollup,
            on=list(OUTCOME_RECONCILIATION_KEY),
            how="full",
            coalesce=True,
        )
        .with_columns(*[pl.col(column).fill_null(0).cast(pl.Int64) for column in fill_columns])
        .with_columns(
            *[
                (pl.col(f"game_{label}") - pl.col(f"season_{label}")).alias(
                    f"{label}_difference"
                )
                for _, _, label in OUTCOME_FIELD_MAP
            ]
        )
        .with_columns(
            pl.any_horizontal([pl.col(column) != 0 for column in difference_columns]).alias(
                "has_any_mismatch"
            )
        )
        .sort(list(OUTCOME_RECONCILIATION_KEY))
    )

    mismatch = comparison.filter(pl.col("has_any_mismatch"))
    field_metrics: dict[str, Any] = {}
    for _, _, label in OUTCOME_FIELD_MAP:
        diff = f"{label}_difference"
        field_metrics[label] = {
            "mismatch_player_league_count": int(comparison.filter(pl.col(diff) != 0).height),
            "signed_difference": int(comparison.get_column(diff).sum() or 0),
            "absolute_difference": int(comparison.get_column(diff).abs().sum() or 0),
            "game_total": int(comparison.get_column(f"game_{label}").sum() or 0),
            "season_total": int(comparison.get_column(f"season_{label}").sum() or 0),
        }

    exact = mismatch.is_empty()
    metrics: dict[str, Any] = {
        "season": year,
        "player_league_row_count": int(comparison.height),
        "mismatch_player_league_count": int(mismatch.height),
        "exact_reconciliation": bool(exact),
        "fields": field_metrics,
        "reconciliation_grain": "season_league_player_across_teams",
        "repair_policy": "diagnostic_only_no_synthetic_repair",
    }
    if require_exact and not exact:
        raise ValueError(
            "historical player-game outcomes do not exactly reconcile to season aggregates: "
            f"mismatch_rows={mismatch.height}"
        )
    return comparison, metrics
