"""Join whole-player expected WAR to dated control and contract terms."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from universal_baseball.contract_economics import ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA
from universal_baseball.team_control import SERVICE_DAYS_PER_YEAR


PROJECTION_SOURCE_ID = "phase1_hitter_pitcher_expected_war_paths_2026_09_08"
UNCERTAINTY_PROJECTION_SOURCE_ID = (
    "phase1_hitter_pitcher_expected_war_with_uncertainty_2026_09_08"
)


@dataclass(frozen=True, slots=True)
class ContractEconomicsInputBuild:
    annual_inputs: pl.DataFrame
    coverage: dict[str, int]


def _projection_component(frame: pl.DataFrame, label: str) -> pl.DataFrame:
    required = {"player_id", "season", "expected_war"}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"{label} expected-WAR paths missing fields: {missing}")
    result = frame.select("player_id", "season", "expected_war")
    if result.group_by("player_id", "season").len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} expected-WAR paths violate player-season grain")
    if result.filter(~pl.col("expected_war").is_finite()).height:
        raise ValueError(f"{label} expected-WAR paths contain invalid WAR")
    return result


def _arbitration_class(status: str, service_days_before_year: int) -> int | None:
    if status == "super_two_eligible":
        return 1
    if status not in {"arbitration", "arbitration_eligible"}:
        return None
    service_years = int(service_days_before_year) // SERVICE_DAYS_PER_YEAR
    return max(1, min(4, service_years - 2))


def build_future_contract_economics_inputs(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    control_path: pl.DataFrame,
    contract_years: pl.DataFrame,
    war_uncertainty: pl.DataFrame | None = None,
) -> ContractEconomicsInputBuild:
    """Build annual inputs without inventing market assumptions."""

    hitter = _projection_component(hitter_paths, "hitter")
    pitcher = _projection_component(pitcher_paths, "pitcher")
    whole_player = pl.concat([hitter, pitcher]).group_by("player_id", "season").agg(
        pl.col("expected_war").sum().alias("projected_war_mean")
    )
    projection_source_id = PROJECTION_SOURCE_ID
    if war_uncertainty is None:
        whole_player = whole_player.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("projected_war_lower"),
            pl.lit(None, dtype=pl.Float64).alias("projected_war_upper"),
        )
    else:
        required_uncertainty = {
            "player_id", "season", "projected_war_mean",
            "projected_war_lower", "projected_war_upper",
        }
        if missing := sorted(required_uncertainty - set(war_uncertainty.columns)):
            raise ValueError(f"WAR uncertainty missing economics fields: {missing}")
        uncertainty = war_uncertainty.select(sorted(required_uncertainty)).rename(
            {"projected_war_mean": "uncertainty_war_mean"}
        )
        if uncertainty.group_by("player_id", "season").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError("WAR uncertainty violates player-season grain")
        projection_keys = set(whole_player.select("player_id", "season").iter_rows())
        uncertainty_keys = set(uncertainty.select("player_id", "season").iter_rows())
        if uncertainty_keys != projection_keys:
            raise ValueError("WAR uncertainty coverage differs from whole-player projections")
        whole_player = whole_player.join(
            uncertainty, on=["player_id", "season"], how="inner", validate="1:1"
        )
        if whole_player.filter(
            (pl.col("projected_war_mean") - pl.col("uncertainty_war_mean")).abs()
            > 1e-10 * pl.max_horizontal(pl.lit(1.0), pl.col("projected_war_mean").abs())
        ).height:
            raise ValueError("WAR uncertainty means differ from whole-player projections")
        whole_player = whole_player.drop("uncertainty_war_mean")
        projection_source_id = UNCERTAINTY_PROJECTION_SOURCE_ID
    control_required = (
        "as_of_date",
        "player_id",
        "organization_id",
        "control_year",
        "service_days_before_year",
        "control_status",
        "projection_basis",
    )
    if missing := sorted(set(control_required) - set(control_path.columns)):
        raise ValueError(f"control path missing economics fields: {missing}")
    control = control_path.select(*control_required).rename({"control_year": "season"})
    if control.group_by("player_id", "season").len().filter(pl.col("len") != 1).height:
        raise ValueError("control path violates player-season grain")
    term_required = (
        "player_id",
        "organization_id",
        "payroll_year",
        "amount_dollars",
        "overlay_status",
        "source_snapshot_id",
    )
    if missing := sorted(set(term_required) - set(contract_years.columns)):
        raise ValueError(f"contract years missing economics fields: {missing}")
    terms = contract_years.filter(
        pl.col("overlay_status") == "accepted_contract_overlay"
    ).select(
        "player_id", "organization_id",
        pl.col("payroll_year").alias("season"),
        pl.col("amount_dollars").alias("known_salary_dollars"),
        pl.col("source_snapshot_id").alias("term_source_id"),
    )
    if terms.group_by("player_id", "organization_id", "season").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("contract years violate player-organization-season grain")
    joined = control.join(
        whole_player, on=["player_id", "season"], how="left"
    ).join(
        terms, on=["player_id", "organization_id", "season"], how="left"
    )
    available = joined.filter(pl.col("projected_war_mean").is_not_null())
    rows = []
    for row in available.iter_rows(named=True):
        rows.append(
            {
                "as_of_date": row["as_of_date"],
                "player_id": int(row["player_id"]),
                "organization_id": int(row["organization_id"]),
                "season": int(row["season"]),
                "projected_war_mean": float(row["projected_war_mean"]),
                "projected_war_lower": row["projected_war_lower"],
                "projected_war_upper": row["projected_war_upper"],
                "control_status": str(row["control_status"]),
                "known_salary_dollars": row["known_salary_dollars"],
                "buyout_dollars": None,
                "arbitration_class": _arbitration_class(
                    str(row["control_status"]), int(row["service_days_before_year"])
                ),
                "projection_source_id": projection_source_id,
                "contract_source_id": str(
                    row["term_source_id"] or row["projection_basis"]
                ),
            }
        )
    annual = pl.DataFrame(rows, schema=ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA).sort(
        ["player_id", "organization_id", "season"]
    )
    projection_keys = set(whole_player.select("player_id", "season").iter_rows())
    control_keys = set(control.select("player_id", "season").iter_rows())
    return ContractEconomicsInputBuild(
        annual_inputs=annual,
        coverage={
            "whole_player_projection_rows": whole_player.height,
            "control_rows": control.height,
            "economics_input_rows": annual.height,
            "projection_rows_without_control": len(projection_keys - control_keys),
            "control_rows_without_projection": len(control_keys - projection_keys),
            "known_salary_rows": annual.filter(
                pl.col("known_salary_dollars").is_not_null()
            ).height,
            "uncertainty_rows": annual.filter(
                pl.col("projected_war_lower").is_not_null()
                & pl.col("projected_war_upper").is_not_null()
            ).height,
            "option_rows_missing_buyout": annual.filter(
                pl.col("control_status").is_in(
                    ["club_option", "player_option", "mutual_option", "vesting_option"]
                )
                & pl.col("buyout_dollars").is_null()
            ).height,
        },
    )
