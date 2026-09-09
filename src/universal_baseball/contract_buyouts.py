"""Link FanGraphs payroll option-buyout rows to stable player identities."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


BUYOUT_DESCRIPTION_PREFIX = "$ due for potential buyout of "


@dataclass(frozen=True, slots=True)
class BuyoutLinkResult:
    links: pl.DataFrame
    coverage: dict[str, int]


def link_option_buyouts(
    contract_years: pl.DataFrame,
    other_payments: pl.DataFrame,
) -> BuyoutLinkResult:
    """Use exact within-workbook team/name identity; never fuzzy-match buyouts."""

    term_required = {
        "team_name",
        "player_name",
        "player_id",
        "organization_id",
        "overlay_status",
    }
    payment_required = {
        "team_name",
        "organization_id",
        "payment_year",
        "description",
        "amount_dollars",
        "payment_type",
        "is_contingent",
        "source_snapshot_id",
    }
    if missing := sorted(term_required - set(contract_years.columns)):
        raise ValueError(f"contract terms missing buyout identity fields: {missing}")
    if missing := sorted(payment_required - set(other_payments.columns)):
        raise ValueError(f"other payments missing buyout fields: {missing}")
    identities = contract_years.filter(
        pl.col("overlay_status") == "accepted_contract_overlay"
    ).select(
        "team_name", "player_name", "player_id", "organization_id"
    ).unique()
    ambiguous = identities.group_by("team_name", "player_name").len().filter(
        pl.col("len") != 1
    )
    usable_identities = identities.join(
        ambiguous.select("team_name", "player_name"),
        on=["team_name", "player_name"],
        how="anti",
    )
    candidates = other_payments.filter(
        (pl.col("payment_type") == "buyout") & pl.col("is_contingent")
    ).with_columns(
        pl.when(pl.col("description").str.starts_with(BUYOUT_DESCRIPTION_PREFIX))
        .then(
            pl.col("description").str.slice(len(BUYOUT_DESCRIPTION_PREFIX))
        )
        .otherwise(pl.lit(None, dtype=pl.String))
        .alias("player_name")
    )
    joined = candidates.join(
        usable_identities,
        on=["team_name", "player_name", "organization_id"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.when(pl.col("player_name").is_null())
        .then(pl.lit("unparsed_description"))
        .when(pl.col("player_id").is_null())
        .then(pl.lit("unresolved_exact_team_name"))
        .otherwise(pl.lit("matched_exact_within_payroll"))
        .alias("buyout_link_status"),
        pl.col("payment_year").alias("season"),
        pl.col("amount_dollars").alias("buyout_dollars"),
    )
    if joined.filter(
        pl.col("buyout_link_status") == "matched_exact_within_payroll"
    ).group_by("player_id", "organization_id", "season").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("linked buyouts violate player-organization-season grain")
    links = joined.select(
        "player_id",
        "organization_id",
        "season",
        "player_name",
        "team_name",
        "buyout_dollars",
        "description",
        "buyout_link_status",
        "source_snapshot_id",
    ).sort(["season", "team_name", "player_name"])
    matched = links.filter(
        pl.col("buyout_link_status") == "matched_exact_within_payroll"
    )
    return BuyoutLinkResult(
        links=links,
        coverage={
            "potential_buyout_rows": candidates.height,
            "linked_buyout_rows": matched.height,
            "unresolved_buyout_rows": links.height - matched.height,
            "ambiguous_team_name_identities": ambiguous.height,
            "name_matching_fuzzy": 0,
        },
    )
