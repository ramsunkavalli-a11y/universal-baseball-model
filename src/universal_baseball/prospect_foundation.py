"""Build the inspectable prospect-talent foundation without assigning FV."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.results_explorer import MLB_ORGANIZATIONS


def _safe_rate(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def _raw_hitter_levels(history: pl.DataFrame, season: int) -> dict[int, list[dict[str, Any]]]:
    source = history.filter(
        (pl.col("season") == season)
        & (pl.col("level_group") != "MLB")
        & (pl.col("plate_appearances") > 0)
    )
    grouped = source.group_by("player_id", "level_group").agg(
        *(pl.col(column).sum() for column in (
            "plate_appearances", "at_bats", "hits", "doubles", "triples",
            "home_runs", "base_on_balls", "intentional_walks", "hit_by_pitch",
            "strike_outs", "sac_flies",
        ))
    )
    result: dict[int, list[dict[str, Any]]] = {}
    for row in grouped.sort(
        ["player_id", "plate_appearances"], descending=[False, True]
    ).iter_rows(named=True):
        at_bats = float(row["at_bats"])
        pa = float(row["plate_appearances"])
        total_bases = (
            float(row["hits"]) + float(row["doubles"])
            + 2.0 * float(row["triples"]) + 3.0 * float(row["home_runs"])
        )
        obp_denominator = (
            at_bats + float(row["base_on_balls"])
            + float(row["hit_by_pitch"]) + float(row["sac_flies"])
        )
        result.setdefault(int(row["player_id"]), []).append({
            "level": str(row["level_group"]),
            "pa": int(row["plate_appearances"]),
            "avg": _safe_rate(float(row["hits"]), at_bats),
            "obp": _safe_rate(
                float(row["hits"]) + float(row["base_on_balls"])
                + float(row["hit_by_pitch"]), obp_denominator,
            ),
            "slg": _safe_rate(total_bases, at_bats),
            "strikeout_rate": _safe_rate(float(row["strike_outs"]), pa),
            "walk_rate": _safe_rate(
                float(row["base_on_balls"]) - float(row["intentional_walks"]), pa
            ),
        })
    return result


def _raw_pitcher_levels(history: pl.DataFrame, season: int) -> dict[int, list[dict[str, Any]]]:
    source = history.filter(
        (pl.col("season") == season)
        & (pl.col("level_group") != "MLB")
        & (pl.col("batters_faced") > 0)
    )
    grouped = source.group_by("player_id", "level_group").agg(
        *(pl.col(column).sum() for column in (
            "batters_faced", "strike_outs", "base_on_balls",
            "intentional_walks", "hit_batters", "home_runs",
        ))
    )
    result: dict[int, list[dict[str, Any]]] = {}
    for row in grouped.sort(
        ["player_id", "batters_faced"], descending=[False, True]
    ).iter_rows(named=True):
        bf = float(row["batters_faced"])
        result.setdefault(int(row["player_id"]), []).append({
            "level": str(row["level_group"]),
            "bf": int(row["batters_faced"]),
            "strikeout_rate": _safe_rate(float(row["strike_outs"]), bf),
            "walk_rate": _safe_rate(
                float(row["base_on_balls"]) - float(row["intentional_walks"]), bf
            ),
            "hit_batter_rate": _safe_rate(float(row["hit_batters"]), bf),
            "home_run_rate": _safe_rate(float(row["home_runs"]), bf),
        })
    return result


def _row_lookup(frame: pl.DataFrame, *keys: str) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {
        tuple(row[key] for key in keys): row
        for row in frame.iter_rows(named=True)
    }


def _raw_history_workload(
    history: pl.DataFrame, *, season: int, player_type: str
) -> dict[int, int]:
    exposure = "plate_appearances" if player_type == "hitter" else "batters_faced"
    return {
        int(row["player_id"]): int(row["history_workload"])
        for row in (
            history.filter(
                pl.col("season").is_between(season - 2, season)
                & (pl.col("level_group") != "MLB")
                & (pl.col(exposure) > 0)
            )
            .group_by("player_id")
            .agg(pl.col(exposure).sum().alias("history_workload"))
            .iter_rows(named=True)
        )
    }


def build_prospect_foundation_payload(
    peak_hitters: pl.DataFrame,
    peak_pitchers: pl.DataFrame,
    future_hitters: pl.DataFrame,
    future_pitchers: pl.DataFrame,
    hitter_arrival: pl.DataFrame,
    pitcher_arrival: pl.DataFrame,
    names: pl.DataFrame,
    raw_hitting: pl.DataFrame,
    raw_pitching: pl.DataFrame,
    hitter_comparables: pl.DataFrame | None = None,
    pitcher_comparables: pl.DataFrame | None = None,
    hitter_upside: pl.DataFrame | None = None,
    pitcher_upside: pl.DataFrame | None = None,
    hitter_six_year_value: pl.DataFrame | None = None,
    pitcher_six_year_value: pl.DataFrame | None = None,
    *,
    season: int,
) -> dict[str, Any]:
    """Join validated talent stages while keeping FV and value unavailable."""

    name_lookup = _row_lookup(
        names.select("player_id", "player_name", "organization_id").unique("player_id"),
        "player_id",
    )
    future_lookup = _row_lookup(
        pl.concat([future_hitters, future_pitchers], how="diagonal_relaxed"),
        "player_id", "player_type", "horizon_years",
    )
    peak_lookup = _row_lookup(
        pl.concat([peak_hitters, peak_pitchers], how="diagonal_relaxed"),
        "player_id", "player_type",
    )
    raw_lookup = {
        "hitter": _raw_hitter_levels(raw_hitting, season),
        "pitcher": _raw_pitcher_levels(raw_pitching, season),
    }
    history_workload_lookup = {
        "hitter": _raw_history_workload(
            raw_hitting, season=season, player_type="hitter"
        ),
        "pitcher": _raw_history_workload(
            raw_pitching, season=season, player_type="pitcher"
        ),
    }
    arrivals = pl.concat([
        hitter_arrival.with_columns(pl.lit("hitter").alias("player_type")),
        pitcher_arrival.with_columns(pl.lit("pitcher").alias("player_type")),
    ], how="diagonal_relaxed")
    comparable_lookup = {
        "hitter": _row_lookup(
            hitter_comparables
            if hitter_comparables is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
        "pitcher": _row_lookup(
            pitcher_comparables
            if pitcher_comparables is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
    }
    upside_lookup = {
        "hitter": _row_lookup(
            hitter_upside
            if hitter_upside is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
        "pitcher": _row_lookup(
            pitcher_upside
            if pitcher_upside is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
    }
    six_year_lookup = {
        "hitter": _row_lookup(
            hitter_six_year_value
            if hitter_six_year_value is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
        "pitcher": _row_lookup(
            pitcher_six_year_value
            if pitcher_six_year_value is not None
            else pl.DataFrame(schema={"player_id": pl.Int64}),
            "player_id",
        ),
    }
    players: list[dict[str, Any]] = []
    for arrival in arrivals.iter_rows(named=True):
        player_id = int(arrival["player_id"])
        player_type = str(arrival["player_type"])
        peak = peak_lookup.get((player_id, player_type))
        if peak is None:
            continue
        identity = name_lookup.get((player_id,), {})
        one_year = future_lookup.get((player_id, player_type, 1), {})
        two_year = future_lookup.get((player_id, player_type, 2), {})
        evidence = float(peak.get("effective_evidence") or 0.0)
        age = peak.get("age_years")
        peak_supported = (
            peak.get("ranking_status") == "ranked"
            and age is not None
            and 16.0 <= float(age) <= 23.0
        )
        comparable = comparable_lookup[player_type].get((player_id,), {})
        upside = upside_lookup[player_type].get((player_id,), {})
        six_year = six_year_lookup[player_type].get((player_id,), {})
        conditional_rate_validated = (
            player_type == "hitter"
            and bool(comparable.get("historical_conditional_rate_supported"))
        )
        raw_levels = raw_lookup[player_type].get(player_id, [])
        current_workload_key = "pa" if player_type == "hitter" else "bf"
        players.append({
            "key": f"{player_id}:{player_type}",
            "id": player_id,
            "name": identity.get("player_name") or peak.get("player_name") or f"MLBAM {player_id}",
            "organization_id": identity.get("organization_id"),
            "team": MLB_ORGANIZATIONS.get(identity.get("organization_id"), "No current club"),
            "player_type": player_type,
            "role": peak.get("current_primary_position") if player_type == "hitter" else peak.get("as_of_role"),
            "age": age,
            "listed_level": arrival.get("level_tier"),
            "primary_level": arrival.get("primary_level_tier"),
            "primary_level_share": arrival.get("primary_level_workload_share"),
            "level_progression": arrival.get("level_progression"),
            "development_seasons": arrival.get("development_history_seasons"),
            "modeled_six_year_arrival_probability": arrival.get(
                "predicted_six_year_arrival_probability"
            ),
            "comparable_six_year_arrival_probability": six_year.get(
                "comparable_arrival_probability_6y"
            ),
            "conditional_partial_war_6y": six_year.get(
                "conditional_partial_war_6y"
            ),
            "expected_partial_war_6y": six_year.get("expected_partial_war_6y"),
            "six_year_historical_support": six_year.get(
                "historical_conditional_arrival_support"
            ),
            "six_year_comparable_players": six_year.get(
                "historical_comparable_players"
            ),
            "six_year_value_method": six_year.get("six_year_value_method"),
            "evidence": evidence,
            "current_raw_workload": sum(
                int(level[current_workload_key]) for level in raw_levels
            ),
            "history_raw_workload": history_workload_lookup[player_type].get(
                player_id, 0
            ),
            "reliability": peak.get("reliability"),
            "evidence_band": peak.get("evidence_band"),
            "present_runs_rate": peak.get("present_runs_rate"),
            "one_year_runs_rate": one_year.get("projected_runs_rate"),
            "two_year_runs_rate": two_year.get("projected_runs_rate"),
            "peak_runs_rate": peak.get("peak_runs_rate") if peak_supported else None,
            "peak_runs_rate_unit": 600 if player_type == "hitter" else 800,
            "peak_above_average_probability": upside.get(
                "peak_above_average_probability"
            ) if peak_supported else None,
            "peak_impact_probability": upside.get(
                "peak_impact_probability"
            ) if peak_supported else None,
            "peak_talent_validated": bool(
                peak_supported
                and peak.get("peak_validation_status") == "historical_gate_passed"
            ),
            "peak_rank": peak.get("prospect_peak_rate_rank") if peak_supported else None,
            "peak_supported": peak_supported,
            "foundation_status": (
                "unresolved_thin_evidence"
                if evidence < 100.0
                else "supported_peak"
                if peak_supported
                else "peak_outside_supported_age"
            ),
            "recent_direction_runs": peak.get("recent_component_direction_runs"),
            "pitch_process_applied": peak.get("pitch_process_applied"),
            "pitch_process_runs_change": peak.get("pitch_process_runs_change"),
            "raw_levels": raw_levels,
            "historical_comparable_level": comparable.get(
                "historical_comparable_level"
            ),
            "historical_outcome_scope": comparable.get("historical_outcome_scope"),
            "historical_comparable_players": comparable.get(
                "historical_comparable_players"
            ),
            "historical_arrivals_4y": comparable.get("historical_arrivals_4y"),
            "historical_conditional_arrival_support": comparable.get(
                "historical_conditional_arrival_support"
            ),
            "historical_arrival_rate_4y": comparable.get(
                "historical_arrival_rate_4y"
            ),
            "historical_conditional_component_war_per_600": comparable.get(
                "historical_conditional_component_war_per_600"
            ),
            "historical_conditional_component_war_rate": comparable.get(
                "historical_conditional_component_war_rate"
            ) if conditional_rate_validated else None,
            "historical_conditional_rate_basis": comparable.get(
                "historical_conditional_rate_basis"
            ) if conditional_rate_validated else None,
            "historical_conditional_rate_validated": conditional_rate_validated,
            "historical_conditional_component_war_4y": comparable.get(
                "historical_conditional_component_war_4y"
            ),
            "historical_component_war_4y": comparable.get(
                "historical_component_war_4y"
            ),
            "historical_component_war_4y_p10": comparable.get(
                "historical_component_war_4y_p10"
            ),
            "historical_component_war_4y_median": comparable.get(
                "historical_component_war_4y_median"
            ),
            "historical_component_war_4y_p90": comparable.get(
                "historical_component_war_4y_p90"
            ),
            "historical_conditional_component_war_4y_p10": comparable.get(
                "historical_conditional_component_war_4y_p10"
            ),
            "historical_conditional_component_war_4y_median": comparable.get(
                "historical_conditional_component_war_4y_median"
            ),
            "historical_conditional_component_war_4y_p90": comparable.get(
                "historical_conditional_component_war_4y_p90"
            ),
            "historical_positive_component_war_4y": comparable.get(
                "historical_positive_component_war_4y"
            ),
            "historical_impact_rate_4y": comparable.get(
                "historical_impact_rate_4y"
            ),
            "historical_three_war_rate_4y": comparable.get(
                "historical_three_war_rate_4y"
            ),
            "historical_six_war_rate_4y": comparable.get(
                "historical_six_war_rate_4y"
            ),
            "historical_expectation_identity_error": comparable.get(
                "historical_expectation_identity_error"
            ),
            "outcome_status": (
                "historical_outcome_available"
                if comparable.get("historical_comparable_players")
                else "historical_outcome_pending"
            ),
            "fv": None,
            "expected_war": None,
            "value": None,
        })
    players.sort(key=lambda row: (
        row["peak_rank"] is None,
        row["peak_rank"] if row["peak_rank"] is not None else 10**9,
        row["name"], row["player_type"],
    ))
    return {
        "meta": {
            "season": season,
            "player_count": len(players),
            "status": "foundation_only_fv_withdrawn",
            "warning": (
                "Prospect FV, whole-player expected WAR and value remain withdrawn "
                "until the complete outcome and control-year model passes."
            ),
            "output_contract": {
                "raw_workload": "undiscounted official PA or BF",
                "translation_confidence": "separate diagnostic; never an eligibility cutoff",
                "conditional_talent": (
                    "validated age-24-to-26 peak component run rate plus above-average "
                    "and impact probabilities; comparable pitcher WAR rate remains withheld"
                ),
                "arrival": (
                    "historical six-year comparable arrival probability, validated "
                    "without using public prospect grades"
                ),
                "conditional_outcome": (
                    "six-year batting- or pitching-plus-replacement partial WAR among "
                    "historical MLB arrivals"
                ),
                "risk_adjusted_outcome": (
                    "arrival probability multiplied by conditional partial WAR; "
                    "non-arrivals remain zero"
                ),
            },
        },
        "players": players,
    }


def write_prospect_foundation_explorer(
    payload: dict[str, Any], template_path: Path, output_path: Path
) -> None:
    def json_safe(value: Any) -> Any:
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [json_safe(item) for item in value]
        return value

    rendered = template_path.read_text(encoding="utf-8").replace(
        "__EXPLORER_DATA__",
        json.dumps(
            json_safe(payload),
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).replace("</", "<\\/"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
