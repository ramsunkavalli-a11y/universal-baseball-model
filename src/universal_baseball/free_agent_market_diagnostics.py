"""Diagnostics for the independent one-year free-agent market check."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.free_agent_market import (
    FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR,
)


def build_one_year_market_diagnostics(forecasts: pl.DataFrame) -> dict[str, object]:
    """Compare the clean one-year sample with the broader published market."""

    required = {
        "free_agent_year",
        "projected_war",
        "fangraphs_projected_war",
        "contract_effective_total_dollars",
        "major_league_minimum_salary",
        "market_fit_eligible",
    }
    if missing := sorted(required - set(forecasts.columns)):
        raise ValueError(f"one-year market forecasts missing columns: {missing}")
    eligible = forecasts.filter(
        pl.col("market_fit_eligible") & (pl.col("projected_war") > 0)
    ).with_columns(
        (
            pl.col("contract_effective_total_dollars")
            - pl.col("major_league_minimum_salary")
        ).alias("salary_above_minimum")
    )
    if eligible.is_empty():
        raise ValueError("one-year market diagnostic has no positive-WAR rows")
    annual = []
    for group in eligible.partition_by("free_agent_year", maintain_order=True):
        year = int(group.item(0, "free_agent_year"))
        war = float(group.get_column("projected_war").sum())
        salary = float(group.get_column("salary_above_minimum").sum())
        internal_rate = salary / war
        published_rate = FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[year]
        annual.append(
            {
                "free_agent_year": year,
                "one_year_rows": group.height,
                "one_year_projected_war": war,
                "one_year_salary_above_minimum": salary,
                "one_year_dollars_per_war": internal_rate,
                "published_all_market_dollars_per_war": published_rate,
                "one_year_to_all_market_rate_ratio": internal_rate / published_rate,
            }
        )
    current = eligible.filter(
        (pl.col("free_agent_year") == 2026)
        & pl.col("fangraphs_projected_war").is_not_null()
    )
    ours = float(current.get_column("projected_war").sum())
    fangraphs = float(current.get_column("fangraphs_projected_war").sum())
    correlation = float(
        current.select(pl.corr("projected_war", "fangraphs_projected_war")).item()
    )
    mae = float(
        current.select(
            (pl.col("projected_war") - pl.col("fangraphs_projected_war"))
            .abs()
            .mean()
        ).item()
    )
    if not all(math.isfinite(value) for value in (ours, fangraphs, correlation, mae)):
        raise RuntimeError("one-year market diagnostics are nonfinite")
    return {
        "positive_war_rows": eligible.height,
        "nonpositive_war_rows_excluded": forecasts.filter(
            pl.col("market_fit_eligible") & (pl.col("projected_war") <= 0)
        ).height,
        "annual": annual,
        "current_2026_projection_comparison": {
            "rows": current.height,
            "internal_projected_war": ours,
            "fangraphs_projected_war": fangraphs,
            "aggregate_war_difference_share": (ours - fangraphs) / fangraphs,
            "player_correlation": correlation,
            "player_mean_absolute_error_war": mae,
        },
        "decision": (
            "independent scale check only; one-year top-50 rows do not identify the "
            "full-market star premium"
        ),
    }
