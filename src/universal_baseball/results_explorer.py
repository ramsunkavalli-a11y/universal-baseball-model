"""Build the local Phase 1 player-results explorer."""

from __future__ import annotations

from datetime import date, datetime
import html
import json
from pathlib import Path
from typing import Any

import polars as pl


MLB_ORGANIZATIONS = {
    108: "Angels",
    109: "Diamondbacks",
    110: "Orioles",
    111: "Red Sox",
    112: "Cubs",
    113: "Reds",
    114: "Guardians",
    115: "Rockies",
    116: "Tigers",
    117: "Astros",
    118: "Royals",
    119: "Dodgers",
    120: "Nationals",
    121: "Mets",
    133: "Athletics",
    134: "Pirates",
    135: "Padres",
    136: "Mariners",
    137: "Giants",
    138: "Cardinals",
    139: "Rays",
    140: "Rangers",
    141: "Blue Jays",
    142: "Twins",
    143: "Phillies",
    144: "Braves",
    145: "White Sox",
    146: "Marlins",
    147: "Yankees",
    158: "Brewers",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def build_explorer_payload(
    values: pl.DataFrame,
    annual: pl.DataFrame,
    names: pl.DataFrame,
    model_details: pl.DataFrame | None = None,
) -> dict[str, Any]:
    """Create a compact, browser-ready payload from canonical Phase 1 outputs."""
    required_values = {
        "player_id",
        "organization_id",
        "rights_state",
        "calculation_status",
        "expected_remaining_war",
        "expected_remaining_war_lower",
        "expected_remaining_war_upper",
        "expected_remaining_cost_dollars",
        "transferable_value_dollars",
        "transferable_value_lower_dollars",
        "transferable_value_upper_dollars",
        "coverage_tier",
        "checkpoint_id",
        "as_of_at_utc",
    }
    if missing := sorted(required_values - set(values.columns)):
        raise ValueError(f"value records missing fields: {missing}")
    required_annual = {
        "player_id",
        "season",
        "projected_war_mean",
        "projected_war_lower",
        "projected_war_upper",
        "control_status",
        "salary_cost_dollars",
        "discounted_contract_value_dollars",
        "discounted_contract_value_lower_dollars",
        "discounted_contract_value_upper_dollars",
        "calculation_status",
        "review_reason",
    }
    if missing := sorted(required_annual - set(annual.columns)):
        raise ValueError(f"annual economics missing fields: {missing}")
    if not {"player_id", "player_name"}.issubset(names.columns):
        raise ValueError("name source requires player_id and player_name")
    if values.get_column("player_id").n_unique() != values.height:
        raise ValueError("value records violate player grain")

    name_lookup = {
        int(row["player_id"]): str(row["player_name"])
        for row in names.select("player_id", "player_name")
        .drop_nulls("player_name")
        .unique("player_id", keep="first")
        .iter_rows(named=True)
    }
    detail_lookup = (
        {
            int(row["player_id"]): row
            for row in model_details.iter_rows(named=True)
        }
        if model_details is not None
        else {}
    )
    phase2 = "expected_controlled_war" in values.columns
    annual_lookup: dict[int, list[dict[str, Any]]] = {}
    annual_columns = [
        "season",
        "projected_war_mean",
        "projected_war_lower",
        "projected_war_upper",
        "control_status",
        "salary_cost_dollars",
        "discounted_contract_value_dollars",
        "discounted_contract_value_lower_dollars",
        "discounted_contract_value_upper_dollars",
        "calculation_status",
        "review_reason",
    ]
    for row in annual.sort(["player_id", "season"]).iter_rows(named=True):
        player_id = int(row["player_id"])
        annual_lookup.setdefault(player_id, []).append(
            {key: _json_value(row[key]) for key in annual_columns}
        )

    players: list[dict[str, Any]] = []
    for row in values.iter_rows(named=True):
        player_id = int(row["player_id"])
        organization_id = row["organization_id"]
        value_method = row.get("value_method") or "phase1_integrated_value"
        is_pre_mlb_value = value_method.endswith("pre_mlb_benchmark_value")
        detail = detail_lookup.get(player_id, {})
        players.append(
            {
                "id": player_id,
                "name": name_lookup.get(player_id, f"MLBAM {player_id}"),
                "organization_id": organization_id,
                "team": MLB_ORGANIZATIONS.get(organization_id, "No current club"),
                "rights": row["rights_state"],
                "status": row["calculation_status"],
                "coverage": row["coverage_tier"],
                "war": row.get("expected_controlled_war", row["expected_remaining_war"]),
                "projection_war": row.get(
                    "statsapi_projected_war", row["expected_remaining_war"]
                ),
                "war_low": row["expected_remaining_war_lower"],
                "war_high": row["expected_remaining_war_upper"],
                "cost": row["expected_remaining_cost_dollars"],
                "value": row["transferable_value_dollars"],
                "value_low": row["transferable_value_lower_dollars"],
                "value_high": row["transferable_value_upper_dollars"],
                "value_method": value_method,
                "model_fv": row.get("model_fv_display"),
                "model_fv_granular": row.get("model_fv_granular"),
                "model_role": row.get("model_role"),
                "model_player_type": row.get("model_player_type"),
                "talent_value": row.get("talent_benchmark_value_dollars"),
                "star_probability": row.get("star_outcome_probability"),
                "arrival_probability": row.get("model_arrival_probability"),
                "arrival_probability_source": row.get("arrival_probability_source"),
                "meaningful_role_probability": row.get(
                    "model_meaningful_role_probability"
                ),
                "established_role_probability": row.get(
                    "model_established_role_probability"
                ),
                "model_position": detail.get("primary_position"),
                "expected_workload": detail.get("three_tier_expected_workload"),
                "conditional_war_rate": detail.get("conditional_war_rate"),
                "conditional_war_rate_unit": detail.get("conditional_war_rate_unit"),
                "batting_runs_per_600": detail.get("batting_runs_per_600"),
                "baserunning_runs_per_600": detail.get("baserunning_runs_per_600"),
                "defense_runs_per_600": detail.get("defense_runs_per_600"),
                "positional_runs_per_600": detail.get("positional_runs_per_600"),
                "pitching_raa_per_800": detail.get(
                    "pitching_runs_above_average_per_800"
                ),
                "workload_war_p10": detail.get("workload_war_p10"),
                "workload_war_p50": detail.get("workload_war_p50"),
                "workload_war_p90": detail.get("workload_war_p90"),
                "workload_only_star_probability": detail.get(
                    "workload_only_star_probability"
                ),
                "research_mean_value": detail.get("research_mean_value_dollars"),
                "research_value_p10": detail.get("research_p10_value_dollars"),
                "research_value_median": detail.get(
                    "research_median_value_dollars"
                ),
                "research_value_p90": detail.get("research_p90_value_dollars"),
                "research_mean_war": detail.get("research_mean_controlled_war"),
                "research_war_p10": detail.get("research_p10_controlled_war"),
                "research_war_median": detail.get("research_median_controlled_war"),
                "research_war_p90": detail.get("research_p90_controlled_war"),
                "research_expected_cost": detail.get(
                    "research_expected_cost_dollars"
                ),
                "research_arrival_probability": detail.get(
                    "research_arrival_probability"
                ),
                "research_bust_probability": detail.get("research_bust_probability"),
                "research_regular_probability": detail.get(
                    "research_regular_probability"
                ),
                "research_star_probability": detail.get("research_star_probability"),
                "is_pre_mlb_value": is_pre_mlb_value,
                "years": [] if is_pre_mlb_value else annual_lookup.get(player_id, []),
            }
        )
    players.sort(
        key=lambda player: (
            player["value"] is not None,
            player["value"] if player["value"] is not None else float("-inf"),
        ),
        reverse=True,
    )
    for rank, player in enumerate(
        (player for player in players if player["value"] is not None), start=1
    ):
        player["rank"] = rank

    as_of = values.item(0, "as_of_at_utc") if values.height else None
    return {
        "meta": {
            "checkpoint": values.item(0, "checkpoint_id") if values.height else "",
            "as_of": _json_value(as_of),
            "player_count": values.height,
            "available_count": values.filter(
                pl.col("calculation_status") == "available"
            ).height,
            "review_count": values.filter(pl.col("calculation_status") != "available").height,
            "total_war": values.get_column("expected_remaining_war").sum(),
            "total_value": values.get_column("transferable_value_dollars").sum(),
            "phase": "Phase 2 preview" if phase2 else "Phase 1",
            "warning": (
                "Private Phase 2 preview. MLB values use corrected market-tier and "
                "sequential-decision logic. Model FV comes only from our projected "
                "production and a provisional nested career hurdle; publication "
                "player grades are validation only."
                if phase2
                else "Research view only. Values use Phase 1 assumptions, uncalibrated "
                "reference ranges and current CBA planning rules."
            ),
        },
        "players": players,
    }


def render_explorer_html(payload: dict[str, Any]) -> str:
    """Render one portable HTML file with its data embedded."""
    payload_json = json.dumps(payload, separators=(",", ":"), default=_json_value).replace(
        "</", "<\\/"
    )
    template_path = Path(__file__).with_name("results_explorer.html")
    template = template_path.read_text(encoding="utf-8")
    return template.replace("__EXPLORER_DATA__", payload_json).replace(
        "__CHECKPOINT__", html.escape(str(payload["meta"]["checkpoint"]))
    )


def write_explorer(
    values_path: Path,
    annual_path: Path,
    names_path: Path,
    output_path: Path,
    *,
    model_details: pl.DataFrame | None = None,
) -> dict[str, Any]:
    payload = build_explorer_payload(
        pl.read_parquet(values_path),
        pl.read_parquet(annual_path),
        pl.read_parquet(names_path),
        model_details,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_explorer_html(payload), encoding="utf-8")
    return payload
