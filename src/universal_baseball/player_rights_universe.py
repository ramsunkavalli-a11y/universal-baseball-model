"""Dated player-rights universe contract.

The universe is the denominator for every downstream forecast and valuation.
Missing evidence is represented explicitly; it never removes a player or turns
unknown rights/talent into a zero-valued record.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.playing_time_roster_source import FORTY_MAN_MEMBERSHIP_SCHEMA


RIGHTS_STATES = frozenset({"organization_controlled", "free_agent", "unknown"})
ROSTER_SCOPES = frozenset(
    {
        "mlb_40man",
        "reserve_list",
        "injured",
        "inactive",
        "newly_signed",
        "other_affiliated",
        "free_agent",
        "unknown",
    }
)
EVIDENCE_TIERS = frozenset({"direct", "corroborated", "prior_only"})

RIGHTS_EVIDENCE_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "rights_state": pl.String,
    "organization_id": pl.Int64,
    "roster_scope": pl.String,
    "source_snapshot_id": pl.String,
    "observed_at_date": pl.Date,
}

REQUIRED_PLAYER_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "player_name": pl.String,
}

PLAYER_RIGHTS_UNIVERSE_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "rights_state": pl.String,
    "organization_id": pl.Int64,
    "roster_scope": pl.String,
    "evidence_tier": pl.String,
    "source_snapshot_ids": pl.String,
    "last_observed_date": pl.Date,
    "coverage_reason": pl.String,
}

_SCOPE_PRIORITY = {
    "mlb_40man": 0,
    "reserve_list": 1,
    "injured": 2,
    "inactive": 3,
    "newly_signed": 4,
    "other_affiliated": 5,
    "free_agent": 6,
    "unknown": 7,
}


def project_40man_membership_to_rights_evidence(
    membership: pl.DataFrame,
    *,
    expected_as_of_date: date,
) -> pl.DataFrame:
    """Convert certified 40-man membership into narrow rights evidence.

    Presence on an official organization's dated 40-man endpoint supports only
    organization control and MLB 40-man scope. Source status and parent-team
    diagnostics are deliberately not interpreted. A player appearing for two
    organizations at the same snapshot fails closed.
    """

    result = _conform(membership, FORTY_MAN_MEMBERSHIP_SCHEMA, "40man_membership")
    required = ["as_of_date", "season", "team_id", "player_id", "on_40man"]
    if result.filter(pl.any_horizontal([pl.col(c).is_null() for c in required])).height:
        raise ValueError("40man_membership has null required values")
    if result.filter(pl.col("as_of_date") != pl.lit(expected_as_of_date)).height:
        raise ValueError("40man_membership contains an unexpected as_of_date")
    if result.filter((pl.col("team_id") <= 0) | (pl.col("player_id") <= 0)).height:
        raise ValueError("40man_membership has non-positive identifiers")
    if result.filter(~pl.col("on_40man")).height:
        raise ValueError("40man_membership may contain only certified positive membership")
    conflicts = (
        result.select("player_id", "team_id")
        .unique()
        .group_by("player_id")
        .len()
        .filter(pl.col("len") > 1)
    )
    if conflicts.height:
        raise ValueError("40man_membership has cross-organization player conflicts")
    if result.group_by(["player_id", "team_id"]).len().filter(pl.col("len") > 1).height:
        raise ValueError("40man_membership has duplicate player-team rows")

    evidence = result.select(
        pl.col("as_of_date"),
        pl.col("player_id"),
        pl.lit(None, dtype=pl.String).alias("player_name"),
        pl.lit("organization_controlled").alias("rights_state"),
        pl.col("team_id").alias("organization_id"),
        pl.lit("mlb_40man").alias("roster_scope"),
        pl.concat_str(
            pl.lit("official_mlb_stats_api_40Man:"),
            pl.col("as_of_date").dt.to_string("%Y-%m-%d"),
            pl.lit(":team:"),
            pl.col("team_id"),
        ).alias("source_snapshot_id"),
        pl.col("as_of_date").alias("observed_at_date"),
    )
    return validate_rights_evidence(evidence, expected_as_of_date=expected_as_of_date)


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    extra = sorted(set(frame.columns) - set(schema))
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    return frame.select(list(schema)).cast(schema, strict=True)


def validate_rights_evidence(
    frame: pl.DataFrame,
    *,
    expected_as_of_date: date | None = None,
) -> pl.DataFrame:
    """Validate source-projected rights evidence before consolidation."""

    result = _conform(frame, RIGHTS_EVIDENCE_SCHEMA, "rights_evidence")
    required = [
        "as_of_date",
        "player_id",
        "rights_state",
        "roster_scope",
        "source_snapshot_id",
        "observed_at_date",
    ]
    if result.filter(pl.any_horizontal([pl.col(c).is_null() for c in required])).height:
        raise ValueError("rights_evidence has null required values")
    if result.filter(pl.col("player_id") <= 0).height:
        raise ValueError("rights_evidence has non-positive player_id")
    if result.filter(~pl.col("rights_state").is_in(sorted(RIGHTS_STATES))).height:
        raise ValueError("rights_evidence has invalid rights_state")
    if result.filter(~pl.col("roster_scope").is_in(sorted(ROSTER_SCOPES))).height:
        raise ValueError("rights_evidence has invalid roster_scope")
    if result.filter(pl.col("observed_at_date") > pl.col("as_of_date")).height:
        raise ValueError("rights_evidence contains future observations")
    if expected_as_of_date is not None and result.filter(
        pl.col("as_of_date") != pl.lit(expected_as_of_date)
    ).height:
        raise ValueError("rights_evidence contains an unexpected as_of_date")

    controlled = pl.col("rights_state") == "organization_controlled"
    free_agent = pl.col("rights_state") == "free_agent"
    if result.filter(controlled & pl.col("organization_id").is_null()).height:
        raise ValueError("organization-controlled evidence requires organization_id")
    if result.filter(~controlled & pl.col("organization_id").is_not_null()).height:
        raise ValueError("only organization-controlled evidence may name an organization")
    if result.filter(free_agent & (pl.col("roster_scope") != "free_agent")).height:
        raise ValueError("free-agent evidence requires free_agent roster_scope")
    if result.filter(~free_agent & (pl.col("roster_scope") == "free_agent")).height:
        raise ValueError("free_agent roster_scope requires free-agent rights_state")
    return result


def _validate_required_players(frame: pl.DataFrame) -> pl.DataFrame:
    result = _conform(frame, REQUIRED_PLAYER_SCHEMA, "required_players")
    if result.filter(pl.col("player_id").is_null() | (pl.col("player_id") <= 0)).height:
        raise ValueError("required_players has null or non-positive player_id")
    if result.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("required_players has duplicate player_id")
    return result


def build_player_rights_universe(
    required_players: pl.DataFrame,
    rights_evidence: pl.DataFrame,
    *,
    as_of_date: date,
) -> pl.DataFrame:
    """Build one complete, conflict-safe player-rights denominator.

    Multiple evidence rows may corroborate the same rights state and owner. A
    disagreement about state or controlling organization fails closed. Scope is
    selected by explicit priority while all source snapshot IDs are retained.
    """

    required = _validate_required_players(required_players)
    evidence = validate_rights_evidence(
        rights_evidence,
        expected_as_of_date=as_of_date,
    )

    evidence_ids = evidence.select("player_id").unique()
    outside = evidence_ids.join(required.select("player_id"), on="player_id", how="anti")
    if outside.height:
        raise ValueError("rights_evidence contains players outside required denominator")

    conflicts = (
        evidence.select("player_id", "rights_state", "organization_id")
        .unique()
        .group_by("player_id")
        .len()
        .filter(pl.col("len") > 1)
    )
    if conflicts.height:
        raise ValueError("rights_evidence has conflicting state or organization")

    if evidence.is_empty():
        consolidated = pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "rights_state": pl.String,
                "organization_id": pl.Int64,
                "roster_scope": pl.String,
                "evidence_tier": pl.String,
                "source_snapshot_ids": pl.String,
                "last_observed_date": pl.Date,
                "coverage_reason": pl.String,
                "evidence_player_name": pl.String,
            }
        )
    else:
        scope_priority = pl.col("roster_scope").replace_strict(
            _SCOPE_PRIORITY,
            return_dtype=pl.Int64,
        )
        consolidated = (
            evidence.with_columns(scope_priority.alias("_scope_priority"))
            .sort(["player_id", "_scope_priority", "source_snapshot_id"])
            .group_by("player_id", maintain_order=True)
            .agg(
                pl.col("rights_state").first(),
                pl.col("organization_id").first(),
                pl.col("roster_scope").first(),
                pl.when(pl.col("source_snapshot_id").n_unique() > 1)
                .then(pl.lit("corroborated"))
                .otherwise(pl.lit("direct"))
                .alias("evidence_tier"),
                pl.col("source_snapshot_id")
                .unique()
                .sort()
                .str.join(",")
                .alias("source_snapshot_ids"),
                pl.col("observed_at_date").max().alias("last_observed_date"),
                pl.lit("observed_rights_evidence").alias("coverage_reason"),
                pl.col("player_name")
                .drop_nulls()
                .filter(pl.col("player_name") != "")
                .first()
                .alias("evidence_player_name"),
            )
        )

    result = (
        required.join(consolidated, on="player_id", how="left")
        .with_columns(
            pl.coalesce("player_name", "evidence_player_name", pl.lit(""))
            .alias("player_name"),
            pl.col("rights_state").fill_null("unknown"),
            pl.col("roster_scope").fill_null("unknown"),
            pl.col("evidence_tier").fill_null("prior_only"),
            pl.col("source_snapshot_ids").fill_null(""),
            pl.col("coverage_reason").fill_null("missing_rights_evidence"),
            pl.lit(as_of_date).cast(pl.Date).alias("as_of_date"),
        )
        .select(list(PLAYER_RIGHTS_UNIVERSE_SCHEMA))
        .cast(PLAYER_RIGHTS_UNIVERSE_SCHEMA, strict=True)
        .sort("player_id")
    )
    return validate_player_rights_universe(result, expected_as_of_date=as_of_date)


def validate_player_rights_universe(
    frame: pl.DataFrame,
    *,
    expected_as_of_date: date | None = None,
) -> pl.DataFrame:
    """Validate a materialized player-rights universe."""

    result = _conform(frame, PLAYER_RIGHTS_UNIVERSE_SCHEMA, "player_rights_universe")
    required = [
        "as_of_date",
        "player_id",
        "rights_state",
        "roster_scope",
        "evidence_tier",
        "source_snapshot_ids",
        "coverage_reason",
    ]
    if result.filter(pl.any_horizontal([pl.col(c).is_null() for c in required])).height:
        raise ValueError("player_rights_universe has null required values")
    if result.group_by(["as_of_date", "player_id"]).len().filter(pl.col("len") > 1).height:
        raise ValueError("player_rights_universe violates as_of_date + player_id grain")
    if expected_as_of_date is not None and result.filter(
        pl.col("as_of_date") != pl.lit(expected_as_of_date)
    ).height:
        raise ValueError("player_rights_universe contains an unexpected as_of_date")
    if result.filter(~pl.col("rights_state").is_in(sorted(RIGHTS_STATES))).height:
        raise ValueError("player_rights_universe has invalid rights_state")
    if result.filter(~pl.col("roster_scope").is_in(sorted(ROSTER_SCOPES))).height:
        raise ValueError("player_rights_universe has invalid roster_scope")
    if result.filter(~pl.col("evidence_tier").is_in(sorted(EVIDENCE_TIERS))).height:
        raise ValueError("player_rights_universe has invalid evidence_tier")
    if result.filter(
        (pl.col("rights_state") == "organization_controlled")
        & pl.col("organization_id").is_null()
    ).height:
        raise ValueError("organization-controlled universe row requires organization_id")
    if result.filter(
        (pl.col("rights_state") != "organization_controlled")
        & pl.col("organization_id").is_not_null()
    ).height:
        raise ValueError("non-controlled universe row cannot name an organization")
    if result.filter(
        pl.col("last_observed_date").is_not_null()
        & (pl.col("last_observed_date") > pl.col("as_of_date"))
    ).height:
        raise ValueError("player_rights_universe contains future observations")
    return result
