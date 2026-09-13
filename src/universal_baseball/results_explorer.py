"""Build the local Phase 1 player-results explorer."""

from __future__ import annotations

from datetime import date, datetime
import html
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.prospect_value import display_fv_label


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
        player = {
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
                "calculated_contract_years": row.get("calculated_contract_years"),
                "review_contract_years": row.get("review_contract_years"),
                "calculated_years_cost": row.get("calculated_years_cost_dollars"),
                "calculated_years_value": row.get("calculated_years_value_dollars"),
                "calculated_years_value_low": row.get(
                    "calculated_years_value_lower_dollars"
                ),
                "calculated_years_value_high": row.get(
                    "calculated_years_value_upper_dollars"
                ),
                "value": row["transferable_value_dollars"],
                "value_low": row["transferable_value_lower_dollars"],
                "value_high": row["transferable_value_upper_dollars"],
                "value_method": value_method,
                "value_review_reason": row.get("value_review_reason"),
                "model_fv": row.get("model_fv_display"),
                "model_fv_granular": row.get("model_fv_granular"),
                "model_fv_label": (
                    None
                    if row.get("model_fv_granular") is None
                    else display_fv_label(float(row["model_fv_granular"]))
                ),
                "conditional_career_war_if_arrived": detail.get(
                    "conditional_career_war_if_arrived"
                ),
                "skill_evidence_tier": detail.get("skill_evidence_tier"),
                "effective_skill_evidence": detail.get("effective_skill_evidence"),
                "skill_reliability": detail.get("skill_reliability"),
                "listed_level": detail.get("level_tier"),
                "primary_evidence_level": detail.get("primary_level_tier"),
                "primary_level_workload_share": detail.get(
                    "primary_level_workload_share"
                ),
                "level_progression": detail.get("level_progression"),
                "development_history_seasons": detail.get(
                    "development_history_seasons"
                ),
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
                "peak_talent_runs_rate": detail.get("peak_talent_runs_rate"),
                "peak_above_average_probability": detail.get(
                    "peak_above_average_probability"
                ),
                "peak_impact_probability": detail.get("peak_impact_probability"),
                "pitch_process_applied": detail.get("pitch_process_applied"),
                "pitch_process_runs_change": detail.get(
                    "pitch_process_runs_change"
                ),
                "process_whiff": detail.get("process_whiff"),
                "process_strike": detail.get("process_strike"),
                "process_swing": detail.get("process_swing"),
                "process_ppbf": detail.get("process_ppbf"),
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
        if is_pre_mlb_value:
            player.update({
                "status": "review",
                "coverage": "prospect_model_withdrawn",
                "war": None,
                "projection_war": None,
                "war_low": None,
                "war_high": None,
                "cost": None,
                "value": None,
                "value_low": None,
                "value_high": None,
                "value_review_reason": (
                    "Prospect FV, WAR and value are withdrawn pending a complete "
                    "historical outcome validation."
                ),
                "model_fv": None,
                "model_fv_granular": None,
                "model_fv_label": None,
                "talent_value": None,
                "star_probability": None,
            })
        players.append(player)
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
            "available_count": sum(
                player["status"] == "available" for player in players
            ),
            "review_count": sum(
                player["status"] != "available" for player in players
            ),
            "total_war": sum(
                float(player["war"]) for player in players
                if player["war"] is not None
            ),
            "total_value": sum(
                float(player["value"]) for player in players
                if player["value"] is not None
            ),
            "phase": "Phase 2 preview" if phase2 else "Phase 1",
            "warning": (
                "Private Phase 2 preview. MLB values use corrected market-tier and "
                "sequential-decision and workload logic. Prospect FV, WAR and value "
                "are withdrawn pending complete historical outcome validation."
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


def render_talent_value_explorer_html(payload: dict[str, Any]) -> str:
    """Render the prospect talent-versus-value view as one portable file."""

    payload_json = json.dumps(payload, separators=(",", ":"), default=_json_value).replace(
        "</", "<\\/"
    )
    template_path = Path(__file__).with_name("talent_value_explorer.html")
    template = template_path.read_text(encoding="utf-8")
    return template.replace("__EXPLORER_DATA__", payload_json).replace(
        "__CHECKPOINT__", html.escape(str(payload["meta"]["checkpoint"]))
    )


def write_talent_value_explorer(
    values_path: Path,
    annual_path: Path,
    names_path: Path,
    output_path: Path,
    *,
    model_details: pl.DataFrame,
) -> dict[str, Any]:
    """Write the separate prospect talent, risk, and value explorer."""

    payload = build_explorer_payload(
        pl.read_parquet(values_path),
        pl.read_parquet(annual_path),
        pl.read_parquet(names_path),
        model_details,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_talent_value_explorer_html(payload), encoding="utf-8"
    )
    return payload
