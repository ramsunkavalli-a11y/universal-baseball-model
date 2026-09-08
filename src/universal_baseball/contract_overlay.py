"""Attach unique payroll terms after the CBA control calculation is complete."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from universal_baseball.contract_terms import PayrollNormalization


CONTRACT_PLAYER_OVERLAY_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "team_name": pl.String,
    "player_id": pl.Int64,
    "fangraphs_id": pl.String,
    "player_name": pl.String,
    "payroll_section": pl.String,
    "contract_text": pl.String,
    "aav_dollars": pl.Int64,
    "identity_match_status": pl.String,
    "overlay_status": pl.String,
    "source_snapshot_id": pl.String,
}

CONTRACT_YEAR_OVERLAY_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "team_name": pl.String,
    "player_id": pl.Int64,
    "fangraphs_id": pl.String,
    "player_name": pl.String,
    "payroll_year": pl.Int64,
    "amount_dollars": pl.Int64,
    "term_label": pl.String,
    "clause_types": pl.String,
    "overlay_status": pl.String,
    "source_snapshot_id": pl.String,
}


@dataclass(frozen=True)
class ContractOverlay:
    players: pl.DataFrame
    year_terms: pl.DataFrame
    unresolved_players: pl.DataFrame


def build_contract_overlay(
    payroll: PayrollNormalization, identity_matches: pl.DataFrame
) -> ContractOverlay:
    """Join payroll by accepted stable ID while retaining every unresolved row."""

    required = {"fangraphs_id", "player_id", "match_status"}
    missing = sorted(required - set(identity_matches.columns))
    if missing:
        raise ValueError(f"identity matches missing columns: {missing}")
    matches = identity_matches.select("fangraphs_id", "player_id", "match_status")
    players = payroll.players.join(matches, on="fangraphs_id", how="left").with_columns(
        pl.col("match_status").fill_null("unmatched").alias("identity_match_status")
    )
    players = players.with_columns(
        pl.when(
            pl.col("identity_match_status").is_in(
                ["matched_stable_id", "stable_id_outside_statsapi_candidates"]
            )
        )
        .then(pl.lit("accepted_contract_overlay"))
        .otherwise(pl.lit("review_identity_before_overlay"))
        .alias("overlay_status")
    )
    player_overlay = players.select(list(CONTRACT_PLAYER_OVERLAY_SCHEMA)).cast(
        CONTRACT_PLAYER_OVERLAY_SCHEMA, strict=True
    )

    clause_years: dict[tuple[str, int], set[str]] = {}
    for clause in payroll.clauses.iter_rows(named=True):
        start = clause["start_year"]
        end = clause["end_year"]
        if start is None or end is None:
            continue
        for year in range(int(start), int(end) + 1):
            clause_years.setdefault((str(clause["fangraphs_id"]), year), set()).add(
                str(clause["clause_type"])
            )
    year_rows: list[dict[str, object]] = []
    player_match = {
        str(row["fangraphs_id"]): row for row in player_overlay.iter_rows(named=True)
    }
    for term in payroll.year_terms.iter_rows(named=True):
        player = player_match[str(term["fangraphs_id"])]
        year = int(term["payroll_year"])
        year_rows.append(
            {
                "season": int(term["season"]),
                "team_name": str(term["team_name"]),
                "player_id": player["player_id"],
                "fangraphs_id": str(term["fangraphs_id"]),
                "player_name": str(term["player_name"]),
                "payroll_year": year,
                "amount_dollars": term["amount_dollars"],
                "term_label": str(term["term_label"]),
                "clause_types": ",".join(
                    sorted(clause_years.get((str(term["fangraphs_id"]), year), set()))
                ),
                "overlay_status": str(player["overlay_status"]),
                "source_snapshot_id": str(term["source_snapshot_id"]),
            }
        )
    year_overlay = pl.DataFrame(year_rows, schema=CONTRACT_YEAR_OVERLAY_SCHEMA).sort(
        ["overlay_status", "player_name", "payroll_year"]
    )
    unresolved = player_overlay.filter(
        pl.col("overlay_status") != "accepted_contract_overlay"
    )
    accepted = player_overlay.filter(
        pl.col("overlay_status") == "accepted_contract_overlay"
    )
    if (
        accepted.drop_nulls("player_id")
        .group_by("player_id")
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("contract overlay has duplicate accepted player IDs")
    return ContractOverlay(
        players=player_overlay.sort(["overlay_status", "player_name"]),
        year_terms=year_overlay,
        unresolved_players=unresolved.sort("player_name"),
    )
