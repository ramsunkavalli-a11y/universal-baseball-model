"""Hitter v2 exhaustive terminal-PA outcome accounting.

This module promotes the already-certified terminal-contact source into an
outcome foundation and reconciles it to independent player-game box scores.
It deliberately contains no estimator, run value, projection, or ranking.
"""

from __future__ import annotations

from typing import Any, Iterable

import polars as pl

from universal_baseball.current_talent_contact_value_source import (
    STRUCTURED_TERMINAL_GROUP,
)
from universal_baseball.current_talent_mlb_evidence import _with_official_outcome_batter


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
BLOCKING_METADATA = ("game_type", "league_id")
MLB_EVENT_OUTCOME = {
    "walk": "UBB",
    "intent_walk": "IBB",
    "hit_by_pitch": "HBP",
    "strikeout": "K",
    "strike_out": "K",
    "strikeout_double_play": "K",
    "strikeout_triple_play": "K",
    **{
        event: TERMINAL_CONTACT_GROUP_MAP[group]
        for event, group in STRUCTURED_TERMINAL_GROUP.items()
    },
    "grounded_into_triple_play": "MULTI_OUT",
    "sac_bunt": "SH_OR_SPECIAL",
    "sac_bunt_double_play": "SH_OR_SPECIAL",
    "catcher_interf": "SH_OR_SPECIAL",
    "batter_interference": "SH_OR_SPECIAL",
    "fan_interference": "SH_OR_SPECIAL",
    "os_ruling_pending_primary": "SH_OR_SPECIAL",
}


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
        "team_id",
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
        "team_id",
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
    team_identity_conflict_count = 0
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
        positive_team_values = {
            row["team_id"]
            for row in values
            if row["team_id"] is not None
            and row["batting_PA"] is not None
            and int(row["batting_PA"]) > 0
        }
        if any(len(values) > 1 for values in blocking_values.values()):
            blocking_conflict_count += 1
            unresolved_count += 1
            rows.append(
                {
                    **base,
                    **{field: None for field in BLOCKING_METADATA},
                    "team_id": None,
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
        if selected is not None and len(positive_team_values) > 1:
            resolution = "unresolved_positive_pa_team_identity"
            unresolved_count += 1
            team_identity_conflict_count += 1
        rows.append(
            {
                **base,
                **{
                    field: next(iter(blocking_values[field]), None)
                    for field in BLOCKING_METADATA
                },
                "team_id": (
                    next(iter(positive_team_values), None)
                    if selected is not None and len(positive_team_values) == 1
                    else None
                ),
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
            for field in ("league_id", "team_id", *OFFICIAL_BATTING_FIELDS)
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
        "positive_pa_team_identity_conflict_player_game_count": team_identity_conflict_count,
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
    accepted = contacts.filter(
        pl.col("terminal_outcome_status").cast(pl.String).str.starts_with("supported")
    )
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


def project_terminal_pa_identities(
    raw_pbp_rows: pl.DataFrame,
    terminal_pas: pl.DataFrame,
    participant_overlay: pl.DataFrame,
    *,
    game_type: str = "R",
) -> pl.DataFrame:
    """Attach a fail-closed batter identity to every retained terminal PA.

    The certified contact target supplies official exception identity where it
    overlaps the terminal PA. Other terminal rows retain the reusable source
    batter only when every repeated terminal snapshot agrees.
    """

    raw_required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "game_type",
        "batter",
    }
    terminal_required = {
        "game_pk",
        "at_bat_index",
        "terminal_pitch_number",
        "terminal_outcome_group",
        "terminal_outcome_status",
    }
    overlay_required = {"game_pk", "at_bat_index", "player_id", "league_id"}
    missing_raw = sorted(raw_required - set(raw_pbp_rows.columns))
    missing_terminal = sorted(terminal_required - set(terminal_pas.columns))
    missing_overlay = sorted(overlay_required - set(participant_overlay.columns))
    if missing_raw:
        raise ValueError(f"raw terminal identity source missing fields: {missing_raw}")
    if missing_terminal:
        raise ValueError(f"terminal PA table missing fields: {missing_terminal}")
    if missing_overlay:
        raise ValueError(f"participant overlay missing fields: {missing_overlay}")

    raw = (
        raw_pbp_rows.select(
            _int_expr("game_pk"),
            _int_expr("at_bat_number", "at_bat_index"),
            _int_expr("pitch_number"),
            pl.col("game_type").cast(pl.String),
            _int_expr("batter", "source_player_id"),
        )
        .drop_nulls(["game_pk", "at_bat_index", "pitch_number"])
        .filter(pl.col("game_type") == game_type)
    )
    terminal_rows = raw.join(
        terminal_pas.select(
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            "terminal_outcome_group",
            "terminal_outcome_status",
        ),
        left_on=["game_pk", "at_bat_index", "pitch_number"],
        right_on=["game_pk", "at_bat_index", "terminal_pitch_number"],
        how="inner",
        validate="m:1",
    )
    identity = terminal_rows.group_by(["game_pk", "at_bat_index"]).agg(
        pl.col("source_player_id").drop_nulls().n_unique().alias("source_player_count"),
        pl.col("source_player_id").drop_nulls().first().alias("source_player_id"),
        pl.col("terminal_outcome_group").drop_nulls().n_unique().alias("group_count"),
        pl.col("terminal_outcome_group").drop_nulls().first().alias(
            "terminal_outcome_group"
        ),
        pl.col("terminal_outcome_status").drop_nulls().n_unique().alias("status_count"),
        pl.col("terminal_outcome_status").drop_nulls().first().alias(
            "terminal_outcome_status"
        ),
        pl.len().alias("raw_terminal_identity_row_count"),
    )
    if identity.height != terminal_pas.height:
        raise ValueError(
            "raw PBP terminal identity coverage does not equal retained terminal PA count"
        )
    overlay = participant_overlay.select(
        "game_pk", "at_bat_index", "player_id", "league_id"
    ).unique()
    overlay_conflict = overlay.group_by(["game_pk", "at_bat_index"]).agg(
        pl.col("player_id").n_unique().alias("players"),
        pl.col("league_id").n_unique().alias("leagues"),
    ).filter((pl.col("players") != 1) | (pl.col("leagues") != 1))
    if not overlay_conflict.is_empty():
        raise ValueError("certified participant overlay conflicts at terminal PA grain")
    overlay = overlay.unique(["game_pk", "at_bat_index"], keep="first").rename(
        {"player_id": "overlay_player_id", "league_id": "overlay_league_id"}
    )
    return (
        identity.join(overlay, on=["game_pk", "at_bat_index"], how="left", validate="1:1")
        .with_columns(
            pl.coalesce("overlay_player_id", "source_player_id")
            .cast(pl.Int64)
            .alias("player_id"),
            pl.when(pl.col("overlay_player_id").is_not_null())
            .then(pl.lit("certified_contact_participant_overlay"))
            .when(pl.col("source_player_count") == 1)
            .then(pl.lit("source_terminal_batter"))
            .otherwise(pl.lit("unresolved_terminal_batter"))
            .alias("participant_authority"),
            (
                (pl.col("source_player_count") == 1)
                | pl.col("overlay_player_id").is_not_null()
            ).alias("identity_resolved"),
        )
        .sort(["game_pk", "at_bat_index"])
    )


def aggregate_projected_terminal_pas(
    projected: pl.DataFrame,
    game_leagues: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Aggregate all supported terminal results, independent of profile eligibility."""

    required = {
        "game_pk",
        "at_bat_index",
        "player_id",
        "identity_resolved",
        "terminal_outcome_group",
        "terminal_outcome_status",
    }
    missing = sorted(required - set(projected.columns))
    if missing:
        raise ValueError(f"projected terminal PAs missing fields: {missing}")
    league_required = {"game_pk", "league_id"}
    league_missing = sorted(league_required - set(game_leagues.columns))
    if league_missing:
        raise ValueError(f"game league authority missing fields: {league_missing}")
    league_map = game_leagues.select("game_pk", "league_id").drop_nulls().unique()
    league_conflict = league_map.group_by("game_pk").agg(
        pl.col("league_id").n_unique().alias("leagues")
    ).filter(pl.col("leagues") != 1)
    if not league_conflict.is_empty():
        raise ValueError("game league authority conflicts at game grain")
    league_map = league_map.unique("game_pk", keep="first")
    supported = projected.filter(
        pl.col("identity_resolved")
        & pl.col("terminal_outcome_status").cast(pl.String).str.starts_with("supported")
        & pl.col("terminal_outcome_group").is_in(list(TERMINAL_CONTACT_GROUP_MAP))
    ).join(league_map, on="game_pk", how="left", validate="m:1")
    if supported.filter(pl.col("league_id").is_null()).height:
        raise ValueError("supported terminal PAs lack game league authority")
    contacts = supported.select(
        "game_pk",
        "at_bat_index",
        "league_id",
        "player_id",
        "terminal_outcome_group",
        "terminal_outcome_status",
    )
    counts = aggregate_terminal_contacts(contacts)
    return counts, {
        "terminal_pa_count": projected.height,
        "identity_resolved_terminal_pa_count": projected.filter(
            pl.col("identity_resolved")
        ).height,
        "identity_unresolved_terminal_pa_count": projected.filter(
            ~pl.col("identity_resolved")
        ).height,
        "supported_terminal_outcome_count": supported.height,
        "unsupported_or_special_terminal_pa_count": projected.height - supported.height,
        "participant_overlay_terminal_pa_count": projected.filter(
            pl.col("participant_authority") == "certified_contact_participant_overlay"
        ).height,
    }


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
        "team_id",
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
        pl.col("batting_HR").alias("HR"),
        pl.col("batting_3B").alias("3B"),
        pl.col("batting_2B").alias("2B"),
        official_1b.alias("1B"),
        pl.col("pbp_ROE").alias("ROE"),
        pl.col("pbp_FC_REACH").alias("FC_REACH"),
        pl.col("batting_SF").alias("SF"),
        pl.col("pbp_MULTI_OUT").alias("MULTI_OUT"),
        pl.col("pbp_OTHER_OUT").alias("OTHER_OUT"),
        known_special.alias("SH_OR_SPECIAL"),
        pl.col("batting_SH").alias("special_SH"),
        pl.col("batting_CI").alias("special_CATCHER_INTERFERENCE"),
        pl.lit(0, dtype=pl.Int64).alias("special_OTHER_KNOWN_SPECIAL"),
        official_1b.alias("official_1B"),
        (pl.col("batting_GiDP") + pl.col("batting_GiTP")).alias("official_multi_out"),
        (pl.col("batting_HR") - pl.col("pbp_HR")).alias("unique_repair_HR"),
        (pl.col("batting_3B") - pl.col("pbp_3B")).alias("unique_repair_3B"),
        (pl.col("batting_2B") - pl.col("pbp_2B")).alias("unique_repair_2B"),
        (official_1b - pl.col("pbp_1B")).alias("unique_repair_1B"),
        (pl.col("batting_SF") - pl.col("pbp_SF")).alias("unique_repair_SF"),
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
        pl.sum_horizontal(
            [
                pl.col(field).clip(lower_bound=0)
                for field in (
                    "unique_repair_HR",
                    "unique_repair_3B",
                    "unique_repair_2B",
                    "unique_repair_1B",
                    "unique_repair_SF",
                )
            ]
        ).alias("official_unique_repair_count"),
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
    has_invalid_repair = pl.any_horizontal(
        [
            pl.col(field) < 0
            for field in (
                "unique_repair_HR",
                "unique_repair_3B",
                "unique_repair_2B",
                "unique_repair_1B",
                "unique_repair_SF",
            )
        ]
    )
    exact = pl.all_horizontal([pl.col(field) == 0 for field in exact_fields])
    return joined.with_columns(
        pl.when(pl.col("outcome_resolution").str.starts_with("unresolved"))
        .then(pl.lit("failed_closed_official_snapshot"))
        .when(pl.col("contact_league_conflict"))
        .then(pl.lit("failed_closed_league_identity"))
        .when(has_negative)
        .then(pl.lit("failed_closed_negative_count"))
        .when(has_invalid_repair)
        .then(pl.lit("failed_closed_pbp_overcount"))
        .when(exact & (pl.col("official_unique_repair_count") > 0))
        .then(pl.lit("accepted_official_unique_repair"))
        .when(exact)
        .then(pl.lit("accepted_exact"))
        .otherwise(pl.lit("failed_closed_reconciliation"))
        .alias("source_status"),
        (
            ~exact
            | has_negative
            | has_invalid_repair
            | pl.col("contact_league_conflict")
        ).alias(
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
        "special_OTHER_KNOWN_SPECIAL",
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
        "unique_repair_HR",
        "unique_repair_3B",
        "unique_repair_2B",
        "unique_repair_1B",
        "unique_repair_SF",
        "official_unique_repair_count",
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
    ).with_columns(
        pl.col("source_status")
        .str.starts_with("accepted")
        .alias("modeling_eligible"),
        pl.lit(
            "affiliated_pbp_terminal_plus_official_player_game_v1"
        ).alias("source_capability_tier"),
    ).sort(["season", "league_id", "game_id", "player_id"])


def aggregate_player_season_outcomes(player_games: pl.DataFrame) -> pl.DataFrame:
    """Build one season/league/player row with accepted and excluded exposure."""

    keys = [
        "season",
        "league_id",
        "player_id",
        "level_group",
        "source_capability_tier",
    ]
    required = {
        *keys,
        *TERMINAL_OUTCOMES,
        "batting_PA",
        "hitter_talent_pa",
        "modeling_eligible",
    }
    missing = sorted(required - set(player_games.columns))
    if missing:
        raise ValueError(f"player-game outcomes missing season aggregate fields: {missing}")
    accepted_numeric = [
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
    ]
    audit_numeric = [
        "official_pa_residual",
        "hit_residual",
        "walk_residual",
        "double_residual",
        "triple_residual",
        "home_run_residual",
        "sac_fly_residual",
        "multi_out_residual",
    ]
    aggregated = (
        player_games.group_by(keys)
        .agg(
            pl.len().alias("player_game_count"),
            pl.col("modeling_eligible").sum().alias("accepted_player_game_count"),
            (~pl.col("modeling_eligible")).sum().alias("excluded_player_game_count"),
            pl.col("batting_PA").sum().alias("official_pa_total"),
            pl.col("batting_PA")
            .filter(~pl.col("modeling_eligible"))
            .sum()
            .alias("excluded_official_pa"),
            pl.col("team_id").drop_nulls().n_unique().alias("team_count"),
            pl.col("game_date").min().alias("first_game_date"),
            pl.col("game_date").max().alias("last_game_date"),
            *[
                pl.col(field)
                .filter(pl.col("modeling_eligible"))
                .sum()
                .alias(field)
                for field in accepted_numeric
            ],
            *[pl.col(field).sum().alias(field) for field in audit_numeric],
        )
    )
    return aggregated.with_columns(
        (pl.col("accepted_player_game_count") > 0).alias("modeling_eligible"),
        pl.when(pl.col("excluded_player_game_count") == 0)
        .then(pl.lit("accepted_all_player_games"))
        .when(pl.col("accepted_player_game_count") > 0)
        .then(pl.lit("accepted_with_excluded_player_games"))
        .otherwise(pl.lit("failed_closed_no_accepted_games"))
        .alias("source_status"),
    ).sort(keys)


def build_mlb_player_game_outcomes(
    savant: pl.DataFrame,
    teams: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Build exhaustive MLB terminal outcomes from certified structured Savant PBP."""

    required = {
        "game_date",
        "game_year",
        "game_pk",
        "league_id",
        "batting_team",
        "batter_mlbam_id",
        "events",
        "result_description",
        "is_plate_appearance_terminal",
        "at_bat_index",
        "pitch_number",
        "pitch_result_code",
    }
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"MLB Hitter v2 source missing fields: {missing}")
    team_required = {"team_id", "abbreviation", "league_id"}
    team_missing = sorted(team_required - set(teams.columns))
    if team_missing:
        raise ValueError(f"MLB team authority missing fields: {team_missing}")

    attributed = _with_official_outcome_batter(savant)
    terminal = attributed.filter(pl.col("is_plate_appearance_terminal"))
    duplicate = terminal.group_by(["game_pk", "at_bat_index"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("MLB Hitter v2 terminal PAs are not unique")
    team_map = teams.select(
        pl.col("team_id").cast(pl.Int64),
        pl.col("abbreviation").cast(pl.String).str.to_uppercase(),
        pl.col("league_id").cast(pl.Int64).alias("team_league_id"),
    ).unique()
    if team_map.group_by("abbreviation").len().filter(pl.col("len") != 1).height:
        raise ValueError("MLB team abbreviations are not unique")
    field_error_interference = (
        (pl.col("events") == "field_error")
        & pl.col("result_description")
        .cast(pl.String)
        .str.to_lowercase()
        .str.contains(r"\binterference error\b")
        .fill_null(False)
    )
    terminal = (
        terminal.with_columns(
            pl.col("game_date").cast(pl.String).str.to_date(strict=False),
            pl.col("game_year").cast(pl.Int64).alias("season"),
            pl.col("game_pk").cast(pl.Int64).alias("game_id"),
            pl.col("league_id").cast(pl.Int64),
            pl.col("_outcome_player_id").cast(pl.Int64).alias("player_id"),
            pl.when(pl.col("batting_team") == "ATH")
            .then(pl.lit("OAK"))
            .otherwise(pl.col("batting_team"))
            .cast(pl.String)
            .str.to_uppercase()
            .alias("abbreviation"),
            pl.when(field_error_interference)
            .then(pl.lit("SH_OR_SPECIAL"))
            .otherwise(
                pl.col("events").replace_strict(MLB_EVENT_OUTCOME, default=None)
            )
            .cast(pl.String)
            .alias("canonical_outcome"),
            field_error_interference.alias("field_error_interference"),
        )
        .join(team_map, on="abbreviation", how="left", validate="m:1")
    )
    invalid = terminal.filter(
        pl.col("game_date").is_null()
        | pl.col("player_id").is_null()
        | pl.col("team_id").is_null()
        | pl.col("canonical_outcome").is_null()
        | (pl.col("team_league_id") != pl.col("league_id"))
    )
    if not invalid.is_empty():
        raise ValueError(
            "MLB Hitter v2 terminal source has unresolved date/player/team/outcome authority"
        )
    keys = ["season", "game_date", "game_id", "league_id", "team_id", "player_id"]
    counts = terminal.pivot(
        on="canonical_outcome",
        index=keys,
        values="at_bat_index",
        aggregate_function="len",
    )
    for outcome in TERMINAL_OUTCOMES:
        if outcome not in counts.columns:
            counts = counts.with_columns(pl.lit(0, dtype=pl.UInt32).alias(outcome))
    event_counts = terminal.group_by(keys).agg(
        pl.col("events").is_in(["sac_bunt", "sac_bunt_double_play"]).sum().alias(
            "special_SH"
        ),
        (
            pl.col("events") == "catcher_interf"
        )
        .sum()
        .alias("special_CATCHER_INTERFERENCE"),
        (
            pl.col("field_error_interference")
            | pl.col("events").is_in(
                ["batter_interference", "fan_interference", "os_ruling_pending_primary"]
            )
        )
        .sum()
        .alias("special_OTHER_KNOWN_SPECIAL"),
        (pl.col("events") == "grounded_into_double_play").sum().alias("batting_GiDP"),
        pl.col("events")
        .is_in(["grounded_into_triple_play", "triple_play"])
        .sum()
        .alias("batting_GiTP"),
        pl.col("events")
        .is_in(["sac_fly", "sac_fly_double_play"])
        .sum()
        .alias("batting_SF"),
    )
    result = counts.join(event_counts, on=keys, how="left", validate="1:1").with_columns(
        *[pl.col(outcome).cast(pl.Int64) for outcome in TERMINAL_OUTCOMES],
        pl.col("special_SH").cast(pl.Int64),
        pl.col("special_CATCHER_INTERFERENCE").cast(pl.Int64),
        pl.col("special_OTHER_KNOWN_SPECIAL").cast(pl.Int64),
        pl.col("batting_GiDP").cast(pl.Int64),
        pl.col("batting_GiTP").cast(pl.Int64),
        pl.col("batting_SF").cast(pl.Int64),
    )
    hits = pl.sum_horizontal([pl.col(x) for x in ("1B", "2B", "3B", "HR")])
    observed_contacts = pl.sum_horizontal(
        [
            pl.col(x)
            for x in (
                "HR",
                "3B",
                "2B",
                "1B",
                "ROE",
                "FC_REACH",
                "SF",
                "MULTI_OUT",
                "OTHER_OUT",
            )
        ]
    )
    accepted = pl.sum_horizontal([pl.col(x) for x in TERMINAL_OUTCOMES])
    talent = pl.sum_horizontal([pl.col(x) for x in HITTER_TALENT_OUTCOMES])
    result = result.with_columns(
        accepted.alias("accepted_terminal_pa"),
        talent.alias("hitter_talent_pa"),
        accepted.alias("batting_PA"),
        (
            accepted
            - pl.col("UBB")
            - pl.col("IBB")
            - pl.col("HBP")
            - pl.col("batting_SF")
            - pl.col("SH_OR_SPECIAL")
        ).alias("batting_AB"),
        hits.alias("batting_H"),
        pl.col("2B").alias("batting_2B"),
        pl.col("3B").alias("batting_3B"),
        pl.col("HR").alias("batting_HR"),
        (pl.col("UBB") + pl.col("IBB")).alias("batting_BB"),
        pl.col("IBB").alias("batting_IBB"),
        pl.col("HBP").alias("batting_HBP"),
        pl.col("K").alias("batting_SO"),
        pl.col("special_SH").alias("batting_SH"),
        pl.col("special_CATCHER_INTERFERENCE").alias("batting_CI"),
        observed_contacts.alias("observed_terminal_contact_count"),
        *[
            pl.lit(0, dtype=pl.Int64).alias(field)
            for field in (
                "unique_repair_HR",
                "unique_repair_3B",
                "unique_repair_2B",
                "unique_repair_1B",
                "unique_repair_SF",
                "official_unique_repair_count",
                "official_pa_residual",
                "hit_residual",
                "walk_residual",
                "double_residual",
                "triple_residual",
                "home_run_residual",
                "sac_fly_residual",
                "multi_out_residual",
            )
        ],
        pl.lit(False).alias("contact_league_conflict"),
        pl.lit("structured_savant_terminal_event").alias("outcome_resolution"),
        pl.lit("accepted_exact").alias("source_status"),
        pl.lit(False).alias("has_blocking_reconciliation_error"),
        pl.lit("MLB").alias("level_group"),
    )
    ordered = result.select(
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
        "special_OTHER_KNOWN_SPECIAL",
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
        "unique_repair_HR",
        "unique_repair_3B",
        "unique_repair_2B",
        "unique_repair_1B",
        "unique_repair_SF",
        "official_unique_repair_count",
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
    ).with_columns(
        pl.lit(True).alias("modeling_eligible"),
        pl.lit("mlb_savant_structured_plus_official_season_v1").alias(
            "source_capability_tier"
        ),
    ).sort(["season", "league_id", "game_id", "player_id"])
    return ordered, {
        "terminal_pa_count": terminal.height,
        "player_game_count": ordered.height,
        "game_count": terminal.get_column("game_id").n_unique(),
        "player_count": terminal.get_column("player_id").n_unique(),
        "two_strike_outcome_reassignment_count": terminal.filter(
            pl.col("_outcome_player_id") != pl.col("_terminal_batter_id")
        ).height,
        "field_error_interference_count": terminal.filter(
            pl.col("field_error_interference")
        ).height,
    }


def assert_outcome_invariants(
    frame: pl.DataFrame,
    *,
    accepted_statuses: Iterable[str] = (
        "accepted_exact",
        "accepted_official_unique_repair",
    ),
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
        pl.any_horizontal(
            [
                pl.col(outcome).is_null() | (pl.col(outcome) < 0)
                for outcome in TERMINAL_OUTCOMES
            ]
        ).any()
    ).item():
        raise ValueError("accepted Hitter v2 outcome counts must be nonnegative integers")
    if accepted.filter(pl.col("accepted_terminal_pa") != pl.col("batting_PA")).height:
        raise ValueError("accepted terminal outcomes do not exhaust official PA")
    if accepted.filter(pl.col("batting_H") != pl.sum_horizontal([pl.col(x) for x in ("1B", "2B", "3B", "HR")])).height:
        raise ValueError("accepted hit outcomes do not reconcile official hits")
    if accepted.filter(pl.col("batting_BB") != pl.col("UBB") + pl.col("IBB")).height:
        raise ValueError("accepted walk outcomes do not reconcile UBB plus IBB")
    special_fields = {
        "special_SH",
        "special_CATCHER_INTERFERENCE",
        "special_OTHER_KNOWN_SPECIAL",
    }
    if special_fields <= set(accepted.columns) and accepted.filter(
        pl.col("SH_OR_SPECIAL")
        != pl.sum_horizontal([pl.col(field) for field in sorted(special_fields)])
    ).height:
        raise ValueError("accepted special outcomes do not reconcile declared subtypes")
