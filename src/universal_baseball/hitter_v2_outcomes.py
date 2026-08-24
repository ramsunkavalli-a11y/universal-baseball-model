"""Hitter v2 exhaustive terminal-PA outcome accounting.

This module promotes the already-certified terminal-contact source into an
outcome foundation and reconciles it to independent player-game box scores.
It deliberately contains no estimator, run value, projection, or ranking.
"""

from __future__ import annotations

from typing import Any, Iterable

import polars as pl


TERMINAL_OUTCOMES = (
    "UBB",
    "IBB",
    "HBP",
    "K",
    "HR",
    "3B",
    "2B",
    "1B",
    "ROE",
    "FC_REACH",
    "SF",
    "MULTI_OUT",
    "OTHER_OUT",
    "SH_OR_SPECIAL",
)
HITTER_TALENT_OUTCOMES = tuple(
    outcome for outcome in TERMINAL_OUTCOMES if outcome not in {"IBB", "SH_OR_SPECIAL"}
)
TERMINAL_CONTACT_GROUP_MAP = {
    "1B": "1B",
    "2B": "2B",
    "3B": "3B",
    "HR": "HR",
    "ROE": "ROE",
    "FC_REACH": "FC_REACH",
    "SF": "SF",
    "MULTI_OUT": "MULTI_OUT",
    "OUT": "OTHER_OUT",
}
OFFICIAL_BATTING_FIELDS = (
    "batting_PA",
    "batting_AB",
    "batting_H",
    "batting_2B",
    "batting_3B",
    "batting_HR",
    "batting_BB",
    "batting_IBB",
    "batting_HBP",
    "batting_SO",
    "batting_SF",
    "batting_SH",
    "batting_CI",
    "batting_GiDP",
    "batting_GiTP",
)
PLAYER_GAME_KEY = ("game_id", "player_id")
BLOCKING_METADATA = ("game_type", "league_id", "team_id")


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def project_official_player_game_outcomes(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None = None,
    game_type: str | None = "R",
) -> pl.DataFrame:
    """Project the independent box-score fields required by the v2 contract."""

    required = {
        "game_id",
        "game_date",
        "game_type",
        "league_id",
        "team_id",
        "player_id",
        *OFFICIAL_BATTING_FIELDS,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_asset} missing Hitter v2 outcome fields: {missing}")
    projected = frame.select(
        _int_expr("game_id"),
        pl.col("game_date").cast(pl.String),
        pl.col("game_type").cast(pl.String),
        _int_expr("league_id"),
        _int_expr("team_id"),
        _int_expr("player_id"),
        *[_int_expr(column) for column in OFFICIAL_BATTING_FIELDS],
        pl.lit(str(source_asset)).alias("source_asset"),
    ).drop_nulls(list(PLAYER_GAME_KEY))
    if season is not None:
        projected = projected.filter(pl.col("game_date").str.starts_with(f"{season}-"))
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == game_type)
    return projected


def _dominates(candidate: dict[str, Any], other: dict[str, Any]) -> bool:
    for field in OFFICIAL_BATTING_FIELDS:
        lower = other[field]
        upper = candidate[field]
        if lower is None:
            continue
        if upper is None or int(upper) < int(lower):
            return False
    return True


def resolve_official_player_game_outcomes(
    observations: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Resolve overlapping cumulative snapshots without filename chronology."""

    required = {
        *PLAYER_GAME_KEY,
        "game_date",
        *BLOCKING_METADATA,
        *OFFICIAL_BATTING_FIELDS,
        "source_asset",
    }
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"Hitter v2 observations missing fields: {missing}")
    if observations.is_empty():
        raise ValueError("Hitter v2 observations cannot be empty")

    raw_rows = observations.height
    exact = observations.unique(maintain_order=True)
    logical = exact.select(
        *PLAYER_GAME_KEY,
        "game_date",
        *BLOCKING_METADATA,
        *OFFICIAL_BATTING_FIELDS,
    ).unique(maintain_order=True)
    source_counts = exact.group_by(list(PLAYER_GAME_KEY)).agg(
        pl.col("source_asset").n_unique().alias("source_asset_count")
    )
    source_count_by_key = {
        (int(row["game_id"]), int(row["player_id"])): int(row["source_asset_count"])
        for row in source_counts.to_dicts()
    }

    rows: list[dict[str, Any]] = []
    dominance_count = 0
    unresolved_count = 0
    date_conflict_count = 0
    blocking_conflict_count = 0
    for group in logical.partition_by(list(PLAYER_GAME_KEY), maintain_order=True):
        values = group.to_dicts()
        first = values[0]
        key = (int(first["game_id"]), int(first["player_id"]))
        blocking_values = {
            field: {row[field] for row in values if row[field] is not None}
            for field in BLOCKING_METADATA
        }
        dates = sorted(
            {
                parsed
                for raw in (row["game_date"] for row in values)
                if raw is not None
                for parsed in [pl.Series([str(raw)]).str.to_date(strict=False).item()]
                if parsed is not None
            }
        )
        date_conflict = len(dates) > 1
        date_conflict_count += int(date_conflict)
        base = {
            "game_id": key[0],
            "player_id": key[1],
            "game_date": dates[-1] if dates else None,
            "game_date_conflict": date_conflict,
            "source_asset_count": source_count_by_key[key],
        }
        if any(len(values) > 1 for values in blocking_values.values()):
            blocking_conflict_count += 1
            unresolved_count += 1
            rows.append(
                {
                    **base,
                    **{field: None for field in BLOCKING_METADATA},
                    **{field: None for field in OFFICIAL_BATTING_FIELDS},
                    "outcome_resolution": "unresolved_blocking_metadata_conflict",
                }
            )
            continue

        vectors: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in values:
            vector = tuple(row[field] for field in OFFICIAL_BATTING_FIELDS)
            vectors.setdefault(vector, row)
        candidates = list(vectors.values())
        resolution = "consensus"
        selected: dict[str, Any] | None = candidates[0]
        if len(candidates) > 1:
            dominators = [
                candidate
                for candidate in candidates
                if all(_dominates(candidate, other) for other in candidates)
            ]
            if len(dominators) == 1:
                selected = dominators[0]
                resolution = "componentwise_dominance"
                dominance_count += 1
            else:
                selected = None
                resolution = "unresolved_nonmonotonic_conflict"
                unresolved_count += 1
        rows.append(
            {
                **base,
                **{
                    field: next(iter(blocking_values[field]), None)
                    for field in BLOCKING_METADATA
                },
                **{
                    field: selected[field] if selected is not None else None
                    for field in OFFICIAL_BATTING_FIELDS
                },
                "outcome_resolution": resolution,
            }
        )

    resolved = pl.DataFrame(rows).with_columns(
        pl.col("game_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("game_date").cast(pl.Date),
        pl.col("game_date_conflict").cast(pl.Boolean),
        *[
            pl.col(field).cast(pl.Int64, strict=False)
            for field in (*BLOCKING_METADATA[1:], *OFFICIAL_BATTING_FIELDS)
        ],
        pl.col("game_type").cast(pl.String),
        pl.col("source_asset_count").cast(pl.Int64),
        pl.col("outcome_resolution").cast(pl.String),
    ).sort(list(PLAYER_GAME_KEY))
    return resolved, {
        "raw_observation_count": raw_rows,
        "exact_duplicate_row_count": raw_rows - exact.height,
        "resolved_player_game_count": resolved.height,
        "resolved_by_componentwise_dominance_count": dominance_count,
        "game_date_conflict_player_game_count": date_conflict_count,
        "blocking_metadata_conflict_player_game_count": blocking_conflict_count,
        "unresolved_player_game_count": unresolved_count,
    }


def aggregate_terminal_contacts(contacts: pl.DataFrame) -> pl.DataFrame:
    """Aggregate accepted, unique terminal contacts to player-game counts."""

    required = {
        "game_pk",
        "at_bat_index",
        "league_id",
        "player_id",
        "terminal_outcome_group",
        "terminal_outcome_status",
    }
    missing = sorted(required - set(contacts.columns))
    if missing:
        raise ValueError(f"terminal contacts missing fields: {missing}")
    duplicate = (
        contacts.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("terminal contacts are not unique at game/at-bat grain")
    unsupported = sorted(
        set(contacts.get_column("terminal_outcome_group").drop_nulls().unique().to_list())
        - set(TERMINAL_CONTACT_GROUP_MAP)
    )
    if unsupported:
        raise ValueError(f"unsupported terminal contact groups: {unsupported}")
    accepted = contacts.filter(pl.col("terminal_outcome_status") == "supported")
    if accepted.height != contacts.height:
        raise ValueError("model-ready terminal contacts include non-supported rows")
    mapped = accepted.with_columns(
        pl.col("terminal_outcome_group")
        .replace_strict(TERMINAL_CONTACT_GROUP_MAP)
        .alias("canonical_outcome")
    )
    base = mapped.group_by(["game_pk", "league_id", "player_id"]).agg(
        pl.len().alias("observed_terminal_contact_count")
    )
    counts = mapped.pivot(
        on="canonical_outcome",
        index=["game_pk", "league_id", "player_id"],
        values="at_bat_index",
        aggregate_function="len",
    )
    for outcome in TERMINAL_CONTACT_GROUP_MAP.values():
        if outcome not in counts.columns:
            counts = counts.with_columns(pl.lit(0, dtype=pl.UInt32).alias(outcome))
    return (
        base.join(counts, on=["game_pk", "league_id", "player_id"], how="left")
        .rename({outcome: f"pbp_{outcome}" for outcome in TERMINAL_CONTACT_GROUP_MAP.values()})
        .with_columns(
            *[
                pl.col(f"pbp_{outcome}").fill_null(0).cast(pl.Int64)
                for outcome in TERMINAL_CONTACT_GROUP_MAP.values()
            ]
        )
        .sort(["game_pk", "player_id"])
    )


def assemble_player_game_outcomes(
    official: pl.DataFrame,
    contact_counts: pl.DataFrame,
    *,
    season: int,
    level_group: str,
) -> pl.DataFrame:
    """Build exhaustive counts and fail-closed reconciliation at player-game grain."""

    official_required = {
        *PLAYER_GAME_KEY,
        "game_date",
        *BLOCKING_METADATA,
        *OFFICIAL_BATTING_FIELDS,
        "outcome_resolution",
    }
    missing = sorted(official_required - set(official.columns))
    if missing:
        raise ValueError(f"official player-game frame missing fields: {missing}")
    contact_required = {"game_pk", "league_id", "player_id", "observed_terminal_contact_count"}
    contact_missing = sorted(contact_required - set(contact_counts.columns))
    if contact_missing:
        raise ValueError(f"contact count frame missing fields: {contact_missing}")
    positive = official.filter(pl.col("batting_PA").is_not_null() & (pl.col("batting_PA") > 0))
    joined = positive.join(
        contact_counts.rename({"game_pk": "game_id", "league_id": "contact_league_id"}),
        on=["game_id", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        pl.lit(int(season)).alias("season"),
        pl.lit(str(level_group)).alias("level_group"),
        pl.col("observed_terminal_contact_count").fill_null(0).cast(pl.Int64),
        *[
            pl.col(f"pbp_{outcome}").fill_null(0).cast(pl.Int64)
            for outcome in TERMINAL_CONTACT_GROUP_MAP.values()
        ],
    )
    official_1b = (
        pl.col("batting_H")
        - pl.col("batting_2B")
        - pl.col("batting_3B")
        - pl.col("batting_HR")
    )
    known_special = pl.col("batting_SH") + pl.col("batting_CI")
    joined = joined.with_columns(
        (pl.col("batting_BB") - pl.col("batting_IBB")).alias("UBB"),
        pl.col("batting_IBB").alias("IBB"),
        pl.col("batting_HBP").alias("HBP"),
        pl.col("batting_SO").alias("K"),
        pl.col("pbp_HR").alias("HR"),
        pl.col("pbp_3B").alias("3B"),
        pl.col("pbp_2B").alias("2B"),
        pl.col("pbp_1B").alias("1B"),
        pl.col("pbp_ROE").alias("ROE"),
        pl.col("pbp_FC_REACH").alias("FC_REACH"),
        pl.col("pbp_SF").alias("SF"),
        pl.col("pbp_MULTI_OUT").alias("MULTI_OUT"),
        pl.col("pbp_OTHER_OUT").alias("OTHER_OUT"),
        known_special.alias("SH_OR_SPECIAL"),
        pl.col("batting_SH").alias("special_SH"),
        pl.col("batting_CI").alias("special_CATCHER_INTERFERENCE"),
        official_1b.alias("official_1B"),
        (pl.col("batting_GiDP") + pl.col("batting_GiTP")).alias("official_multi_out"),
    )
    accepted_sum = pl.sum_horizontal([pl.col(outcome) for outcome in TERMINAL_OUTCOMES])
    hitter_talent_sum = pl.sum_horizontal(
        [pl.col(outcome) for outcome in HITTER_TALENT_OUTCOMES]
    )
    joined = joined.with_columns(
        accepted_sum.alias("accepted_terminal_pa"),
        hitter_talent_sum.alias("hitter_talent_pa"),
        (pl.col("batting_PA") - accepted_sum).alias("official_pa_residual"),
        (pl.col("batting_H") - pl.sum_horizontal([pl.col(x) for x in ("1B", "2B", "3B", "HR")])).alias("hit_residual"),
        (pl.col("batting_BB") - pl.col("UBB") - pl.col("IBB")).alias("walk_residual"),
        (pl.col("batting_2B") - pl.col("2B")).alias("double_residual"),
        (pl.col("batting_3B") - pl.col("3B")).alias("triple_residual"),
        (pl.col("batting_HR") - pl.col("HR")).alias("home_run_residual"),
        (pl.col("batting_SF") - pl.col("SF")).alias("sac_fly_residual"),
        (pl.col("official_multi_out") - pl.col("MULTI_OUT")).alias("multi_out_residual"),
        (
            pl.col("contact_league_id").is_not_null()
            & (pl.col("contact_league_id") != pl.col("league_id"))
        ).alias("contact_league_conflict"),
    )
    exact_fields = (
        "official_pa_residual",
        "hit_residual",
        "walk_residual",
        "double_residual",
        "triple_residual",
        "home_run_residual",
        "sac_fly_residual",
    )
    has_negative = pl.any_horizontal([pl.col(outcome) < 0 for outcome in TERMINAL_OUTCOMES])
    exact = pl.all_horizontal([pl.col(field) == 0 for field in exact_fields])
    return joined.with_columns(
        pl.when(pl.col("outcome_resolution").str.starts_with("unresolved"))
        .then(pl.lit("failed_closed_official_snapshot"))
        .when(pl.col("contact_league_conflict"))
        .then(pl.lit("failed_closed_league_identity"))
        .when(has_negative)
        .then(pl.lit("failed_closed_negative_count"))
        .when(exact)
        .then(pl.lit("accepted_exact"))
        .otherwise(pl.lit("failed_closed_reconciliation"))
        .alias("source_status"),
        (~exact | has_negative | pl.col("contact_league_conflict")).alias(
            "has_blocking_reconciliation_error"
        ),
    ).select(
        "season",
        "game_date",
        "game_id",
        "league_id",
        "team_id",
        "player_id",
        "level_group",
        *TERMINAL_OUTCOMES,
        "special_SH",
        "special_CATCHER_INTERFERENCE",
        "accepted_terminal_pa",
        "hitter_talent_pa",
        "batting_PA",
        "batting_AB",
        "batting_H",
        "batting_2B",
        "batting_3B",
        "batting_HR",
        "batting_BB",
        "batting_IBB",
        "batting_HBP",
        "batting_SO",
        "batting_SF",
        "batting_SH",
        "batting_CI",
        "batting_GiDP",
        "batting_GiTP",
        "observed_terminal_contact_count",
        "official_pa_residual",
        "hit_residual",
        "walk_residual",
        "double_residual",
        "triple_residual",
        "home_run_residual",
        "sac_fly_residual",
        "multi_out_residual",
        "contact_league_conflict",
        "outcome_resolution",
        "source_status",
        "has_blocking_reconciliation_error",
    ).sort(["season", "league_id", "game_id", "player_id"])


def aggregate_player_season_outcomes(player_games: pl.DataFrame) -> pl.DataFrame:
    """Aggregate accepted player-games while preserving league and status."""

    keys = ["season", "league_id", "player_id", "level_group", "source_status"]
    required = {*keys, *TERMINAL_OUTCOMES, "batting_PA", "hitter_talent_pa"}
    missing = sorted(required - set(player_games.columns))
    if missing:
        raise ValueError(f"player-game outcomes missing season aggregate fields: {missing}")
    numeric = [
        *TERMINAL_OUTCOMES,
        "accepted_terminal_pa",
        "hitter_talent_pa",
        "batting_PA",
        "batting_AB",
        "batting_H",
        "batting_2B",
        "batting_3B",
        "batting_HR",
        "batting_BB",
        "batting_IBB",
        "batting_HBP",
        "batting_SO",
        "batting_SF",
        "batting_SH",
        "batting_CI",
        "batting_GiDP",
        "batting_GiTP",
        "observed_terminal_contact_count",
        "official_pa_residual",
        "hit_residual",
        "walk_residual",
        "double_residual",
        "triple_residual",
        "home_run_residual",
        "sac_fly_residual",
        "multi_out_residual",
    ]
    return (
        player_games.group_by(keys)
        .agg(
            pl.len().alias("player_game_count"),
            pl.col("team_id").drop_nulls().n_unique().alias("team_count"),
            pl.col("game_date").min().alias("first_game_date"),
            pl.col("game_date").max().alias("last_game_date"),
            *[pl.col(field).sum().alias(field) for field in numeric],
        )
        .sort(keys)
    )


def assert_outcome_invariants(
    frame: pl.DataFrame,
    *,
    accepted_statuses: Iterable[str] = ("accepted_exact",),
) -> None:
    """Fail if canonical counts violate uniqueness, simplex, or reconciliation."""

    key = ["season", "league_id", "game_id", "player_id"]
    duplicates = frame.group_by(key).len().filter(pl.col("len") != 1)
    if not duplicates.is_empty():
        raise ValueError("Hitter v2 player-game keys are not unique")
    accepted = frame.filter(pl.col("source_status").is_in(list(accepted_statuses)))
    if accepted.is_empty():
        raise ValueError("Hitter v2 accepted outcome table cannot be empty")
    if accepted.select(
        pl.any_horizontal([pl.col(outcome).is_null() | (pl.col(outcome) < 0) for outcome in TERMINAL_OUTCOMES])
    ).item():
        raise ValueError("accepted Hitter v2 outcome counts must be nonnegative integers")
    if accepted.filter(pl.col("accepted_terminal_pa") != pl.col("batting_PA")).height:
        raise ValueError("accepted terminal outcomes do not exhaust official PA")
    if accepted.filter(pl.col("batting_H") != pl.sum_horizontal([pl.col(x) for x in ("1B", "2B", "3B", "HR")])).height:
        raise ValueError("accepted hit outcomes do not reconcile official hits")
    if accepted.filter(pl.col("batting_BB") != pl.col("UBB") + pl.col("IBB")).height:
        raise ValueError("accepted walk outcomes do not reconcile UBB plus IBB")
